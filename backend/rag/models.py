"""
Models for RAG system with Asset management and Cloudinary integration.

Asset: Stores metadata for user-uploaded files (PDFs, DOCX, images)
DocumentChunk: Stores text chunks with embeddings for semantic search
"""

import uuid
from django.db import models
from django.conf import settings
from pgvector.django import VectorField


class Asset(models.Model):
    """
    Represents a user-uploaded file stored in Cloudinary.
    
    Tracks PDFs, DOCX files, and images. When deleted, triggers:
    - Cloudinary file deletion
    - Cascade deletion of all related DocumentChunks
    """
    
    ASSET_TYPES = (
        ('pdf', 'PDF Document'),
        ('docx', 'DOCX Document'),
        ('image', 'Image (PNG/JPG/JPEG)'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assets'
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    cloudinary_url = models.URLField(max_length=500)
    cloudinary_public_id = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'assets'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'asset_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.asset_type}) - {self.user.email}"


class DocumentChunk(models.Model):
    """
    Stores document chunks with their embeddings for RAG retrieval.
    
    Now linked to Asset model for proper lifecycle management.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    
    # NEW: Link to Asset for cascade deletion
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='chunks',
        null=True  # Allow NULL for existing chunks
    )
    
    # Keep document_id for backward compatibility and grouping
    document_id = models.UUIDField(db_index=True)
    doc_type = models.CharField(max_length=50)
    source = models.CharField(max_length=50, default='user_upload')
    content = models.TextField()
    
    # sentence-transformers all-MiniLM-L6-v2 produces 384-dimensional vectors
    embedding = VectorField(dimensions=384)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunks'
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['asset', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Chunk {self.id} (Asset: {self.asset_id}, User: {self.user_id})"


class ChatSession(models.Model):
    """
    Represents a chat conversation session.
    
    Groups related messages together in a conversation thread.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_sessions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Session {self.id} - {self.user.email}"


class ChatMessage(models.Model):
    """
    Stores individual messages in a chat session.
    
    Tracks both user questions and assistant responses.
    """
    
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    used_context = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
