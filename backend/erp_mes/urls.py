from django.urls import path

from .views import (
    ErpMesSnapshotListView,
    ErpMesStreamSnapshotListView,
    ErpMesSnapshotDetailView,
    ErpMesSyncView,
    erp_mes_json_file_view,
)

urlpatterns = [
    # Wszystkie snapshoty (ERP + MES)
    path("snapshots/", ErpMesSnapshotListView.as_view(), name="erp-mes-snapshots"),

    # Sync (admin)
    path("snapshots/sync/", ErpMesSyncView.as_view(), name="erp-mes-sync"),

    # Snapshoty dla konkretnego streamu
    path("<str:stream>/snapshots/", ErpMesStreamSnapshotListView.as_view(), name="erp-mes-stream-snapshots"),

    # Files listing (snapshot detail)
    path("<str:stream>/snapshots/<str:date>/files/", ErpMesSnapshotDetailView.as_view(), name="erp-mes-snapshot-detail"),

    # JSON file content
    path("<str:stream>/snapshots/<str:date>/json/<str:filename>/", erp_mes_json_file_view, name="erp-mes-json-file"),
]
