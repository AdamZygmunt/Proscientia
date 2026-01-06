from django.contrib import admin
from .models import AiSummary, AiArtifact

@admin.register(AiSummary)
class AiSummaryAdmin(admin.ModelAdmin):
    list_display = ['document', 'created_at']


@admin.register(AiArtifact)
class AiArtifactAdmin(admin.ModelAdmin):
    list_display = ['artifact_type', 'document', 'owner', 'created_at']
    list_filter = ['artifact_type', 'owner']
