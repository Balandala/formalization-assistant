import os


class Settings:
    """Конфигурация приложения. Читает значения из переменных окружения."""

    def __init__(self):
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
        self.POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "doc_assistant")
        self.UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
        self.FORMATTER_SERVICE_URL: str = os.getenv(
            "FORMATTER_SERVICE_URL", "http://formatter-service:7272"
        )
        self.TITLE_SERVICE_URL: str = os.getenv(
            "TITLE_SERVICE_URL", "http://title-service:7777"
        )
