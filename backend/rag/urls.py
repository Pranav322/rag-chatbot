"""
RAG URL routes.
"""

from django.urls import path
from rag.views import (
    DocumentUploadView,
    AssetListView,
    AssetDeleteView,
    ChatView,
    ChatStreamView,
    ChatSessionListView,
    ChatSessionDetailView,
)

app_name = 'rag'

urlpatterns = [
    path('documents/upload', DocumentUploadView.as_view(), name='upload_document'),
    path('assets', AssetListView.as_view(), name='list_assets'),
    path('assets/<uuid:asset_id>', AssetDeleteView.as_view(), name='delete_asset'),
    path('chat', ChatView.as_view(), name='chat'),
    path('chat/stream', ChatStreamView.as_view(), name='chat_stream'),
    path('chat/sessions', ChatSessionListView.as_view(), name='list_sessions'),
    path('chat/sessions/<uuid:session_id>', ChatSessionDetailView.as_view(), name='session_detail'),
]
