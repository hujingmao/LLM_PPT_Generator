"""向量库服务。

封装 Chroma 的创建和检索器获取，供 RetrievalService 调用。
"""

from langchain_chroma import Chroma
import config_data as config


class VectorStoreService(object):
    """Chroma 向量库门面。"""

    def __init__(self, embedding):
        """
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding

        # persist_directory 指向本地 chroma_db，数据会持久化，重启后仍可检索。
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )

    def get_retriever(self, top_k: int | None = None):
        """返回向量检索器，方便加入 chain 或直接 invoke。"""

        k_value = top_k or config.similarity_threshold
        return self.vector_store.as_retriever(search_kwargs={"k": k_value})


if __name__ == '__main__':
    from langchain_community.embeddings import DashScopeEmbeddings
    retriever = VectorStoreService(DashScopeEmbeddings(model="text-embedding-v4")).get_retriever()

    res = retriever.invoke("我的体重180斤，尺码推荐")
    print(res)
