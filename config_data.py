"""兼容旧模块的配置映射。

早期 RAG 文件使用小写变量名，这里从 config/settings.py 映射一次，
避免大范围改动旧代码。
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
session_config = {"configurable": {"session_id": "ppt_demo_001"}}
