from typing import Any


class UploadDocument:
    """Класс, представляющий документ для загрузки.

    Attributes:
        stream: Поток данных документа (FastAPI UploadFile или async-readable объект).
        filename (str): Имя файла документа.
        size (int): Размер файла в байтах.
    """

    # TODO: stream должен быть типизирован как AsyncBinaryIO/SpooledTemporaryFile.
    # BinaryIO подразумевает синхронный интерфейс, но FastAPI передаёт UploadFile
    # с асинхронным методом read().
    stream: Any
    filename: str
    size: int

    def __init__(self, stream: Any, filename: str, size: int):
        self.stream = stream
        self.filename = filename
        self.size = size
