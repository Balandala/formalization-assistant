from typing import BinaryIO


class UploadDocument:
    """Класс, представляющий документ для загрузки.
    Attributes:
        stream (BinaryIO): Поток данных документа
        filename (str): Имя файла документа
        size (int): Размер файла в байтах
    """    
    stream: BinaryIO
    filename: str
    size: int 