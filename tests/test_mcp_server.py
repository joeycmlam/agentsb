"""
Unit tests for MCP Server functionality.

Tests the security validation and error handling in the MCP server.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Import the modules to test
from src.mcp_server import JiraMcpServer


class TestMcpServerSecurity:
    """Test cases for MCP server security features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = JiraMcpServer()
    
    @pytest.mark.asyncio
    async def test_read_file_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        dangerous_paths = [
            '../../../etc/passwd',
            '..\\\\..\\\\windows\\\\system32\\\\config',
            '/../../sensitive_file.txt',
            'document/../../../etc/passwd'
        ]
        
        for path in dangerous_paths:
            result = await self.server._tool_read_file({'file_path': path})
            
            assert result['success'] == False
            assert 'path traversal' in result['error'].lower() or 'parent directory' in result['error'].lower()
            assert result['file_path'] == path
    
    @pytest.mark.asyncio
    async def test_read_file_absolute_path_restricted(self):
        """Test that absolute paths outside allowed directories are blocked."""
        restricted_paths = [
            '/etc/passwd',
            '/root/sensitive.txt',
            '/usr/bin/executable',
            'C:\\\\Windows\\\\System32\\\\config'
        ]
        
        for path in restricted_paths:
            result = await self.server._tool_read_file({'file_path': path})
            
            assert result['success'] == False
            assert 'absolute' in result['error'].lower() or 'outside allowed' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_read_file_directory_rejected(self):
        """Test that directories are rejected as input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.server._tool_read_file({'file_path': tmpdir})
            
            assert result['success'] == False
            assert 'not a regular file' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_read_file_safe_path_allowed(self):
        """Test that safe relative paths are allowed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write('Hello, World!')
            tmp_path = tmp.name
        
        try:
            # Create a relative path in current directory
            relative_path = os.path.basename(tmp_path)
            
            # Mock the document converter to avoid actual conversion
            mock_result = {
                'success': True,
                'markdown': '# Hello, World!',
                'filename': relative_path
            }
            
            with patch.object(self.server.doc_converter, 'convert_file_async', return_value=mock_result):
                result = await self.server._tool_read_file({'file_path': relative_path})
                
                # The path should be processed (even if file doesn't exist at relative location)
                # The important thing is that it wasn't blocked by security checks
                assert 'path traversal' not in str(result)
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_read_file_exception_handling(self):
        """Test that exceptions in read_file are properly handled and logged."""
        # Mock the converter to raise an exception
        with patch.object(self.server.doc_converter, 'convert_file_async', side_effect=Exception(\"Test error\")):
            result = await self.server._tool_read_file({'file_path': 'test.txt'})
            
            assert result['success'] == False
            assert 'Unexpected error' in result['error']
            assert result['file_path'] == 'test.txt'
    
    def test_jira_client_initialization_missing_credentials(self):
        """Test that missing JIRA credentials are handled properly."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                self.server._initialize_jira_client()
            
            assert 'Missing JIRA credentials' in str(exc_info.value)
    
    def test_jira_client_initialization_success(self):
        """Test successful JIRA client initialization."""
        env_vars = {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_USER': 'test@example.com',
            'JIRA_API_TOKEN': 'test_token_123'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.mcp_server.JiraClientAsync') as mock_client:
                self.server._initialize_jira_client()
                
                mock_client.assert_called_once_with(
                    'https://test.atlassian.net',
                    'test@example.com',
                    'test_token_123'
                )
                assert self.server.jira_client is not None
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_exception_logging(self):
        """Test that tool execution exceptions are properly logged."""
        # Mock a handler that raises an exception
        with patch.object(self.server, '_tool_read_file', side_effect=Exception(\"Test error\")):
            with patch.object(self.server.logger, 'error') as mock_log:
                result = await self.server._handle_call_tool('read_file', {'file_path': 'test.txt'})
                
                # Check that error was logged
                mock_log.assert_called()
                
                # Check that error response was returned
                assert len(result) == 1
                response_text = result[0].text
                response_data = eval(response_text)  # Safe since we control the content
                assert response_data['error'] == 'Test error'
                assert response_data['tool'] == 'read_file'


class TestMcpServerIntegration:
    """Integration test cases for MCP server."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = JiraMcpServer()
    
    @pytest.mark.asyncio
    async def test_list_tools_contains_expected_tools(self):
        """Test that list_tools returns all expected tools."""
        tools = await self.server._handle_list_tools()
        
        expected_tools = [
            'jira_get_issue',
            'jira_update_description',
            'jira_add_comment',
            'jira_upload_attachment',
            'jira_download_attachments',
            'jira_read_attachment_content',
            'jira_search_issues',
            'read_file'
        ]
        
        tool_names = [tool.name for tool in tools]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f\"Tool {expected_tool} not found in tool list\"
    
    def test_server_initialization(self):
        \"\"\"Test that server initializes correctly.\"\"\"
        server = JiraMcpServer()
        
        assert server.server is not None
        assert server.jira_client is None  # Should be None until initialized
        assert server.doc_converter is not None
        assert hasattr(server, 'logger')


if __name__ == '__main__':
    pytest.main([__file__])