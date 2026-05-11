"""PPT 结构化数据模型。

大模型输出先被校验为这些 Pydantic 模型，再交给 PPTService 渲染。
模型同时兼容旧字段 ppt_title/pages/keywords 和新字段 title/slides/image_keywords。
"""

from typing import List

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


SUPPORTED_LAYOUT_TYPES = {
    "cover",
    "agenda",
    "section",
    "text",
    "image_text",
    "three_cards",
    "timeline",
    "comparison",
    "process",
    "summary",
    "thanks",
}


class PPTPage(BaseModel):
    """单页 PPT 的结构化描述。"""

    model_config = ConfigDict(populate_by_name=True)

    page_no: int = Field(..., ge=1, description="页码")
    page_title: str = Field(..., min_length=1, description="页面标题")
    layout_type: str = Field(default="text", description="页面版式类型")
    bullets: List[str] = Field(default_factory=list, description="要点列表")
    speaker_notes: str = Field(default="", description="讲稿备注")
    keywords: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("keywords", "image_keywords"),
        description="自动配图关键词",
    )

    @field_validator("layout_type", mode="before")
    @classmethod
    def validate_layout_type(cls, value: str | None) -> str:
        layout_type = (value or "text").strip().lower()
        return layout_type if layout_type in SUPPORTED_LAYOUT_TYPES else "text"

    @field_validator("bullets", mode="before")
    @classmethod
    def validate_bullets(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [line.strip() for line in value.splitlines()]
        clean_items = [item.strip() for item in value if item and item.strip()]
        return clean_items[:8]

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        clean_items = [item.strip() for item in value if item and item.strip()]
        return clean_items[:6]

    def to_outline_slide(self) -> dict:
        """转换成前端编辑区使用的稳定字段名。"""

        return {
            "page_no": self.page_no,
            "page_title": self.page_title,
            "layout_type": self.layout_type,
            "bullets": self.bullets,
            "speaker_notes": self.speaker_notes,
            "image_keywords": self.keywords,
        }


class PPTPlan(BaseModel):
    """整份 PPT 的结构化规划。"""

    model_config = ConfigDict(populate_by_name=True)

    ppt_title: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("ppt_title", "title"),
        description="PPT 标题",
    )
    subtitle: str = Field(default="", description="副标题")
    theme: str = Field(default="", description="主题风格说明")
    pages: List[PPTPage] = Field(
        default_factory=list,
        validation_alias=AliasChoices("pages", "slides"),
        description="页面规划",
    )

    def to_outline_dict(self) -> dict:
        """转换成 /api/ppt/outline 返回给前端的稳定 JSON。"""

        return {
            "title": self.ppt_title,
            "subtitle": self.subtitle,
            "slides": [page.to_outline_slide() for page in self.pages],
        }
