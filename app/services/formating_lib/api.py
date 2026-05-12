import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from formating_config import Config
from pydantic import BaseModel
from word_processor import WordProcessor

app = FastAPI(title="Formatting Lib")


class ProcessRequest(BaseModel):
    filepath: str
    check_only: bool = False
    config: Optional[dict] = None


@app.post("/process")
def process_file(request: ProcessRequest):
    if not request.filepath or not os.path.exists(request.filepath):
        raise HTTPException(
            status_code=400,
            detail="File path is required and must point to an existing file",
        )

    if request.config is None:
        config = Config()
    else:
        config = Config(**request.config)

    try:
        wp = WordProcessor(config)
        report = wp.process_file(
            request.filepath,
            check_only=request.check_only,
        )
        return {
            "status": "ok",
            "message": "File processed successfully",
            "report": report,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Server raised an exception: {str(e)}"
        )
