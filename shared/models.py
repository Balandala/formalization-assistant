import uuid
from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class TitleData(BaseModel):
    institute: str
    work_type: str
    subject: str
    theme: str
    author: str
    group: str
    chief: str
    post: str
    year: int = datetime.now().year


class GenerateTitleRequest(BaseModel):
    doc_id: uuid.UUID
    data: TitleData


class FormattingReport(BaseModel):
    paragraphs_formatted: int = 0
    headings_detected: int = 0
    figures_numbered: int = 0
    tables_numbered: int = 0
    page_fields_set: bool = False
    page_numbering_added: bool = False
    details: list[str] = [] 