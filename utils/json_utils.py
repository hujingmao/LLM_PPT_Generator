"""大模型 JSON 提取工具。"""

import json
import re
from typing import Any


def extract_json_text(raw_text: str) -> str:
    """从模型输出中尽量提取 JSON 对象文本。"""

    text = (raw_text or "").strip()
    if not text:
        return ""

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced_match:
        return fenced_match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def try_parse_json(raw_text: str) -> tuple[bool, Any]:
    """尝试解析 JSON，返回 (是否成功, 解析结果或错误信息)。"""

    json_str = extract_json_text(raw_text)
    if not json_str:
        return False, "未找到 JSON 对象"
    try:
        return True, json.loads(json_str)
    except json.JSONDecodeError as exc:
        return False, f"JSON 解析失败: {exc}"
