from abc import ABC, abstractmethod

from backend.domain.entities.document import Document


class FormatterServiceInterface(ABC):
    @abstractmethod
    async def format(self, document: Document) -> dict:
        """Форматирование документа

        Args:
            document (Document): Документ для форматирования

        Returns:
            dict: Репорт о форматировании документа
        """
        pass
