from .document_status import Status

class Document:
    id: str
    filename: str
    path: str
    status: Status
    report: dict | None