from app.backend.application.interfaces.file_storage import AsyncFileStorageInterface


class DownloadDocumentUseCase:
    def __init__(self, storage_service: AsyncFileStorageInterface):
        self.storage_service = storage_service

    async def execute(self, document_id: str) -> str:
        document = await self.storage_service.get(document_id)
        if not document:
            raise ValueError("Document not found")
        return document