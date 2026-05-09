"""向量模型连通性测试。

运行前需要配置 DASHSCOPE_API_KEY。
该脚本会构建 embedding 模型，并打印向量类型、长度和前 10 个数值。
"""

from model_factory import build_embedding

embedding = build_embedding()
vec = embedding.embed_query("今天天气很好")
print(type(vec))
print(len(vec))
print(vec[:10])
