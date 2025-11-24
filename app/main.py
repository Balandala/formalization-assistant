import os
import uuid
import aiofiles
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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

    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024*1024):
            await out_file.write(content)

    new_doc = Document(
        filename=file.filename,
        path=file_path,
        status=TaskStatus.PENDING.value
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    return new_doc

@app.get("/status/{doc_id}", response_model=DocumentResponse)
async def get_status(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc