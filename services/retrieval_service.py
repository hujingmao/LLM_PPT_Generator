"""检索增强服务。

负责把上传资料写入 Chroma 向量库，并根据 PPT 主题检索参考上下文。
这些上下文会被 OutlineService 放入提示词，提高生成内容和用户资料的一致性。
"""

from langchain_core.documents import Document

from knowledge_base import KnowledgeBaseService
from vector_stores import VectorStoreService
from model_factory import build_embedding


class RetrievalService:
    """RAG 检索服务门面。"""

    def __init__(self):
        # KnowledgeBaseService 负责入库，VectorStoreService 负责构造检索器。
        self.kb_service = KnowledgeBaseService()
        self.vector_service = VectorStoreService(embedding=build_embedding())

    def ingest_documents(self, docs: list[tuple[str, str]]) -> list[str]:
        """把解析后的文档写入知识库，并返回每个文件的处理结果。"""

        messages = []
        for filename, content in docs:
            result = self.kb_service.upload_by_str(content, filename)
            messages.append(f"{filename}: {result}")
        return messages

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """按主题检索最相关的资料片段，拼成可放入提示词的文本。"""

        retriever = self.vector_service.get_retriever(top_k=top_k)
        docs = retriever.invoke(query)
        if not docs:
            return ""
        return self._format_documents(docs)

    @staticmethod
    def _format_documents(docs: list[Document]) -> str:
        """把 LangChain Document 列表格式化成带来源标记的上下文。"""

        lines: list[str] = []
        for idx, doc in enumerate(docs, start=1):
            lines.append(
                f"[参考资料{idx}] 来源: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            )
        return "\n\n".join(lines)
