# erp_mes/tasks.py
from __future__ import annotations

import json
from typing import Optional

from celery import shared_task
from django.utils.dateparse import parse_date

from .models import ErpMesSnapshot, SnapshotSyncLog
from .services import MockErpMesClient


@shared_task
def sync_erp_mes_snapshots_task():
    """
    Task Celery do synchronizacji snapshotów ERP/MES z mockiem.
    Odpowiednik ręcznego POST /api/erp-mes/snapshots/sync/.
    """
    client = MockErpMesClient()
    manifest = client.get_manifest()

    for stream in ("erp", "mes"):
        stream_data = manifest.get(stream) or {}
        latest_str = stream_data.get("latest")
        versions = stream_data.get("versions", [])

        ErpMesSnapshot.objects.filter(stream=stream, is_latest=True).update(is_latest=False)

        for ver in versions:
            date_obj = parse_date(ver)
            if not date_obj:
                continue

            snapshot, _ = ErpMesSnapshot.objects.get_or_create(
                stream=stream,
                version_date=date_obj,
            )

            snapshot.is_latest = (ver == latest_str)

            listing = client.get_stream_listing(stream=stream, date=ver)
            files = listing.get("files", [])
            snapshot.files = files
            snapshot.save()

            SnapshotSyncLog.objects.create(
                stream=stream,
                version_date=date_obj,
                snapshot=snapshot,
                status=SnapshotSyncLog.STATUS_SUCCESS,
            )


@shared_task
def fetch_erp_mes_json_file_task(stream: str, date: str, filename: str) -> Optional[dict]:
    """
    Przykładowy task pobierający JSON z mocka.
    Docelowo może zasilać dokumenty/RAG lub generować streszczenia.
    """
    client = MockErpMesClient()
    content_bytes = client.get_file_bytes(stream=stream, name=filename, date=date)
    try:
        return json.loads(content_bytes.decode("utf-8"))
    except Exception:
        return None
