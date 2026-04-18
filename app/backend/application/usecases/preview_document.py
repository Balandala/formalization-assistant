from uuid import UUID

from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.application.interfaces.file_storage import FileStorageRepository
from app.backend.application.interfaces.pdf_converter import PdfConverterInterface


class PreviewDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        storage_repository: FileStorageRepository,
        pdf_converter: PdfConverterInterface,
    ):
        self.document_repo = document_repository
        self.storage_repository = storage_repository
        self.pdf_converter = pdf_converter

    async def execute(self, document_id: UUID) -> str:
        """Генерирует предварительный просмотр документа в формате PDF.

        Args:
            document_id (UUID): Идентификатор документа.

        Raises:
            ValueError: Если документ не найден.
            FileNotFoundError: Если файл не найден на сервере.

        Returns:
            str: Путь к сгенерированному PDF файлу.
        """        
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise ValueError("Document not found")
        path = await self.storage_repository.get_path(document.path)
        if path is None:
            raise FileNotFoundError("File not found on server")
        pdf_path = await self.pdf_converter.convert(document.path)
        return pdf_path
