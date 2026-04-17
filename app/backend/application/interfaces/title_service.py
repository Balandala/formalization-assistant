from abc import ABC, abstractmethod



class TitleServiceInterface(ABC):
    @abstractmethod
    async def create_title(self, title: dict) -> str:
        """Создание титульного листа для документа

        Args:
            title (dict): Данные для создания титульного листа

        Returns:
            str: Путь к титульному листу
        """
        pass
