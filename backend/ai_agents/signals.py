from django.db.models.signals import post_save
from django.dispatch import receiver
from documents.models import Document
from .tasks import process_document_indexing_task

@receiver(post_save, sender=Document)
def auto_index_new_document(sender, instance, created, **kwargs):
    """
    Automatycznie uruchamia indeksowanie (RAG) w tle,
    gdy powstanie nowy obiekt Document.
    """
    if created:
        # created=True oznacza, że to nowy wpis (INSERT), a nie edycja (UPDATE).
        # Uruchamiamy task w Celery
        print(f"[Signal] Nowy dokument ID={instance.id} wykryty. Uruchamiam indeksowanie...")
        process_document_indexing_task.delay(instance.id)