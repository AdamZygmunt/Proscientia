from __future__ import annotations

import logging

from celery import shared_task
from django.core.files.base import ContentFile

from .models import Document

from erp_mes.services import MockErpMesClient

logger = logging.getLogger(__name__)


@shared_task
def fetch_and_store_file_task(document_id: int) -> None:
    """
    Pobiera plik z mocka (ERP/MES/docs) i zapisuje go do FileField w modelu Document.

    Dla:
      - SOURCE_MOCK_ERP / SOURCE_MOCK_MES -> stream = "erp"/"mes", używa date + filename
      - SOURCE_MOCK_DOCS -> stream = "docs", używa filename, bez date
    """

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s does not exist", document_id)
        return

    if not (doc.is_mock_doc or doc.is_mock_erp_mes):
        logger.info("Document %s is not a mock-based document. Skipping.", document_id)
        return

    client = MockErpMesClient()

    if doc.is_mock_erp_mes:
        if not doc.mock_version_date or not doc.mock_filename:
            logger.error(
                "Document %s missing mock_version_date or mock_filename", document_id
            )
            return

        stream = doc.mock_stream  # "erp" lub "mes"
        date_str = doc.mock_version_date.strftime("%Y-%m-%d")
        name = doc.mock_filename

        content_bytes = client.get_file_bytes(stream=stream, name=name, date=date_str)
    else:
        # MOCK_DOCS
        if not doc.mock_filename:
            logger.error("Document %s missing mock_filename", document_id)
            return

        content_bytes = client.get_file_bytes(
            stream="docs",
            name=doc.mock_filename,
            date=None,
        )

    # Zapis do FileField
    file_name = doc.mock_filename or f"document_{doc.id}"                   # type: ignore[attr-defined]
    doc.file.save(file_name, ContentFile(content_bytes), save=True)

    logger.info("Document %s file fetched and stored.", document_id)


@shared_task
def parse_document_task(document_id: int) -> None:
    """
    Prosty placeholder pod parsowanie dokumentu.

    Docelowo:
      - dla PDF: wyciągnąć tekst, podzielić na chunki,
      - zapisać tekst/embeddingi do bazy (np. DocumentChunk / pgvector),
      - wywołać model OpenAI do streszczeń / quizów.

    Teraz: tylko logujemy, że parsowanie zostało wywołane.
    """
    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        logger.warning("Document %s does not exist", document_id)
        return

    logger.info(
        "parse_document_task called for document %s (source=%s, title=%s)",
        document_id,
        doc.source,
        doc.title,
    )
    # tutaj trzeba dołożyć właściwą logikę RAG / embed / LLM
