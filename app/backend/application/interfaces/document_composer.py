from abc import ABC, abstractmethod

from app.backend.domain.entities.document_parts import DocParts


class DocumentComposerInterface(ABC):
    @abstractmethod
    async def compose(self, doc_parts: DocParts) -> str:
        """Компоновка частей документа

        Args:
            doc_parts (DocParts): Части документа для компоновки

        Returns:
            str: Путь к скомпонованному документу
        """
        pass
