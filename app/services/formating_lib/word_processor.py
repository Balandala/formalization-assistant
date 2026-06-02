import difflib
import html
import logging
import os
import re

import styles as styles_lib
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.oxml.shared import OxmlElement, qn
from docx.text.paragraph import Paragraph
from formating_config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _fresh_report(check_only: bool = False) -> dict:
    return {
        "paragraphs_formatted": 0,
        "headings_detected": 0,
        "heading_page_breaks_added": 0,
        "figures_numbered": 0,
        "tables_numbered": 0,
        "page_fields_set": False,
        "page_numbering_added": False,
        "table_of_contents_generated": False,
        "table_of_contents_entries": 0,
        "table_of_contents_page": None,
        "check_only": check_only,
        "diff_path": None,
        "diff_available": False,
        "diff_has_changes": False,
        "details": [],
    }


class WordProcessor:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._report: dict = _fresh_report()
        self._figure_counter: int = 0
        self._table_counter: int = 0

    @property
    def report(self) -> dict:
        return self._report

    def process_file(self, filepath: str, check_only: bool = False) -> dict:
        if not filepath.endswith(".docx"):
            raise ValueError("Invalid file type. Only .docx is supported.")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        self._figure_counter = 0
        self._table_counter = 0
        self._report = _fresh_report(check_only=check_only)

        try:
            logger.info(f"Opening document: {filepath}")
            doc = Document(filepath)
            logger.info("Document initialized successfully")
            original_lines = self._document_to_diff_lines(doc)

            processing_doc = Document(filepath) if check_only else doc
            self.process(processing_doc)
            processed_lines = self._document_to_diff_lines(processing_doc)

            diff_path = self._write_diff_file(
                filepath,
                original_lines,
                processed_lines,
                check_only=check_only,
            )
            self._report["diff_path"] = diff_path
            self._report["diff_available"] = True
            self._report["diff_has_changes"] = original_lines != processed_lines

            if not check_only:
                processing_doc.save(filepath)
                logger.info("Document saved successfully")
        except Exception as e:
            logger.exception(
                f"Failed to process document {filepath} with Exception {e}"
            )
            raise

        return self._report

    def process(self, doc: Document) -> None:
        self._doc_init(doc)
        self._override_styles(doc)
        paragraphs = list(doc.paragraphs)

        for i, p in enumerate(paragraphs):
            if self.config.override_formatting:
                self._override_run_properties(p)

            if self._is_generated_toc_title(p):
                continue
            elif self.config.headings and self._is_title(p, paragraphs, i):
                if i > 0 and not self._is_after_page_break(p, paragraphs, i):
                    self._insert_page_break_before(p)
                    self._report["heading_page_breaks_added"] += 1
                    self._report["details"].append(
                        f"Добавлен разрыв страницы перед заголовком: {p.text.strip()[:50]}"
                    )
                p.style = styles_lib.StyleIds.Heading1
                self._report["headings_detected"] += 1
                self._report["details"].append(f"Заголовок: {p.text.strip()[:50]}")
            elif self.config.captions and self._is_after_media(p, paragraphs, i):
                p.style = styles_lib.StyleIds.Media
                self._number_figure_caption(p)
            elif self.config.captions and self._is_after_table(p):
                p.style = styles_lib.StyleIds.Media
                self._number_table_caption(p)
            elif self._is_contains_media(p):
                p.style = styles_lib.StyleIds.Heading1
            elif self.config.normal_text:
                p.style = styles_lib.StyleIds.Normal
                self._report["paragraphs_formatted"] += 1

        if self.config.pages_numerations:
            self._add_footer(doc)
            self._report["page_numbering_added"] = True
        if self.config.page_fields:
            self._add_page_margins(doc)
            self._report["page_fields_set"] = True
        if self.config.table_of_contents:
            self._ensure_table_of_contents(doc)

    def _doc_init(self, doc: Document) -> None:
        if doc._element.body is None:
            body = OxmlElement("w:body")
            doc._element.append(body)

    def _override_styles(self, doc: Document) -> None:
        # Это не функция это пиздец трогать только в антирадиционном костюме
        try:
            styles_part = doc.part.package.part_related_by(RT.STYLES)
        except KeyError:
            styles_part = None

        if styles_part is None:
            pkg = doc.part.package
            uri = "/word/styles.xml"
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"

            found_parts = [p for p in pkg.iter_parts() if p.partname == uri]
            if found_parts:
                styles_part = found_parts[0]
                styles_element = styles_part.element
            else:
                styles_xml = f"<w:styles {nsdecls('w')}></w:styles>"
                styles_element = parse_xml(styles_xml)
                styles_part = pkg._add_part(uri, content_type, styles_element)

            doc.part.relate_to(styles_part, RT.STYLES)
            logger.info("Created new styles.xml and relationship")
        else:
            styles_element = styles_part.element

        styles_element.clear()
        styles_element.append(styles_lib.make_text_style())
        styles_element.append(styles_lib.make_heading_style())
        styles_element.append(styles_lib.make_caption_style())

        if hasattr(doc, "_styles"):
            delattr(doc, "_styles")
        _ = doc.styles  # Принудительно перезагружается кэш стилей

    def _is_title(
        self, p: Paragraph, all_paragraphs: list[Paragraph], index: int
    ) -> bool:
        if not p.text.strip():
            return False

        score = 0

        if self._is_contains_media(p) or self._is_in_table(p):
            score -= 100

        if self._is_after_page_break(p, all_paragraphs, index):
            score += 2
        if self._is_text_short(p):
            score += 2
        if self._is_heading_by_structural_pattern(p):
            score += 2
        if self._is_heading_by_position(p, all_paragraphs, index):
            score += 2

        return score > 2

    def _is_in_table(self, p: Paragraph) -> bool:
        parent = p._element.getparent()
        while parent is not None:
            if parent.tag.endswith("tbl"):
                return True
            parent = parent.getparent()
        return False

    def _is_after_page_break(
        self, p: Paragraph, all_paragraphs: list[Paragraph], index: int
    ) -> bool:
        if index == 0:
            return False
        prev_p = all_paragraphs[index - 1]
        for br in prev_p._element.iter(qn("w:br")):
            if br.get(qn("w:type")) == "page":
                return True
        return False

    def _is_text_short(self, p: Paragraph) -> bool:
        text = p.text.strip()
        return 0 < len(text) < 200

    def _is_heading_by_structural_pattern(self, p: Paragraph) -> bool:
        text = p.text.strip()
        if not text:
            return False
        starts_with_number = text[0].isdigit()
        is_in_numbered_list = bool(p.style.name.startswith("List"))
        return starts_with_number and not is_in_numbered_list

    def _is_heading_by_position(
        self, p: Paragraph, all_paragraphs: list[Paragraph], index: int
    ) -> bool:
        if index == 0:
            return False
        if index > 0:
            prev_text = all_paragraphs[index - 1].text.strip()
            curr_text = p.text.strip()
            ends_with_punct = lambda t: t.endswith((".", "!", "?"))
            return ends_with_punct(prev_text) and not ends_with_punct(curr_text)
        return False

    def _is_after_media(
        self, p: Paragraph, all_paragraphs: list[Paragraph], index: int
    ) -> bool:
        if index == 0:
            return False
        prev_p = all_paragraphs[index - 1]
        if self._is_contains_media(prev_p):
            return len(p.text.strip()) < 200
        return False

    def _is_contains_media(self, p: Paragraph) -> bool:
        for drawing in p._element.iter(qn("w:drawing")):
            if drawing.find(".//" + qn("pic:pic")) is not None:
                return True
        return False

    def _is_after_table(self, p: Paragraph) -> bool:
        prev = p._element.getprevious()
        if prev is None:
            return False
        if prev.tag.endswith("}tbl") and len(p.text.strip()) < 200:
            return True
        return False

    def _number_figure_caption(self, p: Paragraph) -> None:
        self._figure_counter += 1
        caption_text = p.text.strip()
        if not re.match(r"^Рисунок\s+\d+", caption_text):
            prefix = f"Рисунок {self._figure_counter} — "
            if p.runs:
                p.runs[0].text = prefix + p.runs[0].text
            else:
                p.add_run(prefix)
        self._report["figures_numbered"] += 1
        self._report["details"].append(
            f"Рисунок {self._figure_counter}: {caption_text}"
        )

    def _number_table_caption(self, p: Paragraph) -> None:
        self._table_counter += 1
        caption_text = p.text.strip()
        if not re.match(r"^Таблица\s+\d+", caption_text):
            prefix = f"Таблица {self._table_counter} — "
            if p.runs:
                p.runs[0].text = prefix + p.runs[0].text
            else:
                p.add_run(prefix)
        self._report["tables_numbered"] += 1
        self._report["details"].append(f"Таблица {self._table_counter}: {caption_text}")

    def _override_run_properties(self, p: Paragraph) -> None:
        for run in p.runs:
            run.bold = None
            run.italic = None
            run.underline = None
            run.font.color.rgb = None

    def _add_footer(self, doc: Document) -> None:
        section = doc.sections[0]
        footer = section.footer
        paragraph = (
            footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        )
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.clear()
        run = paragraph.add_run()
        fldChar = OxmlElement("w:fldChar")
        fldChar.set(qn("w:fldCharType"), "begin")
        run._r.append(fldChar)

        instrText = OxmlElement("w:instrText")
        instrText.set(qn("xml:space"), "preserve")
        instrText.text = "PAGE"
        run._r.append(instrText)

        fldChar = OxmlElement("w:fldChar")
        fldChar.set(qn("w:fldCharType"), "end")
        run._r.append(fldChar)

    def _add_page_margins(self, doc: Document) -> None:
        section = doc.sections[0]
        sect_pr = section._sectPr
        pg_mar = sect_pr.find(qn("w:pgMar"))
        if pg_mar is None:
            pg_mar = OxmlElement("w:pgMar")
            sect_pr.append(pg_mar)
        pg_mar.set(qn("w:left"), "1700")
        pg_mar.set(qn("w:right"), "850")
        pg_mar.set(qn("w:top"), "1133")
        pg_mar.set(qn("w:bottom"), "1133")

    def _ensure_table_of_contents(self, doc: Document) -> None:
        headings = self._collect_heading_entries(doc)
        self._report["table_of_contents_entries"] = len(headings)
        self._report["table_of_contents_page"] = self.config.table_of_contents_page
        if not headings:
            return

        anchor, current_page = self._get_toc_anchor(doc, headings[0]["paragraph"])
        additional_breaks = max(0, self.config.table_of_contents_page - current_page)

        title = anchor.insert_paragraph_before("Содержание")
        title.style = styles_lib.StyleIds.Heading1

        for _ in range(additional_breaks):
            self._insert_page_break_before(title)

        for heading in headings:
            entry = anchor.insert_paragraph_before(heading["text"])
            entry.style = styles_lib.StyleIds.Normal
            entry.alignment = WD_ALIGN_PARAGRAPH.LEFT

        self._insert_page_break_before(anchor)

        self._report["table_of_contents_generated"] = True
        self._report["details"].append(
            f"Содержание добавлено {self.config.table_of_contents_page}-й страницей: {len(headings)}"
        )

    def _collect_heading_entries(self, doc: Document) -> list[dict[str, Paragraph | str]]:
        entries: list[dict[str, Paragraph | str]] = []
        for paragraph in doc.paragraphs:
            if self._is_generated_toc_title(paragraph):
                continue
            if (
                paragraph.style is not None
                and paragraph.style.style_id == styles_lib.StyleIds.Heading1
                and paragraph.text.strip()
            ):
                entries.append({"paragraph": paragraph, "text": paragraph.text.strip()})
        return entries

    def _get_toc_anchor(
        self,
        doc: Document,
        first_heading: Paragraph,
    ) -> tuple[Paragraph, int]:
        target_page = self.config.table_of_contents_page
        current_page = 1

        for paragraph in doc.paragraphs:
            if current_page >= target_page:
                return paragraph, current_page
            if paragraph == first_heading:
                return paragraph, current_page
            current_page += self._count_page_breaks(paragraph)

        return first_heading if doc.paragraphs else doc.add_paragraph(), current_page

    def _is_generated_toc_title(self, paragraph: Paragraph) -> bool:
        return paragraph.text.strip().lower() == "содержание"

    def _insert_page_break_before(self, paragraph: Paragraph) -> None:
        page_break = paragraph.insert_paragraph_before()
        page_break.add_run().add_break(WD_BREAK.PAGE)

    def _count_page_breaks(self, paragraph: Paragraph) -> int:
        page_breaks = 0
        for br in paragraph._element.iter(qn("w:br")):
            if br.get(qn("w:type")) == "page":
                page_breaks += 1
        return page_breaks

    def _paragraph_contains_toc_field(self, paragraph: Paragraph) -> bool:
        for instr_text in paragraph._element.iter(qn("w:instrText")):
            if "TOC " in (instr_text.text or ""):
                return True
        return False

    def _document_to_diff_lines(self, doc: Document) -> list[str]:
        lines: list[str] = []

        for paragraph in doc.paragraphs:
            for _ in range(self._count_page_breaks(paragraph)):
                lines.append("[PAGE BREAK]")
            style_name = paragraph.style.name if paragraph.style is not None else "No Style"
            text = self._normalize_diff_text(paragraph.text)
            line = f"[{style_name}]"
            if text:
                line = f"{line} {text}"
            lines.append(line)

        for index, table in enumerate(doc.tables, start=1):
            lines.append(f"[TABLE {index}]")
            for row in table.rows:
                cells = [self._normalize_diff_text(cell.text) for cell in row.cells]
                lines.append(" | ".join(cells))

        if not lines:
            lines.append("[EMPTY DOCUMENT]")

        return lines

    @staticmethod
    def _normalize_diff_text(text: str) -> str:
        return " ".join(text.replace("\xa0", " ").split())

    _DIFF_DARK_CSS = """
    body {
        background: #080808;
        color: #c8c8c8;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* ===== Summary panel ===== */
    .diff-summary {
        padding: 26px 30px 8px;
        background:
            radial-gradient(ellipse at top, rgba(255,255,255,0.04), transparent 65%),
            #0a0a0a;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .summary-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 6px;
    }
    .summary-head h2 {
        margin: 0;
        font-size: 19px;
        font-weight: 600;
        letter-spacing: -0.2px;
        color: rgba(255,255,255,0.92);
    }
    .summary-mode {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: rgba(255,255,255,0.50);
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 4px 12px;
    }
    .summary-mode.is-check {
        color: #bfdbfe;
        background: rgba(147,197,253,0.08);
        border-color: rgba(147,197,253,0.22);
    }
    .summary-hint {
        margin: 0 0 22px;
        font-size: 13px;
        line-height: 1.55;
        color: rgba(255,255,255,0.45);
        max-width: 760px;
    }

    .changes-section { margin-bottom: 22px; }
    .changes-section-title {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 12px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255,255,255,0.58);
    }
    .changes-section-title .dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #4ade80;
        box-shadow: 0 0 12px rgba(74,222,128,0.55);
    }
    .changes-section.is-hidden .changes-section-title .dot {
        background: #93c5fd;
        box-shadow: 0 0 12px rgba(147,197,253,0.55);
    }
    .changes-section-title .count-badge {
        margin-left: auto;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        color: rgba(255,255,255,0.70);
        padding: 2px 9px;
        border-radius: 8px;
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.4px;
    }
    .changes-section-sub {
        margin: -4px 0 12px;
        font-size: 12px;
        color: rgba(255,255,255,0.36);
        line-height: 1.5;
    }
    .changes-list {
        list-style: none;
        counter-reset: ch;
        padding: 0;
        margin: 0;
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
    }
    @media (min-width: 1000px) {
        .changes-list { grid-template-columns: 1fr 1fr; }
    }
    .change-card {
        counter-increment: ch;
        position: relative;
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 14px 16px 14px 52px;
        transition: border-color 0.2s, background 0.2s;
    }
    .change-card:hover {
        background: rgba(255,255,255,0.04);
        border-color: rgba(255,255,255,0.12);
    }
    .change-card::before {
        content: counter(ch);
        position: absolute;
        top: 14px;
        left: 14px;
        width: 26px;
        height: 26px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        background: rgba(74,222,128,0.12);
        border: 1px solid rgba(74,222,128,0.30);
        color: #86efac;
    }
    .changes-section.is-hidden .change-card::before {
        background: rgba(147,197,253,0.10);
        border-color: rgba(147,197,253,0.26);
        color: #bfdbfe;
    }
    .change-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 8px;
    }
    .change-title {
        font-size: 13.5px;
        font-weight: 600;
        color: rgba(255,255,255,0.90);
        line-height: 1.35;
    }
    .change-count {
        flex-shrink: 0;
        font-size: 11px;
        font-weight: 600;
        color: rgba(255,255,255,0.55);
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 2px 8px;
        border-radius: 999px;
        white-space: nowrap;
    }
    .change-quote {
        position: relative;
        margin: 0;
        padding: 10px 12px 10px 16px;
        background: rgba(255,255,255,0.025);
        border-left: 2px solid rgba(255,255,255,0.20);
        border-radius: 0 8px 8px 0;
        color: rgba(255,255,255,0.65);
        font-size: 12.5px;
        font-style: italic;
        line-height: 1.55;
    }
    .change-quote::before {
        content: '\\201C';
        position: absolute;
        left: 4px; top: 2px;
        font-size: 18px;
        font-family: Georgia, serif;
        font-style: normal;
        color: rgba(255,255,255,0.25);
        line-height: 1;
    }
    .change-cite {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 8px;
        font-size: 10.5px;
        font-style: normal;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: rgba(255,255,255,0.40);
    }
    .change-cite::before {
        content: '';
        width: 14px; height: 1px;
        background: rgba(255,255,255,0.25);
    }

    .changes-empty {
        margin: 8px 0 20px;
        padding: 14px 16px;
        background: rgba(74,222,128,0.06);
        border: 1px solid rgba(74,222,128,0.22);
        border-radius: 12px;
        color: #a7f3c4;
        font-size: 13px;
    }

    /* ===== Diff section ===== */
    .diff-section {
        padding: 22px 30px 32px;
    }
    .diff-section-head {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 14px;
    }
    .diff-section-head h3 {
        margin: 0;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255,255,255,0.58);
    }
    .diff-section-head .hint {
        font-size: 12px;
        color: rgba(255,255,255,0.32);
    }
    .diff-empty {
        padding: 14px 16px;
        background: rgba(255,255,255,0.02);
        border: 1px dashed rgba(255,255,255,0.10);
        border-radius: 12px;
        color: rgba(255,255,255,0.45);
        font-size: 13px;
    }

    /* ===== Pretty diff list ===== */
    .diff-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 0 0 18px;
        font-size: 11px;
        color: rgba(255,255,255,0.50);
    }
    .diff-legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 9px 3px 6px;
        border-radius: 999px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .diff-legend-chip .swatch {
        width: 8px; height: 8px;
        border-radius: 50%;
    }
    .diff-legend-chip.is-add .swatch { background: #4ade80; }
    .diff-legend-chip.is-del .swatch { background: #f87171; }
    .diff-legend-chip.is-chg .swatch { background: #facc15; }

    .diff-list {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    .diff-block {
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        overflow: hidden;
        background: rgba(255,255,255,0.015);
    }
    .diff-block.is-add { border-color: rgba(74,222,128,0.25); }
    .diff-block.is-del { border-color: rgba(248,113,113,0.25); }
    .diff-block.is-chg { border-color: rgba(250,204,21,0.22); }

    .diff-block-head {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 16px;
        background: rgba(255,255,255,0.025);
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .diff-marker {
        width: 24px;
        height: 24px;
        border-radius: 7px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        flex-shrink: 0;
        font-family: Menlo, Consolas, monospace;
    }
    .is-add .diff-marker {
        background: rgba(74,222,128,0.16);
        color: #86efac;
        border: 1px solid rgba(74,222,128,0.30);
    }
    .is-del .diff-marker {
        background: rgba(248,113,113,0.16);
        color: #fca5a5;
        border: 1px solid rgba(248,113,113,0.30);
    }
    .is-chg .diff-marker {
        background: rgba(250,204,21,0.16);
        color: #fde68a;
        border: 1px solid rgba(250,204,21,0.28);
    }
    .diff-action {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: rgba(255,255,255,0.80);
    }
    .diff-meta {
        margin-left: auto;
        color: rgba(255,255,255,0.36);
        font-size: 11px;
        font-weight: 500;
    }

    .diff-lines {
        list-style: none;
        padding: 6px 12px 10px;
        margin: 0;
    }
    .diff-line {
        display: flex;
        align-items: baseline;
        gap: 10px;
        padding: 6px 10px;
        margin: 4px 0;
        border-radius: 8px;
        line-height: 1.55;
        font-size: 13.5px;
        color: rgba(255,255,255,0.82);
        word-break: break-word;
    }
    .diff-line.is-add { background: rgba(74,222,128,0.06); }
    .diff-line.is-del {
        background: rgba(248,113,113,0.06);
        text-decoration: line-through;
        text-decoration-color: rgba(248,113,113,0.30);
        text-decoration-thickness: 1px;
    }
    .diff-line.is-del .line-text { color: rgba(255,255,255,0.55); }

    .line-num {
        flex-shrink: 0;
        min-width: 30px;
        text-align: right;
        color: rgba(255,255,255,0.22);
        font-size: 11px;
        font-family: Menlo, Consolas, monospace;
        user-select: none;
    }
    .line-tag {
        display: inline-flex;
        align-items: center;
        padding: 1px 8px;
        border-radius: 6px;
        font-size: 10.5px;
        font-family: Menlo, Consolas, monospace;
        font-weight: 600;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.65);
        flex-shrink: 0;
        white-space: nowrap;
        letter-spacing: 0.2px;
        text-decoration: none;
    }
    .line-tag.tag-heading {
        background: rgba(252,211,77,0.10);
        border-color: rgba(252,211,77,0.26);
        color: #fde68a;
    }
    .line-tag.tag-media {
        background: rgba(216,180,254,0.10);
        border-color: rgba(216,180,254,0.24);
        color: #e9d5ff;
    }
    .line-tag.tag-page-break {
        background: rgba(147,197,253,0.10);
        border-color: rgba(147,197,253,0.26);
        color: #bfdbfe;
    }
    .line-tag.tag-table {
        background: rgba(125,211,252,0.10);
        border-color: rgba(125,211,252,0.26);
        color: #bae6fd;
    }
    .line-tag.tag-empty {
        background: rgba(255,255,255,0.025);
        border-color: rgba(255,255,255,0.06);
        color: rgba(255,255,255,0.40);
    }
    .line-text {
        flex: 1;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .line-text.is-placeholder {
        color: rgba(255,255,255,0.30);
        font-style: italic;
    }
    .diff-inline-add {
        background: rgba(74,222,128,0.22);
        color: #bbf7d0;
        border-radius: 3px;
        padding: 0 2px;
    }
    .diff-inline-del {
        background: rgba(248,113,113,0.22);
        color: #fecaca;
        border-radius: 3px;
        padding: 0 2px;
        text-decoration: line-through;
        text-decoration-color: rgba(248,113,113,0.45);
    }

    .diff-pair {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0;
    }
    @media (min-width: 980px) {
        .diff-pair { grid-template-columns: 1fr 1fr; }
        .diff-pair-side + .diff-pair-side {
            border-left: 1px solid rgba(255,255,255,0.05);
        }
    }
    .diff-pair-side { padding: 4px 4px 8px; }
    .diff-pair-label {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px 4px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255,255,255,0.45);
    }
    .diff-pair-label .swatch {
        width: 7px; height: 7px; border-radius: 50%;
    }
    .diff-pair-side.is-del .diff-pair-label .swatch { background: #f87171; }
    .diff-pair-side.is-add .diff-pair-label .swatch { background: #4ade80; }
    .diff-pair-side.is-del .diff-pair-label { color: #fca5a5; }
    .diff-pair-side.is-add .diff-pair-label { color: #86efac; }

    .diff-gap {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px 0;
        color: rgba(255,255,255,0.32);
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.7px;
    }
    .diff-gap-rule {
        flex: 1;
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255,255,255,0.10),
            transparent
        );
    }

    a { color: rgba(255,255,255,0.50); }

    /* ===== Scrollbar ===== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.20); }
    """

    _GOST_REFS: dict[str, tuple[str, str, str]] = {
        # ключ: (заголовок правки, цитата ГОСТ, источник)
        "heading": (
            "Стиль заголовка раздела",
            "Заголовки разделов выполняются заглавными буквами. Каждый раздел "
            "рекомендуется начинать с нового листа (симметрично тексту, по центру). "
            "Подчёркивать, выделять заголовки не допускается.",
            "ГОСТ 7.32-2017, разд. «Заголовки»",
        ),
        "heading_break": (
            "Разрыв страницы перед разделом",
            "Каждый раздел рекомендуется начинать с нового листа "
            "(симметрично тексту, по центру).",
            "ГОСТ 7.32-2017, разд. «Заголовки»",
        ),
        "figure_caption": (
            "Сквозная нумерация рисунков",
            "Иллюстрации, за исключением иллюстраций приложений, следует "
            "нумеровать арабскими цифрами сквозной нумерацией. Слово «Рисунок», "
            "его номер и наименование помещают после пояснительных данных под "
            "рисунком по центру страницы.",
            "ГОСТ 7.32-2017, разд. «Иллюстрации»",
        ),
        "table_caption": (
            "Сквозная нумерация таблиц",
            "На все таблицы документа должны быть приведены ссылки в тексте. "
            "Слово «Таблица» указывают один раз слева над первой частью таблицы "
            "с абзацного отступа с указанием её номера.",
            "ГОСТ 7.32-2017, разд. «Таблицы»",
        ),
        "normal_text": (
            "Стиль основного текста",
            "Во всей работе, включая сноски, текст выравнивается по ширине рабочего "
            "листа. Абзацы в тексте следует начинать с отступа, равного 1,25 см.",
            "ГОСТ 7.32-2017, разд. «Общие требования»",
        ),
        "toc": (
            "Содержание работы",
            "Содержание включает наименования всех разделов и подразделов работы "
            "с указанием номеров страниц, на которых они расположены. "
            "Содержание помещают после титульного листа в начале работы.",
            "ГОСТ 7.32-2017, разд. «Содержание»",
        ),
        "font_times": (
            "Шрифт Times New Roman, 14 пт",
            "Текст работы должен быть набран на компьютере через 1,5 межстрочных "
            "интервала, размер шрифта 14 пт (Times New Roman).",
            "ГОСТ 7.32-2017, разд. «Общие требования»",
        ),
        "indent": (
            "Абзацный отступ 1,25 см",
            "Абзацы в тексте следует начинать с отступа, равного 1,25 см. "
            "Абзацный отступ должен быть одинаковым по всей работе.",
            "ГОСТ 7.32-2017, разд. «Общие требования»",
        ),
        "page_margins": (
            "Поля страницы 20 / 20 / 30 / 15 мм",
            "Текст печатается на одной стороне листа с полями: сверху — 20 мм, "
            "снизу — 20 мм, слева — 30 мм, справа — 15 мм.",
            "ГОСТ 7.32-2017, разд. «Общие требования»",
        ),
        "page_numbers": (
            "Сквозная нумерация страниц",
            "Страницы следует нумеровать арабскими цифрами, соблюдая сквозную "
            "нумерацию по всему тексту работы. Номер страницы проставляют в "
            "центре нижней части листа без точки (10 пт).",
            "ГОСТ 7.32-2017, разд. «Нумерация страниц»",
        ),
        "heading_style": (
            "Заголовок: полужирный, по центру",
            "Заголовки разделов размещают симметрично тексту, по центру. "
            "Шрифт заголовков — Times New Roman, 14 пт, полужирное начертание; "
            "заголовки оформляются единообразно по всей работе.",
            "ГОСТ 7.32-2017, разд. «Заголовки»",
        ),
        "caption_style": (
            "Подпись к рисунку / таблице",
            "Подпись («Рисунок N — ...», «Таблица N — ...») оформляется единообразно: "
            "по центру страницы, шрифт Times New Roman 14 пт, без точки в конце.",
            "ГОСТ 7.32-2017, разд. «Иллюстрации», «Таблицы»",
        ),
        "clean_runs": (
            "Очищено произвольное выделение текста",
            "Подчёркивать, выделять текст произвольным цветом или начертанием "
            "не допускается. Основной текст оформляется единым стилем работы.",
            "ГОСТ 7.32-2017, разд. «Общие требования»",
        ),
    }

    def _change_card(self, key: str, count: int | None = None) -> str:
        title, quote, source = self._GOST_REFS[key]
        count_html = (
            f'<span class="change-count">× {count}</span>' if count else ""
        )
        return (
            '<li class="change-card">'
            '<div class="change-head">'
            f'<span class="change-title">{title}</span>'
            f"{count_html}"
            "</div>"
            '<div class="change-quote">'
            f"{quote}"
            f'<span class="change-cite">{source}</span>'
            "</div>"
            "</li>"
        )

    def _build_summary_html(self, check_only: bool, has_visible_diff: bool) -> str:
        report = self._report
        cfg = self.config

        visible: list[str] = []
        if report["headings_detected"]:
            visible.append(self._change_card("heading", report["headings_detected"]))
        if report["heading_page_breaks_added"]:
            visible.append(
                self._change_card("heading_break", report["heading_page_breaks_added"])
            )
        if report["figures_numbered"]:
            visible.append(
                self._change_card("figure_caption", report["figures_numbered"])
            )
        if report["tables_numbered"]:
            visible.append(
                self._change_card("table_caption", report["tables_numbered"])
            )
        if report["paragraphs_formatted"]:
            visible.append(
                self._change_card("normal_text", report["paragraphs_formatted"])
            )
        if report["table_of_contents_generated"]:
            visible.append(
                self._change_card("toc", report["table_of_contents_entries"])
            )

        hidden: list[str] = []
        any_text_styled = bool(
            report["paragraphs_formatted"]
            or report["headings_detected"]
            or report["figures_numbered"]
            or report["tables_numbered"]
        )
        if any_text_styled or cfg.normal_text:
            hidden.append(self._change_card("font_times"))
            hidden.append(self._change_card("indent"))
        if report["headings_detected"]:
            hidden.append(self._change_card("heading_style"))
        if report["figures_numbered"] or report["tables_numbered"]:
            hidden.append(self._change_card("caption_style"))
        if report["page_fields_set"]:
            hidden.append(self._change_card("page_margins"))
        if report["page_numbering_added"]:
            hidden.append(self._change_card("page_numbers"))
        if cfg.override_formatting:
            hidden.append(self._change_card("clean_runs"))

        mode_label = (
            '<span class="summary-mode is-check">Режим проверки</span>'
            if check_only
            else '<span class="summary-mode">Применено</span>'
        )

        if not visible and not hidden:
            intro = (
                "Документ уже соответствует требованиям к оформлению — "
                "правки не потребовались."
            )
        elif check_only:
            intro = (
                "Ниже перечислены правки, которые будут применены к документу "
                "при форматировании. Каждая правка сопровождается ссылкой на "
                "соответствующий пункт ГОСТ."
            )
        else:
            intro = (
                "Ниже перечислены применённые правки. Каждая правка сопровождается "
                "ссылкой на соответствующий пункт ГОСТ."
            )

        parts: list[str] = [
            '<div class="diff-summary">',
            '<div class="summary-head">',
            "<h2>Сводка изменений</h2>",
            mode_label,
            "</div>",
            f'<p class="summary-hint">{intro}</p>',
        ]

        if not visible and not hidden:
            parts.append(
                '<div class="changes-empty">'
                "Документ уже соответствует требованиям ГОСТ — правок не вносилось."
                "</div>"
            )

        if visible:
            parts.append('<div class="changes-section is-visible">')
            parts.append(
                '<div class="changes-section-title">'
                '<span class="dot"></span>'
                "Видимые в построчном diff"
                f'<span class="count-badge">{len(visible)}</span>'
                "</div>"
            )
            parts.append('<ol class="changes-list">' + "".join(visible) + "</ol>")
            parts.append("</div>")

        if hidden:
            parts.append('<div class="changes-section is-hidden">')
            parts.append(
                '<div class="changes-section-title">'
                '<span class="dot"></span>'
                "Стилевые правки (не видны в diff)"
                f'<span class="count-badge">{len(hidden)}</span>'
                "</div>"
            )
            parts.append(
                '<p class="changes-section-sub">'
                "Эти правки применяются на уровне стилей и свойств документа "
                "(шрифт, абзацный отступ, поля страницы, колонтитулы). "
                "Они не отображаются в построчном сравнении ниже."
                "</p>"
            )
            parts.append('<ol class="changes-list">' + "".join(hidden) + "</ol>")
            parts.append("</div>")

        parts.append("</div>")
        return "".join(parts)

    _LINE_PATTERN = re.compile(r"^\[(?P<tag>[^\]]+)\](?: (?P<text>.*))?$")

    @classmethod
    def _parse_diff_line(cls, line: str) -> tuple[str | None, str]:
        match = cls._LINE_PATTERN.match(line)
        if match:
            return match.group("tag"), (match.group("text") or "")
        return None, line

    @staticmethod
    def _classify_tag(tag: str) -> str:
        upper = tag.upper()
        if "PAGE BREAK" in upper:
            return "page-break"
        if upper.startswith("HEADING") or upper == "TITLE":
            return "heading"
        if upper == "MEDIA":
            return "media"
        if upper.startswith("TABLE"):
            return "table"
        if upper == "EMPTY DOCUMENT":
            return "empty"
        return "default"

    @staticmethod
    def _pluralize_ru(n: int, one: str, few: str, many: str) -> str:
        n100 = n % 100
        n10 = n % 10
        if 11 <= n100 <= 14:
            return many
        if n10 == 1:
            return one
        if 2 <= n10 <= 4:
            return few
        return many

    def _render_line(
        self,
        line: str,
        line_num: int,
        kind: str,
        *,
        text_html: str | None = None,
    ) -> str:
        tag, text = self._parse_diff_line(line)
        num_html = f'<span class="line-num">{line_num}</span>'
        tag_html = ""
        if tag:
            tag_class = self._classify_tag(tag)
            tag_html = (
                f'<span class="line-tag tag-{tag_class}">{html.escape(tag)}</span>'
            )
        if text_html is None:
            if text:
                content_html = (
                    f'<span class="line-text">{html.escape(text)}</span>'
                )
            elif tag:
                content_html = ""
            else:
                content_html = (
                    '<span class="line-text is-placeholder">пустая строка</span>'
                )
        else:
            content_html = f'<span class="line-text">{text_html}</span>'
        return (
            f'<li class="diff-line is-{kind}">{num_html}{tag_html}{content_html}</li>'
        )

    def _inline_text_diff(self, before: str, after: str) -> tuple[str, str]:
        before_tokens = re.findall(r"\S+|\s+", before)
        after_tokens = re.findall(r"\S+|\s+", after)
        matcher = difflib.SequenceMatcher(
            a=before_tokens, b=after_tokens, autojunk=False
        )
        before_parts: list[str] = []
        after_parts: list[str] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                chunk = html.escape("".join(before_tokens[i1:i2]))
                before_parts.append(chunk)
                after_parts.append(chunk)
            elif tag == "delete":
                before_parts.append(
                    '<span class="diff-inline-del">'
                    + html.escape("".join(before_tokens[i1:i2]))
                    + "</span>"
                )
            elif tag == "insert":
                after_parts.append(
                    '<span class="diff-inline-add">'
                    + html.escape("".join(after_tokens[j1:j2]))
                    + "</span>"
                )
            elif tag == "replace":
                before_parts.append(
                    '<span class="diff-inline-del">'
                    + html.escape("".join(before_tokens[i1:i2]))
                    + "</span>"
                )
                after_parts.append(
                    '<span class="diff-inline-add">'
                    + html.escape("".join(after_tokens[j1:j2]))
                    + "</span>"
                )
        return "".join(before_parts), "".join(after_parts)

    def _render_paired_line(
        self,
        before_line: str,
        before_num: int,
        after_line: str,
        after_num: int,
    ) -> tuple[str, str]:
        before_tag, before_text = self._parse_diff_line(before_line)
        after_tag, after_text = self._parse_diff_line(after_line)
        if before_text and after_text and before_text != after_text:
            before_html, after_html = self._inline_text_diff(
                before_text, after_text
            )
            before_row = self._render_line(
                before_line, before_num, "del", text_html=before_html
            )
            after_row = self._render_line(
                after_line, after_num, "add", text_html=after_html
            )
        else:
            before_row = self._render_line(before_line, before_num, "del")
            after_row = self._render_line(after_line, after_num, "add")
        return before_row, after_row

    def _render_block_head(self, kind: str, count: int) -> str:
        word = self._pluralize_ru(count, "строка", "строки", "строк")
        meta = (
            "1 правка"
            if count == 1
            else f"{count} {word}"
        )
        configs = {
            "add": ("+", "Добавлено"),
            "del": ("−", "Удалено"),
            "chg": ("↔", "Изменено"),
        }
        icon, label = configs[kind]
        return (
            '<div class="diff-block-head">'
            f'<span class="diff-marker">{icon}</span>'
            f'<span class="diff-action">{label}</span>'
            f'<span class="diff-meta">{meta}</span>'
            "</div>"
        )

    def _render_lines(self, lines: list[str], start_num: int, kind: str) -> str:
        items = [
            self._render_line(line, start_num + offset, kind)
            for offset, line in enumerate(lines)
        ]
        return '<ol class="diff-lines">' + "".join(items) + "</ol>"

    def _render_replace_block(
        self,
        before_lines: list[str],
        before_start: int,
        after_lines: list[str],
        after_start: int,
    ) -> str:
        total = max(len(before_lines), len(after_lines))
        head = self._render_block_head("chg", total)

        if len(before_lines) == len(after_lines):
            before_rows: list[str] = []
            after_rows: list[str] = []
            for offset, (before_line, after_line) in enumerate(
                zip(before_lines, after_lines)
            ):
                before_row, after_row = self._render_paired_line(
                    before_line,
                    before_start + offset,
                    after_line,
                    after_start + offset,
                )
                before_rows.append(before_row)
                after_rows.append(after_row)
            before_html = (
                '<ol class="diff-lines">' + "".join(before_rows) + "</ol>"
            )
            after_html = (
                '<ol class="diff-lines">' + "".join(after_rows) + "</ol>"
            )
        else:
            before_html = self._render_lines(before_lines, before_start, "del")
            after_html = self._render_lines(after_lines, after_start, "add")

        body = (
            '<div class="diff-pair">'
            '<div class="diff-pair-side is-del">'
            '<div class="diff-pair-label"><span class="swatch"></span>Было</div>'
            f"{before_html}"
            "</div>"
            '<div class="diff-pair-side is-add">'
            '<div class="diff-pair-label"><span class="swatch"></span>Стало</div>'
            f"{after_html}"
            "</div>"
            "</div>"
        )
        return f'<div class="diff-block is-chg">{head}{body}</div>'

    def _render_gap(self, n: int) -> str:
        word = self._pluralize_ru(n, "строка", "строки", "строк")
        return (
            '<div class="diff-gap">'
            '<span class="diff-gap-rule"></span>'
            f"<span>{n} {word} без изменений</span>"
            '<span class="diff-gap-rule"></span>'
            "</div>"
        )

    _DIFF_GAP_THRESHOLD = 1

    def _build_diff_list_html(
        self, before_lines: list[str], after_lines: list[str]
    ) -> str:
        matcher = difflib.SequenceMatcher(
            a=before_lines, b=after_lines, autojunk=False
        )
        opcodes = matcher.get_opcodes()
        parts: list[str] = [
            '<div class="diff-legend">'
            '<span class="diff-legend-chip is-add">'
            '<span class="swatch"></span>Добавлено</span>'
            '<span class="diff-legend-chip is-del">'
            '<span class="swatch"></span>Удалено</span>'
            '<span class="diff-legend-chip is-chg">'
            '<span class="swatch"></span>Изменено</span>'
            "</div>",
            '<div class="diff-list">',
        ]
        last_was_change = False
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                n = i2 - i1
                # Show gap marker only between changes, and only if the gap
                # is non-trivial.
                if last_was_change and n > self._DIFF_GAP_THRESHOLD:
                    parts.append(self._render_gap(n))
                continue
            if tag == "insert":
                head = self._render_block_head("add", j2 - j1)
                body = self._render_lines(after_lines[j1:j2], j1 + 1, "add")
                parts.append(f'<div class="diff-block is-add">{head}{body}</div>')
            elif tag == "delete":
                head = self._render_block_head("del", i2 - i1)
                body = self._render_lines(before_lines[i1:i2], i1 + 1, "del")
                parts.append(f'<div class="diff-block is-del">{head}{body}</div>')
            elif tag == "replace":
                parts.append(
                    self._render_replace_block(
                        before_lines[i1:i2],
                        i1 + 1,
                        after_lines[j1:j2],
                        j1 + 1,
                    )
                )
            last_was_change = True
        parts.append("</div>")
        return "".join(parts)

    def _build_diff_section_html(
        self, before_lines: list[str], after_lines: list[str], check_only: bool
    ) -> str:
        has_visible_diff = before_lines != after_lines
        target_label = (
            "Потенциальный результат" if check_only else "После форматирования"
        )
        if has_visible_diff:
            head_hint = (
                f"Сравнение текста и стилей абзацев: «Исходный документ» → "
                f"«{target_label}». Стилевые правки (шрифт, поля и т. п.) "
                "перечислены в сводке выше."
            )
            body = self._build_diff_list_html(before_lines, after_lines)
        else:
            head_hint = ""
            body = (
                '<div class="diff-empty">'
                "Текст и стили абзацев не изменились — все правки относятся к "
                "невидимому в diff форматированию (шрифт, поля страницы, колонтитулы)."
                "</div>"
            )
        head_hint_html = f'<span class="hint">{head_hint}</span>' if head_hint else ""
        return (
            '<div class="diff-section">'
            '<div class="diff-section-head">'
            "<h3>Построчное сравнение</h3>"
            f"{head_hint_html}"
            "</div>"
            f"{body}"
            "</div>"
        )

    def _write_diff_file(
        self,
        filepath: str,
        before_lines: list[str],
        after_lines: list[str],
        check_only: bool,
    ) -> str:
        diff_path = f"{os.path.splitext(filepath)[0]}_diff.html"
        has_visible_diff = before_lines != after_lines

        summary_html = self._build_summary_html(
            check_only=check_only, has_visible_diff=has_visible_diff
        )
        diff_section_html = self._build_diff_section_html(
            before_lines=before_lines,
            after_lines=after_lines,
            check_only=check_only,
        )

        page_title = "Diff документа"
        html_document = (
            "<!DOCTYPE html>"
            '<html lang="ru">'
            "<head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{page_title}</title>"
            f"<style>{self._DIFF_DARK_CSS}</style>"
            "</head>"
            "<body>"
            f"{summary_html}"
            f"{diff_section_html}"
            "</body>"
            "</html>"
        )

        with open(diff_path, "w", encoding="utf-8") as diff_file:
            diff_file.write(html_document)

        return diff_path
