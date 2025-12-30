"""
RAG API Views with JWT Authentication, Cloudinary, and Asset management.

ALL blocking operations wrapped with sync_to_async to prevent event loop blocking.
"""

import uuid
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from adrf.views import APIView
from asgiref.sync import sync_to_async

from rag.models import DocumentChunk, Asset, ChatSession, ChatMessage
from rag.serializers import (
    DocumentUploadSerializer,
    DocumentUploadResponseSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    AssetListResponseSerializer,
    AssetSerializer,
)
from rag.services.document_processor import DocumentProcessor, DocumentProcessorError
from rag.services.chunker import TextChunker
from rag.services.embeddings import EmbeddingsService
from rag.services.cloudinary_service import CloudinaryService
from rag.services.image_processor import ImageProcessor
from rag.pipeline.query_classifier import QueryClassifier
from rag.pipeline.retriever import Retriever
from rag.pipeline.generator import Generator


class DocumentUploadView(APIView):
    """
    Upload and process a document for RAG with Cloudinary storage.
    
    POST /api/documents/upload
    Authorization: Bearer <token>
    
    Form data:
        - file: PDF or DOCX file
    """
    permission_classes = [IsAuthenticated]
    
    async def post(self, request: Request) -> Response:
        user = request.user
        
        # Validate request
        serializer = DocumentUploadSerializer(data=request.data)
        is_valid = await sync_to_async(serializer.is_valid)()
        
        if not is_valid:
            errors = await sync_to_async(lambda: serializer.errors)()
            return Response(
                {'error': 'Invalid request', 'detail': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = await sync_to_async(lambda: serializer.validated_data)()
        uploaded_file = validated_data['file']
        filename = uploaded_file.name
        
        # Determine file type
        is_image = ImageProcessor.is_supported_image(filename)
        is_document = DocumentProcessor.is_supported(filename)
        
        if not (is_image or is_document):
            return Response(
                {'error': 'Unsupported file type. Allowed: pdf, docx, png, jpg, jpeg'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Read file content (I/O operation)
            logger.info(f"[Upload] Reading file: {filename}")
            file_content = await sync_to_async(uploaded_file.read)()
            logger.info(f"[Upload] File read complete: {len(file_content)} bytes")
            
            # Upload to Cloudinary (network I/O - MUST be async)
            logger.info(f"[Upload] Uploading to Cloudinary...")
            cloudinary_url, cloudinary_public_id = await sync_to_async(
                CloudinaryService.upload
            )(file_content, filename)
            logger.info(f"[Upload] Cloudinary complete: {cloudinary_url[:50]}...")
            
            
            # Determine asset type
            ext = filename.rsplit('.', 1)[-1].lower()
            if is_image:
                asset_type = 'image'
            elif ext == 'pdf':
                asset_type = 'pdf'
            else:
                asset_type = 'docx'
            
            # Create Asset record (DB operation)
            logger.info("[Upload] Creating Asset record...")
            asset = await sync_to_async(Asset.objects.create)(
                user=user,
                asset_type=asset_type,
                cloudinary_url=cloudinary_url,
                cloudinary_public_id=cloudinary_public_id,
                original_filename=filename
            )
            logger.info(f"[Upload] Asset created: {asset.id}")
            
            # Extract text: different logic for images vs documents
            if is_image:
                # Use ImageProcessor (OCR + conditional Vision)
                logger.info("[Upload] Starting image processing (OCR + Vision)...")
                text = await ImageProcessor.process_image(file_content, cloudinary_url)
                doc_type = 'image'
                logger.info(f"[Upload] Image processing complete: {len(text)} chars")
            else:
                # Use DocumentProcessor for PDF/DOCX
                text, doc_type = await sync_to_async(
                    DocumentProcessor.extract_text
                )(file_content, filename)
            
            # Chunk the text (pure Python, but wrap for safety)
            chunks = await sync_to_async(TextChunker.chunk_text)(text)
            
            if not chunks:
                # Delete asset if no content extracted
                await sync_to_async(asset.delete)()
                return Response(
                    {'error': 'No content could be extracted from the file'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate embeddings for all chunks (already async)
            embeddings = await EmbeddingsService.generate_embeddings(chunks)
            
            # Create document ID for grouping chunks
            document_id = uuid.uuid4()
            
            # Store chunks in database with asset reference
            chunk_objects = [
                DocumentChunk(
                    user_id=str(user.id),
                    asset=asset,
                    document_id=document_id,
                    doc_type=doc_type,
                    source='image' if is_image else 'user_upload',
                    content=chunk_text,
                    embedding=embedding
                )
                for chunk_text, embedding in zip(chunks, embeddings)
            ]
            
            # Bulk create for efficiency (DB operation)
            await sync_to_async(DocumentChunk.objects.bulk_create)(chunk_objects)
            
            response_data = {
                'asset_id': asset.id,
                'document_id': document_id,
                'chunks_created': len(chunks),
                'doc_type': doc_type,
                'cloudinary_url': cloudinary_url,
                'message': f'Successfully processed document with {len(chunks)} chunks'
            }
            
            serialized = await sync_to_async(
                lambda: DocumentUploadResponseSerializer(response_data).data
            )()
            
            return Response(serialized, status=status.HTTP_201_CREATED)
            
        except DocumentProcessorError as e:
            # Clean up cloudinary if processing failed
            if 'cloudinary_public_id' in locals():
                await sync_to_async(CloudinaryService.delete)(cloudinary_public_id)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Clean up on any error
            if 'cloudinary_public_id' in locals():
                await sync_to_async(CloudinaryService.delete)(cloudinary_public_id)
            return Response(
                {'error': 'Failed to process document', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AssetListView(APIView):
    """
    List all assets for the authenticated user.
    
    GET /api/assets
    Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]
    
    async def get(self, request: Request) -> Response:
        user = request.user
        
        # Get all assets for this user (DB operation)
        assets = await sync_to_async(list)(
            Asset.objects.filter(user=user).order_by('-created_at')
        )
        
        # Serialize (can be expensive with many assets)
        serialized = await sync_to_async(
            lambda: AssetListResponseSerializer({
                'assets': assets,
                'total': len(assets)
            }).data
        )()
        
        return Response(serialized, status=status.HTTP_200_OK)


class AssetDeleteView(APIView):
    """
    Delete an asset and all related chunks.
    
    DELETE /api/assets/{asset_id}
    Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]
    
    async def delete(self, request: Request, asset_id: str) -> Response:
        user = request.user
        
        try:
            # Get asset (ensure user owns it) - DB operation
            asset = await sync_to_async(
                lambda: Asset.objects.filter(id=asset_id, user=user).first()
            )()
            
            if not asset:
                return Response(
                    {'error': 'Asset not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete from Cloudinary (network I/O)
            cloudinary_deleted = await sync_to_async(
                CloudinaryService.delete
            )(asset.cloudinary_public_id)
            
            if not cloudinary_deleted:
                return Response(
                    {'error': 'Failed to delete file from Cloudinary'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Delete asset (cascades to chunks automatically) - DB operation
            await sync_to_async(asset.delete)()
            
            return Response(
                {'message': 'Asset and all related data deleted successfully'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': 'Failed to delete asset', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatView(APIView):
    """
    Chat with the RAG system with persistent history.
    
    POST /api/chat
    Authorization: Bearer <token>
    
    JSON body:
        - message: User's question
        - session_id: Optional session ID (creates new if not provided)
    """
    permission_classes = [IsAuthenticated]
    
    async def post(self, request: Request) -> Response:
        user = request.user
        user_id = str(user.id)
        
        # Validate request
        serializer = ChatRequestSerializer(data=request.data)
        is_valid = await sync_to_async(serializer.is_valid)()
        
        if not is_valid:
            errors = await sync_to_async(lambda: serializer.errors)()
            return Response(
                {'error': 'Invalid request', 'detail': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = await sync_to_async(lambda: serializer.validated_data)()
        message = validated_data['message']
        session_id = validated_data.get('session_id')
        
        try:
            # Get or create chat session
            if session_id:
                session = await sync_to_async(
                    lambda: ChatSession.objects.filter(id=session_id, user=user).first()
                )()
                if not session:
                    return Response(
                        {'error': 'Session not found or access denied'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new session
                session = await sync_to_async(ChatSession.objects.create)(user=user)
            
            # Save user message
            user_message = await sync_to_async(ChatMessage.objects.create)(
                session=session,
                role='user',
                content=message,
                used_context=False  # User messages don't use context
            )
            
            # Step 1: Classify the query (already async - uses LLM)
            query_type = await QueryClassifier.classify(message)
            
            # Step 2: Retrieve context if needed (already async)
            chunks = None
            used_context = False
            if QueryClassifier.needs_retrieval(query_type):
                chunks = await Retriever.retrieve(query=message, user_id=user_id)
                used_context = len(chunks) > 0 if chunks else False
            
            # Step 3: Generate answer (already async - uses LLM)
            result = await Generator.generate(question=message, chunks=chunks)
            
            # Save assistant message
            assistant_message = await sync_to_async(ChatMessage.objects.create)(
                session=session,
                role='assistant',
                content=result.answer,
                used_context=result.used_context
            )
            
            response_data = {
                'session_id': session.id,
                'answer': result.answer,
                'used_context': result.used_context
            }
            
            # Add sources if available (Phase 6 - Context Surfacing)
            if result.sources:
                response_data['sources'] = [
                    {'asset_id': source.asset_id, 'excerpt': source.excerpt}
                    for source in result.sources
                ]
            
            serialized = await sync_to_async(
                lambda: ChatResponseSerializer(response_data).data
            )()
            
            return Response(serialized, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Failed to generate response', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatSessionListView(APIView):
    """
    List all chat sessions for authenticated user.
    
    GET /api/chat/sessions
    Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]
    
    async def get(self, request: Request) -> Response:
        user = request.user
        
        # Get all sessions for user
        sessions = await sync_to_async(list)(
            ChatSession.objects.filter(user=user).prefetch_related('messages')
        )
        
        from rag.serializers import ChatSessionSerializer
        serialized = await sync_to_async(
            lambda: [ChatSessionSerializer(s).data for s in sessions]
        )()
        
        return Response({'sessions': serialized, 'total': len(sessions)}, status=status.HTTP_200_OK)


class ChatSessionDetailView(APIView):
    """
    Get details of specific chat session with all messages.
    
    GET /api/chat/sessions/{session_id}
    Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]
    
    async def get(self, request: Request, session_id: str) -> Response:
        user = request.user
        
        # Get session with messages
        session = await sync_to_async(
            lambda: ChatSession.objects.filter(
                id=session_id, user=user
            ).prefetch_related('messages').first()
        )()
        
        if not session:
            return Response(
                {'error': 'Session not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from rag.serializers import ChatSessionDetailSerializer
        serialized = await sync_to_async(
            lambda: ChatSessionDetailSerializer(session).data
        )()
        
        return Response(serialized, status=status.HTTP_200_OK)


class ChatStreamView(APIView):
    """
    Stream chat responses using Server-Sent Events.
    
    POST /api/chat/stream
    Authorization: Bearer <token>
    
    JSON body:
        - message: User's question
        - session_id: Optional session ID
    
    Response: text/event-stream with tokens
    """
    permission_classes = [IsAuthenticated]
    
    # Custom content negotiator to bypass Accept header for SSE
    class IgnoreClientContentNegotiation:
        def select_parser(self, request, parsers):
            return parsers[0] if parsers else None
        
        def select_renderer(self, request, renderers, format_suffix=None):
            return (renderers[0], renderers[0].media_type) if renderers else None
    
    content_negotiation_class = IgnoreClientContentNegotiation
    
    async def post(self, request: Request):
        import json
        from django.http import StreamingHttpResponse
        
        user = request.user
        user_id = str(user.id)
        
        # Validate request
        serializer = ChatRequestSerializer(data=request.data)
        is_valid = await sync_to_async(serializer.is_valid)()
        
        if not is_valid:
            errors = await sync_to_async(lambda: serializer.errors)()
            return Response(
                {'error': 'Invalid request', 'detail': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = await sync_to_async(lambda: serializer.validated_data)()
        message = validated_data['message']
        session_id = validated_data.get('session_id')
        
        # Get or create session
        if session_id:
            session = await sync_to_async(
                lambda: ChatSession.objects.filter(id=session_id, user=user).first()
            )()
            if not session:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            session = await sync_to_async(ChatSession.objects.create)(user=user)
        
        # Save user message
        await sync_to_async(ChatMessage.objects.create)(
            session=session,
            role='user',
            content=message,
            used_context=False
        )
        
        async def event_stream():
            full_response = ""
            used_context = False
            sources = None
            
            try:
                # Classify query
                query_type = await QueryClassifier.classify(message)
                
                # Retrieve context if needed
                chunks = None
                if QueryClassifier.needs_retrieval(query_type):
                    chunks = await Retriever.retrieve(query=message, user_id=user_id)
                
                # Send session info first
                yield f"data: {json.dumps({'type': 'session', 'session_id': str(session.id)})}\n\n"
                
                # Stream tokens
                async for event in Generator.stream_generate(question=message, chunks=chunks):
                    if event['type'] == 'token':
                        full_response += event['content']
                        yield f"data: {json.dumps(event)}\n\n"
                    elif event['type'] == 'done':
                        used_context = event.get('used_context', False)
                        sources = event.get('sources')
                
                # Save assistant message
                await sync_to_async(ChatMessage.objects.create)(
                    session=session,
                    role='assistant',
                    content=full_response,
                    used_context=used_context
                )
                
                # Send final event with metadata
                yield f"data: {json.dumps({'type': 'done', 'used_context': used_context, 'sources': sources})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
