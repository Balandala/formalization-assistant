from .document_status import Status

class Document:
    def __init__(self, filename: str, path: str):
        self.filename = filename
        self.path = path
        self.status = Status.PENDING
        self.report = None
    filename: str
    path: str
    status: Status
    report: dict | None