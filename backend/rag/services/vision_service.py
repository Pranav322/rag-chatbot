"""
Vision Service using OpenAI GPT-4o-mini for image understanding.
"""

from rag.services.llm import LLMService


class VisionService:
    """Vision service using OpenAI's multimodal models."""
    
    @classmethod
    async def describe_image(cls, image_url: str) -> str:
        """
        Generate description using Vision API.
        
        Args:
            image_url: Cloudinary URL of image
            
        Returns:
            Text description
        """
        prompt = """Describe this image concisely in 2-3 sentences.
Focus on:
- Main visual elements (charts, diagrams, photos)
- Key information or concepts shown
- Any text visible in the image

Be specific and factual."""
        
        description = await LLMService.complete_with_vision(
            prompt=prompt,
            image_url=image_url,
            model="gpt-4.1-mini",
            max_tokens=150
        )
        
        return description.strip()
