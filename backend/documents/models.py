from __future__ import annotations

from django.conf import settings
from django.db import models


class Document(models.Model):
    SOURCE_MOCK_DOCS = "MOCK_DOCS"
    SOURCE_MOCK_ERP = "MOCK_ERP"
    SOURCE_MOCK_MES = "MOCK_MES"
    SOURCE_USER_UPLOAD = "USER_UPLOAD"

    SOURCE_CHOICES = [
        (SOURCE_MOCK_DOCS, "Mock - dokumenty (docs)"),
        (SOURCE_MOCK_ERP, "Mock - ERP snapshot"),
        (SOURCE_MOCK_MES, "Mock - MES snapshot"),
        (SOURCE_USER_UPLOAD, "Upload użytkownika"),
    ]

    source = models.CharField(max_length=32, choices=SOURCE_CHOICES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # MIME type, np. application/pdf, application/json
    content_type = models.CharField(max_length=100, blank=True)

    # tagi, np. ["ventilator", "spec", "safety"]
    tags = models.JSONField(default=list, blank=True)

    # kto wrzucił dokument (dla mocków może być null)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )

    # fizyczny plik (dla USER_UPLOAD i dla mocków po ściągnięciu)
    file = models.FileField(
        upload_to="documents/%Y/%m/%d",
        null=True,
        blank=True,
    )

    # --- powiązania z mockiem ERP/MES/docs ---

    # "erp", "mes" lub "docs" – tylko dla dokumentów pochodzących z mocka
    mock_stream = models.CharField(max_length=16, blank=True)

    # data snapshotu ERP/MES (dla source MOCK_ERP / MOCK_MES)
    mock_version_date = models.DateField(null=True, blank=True)

    # nazwa pliku w mocku (relatywna ścieżka, np. "work_orders.json" albo "ventilator_pb560/spec.pdf")
    mock_filename = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # type: ignore[override]
        return f"{self.title} [{self.source}]"

    @property
    def is_user_upload(self) -> bool:
        return self.source == self.SOURCE_USER_UPLOAD

    @property
    def is_mock_doc(self) -> bool:
        return self.source == self.SOURCE_MOCK_DOCS

    @property
    def is_mock_erp_mes(self) -> bool:
        return self.source in (self.SOURCE_MOCK_ERP, self.SOURCE_MOCK_MES)
