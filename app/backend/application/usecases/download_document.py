from uuid import UUID

from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.domain.entities.document import Document
from backend.domain.entities.document_status import Status
from backend.domain.exceptions import (
    DocumentFileNotFoundError,
    DocumentNotFoundError,
    DocumentNotReadyError,
)


class DownloadDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        storage_repository: FileStorageRepository,
    ):
        self.document_repo = document_repository
        self.storage_repository = storage_repository

    async def execute(self, document_id: UUID) -> Document:
        """Возвращает документ, готовый к скачиванию.

        Raises:
            DocumentNotFoundError: Документ не найден.
            DocumentNotReadyError: Документ ещё не готов.
            DocumentFileNotFoundError: Физический файл отсутствует.
        """
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError("Документ не найден")
        if document.status != Status.COMPLETED:
            raise DocumentNotReadyError("Документ не готов к скачиванию")
        path = await self.storage_repository.get_path(document.path)
        if path is None:
            raise DocumentFileNotFoundError("Обработанный файл не найден на сервере")
        return document
