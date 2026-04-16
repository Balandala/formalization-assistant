from dishka import Scope, Provider, provide
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.infra.db.database import AsyncPostgresBase

class DatabaseProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_postgres_session(self, config) -> AsyncSession:
        return AsyncPostgresBase(config).get_session()