import uuid

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