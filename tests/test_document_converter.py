"""
Unit tests for DocumentConverter class.

Tests the core functionality of document conversion with proper error handling.
"""

import pytest
import io
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules to test
from src.document_converter import DocumentConverter, ConverterConfig, get_converter
from src.mime_utils import MimeTypeDetector


class TestDocumentConverter:
    """Test cases for DocumentConverter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConverterConfig(max_file_size_mb=1)  # Small size for testing
        self.converter = DocumentConverter(self.config)
    
    def test_initialization_with_markitdown_available(self):
        """Test converter initialization when markitdown is available."""
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', True):
            converter = DocumentConverter()
            assert converter.is_available() == True
    
    def test_initialization_without_markitdown(self):
        """Test converter initialization when markitdown is not available."""
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', False):
            converter = DocumentConverter()
            assert converter.is_available() == False
    
    def test_config_from_environment(self):
        """Test configuration loading from environment variables."""
        with patch.dict(os.environ, {
            'MAX_DOCUMENT_SIZE_MB': '100',
            'DOCUMENT_CONVERSION_TIMEOUT': '60',
            'DOCUMENT_CONVERTER_DEBUG': 'true'
        }):
            config = ConverterConfig()
            assert config.max_file_size_mb == 100
            assert config.timeout_seconds == 60
            assert config.enable_detailed_logging == True
    
    def test_is_supported_mime_type(self):
        """Test MIME type support checking."""
        # Mock the mime detector
        mock_detector = Mock()
        mock_detector.is_supported.return_value = True
        self.converter.mime_detector = mock_detector
        
        # Test when markitdown is available
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', True):
            assert self.converter.is_supported('application/pdf') == True
            mock_detector.is_supported.assert_called_with('application/pdf')
        
        # Test when markitdown is not available
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', False):
            assert self.converter.is_supported('application/pdf') == False
    
    def test_convert_to_markdown_file_too_large(self):
        """Test file size limit enforcement."""
        # Create a large file content (larger than 1MB limit)
        large_content = b'x' * (2 * 1024 * 1024)  # 2MB
        file_stream = io.BytesIO(large_content)
        
        result = self.converter.convert_to_markdown(
            file_stream, 
            'application/pdf', 
            'test.pdf'
        )
        
        assert result['success'] == False
        assert 'too large' in result['error']
        assert result['filename'] == 'test.pdf'
    
    def test_convert_to_markdown_unsupported_type(self):
        """Test handling of unsupported MIME types."""
        # Mock mime detector to return False for unsupported type
        mock_detector = Mock()
        mock_detector.is_supported.return_value = False
        self.converter.mime_detector = mock_detector
        
        file_stream = io.BytesIO(b'test content')
        
        result = self.converter.convert_to_markdown(
            file_stream,
            'application/unsupported',
            'test.unknown'
        )
        
        assert result['success'] == False
        assert 'Unsupported file type' in result['error']
    
    def test_convert_to_markdown_markitdown_unavailable(self):
        """Test behavior when markitdown is not available."""
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', False):
            converter = DocumentConverter()
            file_stream = io.BytesIO(b'test content')
            
            result = converter.convert_to_markdown(
                file_stream,
                'application/pdf',
                'test.pdf'
            )
            
            assert result['success'] == False
            assert 'not available' in result['error']
    
    @patch('src.document_converter.MARKITDOWN_AVAILABLE', True)
    def test_convert_to_markdown_success(self):
        """Test successful conversion to markdown."""
        # Mock the MarkItDown converter
        mock_converter = Mock()
        mock_result = Mock()
        mock_result.text_content = '# Test Document\\n\\nThis is a test.'
        mock_converter.convert.return_value = mock_result
        
        # Mock mime detector
        mock_detector = Mock()
        mock_detector.is_supported.return_value = True
        
        converter = DocumentConverter()
        converter._converter = mock_converter
        converter.mime_detector = mock_detector
        
        file_stream = io.BytesIO(b'test content')
        
        result = converter.convert_to_markdown(
            file_stream,
            'application/pdf',
            'test.pdf'
        )
        
        assert result['success'] == True
        assert result['markdown'] == '# Test Document\\n\\nThis is a test.'
        assert result['filename'] == 'test.pdf'
        assert 'size_bytes' in result
    
    def test_convert_file_not_exists(self):
        """Test handling of non-existent files."""
        result = self.converter.convert_file('/path/to/nonexistent/file.pdf')
        
        assert result['success'] == False
        assert 'does not exist' in result['error']
    
    def test_convert_file_is_directory(self):
        """Test handling when path points to a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.converter.convert_file(tmpdir)
            
            assert result['success'] == False
            assert 'not a file' in result['error']
    
    def test_convert_file_success(self):
        """Test successful file conversion."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'Hello, World!')
            tmp_path = tmp.name
        
        try:
            # Mock the conversion method
            with patch.object(self.converter, 'convert_to_markdown') as mock_convert:
                mock_convert.return_value = {
                    'success': True,
                    'markdown': '# Hello, World!',
                    'filename': Path(tmp_path).name
                }
                
                result = self.converter.convert_file(tmp_path)
                
                assert result['success'] == True
                assert result['markdown'] == '# Hello, World!'
        finally:
            os.unlink(tmp_path)
    
    def test_convert_file_permission_denied(self):
        """Test handling of permission errors."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Remove read permission
            os.chmod(tmp_path, 0o000)
            
            result = self.converter.convert_file(tmp_path)
            
            assert result['success'] == False
            assert 'Permission denied' in result['error']
        finally:
            # Restore permission and cleanup
            os.chmod(tmp_path, 0o644)
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_convert_file_async(self):
        """Test async file conversion wrapper."""
        with patch.object(self.converter, 'convert_file') as mock_convert:
            mock_convert.return_value = {'success': True, 'markdown': 'test'}
            
            result = await self.converter.convert_file_async('/path/to/file.pdf')
            
            assert result == {'success': True, 'markdown': 'test'}
            mock_convert.assert_called_once_with('/path/to/file.pdf')
    
    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        mock_detector = Mock()
        mock_detector.get_supported_formats.return_value = {'application/pdf', 'text/plain'}
        self.converter.mime_detector = mock_detector
        
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', True):
            formats = self.converter.get_supported_formats()
            assert isinstance(formats, list)
            assert 'application/pdf' in formats
    
    def test_get_supported_formats_unavailable(self):
        """Test getting formats when markitdown is unavailable."""
        with patch('src.document_converter.MARKITDOWN_AVAILABLE', False):
            converter = DocumentConverter()
            formats = converter.get_supported_formats()
            assert formats == []
    
    def test_singleton_pattern(self):
        """Test that get_converter returns the same instance."""
        converter1 = get_converter()
        converter2 = get_converter()
        assert converter1 is converter2


class TestMimeTypeDetector:
    """Test cases for MimeTypeDetector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = MimeTypeDetector()
    
    def test_detect_from_extension_pdf(self):
        """Test MIME type detection for PDF files."""
        mime_type = self.detector.detect_from_extension('.pdf')
        assert mime_type == 'application/pdf'
    
    def test_detect_from_extension_docx(self):
        """Test MIME type detection for DOCX files."""
        mime_type = self.detector.detect_from_extension('.docx')
        assert mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    def test_detect_from_extension_unknown(self):
        """Test MIME type detection for unknown extensions."""
        mime_type = self.detector.detect_from_extension('.unknown')
        assert mime_type == 'application/octet-stream'
    
    def test_is_supported_exact_match(self):
        """Test MIME type support for exact matches."""
        assert self.detector.is_supported('application/pdf') == True
        assert self.detector.is_supported('text/plain') == True
    
    def test_is_supported_base_type(self):
        """Test MIME type support for base types."""
        assert self.detector.is_supported('text/custom') == True
        assert self.detector.is_supported('image/custom') == True
        assert self.detector.is_supported('video/mp4') == False
    
    def test_get_supported_formats(self):
        """Test getting supported format set."""
        formats = self.detector.get_supported_formats()
        assert isinstance(formats, set)
        assert 'application/pdf' in formats
        assert len(formats) > 0
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions list."""
        extensions = self.detector.get_supported_extensions()
        assert isinstance(extensions, list)
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert len(extensions) > 0


class TestSecurityValidation:
    """Test cases for security-related functionality."""
    
    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts."""
        dangerous_paths = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32',
            '/../../sensitive_file',
            'normal_file/../../../etc/passwd'
        ]
        
        for path in dangerous_paths:
            normalized = os.path.normpath(path)
            # The security check should catch paths starting with '..'
            assert normalized.startswith('..'), f\"Path {path} should be flagged as dangerous\"
    
    def test_safe_path_validation(self):
        """Test that safe paths pass validation."""
        safe_paths = [
            'document.pdf',
            'folder/document.pdf',
            './document.pdf',
            'data/files/document.pdf'
        ]
        
        for path in safe_paths:
            normalized = os.path.normpath(path)
            # These should not start with '..' after normalization
            assert not normalized.startswith('..'), f\"Path {path} should be considered safe\"


if __name__ == '__main__':
    pytest.main([__file__])