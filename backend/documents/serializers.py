from __future__ import annotations

from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_email = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "source",
            "title",
            "description",
            "content_type",
            "tags",
            "uploaded_by_email",
            "file_url",
            "mock_stream",
            "mock_version_date",
            "mock_filename",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uploaded_by_email", "file_url", "created_at", "updated_at")

    def get_file_url(self, obj: Document) -> str | None:
        request = self.context.get("request")
        if not obj.file:
            return None
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)

    def get_uploaded_by_email(self, obj: Document) -> str | None:
        if obj.uploaded_by:
            return obj.uploaded_by.email
        return None


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer do uploadu plików przez użytkownika."""

    class Meta:
        model = Document
        fields = ("title", "description", "tags", "file")
        extra_kwargs = {
            "file": {"required": True},
            "title": {"required": False},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        file = validated_data["file"]

        title = validated_data.get("title") or file.name

        doc = Document.objects.create(
            source=Document.SOURCE_USER_UPLOAD,
            title=title,
            description=validated_data.get("description", ""),
            tags=validated_data.get("tags", []),
            uploaded_by=user,
            file=file,
            content_type=getattr(file, "content_type", ""),
        )
        return doc


class DocumentFromErpMesSerializer(serializers.Serializer):
    """
    Tworzenie dokumentu na podstawie pliku z ERP/MES.
    """

    stream = serializers.ChoiceField(choices=("erp", "mes"))
    version_date = serializers.DateField()
    filename = serializers.CharField(max_length=300)

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.JSONField(required=False)

    def create(self, validated_data):
        from .models import Document

        stream = validated_data["stream"]
        version_date = validated_data["version_date"]
        filename = validated_data["filename"]

        source = (
            Document.SOURCE_MOCK_ERP if stream == "erp" else Document.SOURCE_MOCK_MES
        )

        title = validated_data.get("title") or filename

        doc = Document.objects.create(
            source=source,
            title=title,
            description=validated_data.get("description", ""),
            tags=validated_data.get("tags", []),
            mock_stream=stream,
            mock_version_date=version_date,
            mock_filename=filename,
        )
        return doc