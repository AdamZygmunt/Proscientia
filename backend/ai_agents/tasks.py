from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from documents.models import Document
from erp_mes.models import ErpMesSnapshot
from erp_mes.services import MockErpMesClient
from .models import AiArtifact, AiSummary
from .services import run_agent_summary_for_document, build_summary_filename, run_agent_summary_from_text

# Importy do WebSockets (asynchroniczność w synchronicznym tasku)
from channels.layers import get_channel_layer                       # type: ignore
from asgiref.sync import async_to_sync

@shared_task(bind=True)
def generate_summary_task(self, doc_id, user_id, scope=None):
    channel_layer = get_channel_layer()
    User = get_user_model()

    def send_update(status, data=None):
        async_to_sync(channel_layer.group_send)(                                    # type: ignore
            "global_notifications",  # na razie globalnie, później user_<id>
            {
                "type": "task_update",
                "message": {
                    "task_id": self.request.id,
                    "doc_id": doc_id,
                    "user_id": user_id,
                    "status": status,
                    "payload": data or {},
                },
            },
        )

    try:
        send_update("started")

        # 1. Pobranie użytkownika i dokumentu
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            send_update("error", {"error": "Użytkownik nie istnieje."})
            return "User does not exist"

        try:
            doc = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            send_update("error", {"error": "Dokument nie istnieje."})
            return "Document does not exist"

        if not doc.file:
            send_update("error", {"error": "Brak pliku powiązanego z dokumentem."})
            return "No file"

        # 2. Praca agenta – nowa funkcja z obsługą scope/chunkingu
        summary_text, summary_meta = run_agent_summary_for_document(doc, scope=scope)

        # 3. Zapis streszczenia jako plik .txt w AiArtifact
        filename = build_summary_filename(doc, user)
        title = doc.title or doc.mock_filename or f"Document {doc.id}"                      # type: ignore

        artifact = AiArtifact(
            artifact_type=AiArtifact.TYPE_SUMMARY,
            document=doc,
            owner=user,
            title=f"Streszczenie: {title}",
            metadata={
                "scope": scope,
                "summary_meta": summary_meta,
                "source": doc.source,
                "mock_stream": getattr(doc, "mock_stream", None),
                "mock_version_date": (
                    doc.mock_version_date.isoformat() if getattr(doc, "mock_version_date", None) else None      # type: ignore
                ),
            },
        )
        artifact.file.save(filename, ContentFile(summary_text or ""), save=True)

        # (opcjonalnie: można nadal uzupełniać AiSummary, ale nie jest to już wymagane)
        # AiSummary.objects.update_or_create(
        #     document=doc,
        #     defaults={"summary_text": summary_text},
        # )

        # 4. Sukces – wyślij info o artefakcie do frontendu
        send_update(
            "completed",
            {
                "artifact_id": artifact.id,                         # type: ignore 
                "file_url": artifact.file.url,
                "title": artifact.title,
                "summary_preview": (summary_text or "")[:500],
            },
        )

        return "Success"

    except Exception as e:
        send_update("error", {"error": str(e)})
        raise e
    
    
@shared_task(bind=True)
def generate_erp_mes_latest_report_task(self, user_id, scope=None):
    """
    Tworzy szybki raport z najnowszych snapshotów ERP i MES:
    - znajduje snapshoty is_latest=True
    - pobiera wszystkie pliki JSON z tych snapshotów z mock API
    - generuje streszczenie (raport) i zapisuje jako AiArtifact (txt)
    """
    channel_layer = get_channel_layer()
    User = get_user_model()

    def send_update(status, data=None):
        async_to_sync(channel_layer.group_send)(                # type: ignore
            "global_notifications",
            {
                "type": "task_update",
                "message": {
                    "task_id": self.request.id,
                    "doc_id": None,
                    "user_id": user_id,
                    "status": status,
                    "payload": data or {},
                },
            },
        )

    try:
        send_update("started")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            send_update("error", {"error": "Użytkownik nie istnieje."})
            return "User does not exist"

        # 1. Najnowsze snapshoty ERP i MES
        snapshots = list(
            ErpMesSnapshot.objects.filter(
                is_latest=True,
                stream__in=[ErpMesSnapshot.STREAM_ERP, ErpMesSnapshot.STREAM_MES],
            )
        )
        if not snapshots:
            send_update("error", {"error": "Brak najnowszych snapshotów ERP/MES."})
            return "No latest snapshots"

        client = MockErpMesClient()

        # 2. Zbuduj tekst wejściowy z zawartości plików JSON
        sections: list[str] = []
        for snap in snapshots:
            date_str = snap.version_date.isoformat()
            header = f"\n=== SNAPSHOT {snap.get_stream_display()} {date_str} ===\n"             # type: ignore
            sections.append(header)

            for file_info in (snap.files or []):
                name = file_info.get("name", "")
                if not name.endswith(".json"):
                    continue

                try:
                    content_bytes = client.get_file_bytes(
                        stream=snap.stream,
                        name=name,
                        date=date_str,
                    )
                    text = content_bytes.decode("utf-8", errors="ignore")
                except Exception as e:
                    text = f"<<Błąd pobierania pliku {name}: {e}>>"

                # przytnij, żeby nie zalać modelu
                text = text[:2000]
                sections.append(f"\n--- PLIK: {name} ---\n{text}\n")

        full_text = "\n".join(sections).strip()
        if not full_text:
            send_update("error", {"error": "Brak danych z plików JSON ERP/MES."})
            return "No JSON data"

        # 3. LLM – streszczenie raportu
        system_prompt = (
            "Jesteś inżynierem produkcji. Na podstawie danych ERP i MES "
            "z najnowszych snapshotów stwórz krótki raport w punktach. "
            "Skup się na najważniejszych informacjach: liczbie/rodzajach zleceń, "
            "stanach produkcji, potencjalnych problemach lub alertach. "
            "Nie przepisuj danych 1:1 – podsumuj je."
        )

        summary_text, llm_meta = run_agent_summary_from_text(
            full_text,
            scope=scope,
            system_prompt=system_prompt,
        )

        # 4. Zapis jako AiArtifact (bez konkretnego Document)
        snap_info = [
            {
                "id": s.id,                                     # type: ignore
                "stream": s.stream,
                "version_date": s.version_date.isoformat(),
                "files_count": s.files_count,
            }
            for s in snapshots
        ]

        title = "Raport ERP/MES – najnowsze snapshoty"
        artifact = AiArtifact(
            artifact_type=AiArtifact.TYPE_SUMMARY,
            document=None,
            owner=user,
            title=title,
            metadata={
                "scope": scope,
                "llm": llm_meta,
                "report_type": "erp_mes_latest",
                "snapshots": snap_info,
            },
        )
        artifact.file.save(
            "report_erp_mes_latest.txt",
            ContentFile(summary_text or ""),
            save=True,
        )

        send_update(
            "completed",
            {
                "artifact_id": artifact.id,                             # type: ignore
                "file_url": artifact.file.url,
                "title": artifact.title,
                "summary_preview": (summary_text or "")[:500],
            },
        )

        return "Success"

    except Exception as e:
        send_update("error", {"error": str(e)})
        raise e
