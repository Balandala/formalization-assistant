import uuid

from backend.infra.db.database import AsyncPostgresBase
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON, UUID


# TODO: TaskStatus дублирует domain.entities.document_status.Status.
# Рекомендуется использовать единственный enum из domain-слоя.
class Document(AsyncPostgresBase):
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    report = Column(JSON, nullable=True)
