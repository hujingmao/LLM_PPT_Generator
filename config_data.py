"""兼容配置入口（建议新代码使用 config/settings.py）。

早期模块使用小写变量名（如 md5_path、collection_name）。
为了不大规模改动旧 RAG 代码，这里从新的统一配置中导入常量，再映射成旧变量名。
"""

from config.settings import (
    CHAT_MODEL_NAME,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_PROVIDER,
    LLM_API_KEY_ENV,
    LLM_BASE_URL,
    LLM_PROVIDER,
    MAX_SPLIT_CHAR_NUMBER,
    MD5_PATH,
    OPERATOR,
    PERSIST_DIRECTORY,
    RETRIEVAL_TOP_K,
    SEPARATORS,
)

# 保留旧变量名，避免旧模块崩溃。
md5_path = str(MD5_PATH)
collection_name = COLLECTION_NAME
persist_directory = PERSIST_DIRECTORY
chunk_size = CHUNK_SIZE
chunk_overlap = CHUNK_OVERLAP
separators = SEPARATORS
max_split_char_number = MAX_SPLIT_CHAR_NUMBER
similarity_threshold = RETRIEVAL_TOP_K
llm_provider = LLM_PROVIDER
embedding_provider = EMBEDDING_PROVIDER
embedding_model_name = EMBEDDING_MODEL_NAME
chat_model_name = CHAT_MODEL_NAME
llm_base_url = LLM_BASE_URL
llm_api_key_env = LLM_API_KEY_ENV
operator = OPERATOR
# LangChain 历史会话的默认 session_id，主要用于旧 demo 或测试脚本。
session_config = {"configurable": {"session_id": "ppt_demo_001"}}
