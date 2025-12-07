#!/usr/bin/env python3
"""
MCP Server Module

Model Context Protocol server for JIRA operations and document reading.
"""

import json
import os
import logging
from typing import Any, Optional
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from jira_client import JiraClientAsync
from document_converter import get_converter


class JiraMcpServer:
    """MCP Server for JIRA operations and document reading."""

    def __init__(self):
        self.server = Server("jira-mcp-server")
        self.jira_client: Optional[JiraClientAsync] = None
        self.doc_converter = get_converter()
        self.logger = logging.getLogger(__name__)
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        self.server.list_tools()(self._handle_list_tools)
        self.server.call_tool()(self._handle_call_tool)

    async def _handle_list_tools(self) -> list[Tool]:
        """Return list of available JIRA and document reading tools."""
        return [
            Tool(
                name="jira_get_issue",
                description="Get details of a JIRA issue by key (e.g., PROJ-123)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        }
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="jira_update_description",
                description="Update the description of a JIRA issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        },
                        "description_text": {
                            "type": "string",
                            "description": "New description text for the issue"
                        }
                    },
                    "required": ["issue_key", "description_text"]
                }
            ),
            Tool(
                name="jira_add_comment",
                description="Add a comment to a JIRA issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        },
                        "comment_text": {
                            "type": "string",
                            "description": "Comment text to add"
                        }
                    },
                    "required": ["issue_key", "comment_text"]
                }
            ),
            Tool(
                name="jira_upload_attachment",
                description="Upload a file attachment to a JIRA issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to upload"
                        }
                    },
                    "required": ["issue_key", "file_path"]
                }
            ),
            Tool(
                name="jira_download_attachments",
                description="Download all attachments from a JIRA issue",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        },
                        "download_dir": {
                            "type": "string",
                            "description": "Directory to save attachments (default: ./downloads/<issue_key>)",
                            "default": ""
                        }
                    },
                    "required": ["issue_key"]
                }
            ),
            Tool(
                name="jira_read_attachment_content",
                description="Download and convert JIRA attachment (PDF, Word, Excel, etc.) to markdown for reading",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "JIRA issue key (e.g., PROJ-123)"
                        },
                        "filename": {
                            "type": "string",
                            "description": "Attachment filename to read"
                        },
                        "attachment_id": {
                            "type": "string",
                            "description": "Optional attachment ID for disambiguation if multiple files have the same name"
                        }
                    },
                    "required": ["issue_key", "filename"]
                }
            ),
            Tool(
                name="jira_search_issues",
                description="Search for JIRA issues using JQL (JIRA Query Language)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "jql": {
                            "type": "string",
                            "description": "JQL query string (e.g., 'project = PROJ AND status = Open')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 50)",
                            "default": 50
                        }
                    },
                    "required": ["jql"]
                }
            ),
            Tool(
                name="read_file",
                description="Read and convert local files (PDF, Word, Excel, PowerPoint, images, etc.) to markdown. Supports various document formats for AI agents to consume.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read and convert to markdown"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]

    async def _handle_call_tool(self, name: str, arguments: Any) -> list[TextContent]:
        """Handle tool invocation requests."""
        if not self.jira_client and name.startswith("jira_"):
            self._initialize_jira_client()

        handlers = {
            "jira_get_issue": self._tool_get_issue,
            "jira_update_description": self._tool_update_description,
            "jira_add_comment": self._tool_add_comment,
            "jira_upload_attachment": self._tool_upload_attachment,
            "jira_download_attachments": self._tool_download_attachments,
            "jira_read_attachment_content": self._tool_read_attachment_content,
            "jira_search_issues": self._tool_search_issues,
            "read_file": self._tool_read_file
        }

        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        try:
            result = await handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            self.logger.error(f"Tool execution failed for {name}: {e}", exc_info=True)
            error_result = {
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async def _tool_get_issue(self, arguments: dict) -> dict:
        """Get JIRA issue details."""
        issue_key = arguments["issue_key"]
        issue_data = await self.jira_client.get_issue(issue_key)

        return self._format_issue_response(issue_data)

    async def _tool_update_description(self, arguments: dict) -> dict:
        """Update JIRA issue description."""
        issue_key = arguments["issue_key"]
        description_text = arguments["description_text"]

        await self.jira_client.update_description(issue_key, description_text)

        # Fetch updated issue to confirm changes
        updated_issue = await self.jira_client.get_issue(issue_key)

        return {
            "success": True,
            "issue_key": issue_key,
            "message": f"Description updated successfully for {issue_key}",
            "updated_description": self._extract_description_text(
                updated_issue.get('fields', {}).get('description')
            )
        }

    async def _tool_add_comment(self, arguments: dict) -> dict:
        """Add comment to JIRA issue."""
        issue_key = arguments["issue_key"]
        comment_text = arguments["comment_text"]

        result = await self.jira_client.add_comment(issue_key, comment_text)

        return {
            "success": True,
            "issue_key": issue_key,
            "comment_id": result.get("id"),
            "message": f"Comment added successfully to {issue_key}"
        }

    async def _tool_upload_attachment(self, arguments: dict) -> dict:
        """Upload attachment to JIRA issue."""
        issue_key = arguments["issue_key"]
        file_path = arguments["file_path"]

        result = await self.jira_client.upload_attachment(issue_key, file_path)

        return {
            "success": True,
            "issue_key": issue_key,
            "file_path": file_path,
            "attachment": result[0] if result else None,
            "message": f"File uploaded successfully to {issue_key}"
        }

    async def _tool_download_attachments(self, arguments: dict) -> dict:
        """Download all attachments from JIRA issue."""
        issue_key = arguments["issue_key"]
        download_dir = arguments.get("download_dir") or f"./downloads/{issue_key}"

        result = await self.jira_client.download_attachments(issue_key, download_dir)

        return {
            "success": result["downloaded"] == result["total"],
            "issue_key": issue_key,
            **result
        }

    async def _tool_read_attachment_content(self, arguments: dict) -> dict:
        """Read and convert JIRA attachment to markdown."""
        issue_key = arguments["issue_key"]
        filename = arguments["filename"]
        attachment_id = arguments.get("attachment_id")

        result = await self.jira_client.read_attachment_content(
            issue_key,
            filename,
            attachment_id
        )

        return result

    async def _tool_search_issues(self, arguments: dict) -> dict:
        """Search JIRA issues using JQL."""
        jql = arguments["jql"]
        max_results = arguments.get("max_results", 50)

        result = await self.jira_client.search_issues(jql, max_results)

        issues = []
        for issue in result.get("issues", []):
            issues.append(self._format_issue_summary(issue))

        return {
            "total": result.get("total", 0),
            "max_results": max_results,
            "issues": issues
        }

    async def _tool_read_file(self, arguments: dict) -> dict:
        """Read and convert local file to markdown with security validation."""
        file_path = arguments["file_path"]
        
        # Security validation to prevent path traversal attacks
        try:
            # Normalize and validate path
            normalized_path = os.path.normpath(file_path)
            
            # Check for path traversal attempts
            if normalized_path.startswith('..'):
                error_msg = "Invalid file path - parent directory access not allowed"
                self.logger.warning(f"Path traversal attempt blocked: {file_path}")
                return {
                    "error": error_msg,
                    "success": False,
                    "file_path": file_path
                }
            
            # Check for absolute paths outside allowed directories
            if os.path.isabs(normalized_path):
                # For security, only allow absolute paths in specific directories
                allowed_prefixes = [
                    '/tmp/',
                    '/var/tmp/',
                    os.path.expanduser('~/Downloads/'),
                    os.getcwd()  # Current working directory
                ]
                
                if not any(normalized_path.startswith(prefix) for prefix in allowed_prefixes):
                    error_msg = "Absolute file paths outside allowed directories are not permitted"
                    self.logger.warning(f"Absolute path outside allowed directories blocked: {file_path}")
                    return {
                        "error": error_msg,
                        "success": False,
                        "file_path": file_path
                    }
            
            # Convert to Path object for additional validation
            path_obj = Path(normalized_path)
            
            # Ensure it's a file, not a directory or special file
            if path_obj.exists() and not path_obj.is_file():
                error_msg = "Path is not a regular file"
                self.logger.warning(f"Non-file path rejected: {file_path}")
                return {
                    "error": error_msg,
                    "success": False,
                    "file_path": file_path
                }
            
            # Log the conversion attempt
            self.logger.info(f"Processing file conversion request for: {normalized_path}")
            
            # Perform the conversion
            result = await self.doc_converter.convert_file_async(normalized_path)
            
            # Add the validated path to the result
            result["file_path"] = normalized_path
            
            if result.get("success"):
                self.logger.info(f"Successfully converted file: {normalized_path}")
            else:
                self.logger.warning(f"File conversion failed for {normalized_path}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error processing file: {str(e)}"
            self.logger.error(f"Unexpected error in _tool_read_file for {file_path}: {e}", exc_info=True)
            return {
                "error": error_msg,
                "success": False,
                "file_path": file_path
            }

    def _format_issue_response(self, issue_data: dict) -> dict:
        """Format issue data for response."""
        fields = issue_data.get('fields', {})

        return {
            "key": issue_data.get('key'),
            "summary": fields.get('summary'),
            "status": self._extract_field_name(fields.get('status')),
            "type": self._extract_field_name(fields.get('issuetype')),
            "priority": self._extract_field_name(fields.get('priority')),
            "assignee": self._extract_display_name(fields.get('assignee')),
            "reporter": self._extract_display_name(fields.get('reporter')),
            "created": fields.get('created'),
            "updated": fields.get('updated'),
            "description": self._extract_description_text(fields.get('description')),
            "attachments": self._format_attachments(fields.get('attachment', [])),
            "url": f"{self.jira_client.url}/browse/{issue_data.get('key')}"
        }

    def _format_issue_summary(self, issue_data: dict) -> dict:
        """Format issue summary for search results."""
        fields = issue_data.get('fields', {})

        return {
            "key": issue_data.get('key'),
            "summary": fields.get('summary'),
            "status": self._extract_field_name(fields.get('status')),
            "type": self._extract_field_name(fields.get('issuetype')),
            "priority": self._extract_field_name(fields.get('priority')),
            "assignee": self._extract_display_name(fields.get('assignee')),
            "created": fields.get('created'),
            "updated": fields.get('updated')
        }

    def _extract_field_name(self, field: Optional[dict]) -> str:
        """Extract name from field object."""
        if not field or not isinstance(field, dict):
            return 'N/A'
        return field.get('name', 'N/A')

    def _extract_display_name(self, field: Optional[dict]) -> str:
        """Extract display name from user field."""
        if not field or not isinstance(field, dict):
            return 'Unassigned'
        return field.get('displayName', 'Unknown')

    def _extract_description_text(self, description: Optional[dict]) -> str:
        """Extract text from Atlassian Document Format description."""
        if not description or not isinstance(description, dict):
            return ''

        content = description.get('content', [])
        text_parts = []

        for item in content:
            if item.get('type') == 'paragraph':
                for para_content in item.get('content', []):
                    if para_content.get('type') == 'text':
                        text_parts.append(para_content.get('text', ''))

        return '\n'.join(text_parts)

    def _format_attachments(self, attachments: list) -> list:
        """Format attachments list."""
        return [
            {
                "filename": att.get('filename'),
                "size": att.get('size'),
                "mimeType": att.get('mimeType'),
                "created": att.get('created')
            }
            for att in attachments
        ]

    def _initialize_jira_client(self) -> None:
        """Initialize JIRA client with credentials from environment."""
        jira_url = os.getenv('JIRA_URL')
        jira_user = os.getenv('JIRA_USER')
        jira_token = os.getenv('JIRA_API_TOKEN')

        if not all([jira_url, jira_user, jira_token]):
            error_msg = (
                "Missing JIRA credentials. Please set environment variables: "
                "JIRA_URL, JIRA_USER, JIRA_API_TOKEN"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.jira_client = JiraClientAsync(jira_url, jira_user, jira_token)
        self.logger.info(f"JIRA client initialized for {jira_url}")

    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        self._initialize_jira_client()
        self.logger.info("Starting JIRA MCP Server")

        async with stdio_server() as (read_stream, write_stream):
            self.logger.info("MCP Server ready for requests")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
