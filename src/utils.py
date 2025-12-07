#!/usr/bin/env python3
"""
Utilities Module

Utility functions for JIRA MCP Server.
"""

import argparse
import os
import sys


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


def create_cli_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI mode."""
    parser = argparse.ArgumentParser(
        description='JIRA MCP Server - MCP Service and CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as MCP server (default)
  python3 jira_mcp_server.py

  # CLI Mode
  python3 jira_mcp_server.py cli get-issue PROJ-123
  python3 jira_mcp_server.py cli get-issue PROJ-123 --download
  python3 jira_mcp_server.py cli add-comment PROJ-123 "Fix applied"
  python3 jira_mcp_server.py cli upload-attachment PROJ-123 report.pdf
  python3 jira_mcp_server.py cli update-description PROJ-123 "Updated specs"
  python3 jira_mcp_server.py cli search "project = PROJ AND status = Open"
        """
    )

    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')

    # CLI mode subparser
    cli_parser = subparsers.add_parser('cli', help='Command-line interface mode')
    cli_subparsers = cli_parser.add_subparsers(dest='command', help='CLI command')

    # get-issue command
    get_issue_parser = cli_subparsers.add_parser('get-issue', help='Get issue details')
    get_issue_parser.add_argument('issue_key', help='JIRA issue key (e.g., PROJ-123)')
    get_issue_parser.add_argument('--download', action='store_true', help='Download attachments')

    # add-comment command
    add_comment_parser = cli_subparsers.add_parser('add-comment', help='Add comment to issue')
    add_comment_parser.add_argument('issue_key', help='JIRA issue key')
    add_comment_parser.add_argument('comment', help='Comment text')

    # upload-attachment command
    upload_parser = cli_subparsers.add_parser('upload-attachment', help='Upload attachment')
    upload_parser.add_argument('issue_key', help='JIRA issue key')
    upload_parser.add_argument('file_path', help='Path to file to upload')

    # update-description command
    update_desc_parser = cli_subparsers.add_parser('update-description', help='Update issue description')
    update_desc_parser.add_argument('issue_key', help='JIRA issue key')
    update_desc_parser.add_argument('description', help='New description text')

    # search command
    search_parser = cli_subparsers.add_parser('search', help='Search issues with JQL')
    search_parser.add_argument('jql', help='JQL query string')
    search_parser.add_argument('--max-results', type=int, default=50, help='Maximum results (default: 50)')

    return parser