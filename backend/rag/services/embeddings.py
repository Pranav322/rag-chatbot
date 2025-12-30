"""
Local Embeddings Service using sentence-transformers.

Uses all-MiniLM-L6-v2 model (384 dimensions) - free and runs locally.
"""

from typing import List
from functools import lru_cache


# Model produces 384-dimensional embeddings
EMBEDDING_DIMENSIONS = 384
MODEL_NAME = 'all-MiniLM-L6-v2'


@lru_cache(maxsize=1)
def _get_model():
    """
    Lazy load the sentence transformer model.
    Cached to avoid reloading on every request.
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


class EmbeddingsService:
    """
    Service for generating text embeddings using local sentence-transformers.
    
    Uses all-MiniLM-L6-v2 which produces 384-dimensional vectors.
    Runs entirely locally - no API calls needed.
    """
    
    @classmethod
    async def generate_embedding(cls, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector (384 dimensions)
        """
        model = _get_model()
        # sentence-transformers is sync, but fast enough for single texts
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    @classmethod
    async def generate_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch.
        
        Sentence-transformers handles batching internally for efficiency.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors in the same order as input texts
        """
        model = _get_model()
        # Batch encode is very efficient
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]
