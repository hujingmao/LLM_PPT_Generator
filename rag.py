"""PPT 自动生成主流程封装（兼容旧文件名 rag.py）。

前后端分离版本主要通过 backend/main.py 调用服务。
这个类保留为命令行/测试脚本的轻量编排入口，方便直接从 Python 调用完整生成流程。
"""

from models.ppt_schema import PPTPlan
from services.outline_service import OutlineService
from services.ppt_service import PPTService
from services.retrieval_service import RetrievalService


class PPTGenerationService:
    """整合检索增强、规划生成和 PPT 文件落地。"""

    def __init__(self):
        # 三个子服务分别负责资料检索、结构规划和 PPT 文件生成。
        self.retrieval_service = RetrievalService()
        self.outline_service = OutlineService()
        self.ppt_service = PPTService()

    def run(
        self,
        topic: str,
        scene: str,
        page_count: int,
        style: str,
        parsed_docs: list[tuple[str, str]] | None = None,
        use_retrieval: bool = True,
    ) -> tuple[PPTPlan, str]:
        """运行一次完整的 PPT 生成流程。"""

        retrieval_context = ""
        if use_retrieval and parsed_docs:
            # 如果提供了参考资料，先入库再按主题检索相关片段。
            self.retrieval_service.ingest_documents(parsed_docs)
            retrieval_context = self.retrieval_service.retrieve_context(topic)

        plan = self.outline_service.generate_plan(
            topic=topic,
            scene=scene,
            page_count=page_count,
            style=style,
            retrieval_context=retrieval_context,
        )
        output_path = self.ppt_service.generate_ppt(plan=plan, topic=topic)
        return plan, str(output_path)
