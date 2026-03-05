import uuid

from pydantic import BaseModel
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import enum
from backend.server.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status = Column(String, default=TaskStatus.PENDING.value, nullable=False)

