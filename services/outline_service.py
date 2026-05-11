"""PPT 大纲生成服务。

OutlineService 把用户主题、场景、页数、风格和 RAG 检索上下文组装成提示词，
调用大模型生成稳定 JSON，再校验成 PPTPlan。
"""

import json

from pydantic import ValidationError

from config.settings import DEFAULT_LANGUAGE
from models.ppt_schema import PPTPlan, SUPPORTED_LAYOUT_TYPES
from services.llm_service import LLMService
from utils.json_utils import try_parse_json
from utils.logger import get_logger


logger = get_logger(__name__)


class OutlineService:
    """面向业务层的大纲生成服务。"""

    def __init__(self):
        self.llm_service = LLMService()

    def generate_plan(
        self,
        topic: str,
        scene: str,
        page_count: int,
        style: str,
        retrieval_context: str = "",
    ) -> PPTPlan:
        """生成可编辑、可渲染的 PPTPlan。"""

        system_prompt, user_prompt = self._build_plan_prompt(
            topic=topic,
            scene=scene,
            page_count=page_count,
            style=style,
            retrieval_context=retrieval_context,
        )
        raw_output = self.llm_service.invoke(system_prompt, user_prompt)
        ok, parsed_or_error = try_parse_json(raw_output)
        if ok:
            return self._validate_plan(parsed_or_error)

        logger.warning("首次 JSON 解析失败，尝试修复: %s", parsed_or_error)
        repaired = self.repair_json(raw_output)
        ok2, parsed_or_error2 = try_parse_json(repaired)
        if ok2:
            return self._validate_plan(parsed_or_error2)
        raise ValueError(f"模型输出无法解析为 JSON: {parsed_or_error2}")

    def repair_json(self, raw_output: str) -> str:
        """让模型只修复 JSON 格式，不重写内容。"""

        system_prompt = (
            "你是 JSON 修复助手。你只输出合法 JSON 对象，不要输出解释、Markdown 或代码块。"
        )
        user_prompt = (
            "请把下面文本修复为合法 JSON。字段必须包含 title、subtitle、slides；"
            "slides 是数组，每项包含 page_no、page_title、layout_type、bullets、"
            "speaker_notes、image_keywords。\n\n"
            f"待修复内容：\n{raw_output}"
        )
        return self.llm_service.invoke(system_prompt, user_prompt)

    @staticmethod
    def _validate_plan(payload: dict) -> PPTPlan:
        """把普通 dict 校验为 PPTPlan，并补齐页码。"""

        try:
            plan = PPTPlan.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"PPT 大纲结构校验失败: {exc}") from exc
        if not plan.pages:
            raise ValueError("模型未返回任何 PPT 页面")
        for index, page in enumerate(plan.pages, start=1):
            page.page_no = index
        return plan

    @staticmethod
    def _build_plan_prompt(
        topic: str,
        scene: str,
        page_count: int,
        style: str,
        retrieval_context: str,
    ) -> tuple[str, str]:
        """构造生成大纲的 system/user prompt。"""

        system_prompt = (
            "你是资深演示文稿策划专家，擅长把资料整理成结构清晰、适合答辩展示的 PPT。"
            f"默认输出语言为{DEFAULT_LANGUAGE}。"
            "你必须输出严格 JSON 对象，不要输出 JSON 以外的任何内容。"
        )

        context_part = retrieval_context.strip() or "无参考资料，基于主题进行合理生成。"
        schema_hint = {
            "title": "基于大模型的 PPT 自动生成系统",
            "subtitle": scene,
            "slides": [
                {
                    "page_no": 1,
                    "page_title": "研究背景",
                    "layout_type": "cover",
                    "bullets": ["传统 PPT 制作效率较低", "大模型具备内容生成能力"],
                    "speaker_notes": "本页主要介绍研究背景。",
                    "image_keywords": ["AI presentation", "large language model"],
                }
            ],
        }
        layouts = ", ".join(sorted(SUPPORTED_LAYOUT_TYPES))

        user_prompt = (
            f"主题：{topic}\n"
            f"使用场景：{scene}\n"
            f"目标页数：{page_count}\n"
            f"视觉风格：{style}\n"
            f"参考资料上下文：\n{context_part}\n\n"
            "生成要求：\n"
            "1. slides 数量必须尽量等于目标页数，允许最多偏差 1 页。\n"
            "2. 每页必须有 layout_type，且只能从以下值选择："
            f"{layouts}。\n"
            "3. 毕业答辩或课程汇报建议包含：封面、目录、背景、需求、方案、实现、测试/效果、总结、致谢。\n"
            "4. bullets 每页 3 到 5 条，内容要具体，不要空泛。\n"
            "5. speaker_notes 写成答辩时可以照着讲的备注。\n"
            "6. image_keywords 输出 2 到 4 个英文短语，用于自动配图。\n"
            "7. 如果有参考资料，必须优先吸收资料中的事实、术语和流程，体现检索增强而不是凭空生成。\n"
            "8. 只输出 JSON 对象。\n\n"
            f"输出结构示例：\n{json.dumps(schema_hint, ensure_ascii=False)}"
        )
        return system_prompt, user_prompt
