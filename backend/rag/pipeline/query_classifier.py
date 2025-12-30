"""
Query Classifier.

Classifies user queries to determine if document retrieval is needed.
Uses a single LLM call with JSON output for efficiency.
"""

from enum import Enum
from typing import Literal

from rag.services.llm import LLMService
from rag.prompts.classifier import get_classifier_prompt


class QueryType(str, Enum):
    """Query classification types."""
    GENERAL = "GENERAL"
    PROFILE_DEPENDENT = "PROFILE_DEPENDENT"
    HYBRID = "HYBRID"


# Type alias for the query type literals
QueryTypeLiteral = Literal["GENERAL", "PROFILE_DEPENDENT", "HYBRID"]


class QueryClassifier:
    """
    Classifies queries into GENERAL, PROFILE_DEPENDENT, or HYBRID.
    
    Uses a small LLM call to analyze the query intent and determine
    whether document retrieval is needed.
    """
    
    @classmethod
    async def classify(cls, query: str) -> QueryType:
        """
        Classify a user query.
        
        Args:
            query: The user's question/message
            
        Returns:
            QueryType enum value indicating classification
        """
        system_prompt = get_classifier_prompt()
        
        # Use JSON mode for structured output
        response = await LLMService.complete_json(
            system_prompt=system_prompt,
            user_message=query,
            temperature=0.0,  # Deterministic classification
            max_tokens=50  # Very short response needed
        )
        
        # Extract query type from response
        raw_type = response.get("query_type", "GENERAL")
        
        # Validate and map to enum (default to GENERAL if invalid)
        try:
            return QueryType(raw_type)
        except ValueError:
            # If LLM returns unexpected value, default to GENERAL
            # This is safer as it won't expose potentially irrelevant docs
            return QueryType.GENERAL
    
    @classmethod
    def needs_retrieval(cls, query_type: QueryType) -> bool:
        """
        Determine if retrieval is needed based on query type.
        
        Args:
            query_type: The classified query type
            
        Returns:
            True if vector search should be performed
        """
        # Only skip retrieval for purely general questions
        return query_type != QueryType.GENERAL
