from docxtpl import DocxTemplate
from shared.models import TitleData
import os


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(CURRENT_DIR, "templates", "title1.docx")

def generate_document(data: TitleData, filename: str):

    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Шаблон не найден: {TEMPLATE_PATH}")

    doc = DocxTemplate(TEMPLATE_PATH)
    context = {
        "institute": data.institute,
        "work_type": data.work_type,
        "subject": data.subject,
        "theme": data.theme,
        "author": data.author,
        "group": data.group,
        "chief": data.chief,
        "post": data.post,
        "year": data.year,
    }

    doc.render(context)
    output_path = os.path.join(CURRENT_DIR, "titles", f"{filename}.docx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)