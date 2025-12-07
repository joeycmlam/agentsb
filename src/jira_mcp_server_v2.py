#!/usr/bin/env python3
"""
JIRA MCP Server

A Model Context Protocol server that exposes JIRA operations as tools for AI agents.
This server provides capabilities to interact with JIRA issues, including reading,
commenting, managing attachments, and updating descriptions.

Supports two modes:
1. MCP Service Mode (default): Run as MCP server for AI agents
2. Command-Line Mode: Direct CLI operations

Usage:
    # MCP Service Mode (default)
    python3 jira_mcp_server.py

    # Command-Line Mode
    python3 jira_mcp_server.py cli get-issue PROJ-123
    python3 jira_mcp_server.py cli get-issue PROJ-123 --download
    python3 jira_mcp_server.py cli add-comment PROJ-123 "comment text"
    python3 jira_mcp_server.py cli upload-attachment PROJ-123 file.txt
    python3 jira_mcp_server.py cli update-description PROJ-123 "new description"
    python3 jira_mcp_server.py cli search "project = PROJ AND status = Open"

Environment Variables:
    JIRA_URL - JIRA instance URL (e.g., https://your-domain.atlassian.net)
    JIRA_USER - JIRA username/email
    JIRA_API_TOKEN - JIRA API token
"""

import asyncio
import sys

from cli import (
    cli_add_comment,
    cli_get_issue,
    cli_search_issues,
    cli_update_description,
    cli_upload_attachment
)
from jira_client import JiraClientAsync
from mcp_server import JiraMcpServer
from utils import create_cli_parser, validate_environment


async def run_cli_mode(args) -> None:
    """Execute CLI mode command."""
    validate_environment()

    # Initialize JIRA client
    jira_url = __import__('os').getenv('JIRA_URL')
    jira_user = __import__('os').getenv('JIRA_USER')
    jira_token = __import__('os').getenv('JIRA_API_TOKEN')

    client = JiraClientAsync(jira_url, jira_user, jira_token)

    try:
        if args.command == 'get-issue':
            await cli_get_issue(client, args.issue_key, args.download)
        elif args.command == 'add-comment':
            await cli_add_comment(client, args.issue_key, args.comment)
        elif args.command == 'upload-attachment':
            await cli_upload_attachment(client, args.issue_key, args.file_path)
        elif args.command == 'update-description':
            await cli_update_description(client, args.issue_key, args.description)
        elif args.command == 'search':
            await cli_search_issues(client, args.jql, args.max_results)
        else:
            print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


async def run_mcp_mode() -> None:
    """Execute MCP server mode."""
    validate_environment()
    server = JiraMcpServer()
    await server.run()


async def main() -> None:
    """Main entry point - routes to MCP server or CLI mode."""
    # If no arguments or only standalone flags, run MCP server mode
    if len(sys.argv) == 1:
        await run_mcp_mode()
        return

    # Parse arguments
    parser = create_cli_parser()
    args = parser.parse_args()

    # Route to appropriate mode
    if args.mode == 'cli':
        if not args.command:
            parser.print_help()
            sys.exit(1)
        await run_cli_mode(args)
    else:
        # Default to MCP mode
        await run_mcp_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)