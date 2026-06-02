import os
from contextlib import asynccontextmanager

from backend.infra.db.database import AsyncPostgresBase, DatabaseSessionFactory
from backend.infra.di import create_container
from backend.presentation.routers.documents import router as documents_router
from backend.presentation.routers.titles import router as titles_router
from config import Settings
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# main.py находится по пути app/backend/main.py.
# Два уровня вверх (dirname × 2) дают директорию app/, где лежит frontend/.
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_APP_DIR, "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    factory = DatabaseSessionFactory(vars(settings))
    async with factory.engine.begin() as conn:
        await conn.run_sync(AsyncPostgresBase.metadata.create_all)
    yield


app = FastAPI(title="DocHelper", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:7272",
        "http://127.0.0.1:7272",
        "http://localhost:7777",
        "http://127.0.0.1:7777",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/styles",
    StaticFiles(directory=os.path.join(_FRONTEND_DIR, "styles")),
    name="styles",
)
app.mount(
    "/scripts",
    StaticFiles(directory=os.path.join(_FRONTEND_DIR, "scripts")),
    name="scripts",
)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(_FRONTEND_DIR, "static")),
    name="static",
)


def _index_response() -> FileResponse:
    filename = os.path.join(_FRONTEND_DIR, "static", "index.html")
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(filename)


@app.get("/", include_in_schema=False)
async def get_index():
    return _index_response()


app.include_router(documents_router)
app.include_router(titles_router)


# SPA fallback: любой не-API GET-запрос отправляем на лендинг.
# Должен быть зарегистрирован ПОСЛЕ всех роутеров, чтобы не перехватывать их.
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    return RedirectResponse(url="/", status_code=307)


container = create_container()
setup_dishka(container, app=app)
