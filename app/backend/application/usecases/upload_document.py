from app.backend.application.dto.upload_document import UploadDocument
from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.application.interfaces.file_storage import FileStorageRepository
from app.backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from app.backend.domain.entities.document import Document
from app.backend.domain.rules import Rules


class UploadDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        formatter_service: FormatterServiceInterface,
        storage_repository: FileStorageRepository,
    ):
        self.document_repo = document_repository
        self.formatter_service = formatter_service
        self.storage_repository = storage_repository
        self._rules = Rules()

    async def execute(self, upload_document: UploadDocument) ->tuple[Document, dict]:
        """Загружает документ на сервер, сохраняет его в БД и запускает процесс форматирования.

        Args:
            upload_document (UploadDocument): Загружаемый документ.

        Raises:
            ValueError: Если документ не прошел валидацию.

        Returns:
            tuple[Document, dict]: Объект документа и отчет о форматировании.
        """        
        if not self._validate_document(upload_document):
            raise ValueError("Invalid document")

        file_path = await self.storage_repository.save(
            upload_document.stream, upload_document.filename
        )
        document = Document(filename=upload_document.filename, path=file_path)
        await self.document_repo.add(document)
        report = await self.formatter_service.format(document)

        return document, report

    def _validate_document(self, document: UploadDocument) -> bool:
        """Валидация документа на основе правил, определенных в Rules. Проверяет тип файла и размер."""
        file_type = document.filename.split(".")[-1].lower()
        if file_type not in self._rules.allowed_file_types:
            return False

        if document.size > self._rules.max_file_size_bytes:
            return False

        return True
