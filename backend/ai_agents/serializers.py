from rest_framework import serializers
from .models import AiArtifact
from documents.models import Document


class DocumentLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "title")


class AiArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer pod frontend:
    - dokument w polu `document` (id, title)
    - `document_id` jako osobne pole
    - `file_url` – pełny URL do pobrania pliku
    """
    document = DocumentLiteSerializer(read_only=True)
    document_id = serializers.IntegerField(source="document.id", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = AiArtifact
        fields = (
            "id",
            "artifact_type",
            "title",
            "file",        # surowa ścieżka (nie jest potrzebna na froncie, ale nie szkodzi)
            "file_url",    # pełny URL
            "document",
            "document_id",
            "metadata",
            "created_at",
        )

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url
