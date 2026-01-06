from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # <--- IMPORT 1
from django.shortcuts import get_object_or_404
from documents.models import Document
from .tasks import generate_summary_task, generate_erp_mes_latest_report_task
from rest_framework.permissions import IsAuthenticated
from .services import count_user_summaries_for_document
from rest_framework import generics, permissions
from .models import AiArtifact
from .serializers import AiArtifactSerializer


class AiArtifactListView(generics.ListAPIView):
    """
    GET /api/agents/artifacts/?type=summary

    Zwraca listę artefaktów zalogowanego użytkownika.
    Opcjonalny parametr `type` filtruje po polu `artifact_type`
    (np. "summary", "quiz").
    """
    serializer_class = AiArtifactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = AiArtifact.objects.filter(owner=user)
        type_param = self.request.query_params.get("type")
        if type_param:
            qs = qs.filter(artifact_type=type_param)
        return qs


class AiArtifactDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/agents/artifacts/<id>/
    DELETE /api/agents/artifacts/<id>/

    Używane przez frontend do usuwania streszczeń.
    Dostęp tylko do artefaktów bieżącego użytkownika.
    """
    serializer_class = AiArtifactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AiArtifact.objects.filter(owner=self.request.user)


class TriggerSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, doc_id):
        user = request.user

        # 1) Pobierz dokument
        doc = get_object_or_404(Document, pk=doc_id)

        # 2) Sprawdź, czy user ma prawo do dokumentu:
        #    - mockowe (MOCK_*) są globalnie dostępne
        #    - USER_UPLOAD tylko jeśli uploaded_by=user
        if doc.source == Document.SOURCE_USER_UPLOAD:
            if doc.uploaded_by_id != user.id:                               # type: ignore
                return Response(
                    {"detail": "Nie masz dostępu do tego pliku."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # 3) Limit 3 streszczeń na dokument per user
        if count_user_summaries_for_document(user, doc) >= 3:
            return Response(
                {"detail": "Limit 3 streszczeń dla tego pliku został przekroczony."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4) Opcjonalny 'scope' (na przyszłego DocSearch)
        scope = request.data.get("scope")

        # 5) Uruchomienie Celery Task z user_id i scope
        task = generate_summary_task.delay(doc.id, user.id, scope)          # type: ignore

        return Response({
            "message": "Zadanie przyjęte do realizacji.",
            "task_id": task.id,
            "document_id": doc.id,                                          # type: ignore
            "websocket_url": "/ws/notifications/",
        }, status=status.HTTP_202_ACCEPTED)


class ErpMesQuickReportView(APIView):
    """
    POST /api/agents/erp-mes/latest-report/

    Uruchamia agenta generującego szybki raport z najnowszych snapshotów ERP/MES.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        scope = request.data.get("scope")  # opcjonalnie, pod DocSearch w przyszłości

        task = generate_erp_mes_latest_report_task.delay(user.id, scope)        # type: ignore

        return Response(
            {
                "message": "Zadanie raportu ERP/MES przyjęte do realizacji.",
                "task_id": task.id,
                "websocket_url": "/ws/notifications/",
            },
            status=status.HTTP_202_ACCEPTED,
        )
