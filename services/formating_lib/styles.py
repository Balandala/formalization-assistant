from docx.oxml.shared import OxmlElement, qn
from docx.oxml import parse_xml
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

class StyleIds:
    Normal = "Normal"
    Heading1 = "Heading1"
    Media = "Media"


def make_text_style():
    """Создаёт стиль 'Normal' — 1.25 см абз., Times New Roman, 14pt."""
    style_xml = f"""
    <w:style xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
             w:type="paragraph" w:styleId="{StyleIds.Normal}" w:default="true">
        <w:name w:val="Normal"/>
        <w:next w:val="{StyleIds.Normal}"/>
        <w:pPr>
            <w:ind w:firstLine="708"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
            <w:sz w:val="28"/>
            <w:szCs w:val="28"/>
        </w:rPr>
    </w:style>
    """
    return parse_xml(style_xml)


def make_heading_style():
    """Создаёт стиль 'Heading1' — по центру, жирный, 14pt."""
    style_xml = f"""
    <w:style xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
             w:type="paragraph" w:styleId="{StyleIds.Heading1}">
        <w:name w:val="Heading 1"/>
        <w:basedOn w:val="{StyleIds.Normal}"/>
        <w:next w:val="{StyleIds.Normal}"/>
        <w:pPr>
            <w:jc w:val="center"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
            <w:sz w:val="28"/>
            <w:szCs w:val="28"/>
            <w:b/>
        </w:rPr>
    </w:style>
    """
    return parse_xml(style_xml)


def make_caption_style():
    """Создаёт стиль 'Media' — по центру, курсив, 14pt."""
    style_xml = f"""
    <w:style xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
             w:type="paragraph" w:styleId="{StyleIds.Media}">
        <w:name w:val="Media"/>
        <w:basedOn w:val="{StyleIds.Normal}"/>
        <w:next w:val="{StyleIds.Normal}"/>
        <w:pPr>
            <w:jc w:val="center"/>
        </w:pPr>
        <w:rPr>
            <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
            <w:sz w:val="28"/>
            <w:szCs w:val="28"/>
            <w:i/>
        </w:rPr>
    </w:style>
    """
    return parse_xml(style_xml)