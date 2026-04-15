import config_data as config
from rag import RagService

rag = RagService()

resp = rag.chain.invoke(
    {"input": "什么是RAG？"},
    config.session_config
)

print(resp)