#!/usr/bin/env python3
"""
JIRA Helper Script
Usage:
    python3 jira_help.py [JIRA-NUMBER]                              # Get JIRA issue details
    python3 jira_help.py [JIRA-NUMBER] [comment-text]               # Add comment to JIRA issue
    python3 jira_help.py [JIRA-NUMBER] --attach [file1] [file2]...  # Upload attachments
    python3 jira_help.py [JIRA-NUMBER] --comment [text] --attach [files]... # Comment + attachments
"""

import sys
import os
import json
import requests
from typing import Optional, List
from pathlib import Path


class JiraClient:
    """Simple JIRA API client for reading and updating issues."""
    
    def __init__(self, url: str, username: str, api_token: str):
        """Initialize JIRA client with credentials."""
        self.url = url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth = (username, api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_issue(self, issue_key: str) -> Optional[dict]:
        """
        Retrieve JIRA issue details.
        
        Args:
            issue_key: JIRA issue key (e.g., PROJ-123)
            
        Returns:
            Dictionary with issue details or None if error
        """
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}"
        
        try:
            response = requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"Error: Issue '{issue_key}' not found")
            elif response.status_code == 401:
                print("Error: Authentication failed. Check your credentials.")
            else:
                print(f"Error: HTTP {response.status_code} - {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to JIRA - {e}")
            return None
    
    def add_comment(self, issue_key: str, comment_text: str) -> bool:
        """
        Add a comment to a JIRA issue.
        
        Args:
            issue_key: JIRA issue key (e.g., PROJ-123)
            comment_text: Comment text to add
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}/comment"
        
        payload = {
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
        
        try:
            response = requests.post(
                endpoint,
                auth=self.auth,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            print(f"✓ Comment added successfully to {issue_key}")
            return True
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print(f"Error: Issue '{issue_key}' not found")
            elif response.status_code == 401:
                print("Error: Authentication failed. Check your credentials.")
            else:
                print(f"Error: HTTP {response.status_code} - {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to JIRA - {e}")
            return False
    
    def upload_attachment(self, issue_key: str, file_path: str) -> bool:
        """
        Upload an attachment to a JIRA issue.
        
        Args:
            issue_key: JIRA issue key (e.g., PROJ-123)
            file_path: Path to the file to upload
            
        Returns:
            True if successful, False otherwise
        """
        if not self._validate_file_path(file_path):
            return False
        
        endpoint = f"{self.url}/rest/api/3/issue/{issue_key}/attachments"
        attachment_headers = {
            'Accept': 'application/json',
            'X-Atlassian-Token': 'no-check'
        }
        
        file_name = Path(file_path).name
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (file_name, file)}
                response = requests.post(
                    endpoint,
                    auth=self.auth,
                    headers=attachment_headers,
                    files=files,
                    timeout=60
                )
            
            response.raise_for_status()
            print(f"✓ Attachment '{file_name}' uploaded successfully to {issue_key}")
            return True
            
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}")
            return False
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(response, issue_key, e)
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to upload attachment - {e}")
            return False
    
    def upload_attachments(self, issue_key: str, file_paths: List[str]) -> bool:
        """
        Upload multiple attachments to a JIRA issue.
        
        Args:
            issue_key: JIRA issue key (e.g., PROJ-123)
            file_paths: List of file paths to upload
            
        Returns:
            True if all uploads successful, False otherwise
        """
        if not file_paths:
            print("Error: No file paths provided")
            return False
        
        all_successful = True
        for file_path in file_paths:
            if not self.upload_attachment(issue_key, file_path):
                all_successful = False
        
        return all_successful
    
    def add_comment_with_attachments(
        self, 
        issue_key: str, 
        comment_text: str, 
        file_paths: List[str]
    ) -> bool:
        """
        Add a comment and upload attachments to a JIRA issue.
        
        Args:
            issue_key: JIRA issue key (e.g., PROJ-123)
            comment_text: Comment text to add
            file_paths: List of file paths to upload
            
        Returns:
            True if both operations successful, False otherwise
        """
        comment_success = self.add_comment(issue_key, comment_text)
        attachments_success = self.upload_attachments(issue_key, file_paths)
        
        return comment_success and attachments_success
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Validate that file exists and is readable."""
        path = Path(file_path)
        
        if not path.exists():
            print(f"Error: File does not exist - {file_path}")
            return False
        
        if not path.is_file():
            print(f"Error: Path is not a file - {file_path}")
            return False
        
        if not os.access(file_path, os.R_OK):
            print(f"Error: File is not readable - {file_path}")
            return False
        
        return True
    
    def _handle_http_error(self, response, issue_key: str, error: Exception):
        """Handle HTTP errors with appropriate messages."""
        if response.status_code == 404:
            print(f"Error: Issue '{issue_key}' not found")
        elif response.status_code == 401:
            print("Error: Authentication failed. Check your credentials.")
        elif response.status_code == 413:
            print("Error: File too large. Check JIRA's attachment size limits.")
        else:
            print(f"Error: HTTP {response.status_code} - {error}")


def format_issue_details(issue_data: dict) -> str:
    """Format JIRA issue details for display."""
    fields = issue_data.get('fields', {})
    
    # Extract key information
    key = issue_data.get('key', 'N/A')
    summary = fields.get('summary', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A') if fields.get('status') else 'N/A'
    issue_type = fields.get('issuetype', {}).get('name', 'N/A') if fields.get('issuetype') else 'N/A'
    priority = fields.get('priority', {}).get('name', 'N/A') if fields.get('priority') else 'N/A'
    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
    reporter = fields.get('reporter', {}).get('displayName', 'N/A') if fields.get('reporter') else 'N/A'
    created = fields.get('created', 'N/A')
    updated = fields.get('updated', 'N/A')
    description = fields.get('description', {})
    
    # Extract description text
    desc_text = 'N/A'
    if description and isinstance(description, dict):
        content = description.get('content', [])
        desc_parts = []
        for item in content:
            if item.get('type') == 'paragraph':
                for para_content in item.get('content', []):
                    if para_content.get('type') == 'text':
                        desc_parts.append(para_content.get('text', ''))
        if desc_parts:
            desc_text = '\n    '.join(desc_parts)
    
    # Format output
    output = f"""
{'='*60}
JIRA Issue: {key}
{'='*60}
Summary:     {summary}
Type:        {issue_type}
Status:      {status}
Priority:    {priority}
Assignee:    {assignee}
Reporter:    {reporter}
Created:     {created}
Updated:     {updated}

Description:
    {desc_text}
{'='*60}
"""
    return output


def load_credentials():
    """Load JIRA credentials from environment variables."""
    jira_url = os.getenv('JIRA_URL')
    jira_user = os.getenv('JIRA_USER')
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    if not all([jira_url, jira_user, jira_token]):
        print("Error: Missing JIRA credentials in environment variables.")
        print("Please set: JIRA_URL, JIRA_USER, JIRA_API_TOKEN")
        sys.exit(1)
    
    return jira_url, jira_user, jira_token


def parse_arguments() -> dict:
    """Parse command line arguments into structured format."""
    if len(sys.argv) < 2:
        return {'mode': 'help'}
    
    issue_key = sys.argv[1]
    args = sys.argv[2:]
    
    if not args:
        return {'mode': 'read', 'issue_key': issue_key}
    
    parsed = {'mode': 'update', 'issue_key': issue_key}
    
    if '--attach' in args:
        attach_index = args.index('--attach')
        
        if '--comment' in args:
            comment_index = args.index('--comment')
            
            if comment_index < attach_index:
                comment_parts = args[comment_index + 1:attach_index]
                parsed['comment'] = ' '.join(comment_parts)
                parsed['files'] = args[attach_index + 1:]
            else:
                parsed['files'] = args[attach_index + 1:comment_index]
                comment_parts = args[comment_index + 1:]
                parsed['comment'] = ' '.join(comment_parts)
        else:
            parsed['files'] = args[attach_index + 1:]
    else:
        parsed['comment'] = ' '.join(args)
    
    return parsed


def execute_read_mode(client: JiraClient, issue_key: str) -> bool:
    """Execute read mode to fetch and display issue details."""
    print(f"Fetching details for {issue_key}...")
    issue_data = client.get_issue(issue_key)
    
    if issue_data:
        print(format_issue_details(issue_data))
        return True
    return False


def execute_update_mode(client: JiraClient, issue_key: str, parsed_args: dict) -> bool:
    """Execute update mode to add comments and/or attachments."""
    has_comment = 'comment' in parsed_args
    has_files = 'files' in parsed_args
    
    if has_comment and has_files:
        print(f"Adding comment and attachments to {issue_key}...")
        return client.add_comment_with_attachments(
            issue_key, 
            parsed_args['comment'], 
            parsed_args['files']
        )
    elif has_comment:
        print(f"Adding comment to {issue_key}...")
        return client.add_comment(issue_key, parsed_args['comment'])
    elif has_files:
        print(f"Uploading attachments to {issue_key}...")
        return client.upload_attachments(issue_key, parsed_args['files'])
    else:
        print("Error: No comment or attachments specified")
        return False


def main():
    """Main entry point for the script."""
    parsed_args = parse_arguments()
    
    if parsed_args['mode'] == 'help':
        print(__doc__)
        sys.exit(1)
    
    jira_url, jira_user, jira_token = load_credentials()
    client = JiraClient(jira_url, jira_user, jira_token)
    
    issue_key = parsed_args['issue_key']
    
    if parsed_args['mode'] == 'read':
        success = execute_read_mode(client, issue_key)
    else:
        success = execute_update_mode(client, issue_key, parsed_args)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
