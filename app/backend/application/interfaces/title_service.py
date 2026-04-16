from abc import ABC, abstractmethod


class TitleServiceInterface(ABC):
    @abstractmethod
    def create_title(self, document_id: str) -> str:
        """Создание титульного листа для документа

        Args:
            document_id (str): Уникальный идентификатор документа

        Returns:
            str: Путь к титульному листу
        """
        pass
