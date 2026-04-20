from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.title_service import TitleServiceInterface
from backend.domain.entities.document import Document
from backend.domain.entities.document_status import Status


class GenerateTitleUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        title_service: TitleServiceInterface,
    ):
        self.document_repo = document_repository
        self.title_service = title_service

    async def execute(self, title_data: dict) -> Document:
        """Генерирует титульный лист без форматирования основного документа.

        Создаёт сущность Document заранее, чтобы получить стабильный ID для
        запроса к title-service (сервис использует ID для именования файла).

        Args:
            title_data (dict): Поля TitleData (без doc_id — он добавляется здесь).

        Returns:
            Document: Объект документа с сгенерированным титульным листом.
        """
        # Создаём Document первым, чтобы получить его ID до вызова title-service.
        # TODO: рассмотреть явную передачу doc_id через DTO вместо dict.
        document = Document(filename="title_page.docx", path="")
        title_path = await self.title_service.create_title(
            {"doc_id": str(document.id), "data": title_data}
        )
        document.path = title_path
        document.status = Status.COMPLETED
        await self.document_repo.add(document)
        return document
