from rest_framework import serializers
from .models import ErpMesSnapshot


class SnapshotFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField()


class ErpMesSnapshotSerializer(serializers.ModelSerializer):
    files = SnapshotFileSerializer(many=True, read_only=True)

    class Meta:
        model = ErpMesSnapshot
        fields = (
            "id",
            "stream",
            "version_date",
            "is_latest",
            "files",
            "created_at",
            "updated_at",
        )


class ErpMesSnapshotListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErpMesSnapshot
        fields = (
            "id",
            "stream",
            "version_date",
            "is_latest",
        )