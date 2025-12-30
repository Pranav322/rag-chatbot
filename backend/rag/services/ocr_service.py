"""
OCR Service using Tesseract with intelligent signal detection.
"""

from dataclasses import dataclass
from PIL import Image
import pytesseract
import io
from django.conf import settings


@dataclass
class OCRResult:
    """Result from OCR processing with quality signals."""
    text: str
    confidence: float
    text_coverage: float
    box_density: float
    needs_vision: bool


class OCRService:
    """Tesseract OCR with intelligent Vision API triggering."""
    
    MAX_IMAGE_SIZE = 2000  # Max dimension for OCR processing
    
    @classmethod
    def _resize_if_needed(cls, image: Image.Image) -> Image.Image:
        """Resize large images to prevent OCR timeout."""
        width, height = image.size
        if width <= cls.MAX_IMAGE_SIZE and height <= cls.MAX_IMAGE_SIZE:
            return image
        
        # Scale down preserving aspect ratio
        ratio = min(cls.MAX_IMAGE_SIZE / width, cls.MAX_IMAGE_SIZE / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)
    
    @classmethod
    def extract_text_and_signals(cls, image_bytes: bytes) -> OCRResult:
        """Extract text and compute quality signals."""
        image = Image.open(io.BytesIO(image_bytes))
        
        # Resize large images to prevent OCR timeout
        image = cls._resize_if_needed(image)
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image).strip()
        
        # Calculate signals
        confidence = cls._calculate_confidence(ocr_data)
        text_coverage = cls._calculate_text_coverage(ocr_data, image)
        box_density = cls._calculate_box_density(ocr_data, image)
        needs_vision = cls._needs_vision_api(text_coverage, box_density, confidence)
        
        return OCRResult(text, confidence, text_coverage, box_density, needs_vision)
    
    @classmethod
    def _calculate_confidence(cls, ocr_data: dict) -> float:
        """Average OCR confidence from valid detections."""
        confidences = [float(c) for c in ocr_data['conf'] if c != -1]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    @classmethod
    def _calculate_text_coverage(cls, ocr_data: dict, image: Image.Image) -> float:
        """Percentage of image covered by text boxes."""
        image_area = image.width * image.height
        total_text_area = sum(
            ocr_data['width'][i] * ocr_data['height'][i]
            for i in range(len(ocr_data['text']))
            if ocr_data['conf'][i] != -1
        )
        return min(total_text_area / image_area, 1.0) if image_area > 0 else 0.0
    
    @classmethod
    def _calculate_box_density(cls, ocr_data: dict, image: Image.Image) -> float:
        """Density of text boxes in image."""
        valid_boxes = sum(1 for c in ocr_data['conf'] if c != -1)
        image_area = image.width * image.height
        expected_dense = image_area / 10000
        return min(valid_boxes / expected_dense, 1.0) if expected_dense > 0 else 0.0
    
    @classmethod
    def _needs_vision_api(cls, text_coverage: float, box_density: float, confidence: float) -> bool:
        """Determine if Vision API should be triggered based on thresholds."""
        return (
            text_coverage < settings.OCR_TEXT_COVERAGE_THRESHOLD or
            box_density < settings.OCR_BOX_DENSITY_THRESHOLD or
            confidence < settings.OCR_CONFIDENCE_THRESHOLD
        )
