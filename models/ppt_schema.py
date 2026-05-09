"""PPT 结构化数据模型。

大模型输出的 JSON 会先被校验成这些 Pydantic 模型，再交给 PPTService 渲染。
这样可以把“模型输出不稳定”的风险挡在生成 PPT 之前。
"""

from typing import List

from pydantic import BaseModel, Field, field_validator


class PPTPage(BaseModel):
    """单页 PPT 的结构化描述。"""

    page_no: int = Field(..., ge=1, description="页码")
    page_title: str = Field(..., min_length=2, description="页面标题")
    bullets: List[str] = Field(default_factory=list, description="要点列表")
    speaker_notes: str = Field(default="", description="讲稿备注")
    keywords: List[str] = Field(default_factory=list, description="用于配图检索的关键词")

    @field_validator("bullets", mode="before")
    @classmethod
    def validate_bullets(cls, value: list[str] | str | None) -> list[str]:
        """清洗页面要点。

        大模型有时会把 bullets 输出成字符串、空值或过长列表，这里统一转成最多 5 条的列表。
        """

        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        clean_items = [item.strip() for item in value if item and item.strip()]
        return clean_items[:5]

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, value: list[str] | str | None) -> list[str]:
        """清洗配图关键词。

        keywords 主要给 Pexels/Unsplash 搜图使用，限制数量可以减少无效查询和提示词噪声。
        """

        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        clean_items = [item.strip() for item in value if item and item.strip()]
        return clean_items[:6]


class PPTPlan(BaseModel):
    """整份 PPT 的结构化规划。"""

    ppt_title: str = Field(..., min_length=2, description="PPT 标题")
    subtitle: str = Field(default="", description="副标题")
    theme: str = Field(default="", description="主题风格说明")
    pages: List[PPTPage] = Field(default_factory=list, description="页面规划")
