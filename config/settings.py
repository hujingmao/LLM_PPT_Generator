"""项目内部通用配置。

这里放输出目录、模板目录、向量库目录、模型名称等非敏感配置。
API Key、数据库密码、JWT 密钥等敏感信息只从环境变量读取。
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# 本地文件目录
OUTPUT_DIR = BASE_DIR / "output" / "generated_ppt"
UPLOAD_DIR = BASE_DIR / "output" / "uploaded_files"
TEMP_IMAGE_DIR = BASE_DIR / "temp_images"
DATA_DIR = BASE_DIR / "data"
CHAT_HISTORY_DIR = BASE_DIR / "chat_history"
TEMPLATE_DIR = BASE_DIR / "templates"
DEFAULT_TEMPLATE_PATH = TEMPLATE_DIR / "default_master.pptx"

# 知识库与 RAG 配置
MD5_PATH = BASE_DIR / "md5.text"
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rag")
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "chroma_db"))
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""]
MAX_SPLIT_CHAR_NUMBER = int(os.getenv("RAG_MAX_SPLIT_CHAR_NUMBER", "1000"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))

# 大模型配置。具体 Key 只读环境变量，不在代码中写死。
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen_native")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v4")
CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "qwen3-max")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY_ENV = os.getenv("LLM_API_KEY_ENV", "DASHSCOPE_API_KEY")

# 业务默认值
DEFAULT_PAGE_COUNT = int(os.getenv("DEFAULT_PAGE_COUNT", "8"))
MIN_PAGE_COUNT = int(os.getenv("MIN_PAGE_COUNT", "3"))
MAX_PAGE_COUNT = int(os.getenv("MAX_PAGE_COUNT", "20"))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "中文")
OPERATOR = "system"
DEFAULT_PPT_COST_PER_PAGE = int(os.getenv("DEFAULT_PPT_COST_PER_PAGE", "10"))

# 前端模板选择项。文件不存在时由模板服务自动回退，不影响 PPT 导出。
AVAILABLE_TEMPLATES = [
    {"id": "default", "name": "默认模板", "path": "templates/default_master.pptx"},
    {"id": "academic", "name": "学术答辩模板", "path": "templates/academic_master.pptx"},
    {"id": "business", "name": "商务汇报模板", "path": "templates/business_master.pptx"},
    {"id": "tech_blue", "name": "科技蓝白模板", "path": "templates/tech_blue_master.pptx"},
    {"id": "minimal_bw", "name": "简约黑白模板", "path": "templates/minimal_bw_master.pptx"},
]
