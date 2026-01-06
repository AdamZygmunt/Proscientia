from django.urls import path
from .views import (
    TriggerSummaryView,
    ErpMesQuickReportView,
    AiArtifactListView,
    AiArtifactDetailView,
    TriggerIndexingView
)
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("summarize/<int:doc_id>/", TriggerSummaryView.as_view(), name="agent-summarize"),
    path(
        "erp-mes/latest-report/",
        ErpMesQuickReportView.as_view(),
        name="agent-erp-mes-latest-report",
    ),
    path(
        "artifacts/",
        AiArtifactListView.as_view(),
        name="ai-artifact-list",
    ),
    path(
        "artifacts/<int:pk>/",
        AiArtifactDetailView.as_view(),
        name="ai-artifact-detail",
    ),
    path(
        "index/<int:doc_id>/", 
        TriggerIndexingView.as_view(), 
        name="agent-index"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
