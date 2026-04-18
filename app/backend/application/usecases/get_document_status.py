from uuid import UUID

from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.domain.entities.document import Document


class GetDocumentStatusUseCase:
    def __init__(self, document_repository: DocumentRepositoryInterface):
        self.document_repo = document_repository

    async def execute(self, document_id: UUID) -> Document:
        """Получает статус документа по его идентификатору.

        Args:
            document_id (UUID): Идентификатор документа.

        Raises:
            ValueError: Если документ не найден.

        Returns:
            Document: Объект документа с его текущим статусом.
        """        
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found")
        return document
