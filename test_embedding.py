from model_factory import build_embedding

embedding = build_embedding()
vec = embedding.embed_query("今天天气很好")
print(type(vec))
print(len(vec))
print(vec[:10])