from django.contrib import admin
from .models import AiSummary, AiArtifact, DocumentChunk

@admin.register(AiSummary)
class AiSummaryAdmin(admin.ModelAdmin):
    list_display = ['document', 'created_at']


@admin.register(AiArtifact)
class AiArtifactAdmin(admin.ModelAdmin):
    list_display = ['artifact_type', 'document', 'owner', 'created_at']
    list_filter = ['artifact_type', 'owner']

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'short_content', 'created_at']
    list_filter = ['document']
    
    def short_content(self, obj):
        return obj.text_content[:50] + "..."