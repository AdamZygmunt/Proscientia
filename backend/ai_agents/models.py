# ai_agents/models.py
from django.db import models
from django.conf import settings
from documents.models import Document
from pgvector.django import VectorField

class AiSummary(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='ai_summary')
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.document.id}"                # type: ignore


class AiArtifact(models.Model):
    TYPE_SUMMARY = "summary"
    TYPE_QUIZ = "quiz"
    TYPE_CHOICES = [
        (TYPE_SUMMARY, "Summary"),
        (TYPE_QUIZ, "Quiz"),
    ]

    artifact_type = models.CharField(max_length=16, choices=TYPE_CHOICES)

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="ai_artifacts",
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_artifacts",
    )

    # fizycznie wygenerowany plik (txt/jsonl)
    file = models.FileField(upload_to="ai_artifacts/%Y/%m/%d")

    title = models.CharField(max_length=255)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.artifact_type} for doc {self.document_id} (user {self.owner_id})"        # type: ignore[attr-defined]
    

class DocumentChunk(models.Model):
    # (Wiedza RAG)
    """Przechowuje pocięte kawałki dokumentu wraz z ich wektorami."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text_content = models.TextField()
    
    # Wektor o wymiarze 1536 (OpenAI text-embedding-3-small)
    embedding = VectorField(dimensions=1536) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']
        # W przyszłości dodamy tu index HNSW dla wydajności
