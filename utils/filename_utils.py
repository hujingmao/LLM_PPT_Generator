"""文件名处理工具。"""

import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """把任意标题转换成 Windows/Unix 都安全的文件名片段。"""

    safe = re.sub(r"[\\/:*?\"<>|]+", "_", (name or "").strip())
    safe = re.sub(r"\s+", "_", safe)
    return safe[:50] or "ppt"


def build_output_filename(topic: str, suffix: str = ".pptx") -> str:
    """生成带时间戳的输出文件名，避免同名覆盖。"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_filename(topic)}_{timestamp}{suffix}"


def ensure_parent_dir(path: Path) -> None:
    """确保文件父目录存在。"""

    path.parent.mkdir(parents=True, exist_ok=True)
