"""大模型与 Embedding 模型工厂。

业务代码只调用 build_chat_model/build_embedding，不直接依赖某个厂商 SDK。
所有 API Key 都从环境变量读取。
"""

import os

import config_data as config
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings


def _get_required_env(env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"缺少环境变量：{env_name}，请先在 .env 或系统环境变量中配置。")
    return value


def build_embedding():
    """构建向量模型，用于 Chroma 入库和检索。"""

    provider = config.embedding_provider.strip().lower()
    if provider == "dashscope":
        _get_required_env("DASHSCOPE_API_KEY")
        return DashScopeEmbeddings(model=config.embedding_model_name)
    raise ValueError(f"暂不支持的 embedding_provider: {config.embedding_provider}")


def build_chat_model():
    """构建聊天大模型，支持通义千问原生模式和 OpenAI 兼容模式。"""

    provider = config.llm_provider.strip().lower()
    if provider == "qwen_native":
        _get_required_env("DASHSCOPE_API_KEY")
        return ChatTongyi(model=config.chat_model_name)

    if provider in {"qwen_compatible", "openai_compatible"}:
        api_key = _get_required_env(config.llm_api_key_env)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.chat_model_name,
            api_key=api_key,
            base_url=config.llm_base_url,
            temperature=0.2,
        )

    raise ValueError(f"暂不支持的 llm_provider: {config.llm_provider}")
