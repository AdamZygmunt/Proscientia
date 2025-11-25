from __future__ import annotations

import datetime
import json

from django.utils.dateparse import parse_date

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ErpMesSnapshot, SnapshotSyncLog
from .serializers import ErpMesSnapshotSerializer, ErpMesSnapshotListSerializer
from .services import MockErpMesClient


class ErpMesSnapshotListView(generics.ListAPIView):
    """
    GET /api/erp-mes/snapshots/
    Lista wszystkich snapshotów (ERP + MES) z DB.
    """
    queryset = ErpMesSnapshot.objects.all().order_by("stream", "version_date")
    serializer_class = ErpMesSnapshotListSerializer
    permission_classes = [permissions.IsAuthenticated]


class ErpMesStreamSnapshotListView(generics.ListAPIView):
    """
    GET /api/erp-mes/{stream}/snapshots/
    Lista snapshotów dla konkretnego streamu.
    """
    serializer_class = ErpMesSnapshotListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):     # type: ignore
        stream = self.kwargs["stream"]
        return ErpMesSnapshot.objects.filter(stream=stream).order_by("version_date")


class ErpMesSnapshotDetailView(generics.RetrieveAPIView):
    """
    GET /api/erp-mes/{stream}/snapshots/{date}/files/
    Zwraca snapshot (z listą plików) dla danego streamu + daty.
    """
    serializer_class = ErpMesSnapshotSerializer
    lookup_field = "version_date"
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):     # type: ignore
        stream = self.kwargs["stream"]
        return ErpMesSnapshot.objects.filter(stream=stream).order_by("version_date")

    def get_object(self):       # type: ignore
        stream = self.kwargs["stream"]
        date_str = self.kwargs["date"]
        date_obj = parse_date(date_str)
        if not date_obj:
            raise ValueError("Invalid date format, expected YYYY-MM-DD")
        return ErpMesSnapshot.objects.get(stream=stream, version_date=date_obj)


class ErpMesSyncView(APIView):
    """
    POST /api/erp-mes/snapshots/sync/
    Ręczny sync z manifestu mocka:
     - aktualizuje snapshoty ERP/MES w DB
     - dla każdej daty pobiera listing plików
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        client = MockErpMesClient()
        manifest = client.get_manifest()

        for stream in ("erp", "mes"):
            stream_data = manifest.get(stream) or {}
            latest_str = stream_data.get("latest")
            versions = stream_data.get("versions", [])

            # Zresetuj is_latest dla tego streamu
            ErpMesSnapshot.objects.filter(stream=stream, is_latest=True).update(is_latest=False)

            for ver in versions:
                date_obj = parse_date(ver)
                if not date_obj:
                    continue

                snapshot, created = ErpMesSnapshot.objects.get_or_create(
                    stream=stream,
                    version_date=date_obj,
                )

                snapshot.is_latest = (ver == latest_str)

                # Pobierz listing plików z mocka
                listing = client.get_stream_listing(stream=stream, date=ver)
                files = listing.get("files", [])
                snapshot.files = files
                snapshot.save()

                # prosty log
                SnapshotSyncLog.objects.create(
                    stream=stream,
                    version_date=date_obj,
                    snapshot=snapshot,
                    status=SnapshotSyncLog.STATUS_SUCCESS,
                )

        return Response({"detail": "Sync completed"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def erp_mes_json_file_view(request, stream: str, date: str, filename: str):
    """
    GET /api/erp-mes/{stream}/snapshots/{date}/json/{filename}/

    Zwraca zawartość pliku JSON ze snapshotu ERP/MES.
    """
    client = MockErpMesClient()
    # backend dba, że stream to "erp" lub "mes"
    if stream not in ("erp", "mes"):
        return Response({"detail": "Invalid stream"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        content_bytes = client.get_file_bytes(stream=stream, name=filename, date=date)
        data = json.loads(content_bytes.decode("utf-8"))
    except Exception as exc:
        return Response({"detail": f"Error fetching file: {exc}"}, status=status.HTTP_502_BAD_GATEWAY)

    return Response(data, status=status.HTTP_200_OK)
