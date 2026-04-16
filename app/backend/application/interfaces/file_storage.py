from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorageInterface(ABC):
    @abstractmethod
    def save(self, file: BinaryIO, filename: str) -> str:
        """Сохранение файла в хранилище

        Args:
            file (BinaryIO): Файл для сохранения
            filename (str): Имя файла

        Returns:
            str: путь к сохраненному файлу в хранилище
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> BinaryIO:
        """Получение файла из хранилища по его уникальному идентификатору"""
        pass

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """Удаление файла из хранилища по его уникальному идентификатору"""
        pass
