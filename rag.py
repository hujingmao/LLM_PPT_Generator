"""PPT 自动生成主流程封装（兼容旧文件名 rag.py）。"""

from models.ppt_schema import PPTPlan
from services.outline_service import OutlineService
from services.ppt_service import PPTService
from services.retrieval_service import RetrievalService


class PPTGenerationService:
    """整合检索增强、规划生成和 PPT 文件落地。"""

    def __init__(self):
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
        retrieval_context = ""
        if use_retrieval and parsed_docs:
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