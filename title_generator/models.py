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
    year: datetime = datetime.now().year
