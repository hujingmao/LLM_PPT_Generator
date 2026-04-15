from model_factory import build_chat_model

llm = build_chat_model()
resp = llm.invoke("你好，请用一句话介绍你自己。")
print(resp)