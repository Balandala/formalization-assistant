from uuid import UUID

from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.application.interfaces.pdf_converter import PdfConverterInterface
from backend.domain.exceptions import (
    DocumentFileNotFoundError,
    DocumentNotFoundError,
)


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
        """Возвращает путь к PDF-превью документа, конвертируя при необходимости.

        Raises:
            DocumentNotFoundError: Документ не найден.
            DocumentFileNotFoundError: Физический файл отсутствует.
            PdfConversionError: Ошибка конвертации в PDF.
        """
        document = await self.document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found")
        path = await self.storage_repository.get_path(document.path)
        if path is None:
            raise DocumentFileNotFoundError("File not found on server")
        pdf_path = await self.pdf_converter.convert(document.path)
        return pdf_path
