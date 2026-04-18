import uuid

from .document_status import Status


class Document:
    id: uuid.UUID
    filename: str
    path: str
    status: Status
    report: dict | None

    def __init__(self, filename: str, path: str, id: uuid.UUID | None = None):
        self.id = id if id is not None else uuid.uuid4()
        self.filename = filename
        self.path = path
        self.status = Status.PENDING
        self.report = None
