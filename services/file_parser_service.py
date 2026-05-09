"""参考资料解析服务（MVP: txt/md）。

这个服务目前仍保留给后续文件上传/RAG 扩展使用。
前后端分离版本当前用 textarea 传 retrieval_context，未来接文件上传时可复用这里。
"""

from typing import Iterable

from utils.logger import get_logger

logger = get_logger(__name__)


class FileParserService:
    """把上传文件对象解析成 (文件名, 文本内容) 列表。"""

    SUPPORTED_TYPES = {"txt", "md"}

    def parse_uploaded_files(self, uploaded_files: Iterable) -> list[tuple[str, str]]:
        """解析上传文件。

        Streamlit/FastAPI UploadFile 的对象结构不同，所以这里尽量只依赖 name/getvalue 这类通用属性。
        """

        parsed_items: list[tuple[str, str]] = []

        for file_obj in uploaded_files or []:
            file_name = getattr(file_obj, "name", "unknown")
            suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            if suffix not in self.SUPPORTED_TYPES:
                # 不支持的格式直接跳过，避免影响其他合法文件。
                logger.warning("跳过不支持格式: %s", file_name)
                continue

            content = file_obj.getvalue().decode("utf-8", errors="ignore").strip()
            if not content:
                # 空文件不入库，避免污染向量库。
                logger.warning("跳过空文件: %s", file_name)
                continue
            parsed_items.append((file_name, content))

        return parsed_items
