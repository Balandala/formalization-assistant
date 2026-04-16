from abc import ABC, abstractmethod


class FormatterServiceInterface(ABC):
    @abstractmethod
    async def format(self, document_id: str) -> dict:
        """Форматирование документа

        Args:
            document_id (str): Уникальный идентификатор документа

        Returns:
            dict: Репорт о форматировании документа
        """
        pass
