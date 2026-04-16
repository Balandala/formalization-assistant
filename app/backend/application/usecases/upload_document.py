from app.backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from app.backend.application.interfaces.file_storage import FileStorageInterface
from app.backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from app.backend.domain.rules import Rules


class UploadDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepositoryInterface,
        formatter_service: FormatterServiceInterface,
        file_storage: FileStorageInterface
    ):
        self.document_repo = document_repository
        self.formatter_service = formatter_service
        self.file_storage = file_storage
        self._rules = Rules()

    def execute(self, document):
        if not self._validate_document(document):
            raise ValueError("Invalid document")

        
        return 

    def _validate_document(self, document):
        # Implement validation logic here
        # For example, check if the file type is allowed and if the size is within limits


        file_type = document.filename.split(".")[-1].lower()
        if file_type not in self._rules.allowed_file_types:
            return False

        if len(document.content) > self._rules.max_file_size_bytes:
            return False

        return True
