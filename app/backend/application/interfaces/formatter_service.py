from abc import ABC, abstractmethod

from backend.domain.entities.document import Document


class FormatterServiceInterface(ABC):
    @abstractmethod
    async def format(
        self,
        document: Document,
        check_only: bool = False,
        config: dict | None = None,
    ) -> dict:
        """Форматирование или проверка документа.

        Args:
            document (Document): Документ для обработки.
            check_only (bool): Если True, сервис должен только собрать отчёт
                без изменения файла на диске.
            config (dict | None): Дополнительные параметры форматирования.

        Returns:
            dict: Репорт о форматировании документа.
        """
        pass
