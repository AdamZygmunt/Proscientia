from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from documents.models import Document
from .models import AiSummary
from .services import run_agent_summary

# Importy do WebSockets (asynchroniczność w synchronicznym tasku)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task(bind=True)
def generate_summary_task(self, doc_id):
    channel_layer = get_channel_layer()
    
    # Funkcja pomocnicza do wysyłania statusów
    def send_update(status, data=None):
        async_to_sync(channel_layer.group_send)(
            "global_notifications", # Nazwa grupy z consumers.py
            {
                "type": "task_update", # Nazwa metody w consumers.py
                "message": {
                    "task_id": self.request.id,
                    "doc_id": doc_id,
                    "status": status,
                    "payload": data
                }
            }
        )

    try:
        # 1. Info o starcie
        send_update("started")

        # 2. Pobranie dokumentu
        doc = Document.objects.get(id=doc_id)
        if not doc.file:
            send_update("error", {"error": "Brak pliku"})
            return "Brak pliku"

        # 3. Praca Agenta (długa operacja)
        summary_text = run_agent_summary(doc.file.path)

        # 4. Zapis w bazie
        AiSummary.objects.update_or_create(
            document=doc,
            defaults={"summary_text": summary_text}
        )

        # 5. SUKCES - Wyślij gotowe dane do frontendu
        send_update("completed", {"summary": summary_text})
        
        return "Success"

    except Exception as e:
        send_update("error", {"error": str(e)})
        raise e