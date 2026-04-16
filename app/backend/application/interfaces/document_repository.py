from abc import ABC, abstractmethod
from uuid import UUID

from app.backend.domain.entities.document import Document
from app.backend.domain.entities.document_status import Status


class DocumentRepositoryInterface(ABC):
    @abstractmethod
    async def add(self, document: Document) -> None:
        """Добавление документа в БД со статусом PENDING"""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Document:
        """Получение документа по его уникальному идентификатору."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> None:
        """Удаление документа из репозитория по его уникальному идентификатору."""
        pass

    @abstractmethod
    async def update_status(self, document_id: UUID, status: Status) -> None:
        """Обновление статуса документа по его уникальному идентификатору."""
        pass
