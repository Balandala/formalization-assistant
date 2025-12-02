import os
import uuid
import aiofiles
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from asyncio import sleep
from fastapi.background import BackgroundTasks

from .database import engine, Base, get_db
from .models import Document, TaskStatus
from .schemas import DocumentResponse

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="DocHelper", lifespan=lifespan, )

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...),
                          db: AsyncSession = Depends(get_db)):

    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Not a docx")

    doc_id = uuid.uuid4()
    filename = f"{doc_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024*1024):
            await out_file.write(content)

    new_doc = Document(
        id=doc_id,
        filename=file.filename,
        path=file_path,
        status=TaskStatus.PENDING.value
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    await process_doc(new_doc.id, db) # имитация обработки(5 секунд)

    return new_doc

@app.get("/status/{doc_id}", response_model=DocumentResponse)
async def get_status(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc

@app.get("/download/{doc_id}")
async def get_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != TaskStatus.COMPLETED.value:
        return HTTPException(status_code=400, detail="Document not ready")


    if not os.path.exists(doc.path):
        raise HTTPException(status_code=500, detail="Processed file not found on server")

    background_tasks = BackgroundTasks()
    background_tasks.add_task(remove_file, doc.path)

    return FileResponse(
        path=doc.path,
        filename=doc.filename,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        background=background_tasks
    )



async def process_doc(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Заглушка имитации обработки документа"""
    await sleep(5)
    stmt = update(Document).where(Document.id == doc_id).values(status=TaskStatus.COMPLETED.value)
    await db.execute(stmt)
    await db.commit()

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)
        print(f"Файл удалён: {path}")