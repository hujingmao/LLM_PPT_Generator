"""知识库写入测试。

用于验证 KnowledgeBaseService 能否把一段文本写入本地 Chroma 向量库。
重复运行时，由于 MD5 去重，可能返回“内容已经存在知识库中”。
"""

from knowledge_base import KnowledgeBaseService

service = KnowledgeBaseService()
result = service.upload_by_str(
    "RAG 是一种结合检索和生成的大模型应用方案。",
    "demo.txt"
)
print(result)
