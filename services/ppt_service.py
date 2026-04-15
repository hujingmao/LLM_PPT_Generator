"""python-pptx 生成服务。"""

from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt

from config.settings import OUTPUT_DIR
from models.ppt_schema import PPTPlan
from utils.filename_utils import build_output_filename


class PPTService:
    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_ppt(self, plan: PPTPlan, topic: str) -> Path:
        prs = Presentation()
        self._add_cover_slide(prs, plan)
        self._add_toc_slide(prs, plan)

        for page in plan.pages:
            self._add_content_slide(
                prs=prs,
                title=page.page_title,
                bullets=page.bullets,
                notes=page.speaker_notes,
            )

        self._add_summary_slide(prs, plan)

        filename = build_output_filename(topic)
        output_path = self.output_dir / filename
        prs.save(str(output_path))
        return output_path

    @staticmethod
    def _add_cover_slide(prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = plan.ppt_title
        subtitle = slide.placeholders[1]
        subtitle.text = f"{plan.subtitle}\n{datetime.now().strftime('%Y-%m-%d')}"

    @staticmethod
    def _add_toc_slide(prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "目录"
        body = slide.shapes.placeholders[1].text_frame
        body.clear()
        for idx, page in enumerate(plan.pages[:8], start=1):
            p = body.add_paragraph() if idx > 1 else body.paragraphs[0]
            p.text = f"{idx}. {page.page_title}"
            p.font.size = Pt(20)

    @staticmethod
    def _add_content_slide(
        prs: Presentation,
        title: str,
        bullets: list[str],
        notes: str,
    ) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title

        body = slide.shapes.placeholders[1].text_frame
        body.clear()
        bullet_items = bullets[:5] or ["待补充内容"]
        for idx, item in enumerate(bullet_items):
            para = body.add_paragraph() if idx > 0 else body.paragraphs[0]
            para.text = item
            para.level = 0
            para.font.size = Pt(20)

        if notes:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = notes

    @staticmethod
    def _add_summary_slide(prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "总结与展望"
        body = slide.shapes.placeholders[1].text_frame
        body.clear()
        conclusion = [
            f"本次汇报围绕“{plan.ppt_title}”完成自动化内容生成。",
            "系统支持主题驱动和参考资料驱动两种模式。",
            "后续可扩展多模板风格、图文增强与讲稿导出。",
        ]
        for idx, line in enumerate(conclusion):
            para = body.add_paragraph() if idx > 0 else body.paragraphs[0]
            para.text = line
            para.font.size = Pt(20)

