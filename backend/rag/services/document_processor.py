"""
Document Processor Service.

Handles text extraction from PDF and DOCX files.
Validates file types and handles corrupted/unreadable files gracefully.
"""

from io import BytesIO
from typing import Tuple


# Supported file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}


class DocumentProcessorError(Exception):
    """Raised when document processing fails."""
    pass


class DocumentProcessor:
    """
    Extracts text content from uploaded documents.
    
    Supports PDF and DOCX formats. Returns extracted text along with
    the detected document type for metadata storage.
    """
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract lowercase file extension without the dot."""
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[1].lower()
    
    @staticmethod
    def is_supported(filename: str) -> bool:
        """Check if the file type is supported."""
        ext = DocumentProcessor.get_file_extension(filename)
        return ext in ALLOWED_EXTENSIONS
    
    @classmethod
    def extract_text(cls, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        Extract text from a document file.
        
        Args:
            file_content: The raw bytes of the uploaded file
            filename: Original filename to determine file type
            
        Returns:
            Tuple of (extracted_text, doc_type)
            
        Raises:
            DocumentProcessorError: If file type unsupported or extraction fails
        """
        ext = cls.get_file_extension(filename)
        
        if ext not in ALLOWED_EXTENSIONS:
            raise DocumentProcessorError(
                f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        try:
            if ext == 'pdf':
                text = cls._extract_pdf(file_content)
            else:  # docx
                text = cls._extract_docx(file_content)
            
            # Clean up extracted text
            text = cls._clean_text(text)
            
            if not text.strip():
                raise DocumentProcessorError("No text content found in document")
            
            return text, ext
            
        except DocumentProcessorError:
            raise
        except Exception as e:
            raise DocumentProcessorError(f"Failed to extract text: {str(e)}")
    
    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        """Extract text from PDF using pypdf."""
        from pypdf import PdfReader
        
        reader = PdfReader(BytesIO(content))
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return '\n\n'.join(text_parts)
    
    @staticmethod
    def _extract_docx(content: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        from docx import Document
        
        doc = Document(BytesIO(content))
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return '\n\n'.join(text_parts)
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        # Replace multiple newlines with double newline
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)
