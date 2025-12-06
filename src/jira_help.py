#!/usr/bin/env python3
"""
JIRA Helper Script
Usage:
    python3 jira_help.py [JIRA-NUMBER]               # Get JIRA issue details
    python3 jira_help.py [JIRA-NUMBER] [update-info] # Add comment to JIRA issue
"""

import sys
import os
import json
import requests
from typing import Optional


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


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    issue_key = sys.argv[1]
    
    # Load credentials
    jira_url, jira_user, jira_token = load_credentials()
    
    # Create JIRA client
    client = JiraClient(jira_url, jira_user, jira_token)
    
    if len(sys.argv) == 2:
        # Read mode: Get issue details
        print(f"Fetching details for {issue_key}...")
        issue_data = client.get_issue(issue_key)
        
        if issue_data:
            print(format_issue_details(issue_data))
        else:
            sys.exit(1)
    
    elif len(sys.argv) >= 3:
        # Update mode: Add comment
        comment_text = ' '.join(sys.argv[2:])
        print(f"Adding comment to {issue_key}...")
        
        success = client.add_comment(issue_key, comment_text)
        if not success:
            sys.exit(1)
    
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
