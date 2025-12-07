#!/usr/bin/env python3
"""
JIRA Client Module

Async JIRA API client for MCP server operations.
"""

import os
import json
import asyncio
from typing import Any, Optional
from pathlib import Path

import requests

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