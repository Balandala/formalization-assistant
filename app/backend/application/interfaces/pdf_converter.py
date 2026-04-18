from abc import ABC, abstractmethod


class PdfConverterInterface(ABC):
    @abstractmethod
    async def convert(self, file_path: str) -> str:
        """Конвертация файла в PDF.

        Args:
            file_path (str): Путь к исходному файлу

        Returns:
            str: Путь к созданному PDF файлу
        """
        pass
