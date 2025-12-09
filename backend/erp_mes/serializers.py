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
    files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ErpMesSnapshot
        fields = (
            "id",
            "stream",
            "version_date",
            "is_latest",
            "files_count",
        )
        
    def get_files_count(self, obj) -> int:
        return obj.files_count