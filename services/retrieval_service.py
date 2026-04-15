"""检索增强服务。"""

from langchain_core.documents import Document

from knowledge_base import KnowledgeBaseService
from vector_stores import VectorStoreService
from model_factory import build_embedding


class RetrievalService:
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.vector_service = VectorStoreService(embedding=build_embedding())

    def ingest_documents(self, docs: list[tuple[str, str]]) -> list[str]:
        messages = []
        for filename, content in docs:
            result = self.kb_service.upload_by_str(content, filename)
            messages.append(f"{filename}: {result}")
        return messages

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        retriever = self.vector_service.get_retriever(top_k=top_k)
        docs = retriever.invoke(query)
        if not docs:
            return ""
        return self._format_documents(docs)

    @staticmethod
    def _format_documents(docs: list[Document]) -> str:
        lines: list[str] = []
        for idx, doc in enumerate(docs, start=1):
            lines.append(
                f"[参考资料{idx}] 来源: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            )
        return "\n\n".join(lines)

