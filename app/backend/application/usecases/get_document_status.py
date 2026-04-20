from uuid import UUID

from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.domain.entities.document import Document
from backend.domain.exceptions import DocumentNotFoundError


class GetDocumentStatusUseCase:
    def __init__(self, document_repository: DocumentRepositoryInterface):
        self.document_repo = document_repository

    async def execute(self, document_id: UUID) -> Document:
        """Возвращает документ с его текущим статусом.

        Raises:
            DocumentNotFoundError: Документ не найден.
        """
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found")
        return document
