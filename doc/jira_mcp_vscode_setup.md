# JIRA MCP Server - VS Code Setup Guide

## Overview

The JIRA MCP (Model Context Protocol) Server enables AI agents in VS Code to interact with JIRA through a standardized protocol. This guide explains how to set up and use the server.

## Prerequisites

1. **Python 3.8+** installed
2. **MCP Python SDK** installed:
   ```bash
   pip install mcp
   ```
3. **VS Code** with MCP extension support
4. **JIRA credentials**:
   - JIRA instance URL
   - JIRA username/email
   - JIRA API token

## Installation

### 1. Set Environment Variables

Set your JIRA credentials as environment variables:

**macOS/Linux (.bashrc, .zshrc, or .profile):**
```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token-here"
```

**Windows (PowerShell):**
```powershell
$env:JIRA_URL="https://your-domain.atlassian.net"
$env:JIRA_USER="your-email@example.com"
$env:JIRA_API_TOKEN="your-api-token-here"
```

**Windows (Command Prompt):**
```cmd
set JIRA_URL=https://your-domain.atlassian.net
set JIRA_USER=your-email@example.com
set JIRA_API_TOKEN=your-api-token-here
```

### 2. Configure VS Code

The MCP configuration file is already set up at `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "python3",
      "args": [
        "${workspaceFolder}/src/jira_mcp_server.py"
      ],
      "env": {
        "JIRA_URL": "${env:JIRA_URL}",
        "JIRA_USER": "${env:JIRA_USER}",
        "JIRA_API_TOKEN": "${env:JIRA_API_TOKEN}"
      }
    }
  }
}
```

### 3. Verify Installation

Test the server manually:

```bash
cd /Users/joeylam/repo/agentsb
python3 src/jira_mcp_server.py
```

The server should start without errors. Press `Ctrl+C` to stop.

## Available Tools

The JIRA MCP Server exposes five tools:

### 1. jira_get_issue
Get details of a JIRA issue.

**Parameters:**
- `issue_key` (string, required): JIRA issue key (e.g., "SCRUM-5")

**Example:**
```json
{
  "issue_key": "SCRUM-5"
}
```

### 2. jira_add_comment
Add a comment to a JIRA issue.

**Parameters:**
- `issue_key` (string, required): JIRA issue key
- `comment_text` (string, required): Comment text to add

**Example:**
```json
{
  "issue_key": "SCRUM-5",
  "comment_text": "Analysis completed. See attached feature file."
}
```

### 3. jira_upload_attachment
Upload a file as an attachment to a JIRA issue.

**Parameters:**
- `issue_key` (string, required): JIRA issue key
- `file_path` (string, required): Absolute path to file

**Example:**
```json
{
  "issue_key": "SCRUM-5",
  "file_path": "/path/to/file.feature"
}
```

### 4. jira_download_attachments
Download all attachments from a JIRA issue.

**Parameters:**
- `issue_key` (string, required): JIRA issue key
- `download_dir` (string, optional): Directory path (defaults to "./downloads/{issue_key}")

**Example:**
```json
{
  "issue_key": "SCRUM-5",
  "download_dir": "/path/to/downloads"
}
```

### 5. jira_search_issues
Search for JIRA issues using JQL.

**Parameters:**
- `jql` (string, required): JQL query
- `max_results` (number, optional): Maximum results (default: 50, max: 100)

**Example:**
```json
{
  "jql": "project = SCRUM AND status = 'To Do'",
  "max_results": 20
}
```

## Usage in VS Code

Once configured, AI agents in VS Code can use these tools automatically:

1. **Open VS Code** in the workspace directory
2. **Start a conversation** with an AI agent
3. **Ask questions** about JIRA issues:
   - "Get details for SCRUM-5"
   - "Add a comment to SCRUM-5 saying the analysis is complete"
   - "Search for all open issues in project SCRUM"
   - "Download attachments from SCRUM-5"

The AI agent will automatically call the appropriate JIRA MCP tools to fulfill your requests.

## Troubleshooting

### Server Won't Start

**Check environment variables:**
```bash
echo $JIRA_URL
echo $JIRA_USER
echo $JIRA_API_TOKEN
```

All three should return values. If not, set them in your shell profile and restart your terminal.

### Authentication Failed

1. **Verify API token**: Generate a new token at `https://id.atlassian.com/manage-profile/security/api-tokens`
2. **Check username**: Use your email address, not your display name
3. **Verify URL**: Ensure URL has no trailing slash

### Permission Denied

Ensure your JIRA account has permissions to:
- Read issues
- Add comments
- Upload/download attachments
- Search issues

### Python Module Not Found

Install the MCP SDK:
```bash
pip install mcp requests
```

Or use the virtual environment:
```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
pip install mcp requests
```

## Architecture

### Clean Code Design

The server follows clean code principles:

1. **Single Responsibility**: 
   - `JiraClientAsync`: Handles JIRA API calls
   - `JiraMcpServer`: Manages MCP protocol

2. **Meaningful Names**:
   - Functions clearly describe their purpose
   - No abbreviations or cryptic names

3. **Small Functions**:
   - Most functions under 20 lines
   - Each does one thing well

4. **Error Handling**:
   - Exceptions with context
   - Graceful degradation
   - User-friendly error messages

### Protocol Flow

```
VS Code AI Agent
       ↓
  [MCP Protocol]
       ↓
JIRA MCP Server (stdio)
       ↓
  [JIRA REST API]
       ↓
   JIRA Instance
```

## Security

### Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API tokens** regularly
4. **Limit token permissions** to required scopes
5. **Use HTTPS** for JIRA connections

### API Token Generation

1. Go to `https://id.atlassian.com/manage-profile/security/api-tokens`
2. Click **Create API token**
3. Give it a descriptive name (e.g., "MCP Server")
4. Copy the token immediately (you can't view it again)
5. Store it in your environment variables

## Development

### Running Tests

```bash
# Test single tool
python3 -c "
import asyncio
from src.jira_mcp_server import JiraClientAsync
import os

async def test():
    client = JiraClientAsync(
        os.getenv('JIRA_URL'),
        os.getenv('JIRA_USER'),
        os.getenv('JIRA_API_TOKEN')
    )
    issue = await client.get_issue('SCRUM-5')
    print(issue)

asyncio.run(test())
"
```

### Debugging

Enable verbose logging by modifying the server:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Extending the Server

To add a new tool:

1. Add tool definition in `_handle_list_tools()`
2. Create handler method `_tool_your_method()`
3. Add handler mapping in `_handle_call_tool()`
4. Implement JIRA API call in `JiraClientAsync`

## Support

For issues or questions:
- Check JIRA API docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Review MCP spec: https://spec.modelcontextprotocol.io/
- Open an issue in the repository

## License

See repository LICENSE file for details.
