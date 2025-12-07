"""
Document Converter Module

Provides document format conversion capabilities for AI agents:
1. Convert JIRA attachments to markdown (integrated with JIRA client)
2. Convert local files to markdown (standalone service)
3. MCP tool for AI agents to read various file formats

Supports: PDF, Word, Excel, PowerPoint, images, HTML, and more.
"""

import io
import os
import asyncio
import logging
import functools
from typing import Optional, Union, BinaryIO
from pathlib import Path
from dataclasses import dataclass

from mime_utils import get_mime_detector


# Try to import markitdown with graceful fallback
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ConverterConfig:
    """Configuration for DocumentConverter."""
    max_file_size_mb: int = int(os.getenv('MAX_DOCUMENT_SIZE_MB', '50'))
    timeout_seconds: int = int(os.getenv('DOCUMENT_CONVERSION_TIMEOUT', '30'))
    enable_detailed_logging: bool = os.getenv('DOCUMENT_CONVERTER_DEBUG', '').lower() == 'true'


def async_wrapper(func):
    """
    Decorator to wrap synchronous methods with async executor.
    
    Reduces code duplication for async wrapper methods.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: func(*args, **kwargs)
        )
    return wrapper


class DocumentConverter:
    """
    Converts various document formats to markdown using MarkItDown.
    
    Supports: PDF, Word (.docx), Excel (.xlsx, .xls), PowerPoint (.pptx),
    images, HTML, and more.
    """
    
    def __init__(self, config: ConverterConfig = ConverterConfig()):
        """
        Initialize the document converter.
        
        Args:
            config: Configuration object for converter behavior
        """
        self.config = config
        self.mime_detector = get_mime_detector()
        
        # File size limit in bytes
        self.max_file_size = config.max_file_size_mb * 1024 * 1024
        
        if MARKITDOWN_AVAILABLE:
            self._converter = MarkItDown()
            logger.info("DocumentConverter initialized with MarkItDown support")
        else:
            self._converter = None
            logger.warning("DocumentConverter initialized without MarkItDown (install with: pip install markitdown)")
    
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
        
        return self.mime_detector.is_supported(mime_type)
    
    @async_wrapper
    def convert_to_markdown_async(
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
        return self.convert_to_markdown(file_stream, mime_type, filename)
    
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
            
            if file_size > self.max_file_size:
                error_msg = (
                    f"File too large ({file_size / 1024 / 1024:.1f}MB). "
                    f"Maximum size: {self.max_file_size / 1024 / 1024}MB"
                )
                logger.warning(f"File size limit exceeded for {filename}: {error_msg}")
                result["error"] = error_msg
                result["success"] = False
                return result
            
            # Log conversion start
            if self.config.enable_detailed_logging:
                logger.debug(f"Starting conversion of {filename} ({mime_type}, {file_size} bytes)")
            
            # Perform conversion
            conversion_result = self._converter.convert(file_stream)
            result["markdown"] = conversion_result.text_content
            
            # Add metadata
            result["success"] = True
            result["size_bytes"] = file_size
            
            # Log successful conversion
            logger.info(f"Successfully converted {filename} to markdown ({len(result['markdown'])} chars)")
            
        except ImportError as e:
            error_msg = f"Missing dependency for {mime_type}: {str(e)}"
            logger.error(f"Import error during conversion of {filename}: {e}", exc_info=True)
            result["error"] = error_msg
            result["success"] = False
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            logger.error(f"Unexpected error converting {filename}: {e}", exc_info=True)
            result["error"] = error_msg
            result["success"] = False
        
        return result
    
    @async_wrapper
    def convert_file_async(self, file_path: str) -> dict:
        """
        Async version: Convert a local file to markdown.
        
        Args:
            file_path: Path to the file to convert
        
        Returns:
            Dictionary with conversion result
        """
        return self.convert_file(file_path)
    
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
        mime_type = self.mime_detector.detect_from_extension(path.suffix.lower())
        
        logger.debug(f"Detected MIME type {mime_type} for file {file_path}")
        
        try:
            # Check file size before opening
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                error_msg = (
                    f"File too large ({file_size / 1024 / 1024:.1f}MB). "
                    f"Maximum size: {self.max_file_size / 1024 / 1024}MB"
                )
                logger.warning(f"File size check failed for {file_path}: {error_msg}")
                return {
                    "error": error_msg,
                    "success": False,
                    "filename": path.name
                }
            
            with open(file_path, 'rb') as f:
                return self.convert_to_markdown(f, mime_type, path.name)
        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}"
            logger.error(f"Permission error reading {file_path}: {e}")
            return {
                "error": error_msg,
                "success": False,
                "filename": path.name
            }
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            logger.error(f"File not found: {file_path}")
            return {
                "error": error_msg,
                "success": False,
                "filename": path.name
            }
        except Exception as e:
            error_msg = f"Failed to read file: {str(e)}"
            logger.error(f"Unexpected error reading {file_path}: {e}", exc_info=True)
            return {
                "error": error_msg,
                "success": False,
                "filename": path.name
            }
    

    
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of MIME types supported for conversion
        """
        if not self.is_available():
            return []
        return sorted(self.mime_detector.get_supported_formats())
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of file extensions (e.g., ['.pdf', '.docx'])
        """
        if not self.is_available():
            return []
        
        return self.mime_detector.get_supported_extensions()


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
