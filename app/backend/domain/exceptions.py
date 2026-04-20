class DocumentNotFoundError(Exception):
    """Документ не найден в репозитории."""

    pass


class DocumentNotReadyError(Exception):
    """Документ ещё не готов (не завершена обработка)."""

    pass


class DocumentFileNotFoundError(FileNotFoundError):
    """Физический файл документа отсутствует на диске."""

    pass


class FormatterServiceError(Exception):
    """Ошибка при обращении к сервису форматирования."""

    pass


class TitleServiceError(Exception):
    """Ошибка при обращении к сервису генерации титульного листа."""

    pass


class DocumentComposerError(Exception):
    """Ошибка при объединении частей документа."""

    pass


class PdfConversionError(Exception):
    """Ошибка при конвертации документа в PDF."""

    pass
