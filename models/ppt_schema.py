"""PPT 结构化数据模型。"""

from typing import List

from pydantic import BaseModel, Field, field_validator


class PPTPage(BaseModel):
    page_no: int = Field(..., ge=1, description="页码")
    page_title: str = Field(..., min_length=2, description="页面标题")
    bullets: List[str] = Field(default_factory=list, description="要点列表")
    speaker_notes: str = Field(default="", description="讲稿备注")

    @field_validator("bullets")
    @classmethod
    def validate_bullets(cls, value: list[str]) -> list[str]:
        clean_items = [item.strip() for item in value if item and item.strip()]
        return clean_items[:5]


class PPTPlan(BaseModel):
    ppt_title: str = Field(..., min_length=2, description="PPT 标题")
    subtitle: str = Field(default="", description="副标题")
    theme: str = Field(default="", description="主题风格说明")
    pages: List[PPTPage] = Field(default_factory=list, description="页面规划")

