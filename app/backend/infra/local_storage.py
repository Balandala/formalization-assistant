import os
import uuid
from typing import Any

import aiofiles
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.domain.entities.document import Document


class LocalFileStorage(FileStorageRepository):
    """Хранит файлы в локальной файловой системе."""

    def __init__(self, upload_folder: str):
        self._upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    async def save(self, file: Any, filename: str) -> str:
        """Сохраняет файл в папку загрузок под уникальным именем.

        Генерирует UUID-префикс во избежание конфликтов имён.
        file должен поддерживать await file.read(size) (FastAPI UploadFile).
        """
        unique_name = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self._upload_folder, unique_name)
        async with aiofiles.open(file_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                await out.write(chunk)
        return file_path

    async def get(self, file_id: str) -> Document | None:
        # TODO: file_id используется как путь к файлу — это смешивает понятия
        # идентификатора и расположения файла. Стоит разделить.
        return None  # не используется в текущих use-case'ах

    async def get_path(self, file_id: str) -> str | None:
        # TODO: file_id используется как путь к файлу (см. DownloadDocumentUseCase).
        if os.path.exists(file_id):
            return file_id
        return None

    async def delete(self, file_id: str) -> bool:
        # TODO: file_id используется как путь к файлу.
        if os.path.exists(file_id):
            os.remove(file_id)
            return True
        return False
