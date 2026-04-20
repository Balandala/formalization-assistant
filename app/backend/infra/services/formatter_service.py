import requests
from backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from backend.domain.entities.document import Document
from backend.domain.exceptions import FormatterServiceError


class HttpFormatterService(FormatterServiceInterface):
    """Вызывает внешний formatter-service по HTTP для форматирования документа"""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    async def format(self, document: Document) -> dict:
        url = f"{self._base_url}/process"
        abs_path = document.path

        # TODO: requests.post блокирует event loop. Заменить на httpx.AsyncClient
        try:
            response = requests.post(url, json={"filepath": abs_path}, timeout=120)
        except requests.RequestException as exc:
            raise FormatterServiceError(
                f"Formatter service unreachable: {exc}"
            ) from exc

        if response.status_code != 200:
            raise FormatterServiceError(
                f"Formatter service returned {response.status_code}"
            )

        return response.json().get("report") or {}
