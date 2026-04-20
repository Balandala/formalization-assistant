import os
import uuid

from backend.application.interfaces.document_composer import (
    DocumentComposerInterface,
)
from backend.domain.entities.document_parts import DocParts
from backend.domain.exceptions import DocumentComposerError
from docx import Document as DocxDocument
from docxcompose.composer import Composer


class DocxDocumentComposer(DocumentComposerInterface):
    """Объединяет tittle-docx и основной docx в единый файл с помощью docxcompose."""

    def __init__(self, upload_folder: str):
        self._upload_folder = upload_folder

    async def compose(self, doc_parts: DocParts) -> str:
        output_path = os.path.join(self._upload_folder, f"{uuid.uuid4()}_final.docx")
        try:
            master = DocxDocument(doc_parts.title_part_path)
            composer = Composer(master)
            composer.append(DocxDocument(doc_parts.main_part_path))
            composer.save(output_path)
        except Exception as exc:
            raise DocumentComposerError(
                f"Failed to compose document parts: {exc}"
            ) from exc

        return output_path
