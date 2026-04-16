from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class AsyncPostgresBase(DeclarativeBase):
    def __init__(self, config: dict):
        self._db_user = config.get("POSTGRES_USER")
        self._db_password = config.get("POSTGRES_PASSWORD")
        self._db_host = config.get("POSTGRES_HOST", "localhost")
        self._db_port = config.get("POSTGRES_PORT", 5432)
        self._db_name = config.get("POSTGRES_DB", "doc_assistant")
        self._engine = None
        self._session_local = None

    def _build_database_url(self) -> str:
        return f"postgresql+asyncpg://{self._db_user}:{self._db_password}@{self._db_host}:{self._db_port}/{self._db_name}"

    def _create_engine(self) -> None:
        database_url = self._build_database_url()
        self._engine = create_async_engine(database_url, echo=True)
        self._session_local = async_sessionmaker(
            bind=self._engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def get_session(self) -> AsyncSession:
        session_factory = self._session_local
        if session_factory is None:
            self._create_engine()
            session_factory = self._session_local
        
        if session_factory:
            return session_factory()
        raise RuntimeError("Session factory failed to initialize")
    