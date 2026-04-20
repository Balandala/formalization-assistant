import os

import httpx
from backend.application.interfaces.title_service import TitleServiceInterface
from backend.domain.exceptions import TitleServiceError


class HttpTitleService(TitleServiceInterface):
    """Вызывает внешний title-service по HTTP и сохраняет полученный docx локально"""

    def __init__(self, base_url: str, upload_folder: str):
        self._base_url = base_url.rstrip("/")
        self._upload_folder = upload_folder

    async def create_title(self, title: dict) -> str:
        """Запрашивает title-service и сохраняет полученный файл.

        Args:
            title (dict): Словарь вида {"doc_id": str, "data": {...title fields...}}.

        Returns:
            str: Путь к сохранённому файлу титульного листа.
        """
        doc_id = title.get("doc_id")
        file_path = os.path.join(self._upload_folder, f"{doc_id}_title.docx")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/generate-title",
                    json=title,
                )
            except httpx.RequestError as exc:
                raise TitleServiceError(f"Title service unreachable: {exc}") from exc

        if response.status_code != 200:
            raise TitleServiceError(f"Title service returned {response.status_code}")

        os.makedirs(self._upload_folder, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path
