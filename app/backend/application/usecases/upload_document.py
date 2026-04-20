from backend.application.dto.upload_document import UploadDocument
from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from backend.domain.entities.document import Document
from backend.domain.entities.document_status import Status
from backend.domain.rules import Rules


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

    async def execute(
        self, upload_document: UploadDocument
    ) -> tuple[Document, dict | None]:
        """Загружает документ на сервер, сохраняет его в БД и запускает форматирование.

        Сохраняет документ со статусом PENDING, затем вызывает сервис форматирования.
        При успехе — обновляет статус на COMPLETED и сохраняет отчёт.
        При сбое форматирования — устанавливает статус FAILED (не бросает исключение,
        логика повторяет поведение оригинального process_doc).

        Args:
            upload_document (UploadDocument): Загружаемый документ.

        Raises:
            ValueError: Если документ не прошёл валидацию.

        Returns:
            tuple[Document, dict | None]: Документ с финальным статусом и отчёт (или None).
        """
        if not self._validate_document(upload_document):
            raise ValueError("Invalid document")

        file_path = await self.storage_repository.save(
            upload_document.stream, upload_document.filename
        )
        document = Document(filename=upload_document.filename, path=file_path)
        await self.document_repo.add(document)

        try:
            report = await self.formatter_service.format(document)
            await self.document_repo.update_status(
                document.id, Status.COMPLETED, report=report
            )
            document.status = Status.COMPLETED
            document.report = report
        except Exception:
            # TODO: рассмотреть логирование ошибки форматирования
            await self.document_repo.update_status(document.id, Status.FAILED)
            document.status = Status.FAILED
            report = None

        return document, report

    def _validate_document(self, document: UploadDocument) -> bool:
        """Валидация документа на основе правил Rules. Проверяет тип файла и размер."""
        file_type = document.filename.split(".")[-1].lower()
        if file_type not in self._rules.allowed_file_types:
            return False
        if document.size > self._rules.max_file_size_bytes:
            return False
        return True
