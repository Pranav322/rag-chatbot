"""
Vector Retriever.

Performs semantic similarity search using pgvector with strict user filtering.
Returns relevant document chunks above the similarity threshold.
"""

from dataclasses import dataclass
from typing import List
from django.db import connection
from asgiref.sync import sync_to_async

from rag.models import DocumentChunk
from rag.services.embeddings import EmbeddingsService


# Configuration
DEFAULT_TOP_K = 8
# Minimum similarity score to consider a chunk relevant
# Cosine similarity ranges from -1 to 1; 0.25 is a reasonable threshold
SIMILARITY_THRESHOLD = 0.25


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with its similarity score."""
    content: str
    document_id: str
    doc_type: str
    similarity: float
    asset_id: str | None = None


def _execute_vector_search(embedding_str: str, user_id: str, top_k: int) -> List[tuple]:
    """
    Execute the vector similarity search query synchronously.
    This is wrapped with sync_to_async when called from async context.
    """
    sql = """
        SELECT 
            id,
            content,
            document_id,
            doc_type,
            asset_id,
            1 - (embedding <=> %s::vector) as similarity
        FROM document_chunks
        WHERE user_id = %s
        AND (1 - (embedding <=> %s::vector)) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [
            embedding_str, 
            user_id, 
            embedding_str, 
            SIMILARITY_THRESHOLD,
            embedding_str, 
            top_k
        ])
        return cursor.fetchall()


class Retriever:
    """
    Retrieves relevant document chunks using pgvector similarity search.
    
    Strictly filters by user_id to ensure data isolation.
    Uses cosine similarity with a threshold check.
    """
    
    @classmethod
    async def retrieve(
        cls,
        query: str,
        user_id: str,
        top_k: int = DEFAULT_TOP_K
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: The user's question
            user_id: User ID for strict filtering
            top_k: Maximum number of chunks to retrieve
            
        Returns:
            List of RetrievedChunk objects sorted by similarity (highest first)
        """
        # Generate query embedding
        query_embedding = await EmbeddingsService.generate_embedding(query)
        
        # Convert embedding list to pgvector format
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Execute query with sync_to_async wrapper
        rows = await sync_to_async(_execute_vector_search)(
            embedding_str, user_id, top_k
        )
        
        chunks = []
        for row in rows:
            chunks.append(RetrievedChunk(
                content=row[1],
                document_id=str(row[2]),
                doc_type=row[3],
                asset_id=str(row[4]) if row[4] else None,
                similarity=float(row[5])  # Now position 5 after adding asset_id
            ))
        
        return chunks
    
    @classmethod
    def format_context(cls, chunks: List[RetrievedChunk]) -> str | None:
        """
        Format retrieved chunks into a context string.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string, or None if no chunks
        """
        if not chunks:
            return None
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Document {i} - {chunk.doc_type.upper()}]\n{chunk.content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    @classmethod
    def has_relevant_context(cls, chunks: List[RetrievedChunk]) -> bool:
        """
        Check if any retrieved chunks are above the similarity threshold.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            True if there are relevant chunks
        """
        return len(chunks) > 0
