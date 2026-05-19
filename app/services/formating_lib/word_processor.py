import difflib
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
        background: #0a0a0a;
        color: #c8c8c8;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    table.diff {
        font-family: Menlo, Consolas, Monaco, 'Liberation Mono', monospace;
        font-size: 12.5px;
        border: none !important;
        border-collapse: collapse;
        width: 100%;
        background: #0a0a0a;
    }
    table.diff td {
        color: #b8b8b8;
        padding: 2px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.025);
    }
    table.diff thead th {
        background: #111 !important;
        color: rgba(255,255,255,0.35) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
    }
    .diff_header {
        background-color: #111 !important;
        color: rgba(255,255,255,0.22) !important;
        font-size: 11px;
        user-select: none;
        border-right: 1px solid rgba(255,255,255,0.04) !important;
        min-width: 36px;
    }
    td.diff_header { text-align: right !important; }
    .diff_next {
        background-color: #111 !important;
        color: rgba(255,255,255,0.22) !important;
        font-size: 11px;
        text-align: center;
        min-width: 24px;
    }
    .diff_next a { color: rgba(255,255,255,0.30) !important; text-decoration: none; }
    .diff_next a:hover { color: rgba(255,255,255,0.60) !important; }
    td.diff_add { background-color: rgba(74, 222, 128, 0.07) !important; }
    td.diff_chg { background-color: rgba(250, 204, 21, 0.06) !important; }
    td.diff_sub { background-color: rgba(248, 113, 113, 0.08) !important; }
    span.diff_add {
        background-color: rgba(74, 222, 128, 0.25) !important;
        color: #86efac !important;
        border-radius: 2px;
        padding: 0 1px;
    }
    span.diff_chg {
        background-color: rgba(250, 204, 21, 0.22) !important;
        color: #fde68a !important;
        border-radius: 2px;
        padding: 0 1px;
    }
    span.diff_sub {
        background-color: rgba(248, 113, 113, 0.24) !important;
        color: #fca5a5 !important;
        border-radius: 2px;
        padding: 0 1px;
    }
    a { color: rgba(255,255,255,0.35); }
    colgroup { border: none !important; }
    """

    def _write_diff_file(
        self,
        filepath: str,
        before_lines: list[str],
        after_lines: list[str],
        check_only: bool,
    ) -> str:
        diff_path = f"{os.path.splitext(filepath)[0]}_diff.html"
        html_diff = difflib.HtmlDiff(wrapcolumn=100)
        target_label = "Потенциальный результат" if check_only else "После форматирования"
        diff_html = html_diff.make_file(
            before_lines,
            after_lines,
            fromdesc="Исходный документ",
            todesc=target_label,
            context=True,
            numlines=2,
            charset="utf-8",
        )

        diff_html = diff_html.replace("</style>", self._DIFF_DARK_CSS + "\n    </style>", 1)

        summary = (
            "Сравнение построено по тексту и стилям абзацев. "
            "Изменения полей страницы и нумерации смотрите в отчёте."
        )
        if before_lines == after_lines:
            summary = (
                "Текстовых или стилевых различий не найдено. "
                "Возможные изменения полей страницы и нумерации смотрите в отчёте."
            )
        banner = (
            "<div style=\"padding:16px 22px 14px;"
            "background:rgba(255,255,255,0.03);"
            "border-bottom:1px solid rgba(255,255,255,0.07);"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\">"
            "<h2 style=\"margin:0 0 6px;font-size:17px;font-weight:600;"
            "color:rgba(255,255,255,0.88);\">Diff документа</h2>"
            f"<p style=\"margin:0;font-size:13px;color:rgba(255,255,255,0.40);\">{summary}</p>"
            "</div>"
        )
        diff_html = diff_html.replace("<body>", f"<body>{banner}", 1)

        with open(diff_path, "w", encoding="utf-8") as diff_file:
            diff_file.write(diff_html)

        return diff_path
