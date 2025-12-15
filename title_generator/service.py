from docxtpl import DocxTemplate
from models import TitleData

def generate_document(data: TitleData, filename: str):
    doc = DocxTemplate("templates/title1.docx")
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
    doc.save(f"titles/{filename}.docx")
    return