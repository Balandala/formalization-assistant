from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: str

    class Config:
        from_attributes = True