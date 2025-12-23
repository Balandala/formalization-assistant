from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from shared.models import TitleData, GenerateTitleRequest
import os

from .service import generate_document

app = FastAPI(title="Title Generator Microservice")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TITLES_DIR = os.path.join(BASE_DIR, "titles")
os.makedirs(TITLES_DIR, exist_ok=True)


def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)


@app.post("/generate-title")
async def generate_title(request: GenerateTitleRequest):
    filename = str(request.doc_id)
    filepath = os.path.join(TITLES_DIR, f"{filename}.docx")

    try:
        generate_document(request.data, filename)


        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail=f"Сгенерированный файл {filepath} не найден")

        return FileResponse(
            path=filepath,
            filename="generated_title.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")