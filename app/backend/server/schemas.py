from typing import Optional

from pydantic import BaseModel
from uuid import UUID


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    report: Optional[dict] = None

    class Config:
        from_attributes = True

class FormattingConfig(BaseModel):
    OverrideFormatting: bool = False
    NormalText: bool = True
    Headings: bool = True
    Captions: bool = True
    PagesNumeration: bool = True
    PageFields: bool = True