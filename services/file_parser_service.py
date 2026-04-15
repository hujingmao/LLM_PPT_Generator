"""参考资料解析服务（MVP: txt/md）。"""

from typing import Iterable

from utils.logger import get_logger

logger = get_logger(__name__)


class FileParserService:
    SUPPORTED_TYPES = {"txt", "md"}

    def parse_uploaded_files(self, uploaded_files: Iterable) -> list[tuple[str, str]]:
        parsed_items: list[tuple[str, str]] = []

        for file_obj in uploaded_files or []:
            file_name = getattr(file_obj, "name", "unknown")
            suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            if suffix not in self.SUPPORTED_TYPES:
                logger.warning("跳过不支持格式: %s", file_name)
                continue

            content = file_obj.getvalue().decode("utf-8", errors="ignore").strip()
            if not content:
                logger.warning("跳过空文件: %s", file_name)
                continue
            parsed_items.append((file_name, content))

        return parsed_items

