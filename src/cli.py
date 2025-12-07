#!/usr/bin/env python3
"""
CLI Mode Functions

Command-line interface functions for JIRA operations.
"""

from pathlib import Path
from typing import Optional

from .jira_client import JiraClientAsync


async def cli_get_issue(client: JiraClientAsync, issue_key: str, download: bool = False) -> None:
    """CLI: Get issue details and optionally download attachments."""
    print(f"Fetching details for {issue_key}...")
    issue_data = await client.get_issue(issue_key)

    fields = issue_data.get('fields', {})
    print(f"\n{'='*60}")
    print(f"JIRA Issue: {issue_data.get('key')}")
    print(f"{'='*60}")
    print(f"Summary:     {fields.get('summary', 'N/A')}")
    print(f"Type:        {fields.get('issuetype', {}).get('name', 'N/A')}")
    print(f"Status:      {fields.get('status', {}).get('name', 'N/A')}")
    print(f"Priority:    {fields.get('priority', {}).get('name', 'N/A')}")
    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
    print(f"Assignee:    {assignee}")
    reporter = fields.get('reporter', {}).get('displayName', 'N/A') if fields.get('reporter') else 'N/A'
    print(f"Reporter:    {reporter}")
    print(f"Created:     {fields.get('created', 'N/A')}")
    print(f"Updated:     {fields.get('updated', 'N/A')}")
    print(f"\nDescription:")
    print(f"    {_extract_description_text_cli(fields.get('description'))}")

    attachments = fields.get('attachment', [])
    if attachments:
        print(f"\nAttachments: ({len(attachments)})")
        for att in attachments:
            size_kb = att.get('size', 0) / 1024
            print(f"    - {att.get('filename')} ({size_kb:.1f} KB)")
    else:
        print(f"\nAttachments: None")
    print(f"{'='*60}\n")

    if download and attachments:
        download_dir = Path.cwd() / 'downloads' / issue_key
        result = await client.download_attachments(issue_key, str(download_dir))
        print(f"Downloaded {result['downloaded']}/{result['total']} attachments to {result['directory']}")


async def cli_add_comment(client: JiraClientAsync, issue_key: str, comment_text: str) -> None:
    """CLI: Add comment to issue."""
    print(f"Adding comment to {issue_key}...")
    result = await client.add_comment(issue_key, comment_text)
    print(f"✓ Comment added successfully (ID: {result.get('id')})")


async def cli_upload_attachment(client: JiraClientAsync, issue_key: str, file_path: str) -> None:
    """CLI: Upload attachment to issue."""
    print(f"Uploading attachment to {issue_key}...")
    result = await client.upload_attachment(issue_key, file_path)
    filename = Path(file_path).name
    print(f"✓ Attachment '{filename}' uploaded successfully")


async def cli_update_description(client: JiraClientAsync, issue_key: str, description_text: str) -> None:
    """CLI: Update issue description."""
    print(f"Updating description for {issue_key}...")
    await client.update_description(issue_key, description_text)
    print(f"✓ Description updated successfully")


async def cli_search_issues(client: JiraClientAsync, jql: str, max_results: int = 50) -> None:
    """CLI: Search issues using JQL."""
    print(f"Searching with JQL: {jql}")
    result = await client.search_issues(jql, max_results)

    total = result.get('total', 0)
    issues = result.get('issues', [])

    print(f"\nFound {total} issue(s), showing {len(issues)}:\n")

    for issue in issues:
        fields = issue.get('fields', {})
        key = issue.get('key')
        summary = fields.get('summary', 'N/A')
        status = fields.get('status', {}).get('name', 'N/A')
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'

        print(f"  {key}: {summary}")
        print(f"    Status: {status} | Assignee: {assignee}\n")


def _extract_description_text_cli(description: Optional[dict]) -> str:
    """Extract text from Atlassian Document Format description for CLI display."""
    if not description or not isinstance(description, dict):
        return 'N/A'

    content = description.get('content', [])
    text_parts = []

    for item in content:
        if item.get('type') == 'paragraph':
            for para_content in item.get('content', []):
                if para_content.get('type') == 'text':
                    text_parts.append(para_content.get('text', ''))

    return '\n    '.join(text_parts) if text_parts else 'N/A'