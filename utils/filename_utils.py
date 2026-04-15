"""文件名处理工具。"""

import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]+", "_", name.strip())
    return safe[:50] or "ppt"


def build_output_filename(topic: str, suffix: str = ".pptx") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{sanitize_filename(topic)}_{timestamp}{suffix}"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

