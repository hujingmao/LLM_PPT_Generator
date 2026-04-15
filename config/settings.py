"""统一配置模块。"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "generated_ppt"
DATA_DIR = BASE_DIR / "data"
CHAT_HISTORY_DIR = BASE_DIR / "chat_history"

# 文件去重记录
MD5_PATH = BASE_DIR / "md5.text"

# Chroma 配置
COLLECTION_NAME = "rag"
PERSIST_DIRECTORY = str(BASE_DIR / "chroma_db")

# 文本切分配置
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
MAX_SPLIT_CHAR_NUMBER = 1000

# 检索配置
RETRIEVAL_TOP_K = 3

# 模型配置
LLM_PROVIDER = "qwen_native"
EMBEDDING_PROVIDER = "dashscope"
EMBEDDING_MODEL_NAME = "text-embedding-v4"
CHAT_MODEL_NAME = "qwen3-max"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY_ENV = "OPENAI_API_KEY"

# 业务默认值
DEFAULT_PAGE_COUNT = 8
MIN_PAGE_COUNT = 6
MAX_PAGE_COUNT = 10
DEFAULT_LANGUAGE = "中文"
OPERATOR = "system"

