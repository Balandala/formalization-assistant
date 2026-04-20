from uuid import UUID

from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.domain.entities.document import Document as DomainDocument
from backend.domain.entities.document_status import Status
from backend.infra.db.models import Document as OrmDocument
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository(DocumentRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, document: DomainDocument) -> None:
        orm_doc = OrmDocument(
            id=document.id,
            filename=document.filename,
            path=document.path,
            status=document.status.value,
            report=document.report,
        )
        self._session.add(orm_doc)
        await self._session.commit()

    async def get_by_id(self, document_id: UUID) -> DomainDocument | None:
        result = await self._session.execute(
            select(OrmDocument).where(OrmDocument.id == document_id)
        )
        orm_doc = result.scalar_one_or_none()
        if orm_doc is None:
            return None
        return self._to_domain(orm_doc)

    async def delete(self, document_id: UUID) -> None:
        await self._session.execute(
            delete(OrmDocument).where(OrmDocument.id == document_id)
        )
        await self._session.commit()

    async def update_status(
        self,
        document_id: UUID,
        status: Status,
        report: dict | None = None,
    ) -> None:
        values: dict = {"status": status.value}
        if report is not None:
            values["report"] = report
        await self._session.execute(
            update(OrmDocument).where(OrmDocument.id == document_id).values(**values)
        )
        await self._session.commit()

    @staticmethod
    def _to_domain(orm_doc: OrmDocument) -> DomainDocument:
        doc = DomainDocument(
            id=orm_doc.id,
            filename=orm_doc.filename,
            path=orm_doc.path,
        )
        doc.status = Status(orm_doc.status)
        doc.report = orm_doc.report
        return doc
