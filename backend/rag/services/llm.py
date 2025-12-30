"""
Pluggable LLM Service.

Provides a unified interface for LLM completions using OpenAI's API.
Supports both regular chat completions and JSON mode for structured outputs.
"""

import os
from typing import Any
import httpx
from openai import AsyncOpenAI


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DEFAULT_MODEL = os.getenv('OPENAI_LLM_MODEL', 'gpt-4.1-mini')
# Temperature for creative vs deterministic outputs
DEFAULT_TEMPERATURE = 0.7
# Lower temperature for classification tasks
CLASSIFICATION_TEMPERATURE = 0.0


class LLMService:
    """
    Async service for LLM chat completions.
    
    Supports regular text completions and JSON mode for structured outputs.
    Uses gpt-4.1-mini by default for cost efficiency.
    """
    
    _client: AsyncOpenAI | None = None
    
    @classmethod
    def _get_client(cls) -> AsyncOpenAI:
        """Get or create the OpenAI async client."""
        if cls._client is None:
            cls._client = AsyncOpenAI(
                api_key=OPENAI_API_KEY,
                http_client=httpx.AsyncClient(timeout=120.0)
            )
        return cls._client
    
    @classmethod
    async def complete(
        cls,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            system_prompt: The system instructions
            user_message: The user's message
            model: Override the default model
            temperature: Override the default temperature (0.0-1.0)
            max_tokens: Maximum tokens in the response
            
        Returns:
            The assistant's response text
        """
        client = cls._get_client()
        response = await client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""
    
    @classmethod
    async def complete_json(
        cls,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 1024
    ) -> dict[str, Any]:
        """
        Generate a chat completion with JSON output.
        
        Uses OpenAI's JSON mode to ensure valid JSON output.
        Useful for classification and structured extraction tasks.
        
        Args:
            system_prompt: The system instructions (should mention JSON output)
            user_message: The user's message
            model: Override the default model
            temperature: Override the default temperature
            max_tokens: Maximum tokens in the response
            
        Returns:
            Parsed JSON response as a dictionary
        """
        import json
        
        client = cls._get_client()
        response = await client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature if temperature is not None else CLASSIFICATION_TEMPERATURE,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    
    @classmethod
    async def complete_with_vision(
        cls,
        prompt: str,
        image_url: str,
        model: str = "gpt-4.1-mini",
        max_tokens: int = 300
    ) -> str:
        """
        Generate completion with vision (image input).
        
        Args:
            prompt: Text prompt/question about the image
            image_url: URL of the image (must be accessible)
            model: Model with vision support (gpt-4.1-mini, gpt-4o, etc.)
            max_tokens: Maximum tokens in response
            
        Returns:
            Text description/analysis of the image
        """
        client = cls._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""
    
    @classmethod
    async def stream_complete(
        cls,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 2048
    ):
        """
        Stream a chat completion token by token.
        
        Args:
            system_prompt: The system instructions
            user_message: The user's message
            model: Override the default model
            temperature: Override the default temperature
            max_tokens: Maximum tokens in the response
            
        Yields:
            String tokens as they are generated
        """
        client = cls._get_client()
        stream = await client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
