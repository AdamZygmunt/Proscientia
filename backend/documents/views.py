from __future__ import annotations
import os

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied


from .models import Document
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    DocumentFromErpMesSerializer,
)
from .tasks import fetch_and_store_file_task, parse_document_task


# HELPERS
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".txt", ".json", ".jsonl", ".yaml", ".yml",
    ".xml", ".doc", ".docx",
}


def count_user_uploaded_documents(user) -> int:
    """
    Liczy aktywne dokumenty wgrane przez użytkownika.
    Używane do limitu 5 własnych plików.
    """
    if user.is_anonymous:
        return 0

    return Document.objects.filter(
        source=Document.SOURCE_USER_UPLOAD,
        uploaded_by=user,
        is_active=True,
    ).count()


def is_allowed_user_file(filename: str) -> bool:
    """
    Sprawdza rozszerzenie pliku użytkownika.
    Odrzucamy excele, skrypty itd.
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_UPLOAD_EXTENSIONS




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


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/documents/<id>/
    DELETE /api/documents/<id>/
    """

    queryset = Document.objects.filter(is_active=True)
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        # Można usuwać tylko własne uploady użytkownika
        if instance.source != Document.SOURCE_USER_UPLOAD:
            raise PermissionDenied("Można usuwać tylko własne pliki użytkownika.")
        if instance.uploaded_by != self.request.user:
            raise PermissionDenied("Można usuwać tylko własne pliki użytkownika.")
        instance.delete()


"""class DocumentUploadView(APIView):
    \"""
    POST /api/documents/upload/
    Upload pliku przez użytkownika.
    \"""

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
        return Response(out.data, status=status.HTTP_201_CREATED)"""
        
class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        # 1) Limit 5 własnych plików
        if count_user_uploaded_documents(user) >= 5:
            return Response(
                {"detail": "Limit 5 własnych plików na użytkownika został przekroczony."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload_file = request.FILES.get("file")
        if not upload_file:
            return Response(
                {"detail": "Brak pliku w żądaniu."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) Walidacja typu/rozszerzenia
        if not is_allowed_user_file(upload_file.name):
            return Response(
                {"detail": "Niedozwolony typ pliku. Dozwolone: pdf, txt, json, jsonl, yaml, xml, doc, docx."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) Standardowy upload
        serializer = DocumentUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        doc = serializer.save(uploaded_by=user)

        # (opcjonalnie) możesz znów przywrócić parsowanie:
        # parse_document_task.delay(doc.id)

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
