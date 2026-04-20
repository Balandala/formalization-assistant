import os
import subprocess

from backend.application.interfaces.pdf_converter import PdfConverterInterface
from backend.domain.exceptions import PdfConversionError


class LibreOfficePdfConverter(PdfConverterInterface):
    """Конвертирует документ в PDF с помощью LibreOffice (headless)."""

    async def convert(self, file_path: str) -> str:
        pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"
        if os.path.exists(pdf_path):
            return pdf_path

        try:
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    os.path.dirname(file_path),
                    file_path,
                ],
                check=True,
                timeout=60,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise PdfConversionError(f"PDF conversion failed: {exc}") from exc

        if not os.path.exists(pdf_path):
            raise PdfConversionError("PDF was not created by LibreOffice")

        return pdf_path
