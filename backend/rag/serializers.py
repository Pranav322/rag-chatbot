"""
API Serializers for RAG system including Asset management.
"""

from rest_framework import serializers
from rag.models import Asset, ChatSession, ChatMessage


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload request."""
    file = serializers.FileField(help_text="PDF or DOCX file to upload")


class DocumentUploadResponseSerializer(serializers.Serializer):
    """Response for successful document upload."""
    asset_id = serializers.UUIDField(help_text="Asset identifier")
    document_id = serializers.UUIDField(help_text="Unique document identifier (legacy)")
    chunks_created = serializers.IntegerField(help_text="Number of chunks stored")
    doc_type = serializers.CharField(help_text="Detected document type")
    cloudinary_url = serializers.URLField(help_text="Cloudinary URL of uploaded file")
    message = serializers.CharField(help_text="Success message")


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request."""
    message = serializers.CharField(help_text="User's question or message")
    session_id = serializers.UUIDField(required=False, help_text="Optional chat session ID")


class SourceSnippetSerializer(serializers.Serializer):
    """Source snippet from retrieved context."""
    asset_id = serializers.UUIDField(help_text="Asset this snippet came from")
    excerpt = serializers.CharField(help_text="Text excerpt (first 100 chars)")


class ChatResponseSerializer(serializers.Serializer):
    """Response for chat endpoint."""
    session_id = serializers.UUIDField(help_text="Chat session ID")
    answer = serializers.CharField(help_text="Generated answer")
    used_context = serializers.BooleanField(
        help_text="Whether user documents were used in the answer"
    )
    sources = SourceSnippetSerializer(many=True, required=False, help_text="Source snippets")


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for Asset model."""
    class Meta:
        model = Asset
        fields = [
            'id',
            'asset_type',
            'cloudinary_url',
            'original_filename',
            'created_at'
        ]
        read_only_fields = fields


class AssetListResponseSerializer(serializers.Serializer):
    """Response for asset list endpoint."""
    assets = AssetSerializer(many=True)
    total = serializers.IntegerField()


class ErrorSerializer(serializers.Serializer):
    """Standard error response."""
    error = serializers.CharField(help_text="Error message")
    detail = serializers.CharField(required=False, help_text="Additional details")


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model."""
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'used_context', 'created_at']
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession with message count."""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'created_at', 'updated_at', 'message_count', 'last_message']
        read_only_fields = fields
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        return last_msg.content[:100] if last_msg else None


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession with all messages."""
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'created_at', 'updated_at', 'messages']
        read_only_fields = fields
