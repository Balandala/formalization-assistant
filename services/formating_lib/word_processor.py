from docx import Document
from docx.oxml.shared import OxmlElement, qn
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from . import StylesLib
from .FormatingConfiguration import FormatingConfiguration

import os


class WordProcessor:
    def __init__(self, config: FormatingConfiguration):
        self.config = config

    def process_file(self, filepath: str):
        if not filepath.endswith(".docx"):
            raise ValueError("Invalid file type. Only .docx is supported.")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        doc = Document(filepath)
        self.process(doc)
        doc.save(filepath)  # Перезаписываем исходный файл

    def process(self, doc):
        self._doc_init(doc)
        self._override_styles(doc)
        paragraphs = list(doc.paragraphs)  # python-docx не поддерживает Descendants напрямую

        for i, p in enumerate(paragraphs):
            if self.config.override_formatting:
                self._override_run_properties(p)

            if self.config.headings and self._is_title(p, paragraphs, i):
                p.style = StylesLib.StyleIds.Heading1
            elif self.config.captions and self._is_after_media(p, paragraphs, i):
                p.style = StylesLib.StyleIds.Media
            elif self._is_contains_media(p):
                p.style = StylesLib.StyleIds.Heading1
            elif self.config.normal_text:
                p.style = StylesLib.StyleIds.Normal

        if self.config.pages_numeration:
            self._add_footer(doc)
        if self.config.page_fields:
            self._add_page_margins(doc)

    def _doc_init(self, doc):
        if not doc._element.body:
            doc._element.body = OxmlElement("w:body")
            doc._element.append(doc._element.body)

    def _override_styles(self, doc):
        styles_part = doc.styles._element.getparent()
        # Удаляем старые стили и добавляем свои
        styles_part.clear()  # Осторожно! Это удаляет все стили.
        styles_part.append(StylesLib.make_text_style())
        styles_part.append(StylesLib.make_heading_style())
        styles_part.append(StylesLib.make_caption_style())

    def _is_title(self, p, all_paragraphs, index):
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

    def _is_in_table(self, p):
        # python-docx не даёт прямого доступа к родителям — нужно проверять через XML
        parent = p._element.getparent()
        while parent is not None:
            if parent.tag.endswith("tbl"):
                return True
            parent = parent.getparent()
        return False

    def _is_after_page_break(self, p, all_paragraphs, index):
        if index == 0:
            return False
        prev_p = all_paragraphs[index - 1]
        for br in prev_p._element.iter(qn("w:br")):
            if br.get(qn("w:type")) == "page":
                return True
        return False

    def _is_text_short(self, p):
        text = p.text.strip()
        return 0 < len(text) < 200

    def _is_heading_by_structural_pattern(self, p):
        text = p.text.strip()
        if not text:
            return False
        starts_with_number = text[0].isdigit()
        # Проверка на нумерованный список — упрощённо
        is_in_numbered_list = bool(p.style.name.startswith("List"))
        return starts_with_number and not is_in_numbered_list

    def _is_heading_by_position(self, p, all_paragraphs, index):
        if index == 0:
            return True
        if index > 0:
            prev_text = all_paragraphs[index - 1].text.strip()
            curr_text = p.text.strip()
            ends_with_punct = lambda t: t.endswith((".", "!", "?"))
            return ends_with_punct(prev_text) and not ends_with_punct(curr_text)
        return False

    def _is_after_media(self, p, all_paragraphs, index):
        if index == 0:
            return False
        prev_p = all_paragraphs[index - 1]
        if self._is_contains_media(prev_p):
            return len(p.text.strip()) < 200
        return False

    def _is_contains_media(self, p):
        # Проверка на изображение
        for drawing in p._element.iter(qn("w:drawing")):
            if drawing.find(".//" + qn("pic:pic")) is not None:
                return True
        return False

    def _override_run_properties(self, p):
        for run in p.runs:
            run.bold = None
            run.italic = None
            run.underline = None
            run.font.color.rgb = None

    def _add_footer(self, doc):
        # Создание нижнего колонтитула с номером страницы
        section = doc.sections[0]
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.clear()
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar)

        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        run._r.append(instrText)

        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar)

    def _add_page_margins(self, doc):
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