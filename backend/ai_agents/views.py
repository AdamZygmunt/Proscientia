from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # <--- IMPORT 1
from django.shortcuts import get_object_or_404
from documents.models import Document
from .tasks import generate_summary_task

class TriggerSummaryView(APIView):
    #permission_classes = [IsAuthenticated] # Odkomentuj jak będziesz gotowy
    permission_classes = [AllowAny]  # <--- LINIA ODPOWIADAJĄCA ZA DOSTĘP DLA WSZYSTKIC

    def post(self, request, doc_id):
        # Sprawdzenie czy dokument istnieje
        doc = get_object_or_404(Document, pk=doc_id)
        
        # Uruchomienie Celery Task
        task = generate_summary_task.delay(doc.id)
        
        return Response({
            "message": "Zadanie przyjęte do realizacji.",
            "task_id": task.id,
            "document_id": doc.id,
            "websocket_url": "/ws/notifications/"
        }, status=status.HTTP_202_ACCEPTED)