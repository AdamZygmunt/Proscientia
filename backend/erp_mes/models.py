from django.db import models


class ErpMesSnapshot(models.Model):
    STREAM_ERP = "erp"
    STREAM_MES = "mes"

    STREAM_CHOICES = [
        (STREAM_ERP, "ERP"),
        (STREAM_MES, "MES"),
    ]

    stream = models.CharField(max_length=8, choices=STREAM_CHOICES)
    version_date = models.DateField()  # np. 2026-02-22
    is_latest = models.BooleanField(default=False)

    # Cache listingu plików z mocka:
    # [{ "name": "work_orders.json", "size": 12345 }, ...]
    files = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("stream", "version_date")
        ordering = ["stream", "version_date"]

    def __str__(self) -> str:
        return f"{self.get_stream_display()} {self.version_date}"   # type: ignore


class SnapshotSyncLog(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    stream = models.CharField(max_length=8, choices=ErpMesSnapshot.STREAM_CHOICES)
    version_date = models.DateField()

    snapshot = models.ForeignKey(
        ErpMesSnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sync_logs",
    )

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.stream.upper()} {self.version_date} [{self.status}]"