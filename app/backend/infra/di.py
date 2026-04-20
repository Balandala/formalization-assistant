from typing import AsyncGenerator

from backend.application.interfaces.document_composer import (
    DocumentComposerInterface,
)
from backend.application.interfaces.document_repository import (
    DocumentRepositoryInterface,
)
from backend.application.interfaces.file_storage import FileStorageRepository
from backend.application.interfaces.formatter_service import (
    FormatterServiceInterface,
)
from backend.application.interfaces.pdf_converter import PdfConverterInterface
from backend.application.interfaces.title_service import TitleServiceInterface
from backend.application.usecases.download_document import DownloadDocumentUseCase
from backend.application.usecases.generate_titile import GenerateTitleUseCase
from backend.application.usecases.get_document_status import (
    GetDocumentStatusUseCase,
)
from backend.application.usecases.preview_document import PreviewDocumentUseCase
from backend.application.usecases.upload_document import UploadDocumentUseCase
from backend.application.usecases.upload_with_title import UploadWithTitleUseCase
from backend.infra.db.database import DatabaseSessionFactory
from backend.infra.db.repository import DocumentRepository
from backend.infra.local_storage import LocalFileStorage
from backend.infra.pdf_converter import LibreOfficePdfConverter
from backend.infra.services.document_composer import DocxDocumentComposer
from backend.infra.services.formatter_service import HttpFormatterService
from backend.infra.services.title_service import HttpTitleService
from config import Settings
from dishka import Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncSession


class AppProvider(Provider):
    # ── Config & DB infrastructure ──────────────────────────────────────────

    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return Settings()

    @provide(scope=Scope.APP)
    def provide_db_factory(self, settings: Settings) -> DatabaseSessionFactory:
        return DatabaseSessionFactory(vars(settings))

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self, factory: DatabaseSessionFactory
    ) -> AsyncGenerator[AsyncSession, None]:
        session = factory.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # ── Repositories & storage ───────────────────────────────────────────────

    @provide(scope=Scope.REQUEST)
    def provide_document_repo(
        self, session: AsyncSession
    ) -> DocumentRepositoryInterface:
        return DocumentRepository(session)

    @provide(scope=Scope.APP)
    def provide_file_storage(self, settings: Settings) -> FileStorageRepository:
        return LocalFileStorage(settings.UPLOAD_FOLDER)

    # ── External services ────────────────────────────────────────────────────

    @provide(scope=Scope.APP)
    def provide_formatter(self, settings: Settings) -> FormatterServiceInterface:
        return HttpFormatterService(settings.FORMATTER_SERVICE_URL)

    @provide(scope=Scope.APP)
    def provide_title_service(self, settings: Settings) -> TitleServiceInterface:
        return HttpTitleService(settings.TITLE_SERVICE_URL, settings.UPLOAD_FOLDER)

    @provide(scope=Scope.APP)
    def provide_pdf_converter(self) -> PdfConverterInterface:
        return LibreOfficePdfConverter()

    @provide(scope=Scope.APP)
    def provide_composer(self, settings: Settings) -> DocumentComposerInterface:
        return DocxDocumentComposer(settings.UPLOAD_FOLDER)

    # ── Use cases ────────────────────────────────────────────────────────────

    @provide(scope=Scope.REQUEST)
    def provide_upload_uc(
        self,
        doc_repo: DocumentRepositoryInterface,
        formatter: FormatterServiceInterface,
        storage: FileStorageRepository,
    ) -> UploadDocumentUseCase:
        return UploadDocumentUseCase(doc_repo, formatter, storage)

    @provide(scope=Scope.REQUEST)
    def provide_download_uc(
        self,
        doc_repo: DocumentRepositoryInterface,
        storage: FileStorageRepository,
    ) -> DownloadDocumentUseCase:
        return DownloadDocumentUseCase(doc_repo, storage)

    @provide(scope=Scope.REQUEST)
    def provide_status_uc(
        self, doc_repo: DocumentRepositoryInterface
    ) -> GetDocumentStatusUseCase:
        return GetDocumentStatusUseCase(doc_repo)

    @provide(scope=Scope.REQUEST)
    def provide_preview_uc(
        self,
        doc_repo: DocumentRepositoryInterface,
        storage: FileStorageRepository,
        pdf_converter: PdfConverterInterface,
    ) -> PreviewDocumentUseCase:
        return PreviewDocumentUseCase(doc_repo, storage, pdf_converter)

    @provide(scope=Scope.REQUEST)
    def provide_generate_title_uc(
        self,
        doc_repo: DocumentRepositoryInterface,
        title_service: TitleServiceInterface,
    ) -> GenerateTitleUseCase:
        return GenerateTitleUseCase(doc_repo, title_service)

    @provide(scope=Scope.REQUEST)
    def provide_upload_with_title_uc(
        self,
        doc_repo: DocumentRepositoryInterface,
        formatter: FormatterServiceInterface,
        storage: FileStorageRepository,
        composer: DocumentComposerInterface,
        title_service: TitleServiceInterface,
    ) -> UploadWithTitleUseCase:
        return UploadWithTitleUseCase(
            doc_repo, formatter, storage, composer, title_service
        )


def create_container():
    return make_async_container(AppProvider())
