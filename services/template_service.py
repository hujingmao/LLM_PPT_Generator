"""PPT 模板选择与路径校验服务。"""

from pathlib import Path

from config.settings import AVAILABLE_TEMPLATES, BASE_DIR, TEMPLATE_DIR


class TemplateService:
    """把前端模板 id 映射为安全的本地模板路径。"""

    def list_templates(self) -> list[dict]:
        templates = []
        for item in AVAILABLE_TEMPLATES:
            path = self._path_from_config(item["path"])
            templates.append({**item, "exists": bool(path and path.exists())})
        return templates

    def resolve_template(self, template_id: str | None = "default", template_path: str | None = None) -> tuple[Path | None, dict]:
        """解析模板。

        template_path 只为兼容旧接口保留，且只能指向 templates/ 目录内的 pptx。
        任意系统路径会被拒绝；模板不存在时自动回退默认模板，默认模板也不存在时返回 None。
        """

        selected = self._find_template(template_id)
        if template_path:
            path = self._safe_template_path(template_path)
            if path and path.exists():
                return path, {"id": selected["id"], "name": selected["name"], "path": str(path), "exists": True}

        configured_path = self._path_from_config(selected["path"])
        if configured_path and configured_path.exists():
            return configured_path, {**selected, "exists": True}

        default_item = self._find_template("default")
        default_path = self._path_from_config(default_item["path"])
        if default_path and default_path.exists():
            return default_path, {**default_item, "exists": True}

        return None, {**default_item, "exists": False}

    @staticmethod
    def _find_template(template_id: str | None) -> dict:
        clean_id = template_id or "default"
        for item in AVAILABLE_TEMPLATES:
            if item["id"] == clean_id:
                return item
        return AVAILABLE_TEMPLATES[0]

    @staticmethod
    def _path_from_config(path_text: str) -> Path | None:
        path = Path(path_text)
        if not path.is_absolute():
            path = BASE_DIR / path
        path = path.resolve()
        if path.suffix.lower() != ".pptx":
            return None
        return path

    @staticmethod
    def _safe_template_path(path_text: str) -> Path | None:
        path = Path(path_text)
        if path.is_absolute():
            candidate = path.resolve()
        else:
            candidate = (BASE_DIR / path).resolve()

        template_root = TEMPLATE_DIR.resolve()
        try:
            candidate.relative_to(template_root)
        except ValueError:
            return None
        if candidate.suffix.lower() != ".pptx":
            return None
        return candidate
