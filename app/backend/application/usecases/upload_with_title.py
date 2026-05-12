from backend.application.dto.upload_document import UploadDocument
from backend.application.interfaces.document_composer import (
    DocumentComposerInterface,
)
from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from backend.application.interfaces.title_service import TitleServiceInterface
from backend.domain.entities.document import Document
from backend.domain.entities.document_parts import DocParts
from backend.domain.entities.document_status import Status
from backend.domain.rules import Rules


class UploadWithTitleUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        formatter_service: FormatterServiceInterface,
        storage_repository: FileStorageRepository,
        document_composer: DocumentComposerInterface,
        title_service: TitleServiceInterface,
    ):
        self.document_repo = document_repository
        self.formatter_service = formatter_service
        self.storage_repository = storage_repository
        self.document_composer = document_composer
        self.title_service = title_service
        self._rules = Rules()

    async def execute(
        self,
        upload_document: UploadDocument,
        title_data: dict,
        formatting_config: dict | None = None,
    ) -> tuple[Document, dict]:
        """Загружает документ, форматирует, генерирует титульный лист и объединяет в один файл.

        Промежуточные файлы (исходная загрузка и титул) удаляются после успешного
        объединения. При возникновении ошибки на любом этапе все созданные файлы
        очищаются.

        Args:
            upload_document (UploadDocument): Загружаемый документ.
            title_data (dict): Поля TitleData для генерации титульного листа.
            formatting_config (dict | None): Опции форматирования для formatter-service.

        Raises:
            ValueError: Если документ не прошёл валидацию.

        Returns:
            tuple[Document, dict]: Готовый документ (COMPLETED) и отчёт о форматировании.
        """
        if not self._validate_document(upload_document):
            raise ValueError("Invalid document")

        file_path = None
        title_path = None

        try:
            file_path = await self.storage_repository.save(
                upload_document.stream, upload_document.filename
            )
            document = Document(filename=upload_document.filename, path=file_path)

            report = await self.formatter_service.format(
                document,
                config=formatting_config,
            )

            # Передаём doc_id сервису, чтобы он мог уникально назвать файл.
            title_path = await self.title_service.create_title(
                {"doc_id": str(document.id), "data": title_data}
            )

            doc_parts = DocParts(main_part_path=file_path, title_part_path=title_path)
            final_path = await self.document_composer.compose(doc_parts)

            document.path = final_path
            document.status = Status.COMPLETED
            document.report = report

            # Удаляем промежуточные файлы после успешного объединения.
            await self.storage_repository.delete(file_path)
            file_path = None
            await self.storage_repository.delete(title_path)
            title_path = None

            await self.document_repo.add(document)
            return document, report

        except Exception:
            # TODO: если исключение возникло уже после compose(), финальный файл
            # останется на диске без записи в БД. Нужен механизм компенсирующей транзакции.
            for path in filter(None, [file_path, title_path]):
                await self.storage_repository.delete(path)
            raise

    def _validate_document(self, document: UploadDocument) -> bool:
        """Валидация документа на основе правил Rules. Проверяет тип файла и размер."""
        file_type = document.filename.split(".")[-1].lower()
        if file_type not in self._rules.allowed_file_types:
            return False
        if document.size > self._rules.max_file_size_bytes:
            return False
        return True
