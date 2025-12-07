"""
Document Converter Module

Provides document format conversion capabilities for AI agents:
1. Convert JIRA attachments to markdown (integrated with JIRA client)
2. Convert local files to markdown (standalone service)
3. MCP tool for AI agents to read various file formats

Supports: PDF, Word, Excel, PowerPoint, images, HTML, and more.
"""

import io
import asyncio
from typing import Optional, Union, BinaryIO
from pathlib import Path


# Try to import markitdown with graceful fallback
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False


class DocumentConverter:
    """
    Converts various document formats to markdown using MarkItDown.
    
    Supports: PDF, Word (.docx), Excel (.xlsx, .xls), PowerPoint (.pptx),
    images, HTML, and more.
    """
    
    # MIME types supported by markitdown
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'application/vnd.ms-powerpoint',  # .ppt
        'text/html',
        'text/csv',
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
    
    # File size limit (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self):
        """Initialize the document converter."""
        if MARKITDOWN_AVAILABLE:
            self._converter = MarkItDown()
        else:
            self._converter = None
    
    def is_available(self) -> bool:
        """Check if markitdown is available."""
        return MARKITDOWN_AVAILABLE
    
    def is_supported(self, mime_type: str) -> bool:
        """
        Check if the given MIME type is supported for conversion.
        
        Args:
            mime_type: MIME type of the file (e.g., 'application/pdf')
        
        Returns:
            True if supported, False otherwise
        """
        if not self.is_available():
            return False
        
        # Check exact match or base type (e.g., 'text/*')
        return mime_type in self.SUPPORTED_MIME_TYPES or \
               mime_type.split('/')[0] in ['text', 'image']
    
    async def convert_to_markdown_async(
        self,
        file_stream: Union[BinaryIO, bytes],
        mime_type: str,
        filename: Optional[str] = None
    ) -> dict:
        """
        Async version: Convert a document to markdown format.
        
        Args:
            file_stream: Binary file stream or bytes content
            mime_type: MIME type of the file
            filename: Optional filename for context
        
        Returns:
            Dictionary with:
                - markdown: Converted markdown text (if successful)
                - error: Error message (if failed)
                - mime_type: Original MIME type
                - filename: Original filename (if provided)
                - success: Boolean indicating conversion success
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.convert_to_markdown(file_stream, mime_type, filename)
        )
    
    def convert_to_markdown(
        self,
        file_stream: Union[BinaryIO, bytes],
        mime_type: str,
        filename: Optional[str] = None
    ) -> dict:
        """
        Convert a document to markdown format.
        
        Args:
            file_stream: Binary file stream or bytes content
            mime_type: MIME type of the file
            filename: Optional filename for context
        
        Returns:
            Dictionary with:
                - markdown: Converted markdown text (if successful)
                - error: Error message (if failed)
                - mime_type: Original MIME type
                - filename: Original filename (if provided)
                - success: Boolean indicating conversion success
        """
        result = {
            "mime_type": mime_type,
            "filename": filename or "unknown"
        }
        
        # Check if markitdown is available
        if not self.is_available():
            result["error"] = (
                "Document conversion not available. "
                "Install with: pip install markitdown"
            )
            result["success"] = False
            return result
        
        # Check if MIME type is supported
        if not self.is_supported(mime_type):
            result["error"] = f"Unsupported file type: {mime_type}"
            result["success"] = False
            return result
        
        try:
            # Convert bytes to BytesIO if needed
            if isinstance(file_stream, bytes):
                file_stream = io.BytesIO(file_stream)
            
            # Check file size
            current_pos = file_stream.tell()
            file_stream.seek(0, io.SEEK_END)
            file_size = file_stream.tell()
            file_stream.seek(current_pos)
            
            if file_size > self.MAX_FILE_SIZE:
                result["error"] = (
                    f"File too large ({file_size / 1024 / 1024:.1f}MB). "
                    f"Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB"
                )
                result["success"] = False
                return result
            
            # Perform conversion
            conversion_result = self._converter.convert(file_stream)
            result["markdown"] = conversion_result.text_content
            
            # Add metadata
            result["success"] = True
            result["size_bytes"] = file_size
            
        except Exception as e:
            result["error"] = f"Conversion failed: {str(e)}"
            result["success"] = False
        
        return result
    
    async def convert_file_async(self, file_path: str) -> dict:
        """
        Async version: Convert a local file to markdown.
        
        Args:
            file_path: Path to the file to convert
        
        Returns:
            Dictionary with conversion result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.convert_file(file_path)
        )
    
    def convert_file(self, file_path: str) -> dict:
        """
        Convert a local file to markdown.
        
        Args:
            file_path: Path to the file to convert
        
        Returns:
            Dictionary with conversion result
        """
        path = Path(file_path)
        
        # Validate file
        if not path.exists():
            return {
                "error": f"File does not exist: {file_path}",
                "success": False,
                "filename": path.name
            }
        
        if not path.is_file():
            return {
                "error": f"Path is not a file: {file_path}",
                "success": False,
                "filename": path.name
            }
        
        # Detect MIME type from extension
        mime_type = self._detect_mime_type(path.suffix.lower())
        
        try:
            with open(file_path, 'rb') as f:
                return self.convert_to_markdown(f, mime_type, path.name)
        except Exception as e:
            return {
                "error": f"Failed to read file: {str(e)}",
                "success": False,
                "filename": path.name
            }
    
    def _detect_mime_type(self, extension: str) -> str:
        """
        Detect MIME type from file extension.
        
        Args:
            extension: File extension (e.g., '.pdf', '.docx')
        
        Returns:
            MIME type string
        """
        mime_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.zip': 'application/zip',
            '.epub': 'application/epub+zip',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
        }
        
        return mime_map.get(extension, 'application/octet-stream')
    
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of MIME types supported for conversion
        """
        if not self.is_available():
            return []
        return sorted(self.SUPPORTED_MIME_TYPES)
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of file extensions (e.g., ['.pdf', '.docx'])
        """
        if not self.is_available():
            return []
        
        return [
            '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
            '.html', '.htm', '.csv', '.json', '.xml',
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
            '.wav', '.mp3', '.zip', '.epub', '.txt', '.md'
        ]


# Global singleton instance
_converter_instance: Optional[DocumentConverter] = None


def get_converter() -> DocumentConverter:
    """
    Get the global DocumentConverter instance (singleton pattern).
    
    Returns:
        DocumentConverter instance
    """
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = DocumentConverter()
    return _converter_instance


def convert_to_markdown(
    file_stream: Union[BinaryIO, bytes],
    mime_type: str,
    filename: Optional[str] = None
) -> dict:
    """
    Convenience function to convert a document to markdown.
    
    Args:
        file_stream: Binary file stream or bytes content
        mime_type: MIME type of the file
        filename: Optional filename for context
    
    Returns:
        Dictionary with conversion result
    """
    converter = get_converter()
    return converter.convert_to_markdown(file_stream, mime_type, filename)


async def convert_to_markdown_async(
    file_stream: Union[BinaryIO, bytes],
    mime_type: str,
    filename: Optional[str] = None
) -> dict:
    """
    Async convenience function to convert a document to markdown.
    
    Args:
        file_stream: Binary file stream or bytes content
        mime_type: MIME type of the file
        filename: Optional filename for context
    
    Returns:
        Dictionary with conversion result
    """
    converter = get_converter()
    return await converter.convert_to_markdown_async(file_stream, mime_type, filename)


def convert_file(file_path: str) -> dict:
    """
    Convenience function to convert a local file to markdown.
    
    Args:
        file_path: Path to the file to convert
    
    Returns:
        Dictionary with conversion result
    """
    converter = get_converter()
    return converter.convert_file(file_path)


async def convert_file_async(file_path: str) -> dict:
    """
    Async convenience function to convert a local file to markdown.
    
    Args:
        file_path: Path to the file to convert
    
    Returns:
        Dictionary with conversion result
    """
    converter = get_converter()
    return await converter.convert_file_async(file_path)
