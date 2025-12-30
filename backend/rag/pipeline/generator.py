"""
Answer Generator.

Generates answers using LLM with optional context from retrieved documents.
Handles the logic of when to use context vs general knowledge.
"""

from dataclasses import dataclass

from rag.services.llm import LLMService
from rag.prompts.rag import get_rag_system_prompt, format_rag_user_message
from rag.pipeline.retriever import RetrievedChunk, Retriever


@dataclass
class SourceSnippet:
    """Source information for a retrieved chunk."""
    asset_id: str
    excerpt: str


@dataclass
class GeneratedAnswer:
    """The generated answer with metadata."""
    answer: str
    used_context: bool
    sources: list[SourceSnippet] | None = None


class Generator:
    """
    Generates answers using the RAG prompt template.
    
    Decides whether to include context based on retrieval results
    and query type.
    """
    
    @classmethod
    async def generate(
        cls,
        question: str,
        chunks: list[RetrievedChunk] | None = None
    ) -> GeneratedAnswer:
        """
        Generate an answer to the user's question.
        
        Args:
            question: The user's question
            chunks: Retrieved document chunks, or None for general-only answers
            
        Returns:
            GeneratedAnswer with the response and context usage flag
        """
        # Determine if we should use context
        use_context = chunks is not None and Retriever.has_relevant_context(chunks)
        
        # Format context if available
        context = None
        if use_context:
            context = Retriever.format_context(chunks)
        
        # Build the prompt
        system_prompt = get_rag_system_prompt()
        user_message = format_rag_user_message(question, context)
        
        # Generate the answer
        answer = await LLMService.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,  # Some creativity for helpful responses
            max_tokens=1024
        )
        
        # Extract source snippets if context was used
        sources = None
        if use_context and chunks:
            sources = [
                SourceSnippet(
                    asset_id=str(chunk.asset_id) if chunk.asset_id else "unknown",
                    excerpt=chunk.content[:100]  # First 100 chars as excerpt
                )
                for chunk in chunks[:3]  # Top 3 sources
            ]
        
        return GeneratedAnswer(
            answer=answer.strip(),
            used_context=use_context,
            sources=sources
        )
    
    @classmethod
    async def stream_generate(
        cls,
        question: str,
        chunks: list[RetrievedChunk] | None = None
    ):
        """
        Stream-generate an answer token by token.
        
        Args:
            question: The user's question
            chunks: Retrieved document chunks
            
        Yields:
            Tokens as they are generated, then final metadata
        """
        # Determine if we should use context
        use_context = chunks is not None and Retriever.has_relevant_context(chunks)
        
        # Format context if available
        context = None
        if use_context:
            context = Retriever.format_context(chunks)
        
        # Build the prompt
        system_prompt = get_rag_system_prompt()
        user_message = format_rag_user_message(question, context)
        
        # Stream the answer
        async for token in LLMService.stream_complete(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
            max_tokens=1024
        ):
            yield {"type": "token", "content": token}
        
        # Extract source snippets
        sources = None
        if use_context and chunks:
            sources = [
                {"asset_id": str(chunk.asset_id) if chunk.asset_id else "unknown", "excerpt": chunk.content[:100]}
                for chunk in chunks[:3]
            ]
        
        # Yield final metadata
        yield {"type": "done", "used_context": use_context, "sources": sources}
