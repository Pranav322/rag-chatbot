"""
Image Processor combining OCR and Vision services.

Handles image ingestion with intelligent Vision API triggering.
"""

from typing import Tuple
from asgiref.sync import sync_to_async
from rag.services.ocr_service import OCRService
from rag.services.vision_service import VisionService


class ImageProcessor:
    """
    Processes images for RAG using OCR + conditional Vision.
    
    Flow:
    1. Run Tesseract OCR
    2. Analyze quality signals
    3. If poor signals, call Vision API
    4. Merge OCR text + Vision description
    """
    
    @classmethod
    async def process_image(cls, image_bytes: bytes, cloudinary_url: str) -> str:
        """
        Process image and extract searchable text.
        
        Args:
            image_bytes: Raw image bytes
            cloudinary_url: Cloudinary URL for Vision API
            
        Returns:
            Combined text (OCR + optional Vision description)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[ImageProcessor] Starting OCR for image ({len(image_bytes)} bytes)")
        
        # Run OCR with signal detection (CPU-intensive, wrap in sync_to_async)
        ocr_result = await sync_to_async(
            OCRService.extract_text_and_signals
        )(image_bytes)
        
        logger.info(f"[ImageProcessor] OCR complete - confidence: {ocr_result.confidence:.1f}, needs_vision: {ocr_result.needs_vision}")
        
        # Start with OCR text
        final_text = ocr_result.text
        
        # If signals indicate complex visual content, use Vision API
        if ocr_result.needs_vision:
            logger.info("[ImageProcessor] Calling Vision API...")
            vision_description = await VisionService.describe_image(cloudinary_url)
            logger.info(f"[ImageProcessor] Vision API returned: {len(vision_description)} chars")
            
            # Merge: Vision description first, then OCR text
            if vision_description:
                final_text = f"{vision_description}\n\n{ocr_result.text}".strip()
        
        logger.info(f"[ImageProcessor] Final text: {len(final_text)} chars")
        return final_text
    
    @classmethod
    def is_supported_image(cls, filename: str) -> bool:
        """Check if file is a supported image format."""
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in ('png', 'jpg', 'jpeg', 'gif', 'webp')
