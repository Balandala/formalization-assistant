from backend.application.dto.upload_document import UploadDocument
from backend.application.usecases.generate_titile import GenerateTitleUseCase
from backend.application.usecases.upload_with_title import UploadWithTitleUseCase
from backend.domain.exceptions import FormatterServiceError, TitleServiceError
from backend.presentation.schemas import DocumentResponse
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from shared.models import TitleData

router = APIRouter(route_class=DishkaRoute, tags=["titles"])


@router.post("/generate-title", response_model=DocumentResponse)
async def generate_title(
    data: TitleData,
    use_case: FromDishka[GenerateTitleUseCase] = ...,  # type: ignore[assignment]
):
    try:
        document = await use_case.execute(data.model_dump())
    except TitleServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return document


@router.post("/upload-with-title", response_model=DocumentResponse)
async def upload_with_title(
    file: UploadFile = File(...),
    institute: str = Form(...),
    work_type: str = Form(...),
    subject: str = Form(...),
    theme: str = Form(...),
    author: str = Form(...),
    group: str = Form(...),
    chief: str = Form(...),
    post: str = Form(...),
    generate_toc: bool = Form(False),
    toc_page_number: int = Form(2),
    use_case: FromDishka[UploadWithTitleUseCase] = ...,  # type: ignore[assignment]
):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are allowed")
    if toc_page_number < 1:
        raise HTTPException(status_code=400, detail="toc_page_number must be >= 1")

    title_data = TitleData(
        institute=institute,
        work_type=work_type,
        subject=subject,
        theme=theme,
        author=author,
        group=group,
        chief=chief,
        post=post,
    )
    dto = UploadDocument(
        stream=file,
        filename=file.filename,
        size=file.size or 0,
    )
    try:
        formatting_config = {
            "table_of_contents": generate_toc,
            "table_of_contents_page": toc_page_number,
        }
        document, _ = await use_case.execute(
            dto,
            title_data.model_dump(),
            formatting_config=formatting_config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (FormatterServiceError, TitleServiceError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    return document
