from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentFromErpMesSerializer,
)
from .tasks import fetch_and_store_file_task, parse_document_task


class DocumentListView(generics.ListAPIView):
    """
    GET /api/documents/
    Lista dokumentów z prostym filtrowaniem.
    """

    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):     # type: ignore[override]
        qs = Document.objects.filter(is_active=True)

        source = self.request.query_params.get("source")                            # type: ignore[var-annotated]
        if source:
            qs = qs.filter(source=source)

        stream = self.request.query_params.get("stream")                            # type: ignore[var-annotated]
        if stream:
            qs = qs.filter(mock_stream=stream)

        version_date = self.request.query_params.get("version_date")                # type: ignore[var-annotated]
        if version_date:
            qs = qs.filter(mock_version_date=version_date)

        return qs.order_by("-created_at")


class DocumentDetailView(generics.RetrieveAPIView):
    """
    GET /api/documents/<id>/
    Szczegóły dokumentu.
    """

    queryset = Document.objects.filter(is_active=True)
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/
    Upload pliku przez użytkownika.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        doc = serializer.save()

        # Opcjonalnie od razu parsujemy dokument asynchronicznie
        parse_document_task.delay(doc.id)               # type: ignore[attr-defined]

        out = DocumentSerializer(doc, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class DocumentFromErpMesView(APIView):
    """
    POST /api/documents/from-erp-mes/
    Tworzy dokument powiązany z plikiem z ERP/MES (mock).

    Nie pobiera od razu pliku, ale zleca task Celery `fetch_and_store_file_task`.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DocumentFromErpMesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = serializer.save()

        # Pobranie fizycznego pliku z mocka i zapis do FileField
        fetch_and_store_file_task.delay(doc.id)         # type: ignore[attr-defined]

        out = DocumentSerializer(doc, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)
