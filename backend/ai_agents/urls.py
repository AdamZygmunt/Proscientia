from django.urls import path
from .views import TriggerSummaryView

urlpatterns = [
    path('summarize/<int:doc_id>/', TriggerSummaryView.as_view(), name='trigger-summary'),
]