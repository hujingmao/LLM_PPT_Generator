"""统一配置模块。

这里放项目内部服务共享的常量配置，例如输出目录、模板目录、向量库路径和模型名称。
后端运行时配置（数据库、JWT、CORS）放在 backend/config.py，避免业务配置和部署配置混在一起。
"""

from pathlib import Path


# 项目根目录。所有相对目录都基于它计算，避免从不同工作目录启动时路径混乱。
BASE_DIR = Path(__file__).resolve().parent.parent

# PPT 文件输出目录和配图临时缓存目录。
OUTPUT_DIR = BASE_DIR / "output" / "generated_ppt"
TEMP_IMAGE_DIR = BASE_DIR / "output" / "tmp_images"

# 本地资料目录、聊天记录目录和 PPT 模板目录。
DATA_DIR = BASE_DIR / "data"
CHAT_HISTORY_DIR = BASE_DIR / "chat_history"
TEMPLATE_DIR = BASE_DIR / "templates"

# 默认母版路径；文件存在时 PPTService 会自动加载。
DEFAULT_TEMPLATE_PATH = TEMPLATE_DIR / "default_master.pptx"

# 文件去重记录
MD5_PATH = BASE_DIR / "md5.text"

# Chroma 配置
COLLECTION_NAME = "rag"
PERSIST_DIRECTORY = str(BASE_DIR / "chroma_db")

# 文本切分配置：资料过长时切成多个块再写入向量库。
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
SEPARATORS = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
MAX_SPLIT_CHAR_NUMBER = 1000

# 检索配置
RETRIEVAL_TOP_K = 3

# 模型配置：当前默认使用 DashScope/通义千问。
LLM_PROVIDER = "qwen_native"
EMBEDDING_PROVIDER = "dashscope"
EMBEDDING_MODEL_NAME = "text-embedding-v4"
CHAT_MODEL_NAME = "qwen3-max"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_API_KEY_ENV = "OPENAI_API_KEY"

# 业务默认值：前端默认页数、页数边界和每页扣费规则。
DEFAULT_PAGE_COUNT = 8
MIN_PAGE_COUNT = 6
MAX_PAGE_COUNT = 10
DEFAULT_LANGUAGE = "中文"
OPERATOR = "system"
DEFAULT_PPT_COST_PER_PAGE = 10
