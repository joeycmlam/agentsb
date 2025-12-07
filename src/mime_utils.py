"""
MIME Type Detection and Validation Module

Provides centralized MIME type handling for document conversion.
"""

import mimetypes
from typing import Set, Optional


class MimeTypeDetector:
    """
    Handles MIME type detection and validation for document conversion.
    """
    
    # Explicitly supported MIME types
    SUPPORTED_MIME_TYPES: Set[str] = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'application/vnd.ms-powerpoint',  # .ppt
        'text/html',
        'text/csv',
        'text/plain',
        'text/markdown',
        'application/json',
        'application/xml',
        'text/xml',
        'image/jpeg',
        'image/png',
        'image/bmp',
        'image/tiff',
        'audio/wav',
        'audio/mpeg',  # .mp3
        'application/zip',
        'application/epub+zip',
    }
    
    # Supported wildcard types (base types)
    SUPPORTED_BASE_TYPES: Set[str] = {
        'text',  # text/*
        'image'  # image/*
    }
    
    def __init__(self):
        """Initialize MIME type detection with system database."""
        mimetypes.init()
    
    def detect_from_extension(self, file_extension: str) -> str:
        """
        Detect MIME type from file extension using system database.
        
        Args:
            file_extension: File extension (e.g., '.pdf', '.docx')
        
        Returns:
            MIME type string
        """
        # Use system mimetypes database as primary source
        mime_type = mimetypes.guess_type(f"dummy{file_extension}")[0]
        
        if mime_type:
            return mime_type
        
        # Fallback to custom mappings for newer formats
        custom_mappings = {
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        
        return custom_mappings.get(file_extension.lower(), 'application/octet-stream')
    
    def is_supported(self, mime_type: str) -> bool:
        """
        Check if the MIME type is supported for conversion.
        
        Args:
            mime_type: MIME type to check (e.g., 'application/pdf')
        
        Returns:
            True if supported, False otherwise
        """
        # Check exact match
        if mime_type in self.SUPPORTED_MIME_TYPES:
            return True
        
        # Check base type (e.g., 'text/plain' -> 'text')
        base_type = mime_type.split('/')[0]
        return base_type in self.SUPPORTED_BASE_TYPES
    
    def get_supported_formats(self) -> Set[str]:
        """
        Get all supported MIME types.
        
        Returns:
            Set of supported MIME type strings
        """
        return self.SUPPORTED_MIME_TYPES.copy()
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of file extensions (e.g., ['.pdf', '.docx'])
        """
        extensions = []
        
        # Get extensions from mimetypes database for supported types
        for mime_type in self.SUPPORTED_MIME_TYPES:
            exts = mimetypes.guess_all_extensions(mime_type)
            extensions.extend(exts)
        
        # Add common extensions not in mimetypes database
        additional_extensions = ['.docx', '.xlsx', '.pptx']
        extensions.extend(additional_extensions)
        
        return sorted(list(set(extensions)))


# Global singleton instance
_detector_instance: Optional[MimeTypeDetector] = None


def get_mime_detector() -> MimeTypeDetector:
    """
    Get the global MimeTypeDetector instance (singleton pattern).
    
    Returns:
        MimeTypeDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = MimeTypeDetector()
    return _detector_instance