"""python-pptx generation service with template and image support."""

from datetime import datetime
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from config.settings import DEFAULT_TEMPLATE_PATH, OUTPUT_DIR, TEMPLATE_DIR
from models.ppt_schema import PPTPage, PPTPlan
from services.image_service import ImageSearchService
from utils.filename_utils import build_output_filename
from utils.logger import get_logger


logger = get_logger(__name__)


class PPTService:
    """Generate polished PPT files from structured plans."""

    font_name = "Microsoft YaHei"
    dark = RGBColor(15, 23, 42)
    ink = RGBColor(31, 41, 55)
    muted = RGBColor(100, 116, 139)
    light = RGBColor(248, 250, 252)
    white = RGBColor(255, 255, 255)
    teal = RGBColor(20, 184, 166)
    coral = RGBColor(244, 114, 82)
    amber = RGBColor(245, 158, 11)

    def __init__(
        self,
        output_dir: Path | None = None,
        template_path: Path | str | None = None,
        image_service: ImageSearchService | None = None,
    ):
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        self.template_path = Path(template_path) if template_path else (
            DEFAULT_TEMPLATE_PATH if DEFAULT_TEMPLATE_PATH.exists() else None
        )
        self.image_service = image_service

    def generate_ppt(
        self,
        plan: PPTPlan,
        topic: str,
        template_path: Path | str | None = None,
        use_images: bool = True,
    ) -> Path:
        prs, used_template = self._load_presentation(template_path)
        if used_template:
            self._clear_existing_slides(prs)

        self._add_cover_slide(prs, plan)
        self._add_toc_slide(prs, plan)

        image_service = self.image_service or (ImageSearchService() if use_images else None)
        for page in plan.pages:
            image_path = self._fetch_image_for_page(image_service, page, topic) if use_images else None
            self._add_content_slide(
                prs=prs,
                page=page,
                image_path=image_path,
            )

        self._add_summary_slide(prs, plan)

        filename = build_output_filename(topic)
        output_path = self.output_dir / filename
        prs.save(str(output_path))
        return output_path

    def _load_presentation(self, template_path: Path | str | None = None) -> tuple[Presentation, Path | None]:
        resolved_template = self._resolve_template_path(template_path or self.template_path)
        if resolved_template:
            return Presentation(str(resolved_template)), resolved_template

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        return prs, None

    @staticmethod
    def _resolve_template_path(template_path: Path | str | None) -> Path | None:
        if not template_path:
            return None

        path = Path(template_path)
        if not path.is_absolute():
            template_candidate = TEMPLATE_DIR / path
            path = template_candidate if template_candidate.exists() else Path.cwd() / path
        path = path.resolve()

        if path.suffix.lower() != ".pptx" or not path.exists():
            raise ValueError(f"模板文件不存在或不是 .pptx: {path}")
        return path

    @staticmethod
    def _clear_existing_slides(prs: Presentation) -> None:
        slide_id_list = prs.slides._sldIdLst
        for slide_id in list(slide_id_list):
            prs.part.drop_rel(slide_id.rId)
            slide_id_list.remove(slide_id)

    @staticmethod
    def _blank_layout(prs: Presentation):
        return prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]

    def _add_cover_slide(self, prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(self._blank_layout(prs))
        self._add_background(slide, prs, self.dark)

        margin_x = Inches(0.72)
        title_box = slide.shapes.add_textbox(margin_x, Inches(1.45), int(prs.slide_width * 0.78), Inches(1.5))
        tf = title_box.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = plan.ppt_title
        p.font.name = self.font_name
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = self.white

        subtitle = slide.shapes.add_textbox(margin_x, Inches(3.1), int(prs.slide_width * 0.66), Inches(0.8))
        tf = subtitle.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = plan.subtitle or plan.theme or "AI generated presentation"
        p.font.name = self.font_name
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(203, 213, 225)

        meta = slide.shapes.add_textbox(margin_x, int(prs.slide_height - Inches(1.05)), Inches(4.2), Inches(0.38))
        tf = meta.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = datetime.now().strftime("%Y-%m-%d")
        p.font.name = self.font_name
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(148, 163, 184)

        self._add_accent_bar(slide, int(prs.slide_width - Inches(3.4)), Inches(1.25), Inches(2.4), Inches(4.7))

    def _add_toc_slide(self, prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(self._blank_layout(prs))
        self._add_background(slide, prs, self.light)
        self._add_section_title(slide, "目录", "CONTENTS", prs)

        start_y = Inches(1.55)
        row_h = Inches(0.55)
        left_x = Inches(0.9)
        width = int(prs.slide_width - Inches(1.8))
        for idx, page in enumerate(plan.pages[:10], start=1):
            y = int(start_y + row_h * (idx - 1))
            marker = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_x, y, Inches(0.34), Inches(0.34))
            marker.fill.solid()
            marker.fill.fore_color.rgb = self.teal if idx % 2 else self.coral
            marker.line.fill.background()

            box = slide.shapes.add_textbox(int(left_x + Inches(0.52)), int(y - Inches(0.04)), width, Inches(0.44))
            tf = box.text_frame
            tf.clear()
            p = tf.paragraphs[0]
            p.text = f"{idx:02d}  {page.page_title}"
            p.font.name = self.font_name
            p.font.size = Pt(18)
            p.font.color.rgb = self.ink

        self._add_footer(slide, prs, plan.ppt_title)

    def _add_content_slide(
        self,
        prs: Presentation,
        page: PPTPage,
        image_path: Path | None,
    ) -> None:
        slide = prs.slides.add_slide(self._blank_layout(prs))
        self._add_background(slide, prs, self.white)

        self._add_slide_label(slide, page.page_no)
        title = slide.shapes.add_textbox(Inches(0.72), Inches(0.55), int(prs.slide_width * 0.48), Inches(0.8))
        tf = title.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = page.page_title
        p.font.name = self.font_name
        p.font.bold = True
        p.font.size = Pt(26)
        p.font.color.rgb = self.dark

        bullets = page.bullets[:5] or ["待补充内容"]
        body = slide.shapes.add_textbox(Inches(0.82), Inches(1.62), int(prs.slide_width * 0.48), Inches(4.6))
        tf = body.text_frame
        tf.clear()
        tf.margin_left = Inches(0.05)
        tf.margin_right = Inches(0.05)
        for idx, item in enumerate(bullets):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.name = self.font_name
            p.font.size = Pt(17)
            p.font.color.rgb = self.ink
            p.space_after = Pt(10)

        image_x = int(prs.slide_width * 0.58)
        image_y = Inches(1.12)
        image_w = int(prs.slide_width * 0.36)
        image_h = int(prs.slide_height * 0.68)
        if image_path:
            self._add_cropped_picture(slide, image_path, image_x, image_y, image_w, image_h)
        else:
            self._add_visual_fallback(slide, image_x, image_y, image_w, image_h, page)

        if page.speaker_notes:
            slide.notes_slide.notes_text_frame.text = page.speaker_notes

        self._add_footer(slide, prs, page.page_title)

    def _add_summary_slide(self, prs: Presentation, plan: PPTPlan) -> None:
        slide = prs.slides.add_slide(self._blank_layout(prs))
        self._add_background(slide, prs, self.dark)

        title = slide.shapes.add_textbox(Inches(0.78), Inches(0.88), int(prs.slide_width * 0.72), Inches(0.8))
        tf = title.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = "总结与展望"
        p.font.name = self.font_name
        p.font.bold = True
        p.font.size = Pt(30)
        p.font.color.rgb = self.white

        conclusion = [
            f"围绕“{plan.ppt_title}”完成结构化内容生成。",
            "模板、内容、讲稿与配图可以组合成可编辑的演示文稿。",
            "后续可继续扩展企业模板库、支付回调与团队协作能力。",
        ]

        for idx, line in enumerate(conclusion):
            x = Inches(0.82 + idx * 4.05)
            y = Inches(2.25)
            card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(3.45), Inches(2.55))
            card.fill.solid()
            card.fill.fore_color.rgb = RGBColor(30, 41, 59)
            card.line.color.rgb = RGBColor(51, 65, 85)

            label = slide.shapes.add_textbox(int(x + Inches(0.3)), int(y + Inches(0.26)), Inches(0.72), Inches(0.42))
            label_tf = label.text_frame
            label_tf.clear()
            p = label_tf.paragraphs[0]
            p.text = f"{idx + 1:02d}"
            p.font.name = self.font_name
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = self.teal if idx == 0 else self.coral if idx == 1 else self.amber

            text = slide.shapes.add_textbox(int(x + Inches(0.3)), int(y + Inches(0.92)), Inches(2.82), Inches(1.1))
            text_tf = text.text_frame
            text_tf.clear()
            p = text_tf.paragraphs[0]
            p.text = line
            p.font.name = self.font_name
            p.font.size = Pt(16)
            p.font.color.rgb = RGBColor(226, 232, 240)

    def _fetch_image_for_page(
        self,
        image_service: ImageSearchService | None,
        page: PPTPage,
        topic: str,
    ) -> Path | None:
        if not image_service:
            return None

        fallback_query = f"{topic} {page.page_title}"
        try:
            return image_service.fetch_slide_image(page.keywords, fallback_query=fallback_query)
        except Exception as exc:
            logger.warning("配图获取失败，已跳过当前页: %s", exc)
            return None

    def _add_background(self, slide, prs: Presentation, color: RGBColor) -> None:
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()

    def _add_section_title(self, slide, title: str, eyebrow: str, prs: Presentation) -> None:
        box = slide.shapes.add_textbox(Inches(0.75), Inches(0.55), Inches(4.8), Inches(0.62))
        tf = box.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = self.font_name
        p.font.bold = True
        p.font.size = Pt(28)
        p.font.color.rgb = self.dark

        tag = slide.shapes.add_textbox(int(prs.slide_width - Inches(2.55)), Inches(0.72), Inches(1.8), Inches(0.35))
        tf = tag.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = eyebrow
        p.alignment = PP_ALIGN.RIGHT
        p.font.name = self.font_name
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = self.teal

    def _add_slide_label(self, slide, page_no: int) -> None:
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.72), Inches(6.55), Inches(0.5), Inches(0.34))
        box.fill.solid()
        box.fill.fore_color.rgb = self.dark
        box.line.fill.background()

        label = slide.shapes.add_textbox(Inches(0.72), Inches(6.58), Inches(0.5), Inches(0.22))
        tf = label.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = f"{page_no:02d}"
        p.alignment = PP_ALIGN.CENTER
        p.font.name = self.font_name
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = self.white

    def _add_footer(self, slide, prs: Presentation, text: str) -> None:
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.72),
            int(prs.slide_height - Inches(0.42)),
            int(prs.slide_width - Inches(1.44)),
            Inches(0.02),
        )
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(226, 232, 240)
        line.line.fill.background()

        footer = slide.shapes.add_textbox(Inches(0.72), int(prs.slide_height - Inches(0.34)), Inches(5.8), Inches(0.22))
        tf = footer.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = text[:48]
        p.font.name = self.font_name
        p.font.size = Pt(8)
        p.font.color.rgb = self.muted

    def _add_accent_bar(self, slide, x, y, width, height) -> None:
        colors = [self.teal, self.coral, self.amber]
        for idx, color in enumerate(colors):
            bar = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                x + int(width * idx / 3),
                y + int(height * idx * 0.08),
                int(width / 3),
                int(height * (1 - idx * 0.08)),
            )
            bar.fill.solid()
            bar.fill.fore_color.rgb = color
            bar.line.fill.background()

    def _add_visual_fallback(self, slide, x, y, width, height, page: PPTPage) -> None:
        panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, width, height)
        panel.fill.solid()
        panel.fill.fore_color.rgb = RGBColor(241, 245, 249)
        panel.line.color.rgb = RGBColor(226, 232, 240)

        for idx, color in enumerate([self.teal, self.coral, self.amber]):
            bar = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                int(x + Inches(0.42)),
                int(y + Inches(0.62 + idx * 0.62)),
                int(width * (0.72 - idx * 0.12)),
                Inches(0.18),
            )
            bar.fill.solid()
            bar.fill.fore_color.rgb = color
            bar.line.fill.background()

        keyword_text = " / ".join(page.keywords[:3]) or page.page_title
        box = slide.shapes.add_textbox(int(x + Inches(0.42)), int(y + height - Inches(1.1)), int(width - Inches(0.84)), Inches(0.48))
        tf = box.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        p.text = keyword_text[:48]
        p.font.name = self.font_name
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = self.dark

    @staticmethod
    def _add_cropped_picture(slide, image_path: Path, x, y, width, height) -> None:
        try:
            with Image.open(image_path) as image:
                image_width, image_height = image.size
            image_ratio = image_width / image_height
            box_ratio = width / height
            picture = slide.shapes.add_picture(str(image_path), x, y, width=width, height=height)
            if image_ratio > box_ratio:
                crop = min((image_ratio - box_ratio) / (2 * image_ratio), 0.49)
                picture.crop_left = crop
                picture.crop_right = crop
            elif image_ratio < box_ratio:
                crop = min((box_ratio - image_ratio) / (2 * box_ratio), 0.49)
                picture.crop_top = crop
                picture.crop_bottom = crop
        except Exception:
            slide.shapes.add_picture(str(image_path), x, y, width=width, height=height)
