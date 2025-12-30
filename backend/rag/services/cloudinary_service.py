"""
Cloudinary Service for file storage.

Handles uploading and deleting files from Cloudinary.
Never stores raw files locally.
"""

import cloudinary
import cloudinary.uploader
from django.conf import settings
from typing import Tuple


# Configure Cloudinary on module load
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class CloudinaryService:
    """
    Service for uploading and managing files on Cloudinary.
    
    Why Cloudinary?
    - Free tier: 25GB storage, 25GB bandwidth/month
    - Automatic format optimization
    - Built-in CDN
    - Easy Python SDK
    """
    
    @classmethod
    def upload(
        cls,
        file_bytes: bytes,
        filename: str,
        folder: str = "rag_uploads",
        resource_type: str = "auto"
    ) -> Tuple[str, str]:
        """
        Upload a file to Cloudinary.
        
        Args:
            file_bytes: Raw file content
            filename: Original filename for metadata
            folder: Cloudinary folder to organize files
            resource_type: "auto", "image", or "raw" (for PDFs/docs)
            
        Returns:
            Tuple of (url, public_id) for storage and deletion
        """
        # Determine resource type based on file extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        # PDFs and documents need resource_type="raw"
        if ext in ('pdf', 'docx', 'doc', 'txt'):
            resource_type = 'raw'
        elif ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
            resource_type = 'image'
        
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            resource_type=resource_type,
            public_id=filename.rsplit('.', 1)[0] if '.' in filename else filename,
            use_filename=True,
            unique_filename=True,
        )
        
        return result['secure_url'], result['public_id']
    
    @classmethod
    def delete(cls, public_id: str, resource_type: str = "auto") -> bool:
        """
        Delete a file from Cloudinary.
        
        Args:
            public_id: The Cloudinary public ID
            resource_type: Must match the upload resource_type
            
        Returns:
            True if deletion was successful
        """
        try:
            # Try as raw first (for documents)
            result = cloudinary.uploader.destroy(public_id, resource_type='raw')
            if result.get('result') == 'ok':
                return True
            
            # Try as image
            result = cloudinary.uploader.destroy(public_id, resource_type='image')
            return result.get('result') == 'ok'
        except Exception:
            return False
