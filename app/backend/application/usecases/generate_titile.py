from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.application.interfaces.title_service import TitleServiceInterface
from app.backend.domain.entities.document import Document
from app.backend.domain.entities.document_status import Status


class GenerateTitleUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        title_service: TitleServiceInterface,
    ):
        self.document_repo = document_repository
        self.title_service = title_service

    async def execute(self, title_data: dict) -> Document:
        """Генерирует титульный лист без форматирования документа

        Args:
            title_data (dict): Данные для генерации титульного листа.

        Returns:
            Document: Объект документа с сгенерированным титульным листом.
        """        
        title_path = await self.title_service.create_title(title_data)
        document = Document(filename="title_page.docx", path=title_path)
        document.status = Status.COMPLETED
        await self.document_repo.add(document)
        return document
