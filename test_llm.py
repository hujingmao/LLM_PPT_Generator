"""聊天模型连通性测试。

运行前需要配置 DASHSCOPE_API_KEY 或 config_data.py 中指定的兼容模型 Key。
"""

from model_factory import build_chat_model

llm = build_chat_model()
resp = llm.invoke("你好，请用一句话介绍你自己。")
print(resp)
