from uuid import UUID

from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.application.interfaces.file_storage import FileStorageRepository
from app.backend.domain.entities.document import Document
from app.backend.domain.entities.document_status import Status


class DownloadDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        storage_repository: FileStorageRepository,
    ):
        self.document_repo = document_repository
        self.storage_repository = storage_repository

    async def execute(self, document_id: UUID) -> Document:
        """Достает по id документ из хранилища и возвращает пользователю 

        Args:
            document_id (UUID): Идентификатор документа.

        Raises:
            ValueError: Если документ не найден.
            ValueError: Если документ не готов к скачиванию.
            FileNotFoundError: Если обработанный файл не найден на сервере.


        Returns:
            Document: Объект документа, готового к скачиванию.
        """        
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found")
        if document.status != Status.COMPLETED:
            raise ValueError("Document not ready")
        path = await self.storage_repository.get_path(document.path)
        if path is None:
            raise FileNotFoundError("Processed file not found on server")
        return document
