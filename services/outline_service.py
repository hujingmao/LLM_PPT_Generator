"""PPT 大纲与页面规划服务。

OutlineService 负责把用户主题、场景、页数、风格和检索上下文拼成提示词，
调用大模型生成严格 JSON，再校验成 PPTPlan。
"""

import json

from pydantic import ValidationError

from config.settings import DEFAULT_LANGUAGE
from models.ppt_schema import PPTPlan
from services.llm_service import LLMService
from utils.json_utils import try_parse_json
from utils.logger import get_logger

logger = get_logger(__name__)


class OutlineService:
    """面向业务层的大纲生成服务。"""

    def __init__(self):
        # LLMService 封装具体模型，便于后续切换通义千问或 OpenAI 兼容模型。
        self.llm_service = LLMService()

    def generate_plan(
        self,
        topic: str,
        scene: str,
        page_count: int,
        style: str,
        retrieval_context: str = "",
    ) -> PPTPlan:
        """生成可直接渲染成 PPT 的结构化规划。

        大模型第一次输出如果不是合法 JSON，会再调用一次 repair_json 做容错修复。
        """

        system_prompt, user_prompt = self._build_plan_prompt(
            topic=topic,
            scene=scene,
            page_count=page_count,
            style=style,
            retrieval_context=retrieval_context,
        )
        raw_output = self.llm_service.invoke(system_prompt, user_prompt)
        # 先尝试从原始输出中提取 JSON；兼容模型额外包裹 markdown 代码块的情况。
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
        """让模型把非严格 JSON 输出修复为合法 JSON。

        这个方法只负责格式修复，不重新生成内容，尽量保留第一次输出的信息。
        """

        system_prompt = (
            "你是 JSON 修复助手。"
            "你会把输入文本修复为合法 JSON。"
            "只输出 JSON 对象，不要任何解释。"
        )
        user_prompt = (
            "请将下面文本修复为严格合法的 JSON。"
            "字段结构必须包含: ppt_title, subtitle, theme, pages。"
            "pages 是数组，每项包含 page_no, page_title, bullets, speaker_notes，可选 keywords。\n\n"
            f"待修复内容:\n{raw_output}"
        )
        return self.llm_service.invoke(system_prompt, user_prompt)

    @staticmethod
    def _validate_plan(payload: dict) -> PPTPlan:
        """把普通 dict 校验为 PPTPlan，统一抛出更容易理解的业务异常。"""

        try:
            return PPTPlan.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"PPT 结构校验失败: {exc}") from exc

    @staticmethod
    def _build_plan_prompt(
        topic: str,
        scene: str,
        page_count: int,
        style: str,
        retrieval_context: str,
    ) -> tuple[str, str]:
        """构造生成大纲的 system/user prompt。

        system_prompt 约束模型角色和输出格式；user_prompt 放业务参数、参考上下文和 JSON 示例。
        """

        system_prompt = (
            "你是资深演示文稿策划专家。"
            f"默认输出语言为{DEFAULT_LANGUAGE}。"
            "你需要输出可直接用于生成 PPT 的结构化 JSON。"
            "严禁输出 JSON 以外的任何内容。"
        )

        # 检索上下文为空时明确告诉模型“纯主题生成”，避免模型以为漏传资料。
        context_part = retrieval_context.strip() or "无参考资料，基于主题生成。"
        schema_hint = {
            "ppt_title": "PPT标题",
            "subtitle": "副标题",
            "theme": "风格说明",
            "pages": [
                {
                    "page_no": 1,
                    "page_title": "页面标题",
                    "bullets": ["要点1", "要点2", "要点3"],
                    "speaker_notes": "该页讲稿说明",
                    "keywords": ["高清配图关键词1", "高清配图关键词2"],
                }
            ],
        }

        user_prompt = (
            f"主题: {topic}\n"
            f"应用场景: {scene}\n"
            f"目标页数: {page_count}\n"
            f"风格: {style}\n"
            f"参考资料上下文:\n{context_part}\n\n"
            "要求:\n"
            "1) 总页数控制在目标页数附近(允许 +/-1)。\n"
            "2) 每页 bullet 3~5 条，内容具体可讲。\n"
            "3) 每页 keywords 输出 2~4 个适合图片搜索的关键词，优先使用英文短语。\n"
            "4) 页面标题自然，不要机械命名为第X页。\n"
            "5) 逻辑包含背景、方法/方案、结果/价值、总结展望。\n"
            "6) 输出严格 JSON 对象。\n\n"
            f"输出结构示例:\n{json.dumps(schema_hint, ensure_ascii=False)}"
        )
        return system_prompt, user_prompt
