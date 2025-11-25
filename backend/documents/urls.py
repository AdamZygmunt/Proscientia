from django.urls import path

from .views import (
    DocumentListView,
    DocumentDetailView,
    DocumentUploadView,
    DocumentFromErpMesView,
)

urlpatterns = [
    path("", DocumentListView.as_view(), name="document-list"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="document-detail"),
    path("upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("from-erp-mes/", DocumentFromErpMesView.as_view(), name="document-from-erp-mes"),
]
