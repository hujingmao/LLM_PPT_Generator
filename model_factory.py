import os

import config_data as config
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings


def _get_required_env(env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        raise ValueError(
            f"缺少环境变量：{env_name}\n"
            f"请先在系统环境变量中配置它，再重新运行项目。"
        )
    return value


def build_embedding():
    provider = config.embedding_provider.strip().lower()

    if provider == "dashscope":
        # 提前校验，避免运行到一半才报错
        _get_required_env("DASHSCOPE_API_KEY")
        return DashScopeEmbeddings(model=config.embedding_model_name)

    raise ValueError(f"暂不支持的 embedding_provider: {config.embedding_provider}")


def build_chat_model():
    provider = config.llm_provider.strip().lower()

    if provider == "qwen_native":
        _get_required_env("DASHSCOPE_API_KEY")
        return ChatTongyi(model=config.chat_model_name)

    if provider == "qwen_compatible":
        _get_required_env(config.llm_api_key_env)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.chat_model_name,
            api_key=os.getenv(config.llm_api_key_env),
            base_url=config.llm_base_url,
            temperature=0,
        )

    raise ValueError(f"暂不支持的 llm_provider: {config.llm_provider}")