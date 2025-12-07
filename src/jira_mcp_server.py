#!/usr/bin/env python3
"""
JIRA MCP Server

A Model Context Protocol server that exposes JIRA operations as tools for AI agents.
This server provides capabilities to interact with JIRA issues, including reading,
commenting, managing attachments, and updating descriptions.

Usage:
    python3 jira_mcp_server.py

Environment Variables:
    JIRA_URL - JIRA instance URL (e.g., https://your-domain.atlassian.net)
    JIRA_USER - JIRA username/email
    JIRA_API_TOKEN - JIRA API token
"""

import os
import json
import asyncio
import sys
from typing import Any, Optional
from pathlib import Path

import requests
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server


CONTENT_TYPE_JSON = 'application/json'
DEFAULT_TIMEOUT = 30
UPLOAD_TIMEOUT = 60
DOWNLOAD_CHUNK_SIZE = 8192


class JiraClientAsync:
    """Async JIRA API client for MCP server operations."""
    
    def __init__(self, url: str, username: str, api_token: str):
        self.url = url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth = (username, api_token)
        self.headers = {
            'Accept': CONTENT_TYPE_JSON,
            'Content-Type': CONTENT_TYPE_JSON
        }
    
    async def get_issue(self, issue_key: str) -> dict:
        """Retrieve JIRA issue details."""
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}"
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                timeout=DEFAULT_TIMEOUT
            )
        )
        
        if not response.ok:
            self._raise_http_error(response, issue_key)
        
        return response.json()
    
    async def update_description(self, issue_key: str, description_text: str) -> dict:
        """Update the description of a JIRA issue."""
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}"
        
        payload = {
            "fields": {
                "description": self._create_description_payload(description_text)
            }
        }
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.put(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=DEFAULT_TIMEOUT
            )
        )
        
        if not response.ok:
            self._raise_http_error(response, issue_key)
        
        # PUT returns 204 No Content on success
        return {"status": "success", "issue_key": issue_key}
    
    async def add_comment(self, issue_key: str, comment_text: str) -> dict:
        """Add a comment to a JIRA issue."""
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}/comment"
        
        payload = self._create_comment_payload(comment_text)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=DEFAULT_TIMEOUT
            )
        )
        
        if not response.ok:
            self._raise_http_error(response, issue_key)
        
        return response.json()
    
    async def upload_attachment(self, issue_key: str, file_path: str) -> dict:
        """Upload an attachment to a JIRA issue."""
        self._validate_file_path(file_path)
        
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}/attachments"
        attachment_headers = {
            'Accept': CONTENT_TYPE_JSON,
            'X-Atlassian-Token': 'no-check'
        }
        
        file_name = Path(file_path).name
        
        loop = asyncio.get_event_loop()
        with open(file_path, 'rb') as file:
            files = {'file': (file_name, file.read())}
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    endpoint,
                    auth=self.auth,
                    headers=attachment_headers,
                    files={'file': (file_name, files['file'][1])},
                    timeout=UPLOAD_TIMEOUT
                )
            )
        
        if not response.ok:
            self._raise_http_error(response, issue_key)
        
        return response.json()
    
    async def download_attachments(self, issue_key: str, download_dir: str) -> dict:
        """Download all attachments from a JIRA issue."""
        issue_data = await self.get_issue(issue_key)
        attachments = issue_data.get('fields', {}).get('attachment', [])
        
        if not attachments:
            return {
                'downloaded': 0,
                'total': 0,
                'message': f'No attachments found for {issue_key}'
            }
        
        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        for attachment in attachments:
            result = await self._download_single_attachment(
                attachment, 
                download_path
            )
            results.append(result)
        
        successful = sum(1 for r in results if r['success'])
        
        return {
            'downloaded': successful,
            'total': len(attachments),
            'files': results,
            'directory': str(download_path)
        }
    
    async def search_issues(self, jql: str, max_results: int = 50) -> dict:
        """Search for JIRA issues using JQL."""
        endpoint = f"{self.url}/rest/api/3/search"
        
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'key,summary,status,issuetype,priority,assignee,created,updated'
        }
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                params=params,
                timeout=DEFAULT_TIMEOUT
            )
        )
        
        if not response.ok:
            self._raise_http_error(response, jql)
        
        return response.json()
    
    def _create_description_payload(self, description_text: str) -> dict:
        """Create description payload in Atlassian Document Format."""
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description_text
                        }
                    ]
                }
            ]
        }
    
    def _create_comment_payload(self, comment_text: str) -> dict:
        """Create comment payload in Atlassian Document Format."""
        return {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment_text
                            }
                        ]
                    }
                ]
            }
        }
    
    def _validate_file_path(self, file_path: str) -> None:
        """Validate that file exists and is readable."""
        path = Path(file_path)
        
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise ValueError(f"File is not readable: {file_path}")
    
    async def _download_single_attachment(
        self, 
        attachment: dict, 
        download_dir: Path
    ) -> dict:
        """Download a single attachment."""
        filename = attachment.get('filename', 'unknown')
        url = attachment.get('content')
        
        if not url:
            return {
                'filename': filename,
                'success': False,
                'error': 'No download URL provided'
            }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    url,
                    auth=self.auth,
                    timeout=UPLOAD_TIMEOUT,
                    stream=True
                )
            )
            
            if not response.ok:
                return {
                    'filename': filename,
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }
            
            file_path = download_dir / filename
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    file.write(chunk)
            
            return {
                'filename': filename,
                'success': True,
                'path': str(file_path)
            }
        except Exception as e:
            return {
                'filename': filename,
                'success': False,
                'error': str(e)
            }
    
    def _raise_http_error(self, response: requests.Response, context: str) -> None:
        """Raise appropriate error based on HTTP status code."""
        status_code = response.status_code
        
        error_messages = {
            404: f"Not found: {context}",
            401: "Authentication failed. Check credentials.",
            403: "Permission denied. Check access rights.",
            413: "File too large. Check attachment size limits.",
        }
        
        message = error_messages.get(
            status_code, 
            f"HTTP {status_code}: {response.reason}"
        )
        
        raise Exception(message)


class JiraMcpServer:
    """MCP Server for JIRA operations."""
    
    def __init__(self):
        self.server = Server("jira-mcp-server")
        self.jira_client: Optional[JiraClientAsync] = None
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""
        self.server.list_tools()(self._handle_list_tools)
        self.server.call_tool()(self._handle_call_tool)
    
    async def _handle_list_tools(self) -> list[Tool]:
        """Return list of available JIRA tools."""
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
            )
        ]
    
    async def _handle_call_tool(self, name: str, arguments: Any) -> list[TextContent]:
        """Handle tool invocation requests."""
        if not self.jira_client:
            self._initialize_jira_client()
        
        handlers = {
            "jira_get_issue": self._tool_get_issue,
            "jira_update_description": self._tool_update_description,
            "jira_add_comment": self._tool_add_comment,
            "jira_upload_attachment": self._tool_upload_attachment,
            "jira_download_attachments": self._tool_download_attachments,
            "jira_search_issues": self._tool_search_issues
        }
        
        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        
        try:
            result = await handler(arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
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
            raise ValueError(
                "Missing JIRA credentials. Please set environment variables: "
                "JIRA_URL, JIRA_USER, JIRA_API_TOKEN"
            )
        
        self.jira_client = JiraClientAsync(jira_url, jira_user, jira_token)
    
    async def run(self) -> None:
        """Run the MCP server with stdio transport."""
        self._initialize_jira_client()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def validate_environment() -> None:
    """Validate required environment variables are set."""
    required_vars = ['JIRA_URL', 'JIRA_USER', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        print("\nPlease set the following environment variables:", file=sys.stderr)
        print("  JIRA_URL - Your JIRA instance URL (e.g., https://your-domain.atlassian.net)", file=sys.stderr)
        print("  JIRA_USER - Your JIRA username/email", file=sys.stderr)
        print("  JIRA_API_TOKEN - Your JIRA API token", file=sys.stderr)
        sys.exit(1)


async def main() -> None:
    """Main entry point for the MCP server."""
    validate_environment()
    
    server = JiraMcpServer()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
