from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorageRepository(ABC):

    @abstractmethod
    async def save(self, file: BinaryIO, filename: str) -> str:
        """Асинхронное сохранение файла в хранилище. Возвращает путь к сохраненному файлу в хранилище."""
        pass

    @abstractmethod
    async def get(self, file_id: str) -> BinaryIO | None:
        """Получение файла из хранилища по его уникальному идентификатору"""
        pass

    @abstractmethod
    async def get_path(self, file_id: str) -> str | None:
        """Получение пути к файлу в хранилище по его уникальному идентификатору"""
        pass

    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Удаление файла из хранилища по его уникальному идентификатору"""
        pass
