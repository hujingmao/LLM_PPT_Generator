"""旧 RAG 测试脚本。

该脚本属于早期问答链路验证，当前前后端分离主流程请使用 backend/main.py。
如果后续继续维护旧 RAG 问答链，需要同步更新这里导入的服务类。
"""

import config_data as config
from rag import RagService

rag = RagService()

resp = rag.chain.invoke(
    {"input": "什么是RAG？"},
    config.session_config
)

print(resp)
