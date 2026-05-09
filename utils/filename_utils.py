"""文件名处理工具。

生成的 PPT 会使用用户主题作为文件名的一部分，因此必须清理 Windows/Unix 不允许的字符。
"""

import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """把任意主题转换成安全文件名片段。"""

    safe = re.sub(r"[\\/:*?\"<>|]+", "_", name.strip())
    return safe[:50] or "ppt"


def build_output_filename(topic: str, suffix: str = ".pptx") -> str:
    """生成带时间戳的输出文件名，避免同一主题多次生成时覆盖旧文件。"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_filename(topic)}_{timestamp}{suffix}"


def ensure_parent_dir(path: Path) -> None:
    """确保某个文件路径的父目录存在。"""

    path.parent.mkdir(parents=True, exist_ok=True)
