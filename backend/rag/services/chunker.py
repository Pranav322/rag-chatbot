"""
Text Chunking Service.

Splits text into overlapping chunks for embedding and retrieval.
Uses tiktoken for accurate token counting with OpenAI models.
"""

from typing import List
import tiktoken


# Configuration: matches OpenAI embedding model tokenization
ENCODING_NAME = 'cl100k_base'
# Target chunk size in tokens
DEFAULT_CHUNK_SIZE = 500
# Overlap between consecutive chunks for context continuity
DEFAULT_CHUNK_OVERLAP = 100


class TextChunker:
    """
    Splits text into overlapping token-based chunks.
    
    Uses tiktoken for accurate token counting to ensure chunks
    fit within embedding model limits. Overlap helps maintain
    context across chunk boundaries.
    """
    
    _encoder: tiktoken.Encoding | None = None
    
    @classmethod
    def _get_encoder(cls) -> tiktoken.Encoding:
        """Get or create the tiktoken encoder."""
        if cls._encoder is None:
            cls._encoder = tiktoken.get_encoding(ENCODING_NAME)
        return cls._encoder
    
    @classmethod
    def chunk_text(
        cls,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> List[str]:
        """
        Split text into overlapping chunks based on token count.
        
        Args:
            text: The text to chunk
            chunk_size: Maximum tokens per chunk (default: 500)
            chunk_overlap: Tokens to overlap between chunks (default: 100)
            
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        encoder = cls._get_encoder()
        
        # Encode the entire text to tokens
        tokens = encoder.encode(text)
        
        if len(tokens) <= chunk_size:
            # Text fits in a single chunk
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get chunk_size tokens starting from start
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode tokens back to text
            chunk_text = encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start forward by (chunk_size - overlap)
            # This creates the overlap with the next chunk
            start += chunk_size - chunk_overlap
            
            # Safety check: ensure we make progress
            if start <= 0:
                start = chunk_size
        
        return chunks
    
    @classmethod
    def count_tokens(cls, text: str) -> int:
        """Count the number of tokens in text."""
        encoder = cls._get_encoder()
        return len(encoder.encode(text))
