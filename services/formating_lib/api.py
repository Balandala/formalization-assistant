from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os



from word_processor import WordProcessor
from formating_config import Config

app = FastAPI(title="Formatting Lib")

class ProcessRequest(BaseModel):
    filepath: str
    config: Optional[dict] = None

@app.post("/process")
def process_file(request: ProcessRequest):
    if not request.filepath or not os.path.exists(request.filepath):
        raise HTTPException(status_code=400, detail="File path is required and must point to an existing file")

    if request.config is None:
        config = Config()
    else:
        config = Config(**request.config)

    try:
        wp = WordProcessor(config)
        wp.process_file(request.filepath)
        return {"status": "ok", "message": "File processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server raised an exception: {str(e)}")