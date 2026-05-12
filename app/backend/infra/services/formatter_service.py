import httpx
from backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from backend.domain.entities.document import Document
from backend.domain.exceptions import FormatterServiceError


class HttpFormatterService(FormatterServiceInterface):
    """Вызывает внешний formatter-service по HTTP для форматирования документа"""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    async def format(
        self,
        document: Document,
        check_only: bool = False,
        config: dict | None = None,
    ) -> dict:
        url = f"{self._base_url}/process"
        abs_path = document.path
        payload: dict[str, object] = {"filepath": abs_path, "check_only": check_only}
        if config:
            payload["config"] = config

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                )
            except httpx.RequestError as exc:
                raise FormatterServiceError(
                    f"Formatter service unreachable: {exc}"
                ) from exc

        if response.status_code != 200:
            raise FormatterServiceError(
                f"Formatter service returned {response.status_code}"
            )

        return response.json().get("report") or {}
