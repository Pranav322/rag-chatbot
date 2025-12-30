"""
Django Admin configuration for RAG app.
"""

from django.contrib import admin
from django.utils.html import format_html
from rag.models import Asset, DocumentChunk, ChatSession, ChatMessage


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin for Asset model."""
    
    list_display = ('id', 'original_filename', 'asset_type', 'user_email', 'cloudinary_link', 'chunks_count', 'created_at')
    list_filter = ('asset_type', 'created_at')
    search_fields = ('original_filename', 'user__email', 'cloudinary_public_id')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'cloudinary_url', 'cloudinary_public_id', 'cloudinary_preview')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'original_filename', 'asset_type')
        }),
        ('Cloudinary', {
            'fields': ('cloudinary_url', 'cloudinary_public_id', 'cloudinary_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def cloudinary_link(self, obj):
        return format_html('<a href="{}" target="_blank">View</a>', obj.cloudinary_url)
    cloudinary_link.short_description = 'Cloudinary'
    
    def cloudinary_preview(self, obj):
        if obj.asset_type == 'image':
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px;" />', obj.cloudinary_url)
        return format_html('<a href="{}" target="_blank">{}</a>', obj.cloudinary_url, obj.cloudinary_url)
    cloudinary_preview.short_description = 'Preview'
    
    def chunks_count(self, obj):
        return obj.chunks.count()
    chunks_count.short_description = 'Chunks'


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin for DocumentChunk model."""
    
    list_display = ('id', 'user_id', 'asset_filename', 'doc_type', 'source', 'content_preview', 'created_at')
    list_filter = ('doc_type', 'source', 'created_at')
    search_fields = ('user_id', 'content', 'asset__original_filename')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'user_id', 'document_id', 'created_at', 'embedding_dimension')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user_id', 'asset', 'document_id')
        }),
        ('Content', {
            'fields': ('doc_type', 'source', 'content')
        }),
        ('Vector', {
            'fields': ('embedding_dimension',),
            'description': 'Embedding vector stored for similarity search'
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def asset_filename(self, obj):
        return obj.asset.original_filename if obj.asset else '-'
    asset_filename.short_description = 'Asset'
    asset_filename.admin_order_field = 'asset__original_filename'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def embedding_dimension(self, obj):
        return f"{len(obj.embedding)} dimensions" if obj.embedding else 'No embedding'
    embedding_dimension.short_description = 'Embedding'


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin for ChatSession model."""
    
    list_display = ('id', 'user_email', 'message_count', 'last_message_preview', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'messages__content')
    ordering = ('-updated_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def last_message_preview(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            preview = last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content
            return f"[{last_msg.role}] {preview}"
        return '-'
    last_message_preview.short_description = 'Last Message'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin for ChatMessage model."""
    
    list_display = ('id', 'session_id', 'role', 'content_preview', 'used_context', 'created_at')
    list_filter = ('role', 'used_context', 'created_at')
    search_fields = ('session__id', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'session', 'role')
        }),
        ('Content', {
            'fields': ('content', 'used_context')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def session_id(self, obj):
        return str(obj.session.id)[:8] + '...'
    session_id.short_description = 'Session'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
