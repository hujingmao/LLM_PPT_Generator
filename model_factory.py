"""模型工厂。

根据配置创建聊天模型和向量模型。业务代码只调用 build_chat_model/build_embedding，
不直接依赖具体厂商 SDK，从而方便以后切换模型供应商。
"""

import os

import config_data as config
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings


def _get_required_env(env_name: str) -> str:
    """读取必填环境变量，缺失时抛出明确错误。"""

    value = os.getenv(env_name)
    if not value:
        raise ValueError(
            f"缺少环境变量：{env_name}\n"
            f"请先在系统环境变量中配置它，再重新运行项目。"
        )
    return value


def build_embedding():
    """构建向量模型。

    当前默认使用 DashScopeEmbeddings，用于 Chroma 向量库入库和检索。
    """

    provider = config.embedding_provider.strip().lower()

    if provider == "dashscope":
        # 提前校验，避免运行到一半才报错
        _get_required_env("DASHSCOPE_API_KEY")
        return DashScopeEmbeddings(model=config.embedding_model_name)

    raise ValueError(f"暂不支持的 embedding_provider: {config.embedding_provider}")


def build_chat_model():
    """构建聊天模型。

    支持通义千问原生 ChatTongyi，也支持 OpenAI 兼容接口。
    """

    provider = config.llm_provider.strip().lower()

    if provider == "qwen_native":
        _get_required_env("DASHSCOPE_API_KEY")
        return ChatTongyi(model=config.chat_model_name)

    if provider == "qwen_compatible":
        _get_required_env(config.llm_api_key_env)
        from langchain_openai import ChatOpenAI

        # OpenAI 兼容模式适合接入 DashScope compatible endpoint 或其他兼容服务。
        return ChatOpenAI(
            model=config.chat_model_name,
            api_key=os.getenv(config.llm_api_key_env),
            base_url=config.llm_base_url,
            temperature=0,
        )

    raise ValueError(f"暂不支持的 llm_provider: {config.llm_provider}")
