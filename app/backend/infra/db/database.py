from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


# TODO: В исходном дизайне AsyncPostgresBase объединял роль ORM-базы (DeclarativeBase)
# и фабрики соединений (хранила конфиг и создавала engine в __init__).
# Это противоречит назначению DeclarativeBase: он является базовым классом для ORM-моделей
# и не предназначен для хранения конфига и создания engine.
# Разделено на два класса: AsyncPostgresBase (ORM-база) и DatabaseSessionFactory (фабрика).
class AsyncPostgresBase(DeclarativeBase):
    """ORM declarative base. Все SQLAlchemy-модели наследуют этот класс."""

    pass


class DatabaseSessionFactory:
    """Управляет созданием async SQLAlchemy engine и сессий."""

    def __init__(self, config: dict):
        self._db_user = config.get("POSTGRES_USER")
        self._db_password = config.get("POSTGRES_PASSWORD")
        self._db_host = config.get("POSTGRES_HOST", "localhost")
        self._db_port = config.get("POSTGRES_PORT", 5432)
        self._db_name = config.get("POSTGRES_DB", "doc_assistant")
        self._engine = None
        self._session_factory = None

    def _build_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self._db_user}:{self._db_password}"
            f"@{self._db_host}:{self._db_port}/{self._db_name}"
        )

    def _ensure_engine(self) -> None:
        if self._engine is None:
            database_url = self._build_database_url()
            self._engine = create_async_engine(database_url, echo=True)
            self._session_factory = async_sessionmaker(
                bind=self._engine, class_=AsyncSession, expire_on_commit=False
            )

    @property
    def engine(self) -> AsyncEngine:
        self._ensure_engine()
        assert self._engine is not None, "Engine failed to initialize"
        return self._engine

    def get_session(self) -> AsyncSession:
        self._ensure_engine()
        if self._session_factory:
            return self._session_factory()
        raise RuntimeError("Session factory failed to initialize")
