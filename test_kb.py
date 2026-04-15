from knowledge_base import KnowledgeBaseService

service = KnowledgeBaseService()
result = service.upload_by_str(
    "RAG 是一种结合检索和生成的大模型应用方案。",
    "demo.txt"
)
print(result)