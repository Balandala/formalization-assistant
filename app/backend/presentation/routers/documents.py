from backend.application.dto.upload_document import UploadDocument
from backend.application.usecases.download_document import DownloadDocumentUseCase
from backend.application.usecases.get_document_status import (
    GetDocumentStatusUseCase,
)
from backend.application.usecases.preview_document import PreviewDocumentUseCase
from backend.application.usecases.upload_document import UploadDocumentUseCase
from backend.domain.exceptions import (
    DocumentFileNotFoundError,
    DocumentNotFoundError,
    PdfConversionError,
)
from backend.presentation.schemas import DocumentResponse
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(route_class=DishkaRoute, tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    use_case: FromDishka[UploadDocumentUseCase] = ...,  # type: ignore[assignment]
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed")

    dto = UploadDocument(
        stream=file,
        filename=file.filename,
        size=file.size or 0,
    )
    try:
        document, _ = await use_case.execute(dto)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return document


@router.get("/status/{doc_id}", response_model=DocumentResponse)
async def get_status(
    doc_id: str,
    use_case: FromDishka[GetDocumentStatusUseCase] = ...,  # type: ignore[assignment]
):
    try:
        document = await use_case.execute(_parse_uuid(doc_id))
    except (ValueError, DocumentNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return document


@router.get("/download/{doc_id}")
async def download_document(
    doc_id: str,
    use_case: FromDishka[DownloadDocumentUseCase] = ...,  # type: ignore[assignment]
):
    try:
        document = await use_case.execute(_parse_uuid(doc_id))
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        # документ не готов
        raise HTTPException(status_code=400, detail=str(exc))
    except (FileNotFoundError, DocumentFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return FileResponse(
        path=document.path,
        filename=document.filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/report/{doc_id}")
async def get_report(
    doc_id: str,
    use_case: FromDishka[GetDocumentStatusUseCase] = ...,  # type: ignore[assignment]
):
    try:
        document = await use_case.execute(_parse_uuid(doc_id))
    except (ValueError, DocumentNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if document.report is None:
        raise HTTPException(status_code=404, detail="Отчёт недоступен")
    return document.report


@router.get("/preview/{doc_id}")
async def get_preview(
    doc_id: str,
    use_case: FromDishka[PreviewDocumentUseCase] = ...,  # type: ignore[assignment]
):
    try:
        pdf_path = await use_case.execute(_parse_uuid(doc_id))
    except (ValueError, DocumentNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (FileNotFoundError, DocumentFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except PdfConversionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return FileResponse(pdf_path, media_type="application/pdf")


def _parse_uuid(value: str):
    """Парсит UUID из строки, бросает HTTP 422 при некорректном формате."""
    import uuid as _uuid

    try:
        return _uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid UUID: {value}")
