"""RAG 检索增强服务。

上传资料解析完成后，本服务负责把文本切分并写入 Chroma。生成大纲前，
再按当前用户、文件 ID 和 PPT 主题检索相关片段，把检索结果交给大模型。
"""

import hashlib
from datetime import datetime

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings as app_settings
from model_factory import build_embedding


class RetrievalService:
    """Chroma 向量库门面。"""

    def __init__(self):
        self.embedding = build_embedding()
        self.vector_store = Chroma(
            collection_name=app_settings.COLLECTION_NAME,
            embedding_function=self.embedding,
            persist_directory=app_settings.PERSIST_DIRECTORY,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=app_settings.CHUNK_SIZE,
            chunk_overlap=app_settings.CHUNK_OVERLAP,
            separators=app_settings.SEPARATORS,
            length_function=len,
        )

    def ingest_file_text(self, user_id: int, file_id: int, filename: str, text: str) -> int:
        """把单个文件文本切分后写入向量库，返回写入片段数量。"""

        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError(f"{filename}：解析文本为空，无法写入知识库")

        chunks = self.splitter.split_text(clean_text)
        if not chunks:
            raise ValueError(f"{filename}：文本切分后为空，无法写入知识库")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadatas = [
            {
                "user_id": str(user_id),
                "file_id": str(file_id),
                "source": filename,
                "chunk_index": index,
                "created_at": now,
            }
            for index, _ in enumerate(chunks)
        ]
        ids = [self._chunk_id(user_id, file_id, index, chunk) for index, chunk in enumerate(chunks)]
        self.vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
        return len(chunks)

    def retrieve_context(
        self,
        query: str,
        user_id: int,
        file_ids: list[int] | None = None,
        top_k: int | None = None,
    ) -> str:
        """按用户和文件过滤检索相关片段，并格式化为提示词上下文。"""

        clean_query = (query or "").strip()
        if not clean_query:
            return ""

        where = self._build_filter(user_id, file_ids or [])
        docs = self.vector_store.similarity_search(
            clean_query,
            k=top_k or app_settings.RETRIEVAL_TOP_K,
            filter=where,
        )
        if not docs:
            return ""
        return self._format_documents(docs)

    @staticmethod
    def _build_filter(user_id: int, file_ids: list[int]) -> dict:
        """构造 Chroma metadata 过滤条件。"""

        user_filter = {"user_id": str(user_id)}
        clean_file_ids = [str(file_id) for file_id in file_ids if file_id]
        if not clean_file_ids:
            return user_filter
        if len(clean_file_ids) == 1:
            return {"$and": [user_filter, {"file_id": clean_file_ids[0]}]}
        return {"$and": [user_filter, {"file_id": {"$in": clean_file_ids}}]}

    @staticmethod
    def _format_documents(docs: list[Document]) -> str:
        """把 LangChain Document 列表转换成带来源标注的上下文。"""

        lines: list[str] = []
        for index, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "unknown")
            chunk_index = doc.metadata.get("chunk_index", "")
            lines.append(f"[参考资料{index}] 来源: {source} 片段: {chunk_index}\n{doc.page_content}")
        return "\n\n".join(lines)

    @staticmethod
    def _chunk_id(user_id: int, file_id: int, index: int, chunk: str) -> str:
        digest = hashlib.md5(chunk.encode("utf-8")).hexdigest()[:12]
        return f"user-{user_id}-file-{file_id}-chunk-{index}-{digest}"
