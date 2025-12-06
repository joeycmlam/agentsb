# JIRA MCP Server

A Model Context Protocol (MCP) server that enables AI agents to interact with JIRA.

## Quick Start

### 1. Set Environment Variables

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

### 2. Test the Server

```bash
./script/test_jira_mcp.sh
```

### 3. Use in VS Code

The server is automatically configured in `.vscode/mcp.json`. Just start VS Code and ask AI agents to interact with JIRA.

## Architecture

```
┌─────────────────────┐
│   VS Code AI Agent  │
└──────────┬──────────┘
           │ MCP Protocol (stdio)
           ↓
┌─────────────────────┐
│  JiraMcpServer      │  ← Protocol handler
│  ├─ list_tools()    │
│  └─ call_tool()     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  JiraClientAsync    │  ← JIRA API wrapper
│  ├─ get_issue()     │
│  ├─ add_comment()   │
│  ├─ upload_file()   │
│  └─ search()        │
└──────────┬──────────┘
           │ REST API
           ↓
┌─────────────────────┐
│   JIRA Instance     │
└─────────────────────┘
```

## Clean Code Principles Applied

### 1. Meaningful Names
- `JiraClientAsync` - Clearly indicates async JIRA operations
- `validate_environment()` - Self-explanatory validation function
- `_tool_get_issue()` - Tool handler with clear prefix

### 2. Single Responsibility
- `JiraClientAsync`: Only handles JIRA API calls
- `JiraMcpServer`: Only handles MCP protocol
- Each tool handler does exactly one thing

### 3. Small Functions
- Most functions under 20 lines
- Complex operations broken into smaller methods
- Helper methods with focused responsibilities

### 4. Error Handling
```python
# Validate early, fail fast
def validate_environment() -> None:
    required_vars = ['JIRA_URL', 'JIRA_USER', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)

# Provide context in exceptions
async def get_issue(self, issue_key: str) -> dict:
    try:
        response = await self._fetch_issue(issue_key)
        return response.json()
    except Exception as e:
        raise Exception(f"Failed to get issue {issue_key}: {e}")
```

### 5. No Comments (Self-Documenting Code)
```python
# Bad:
# Check if vars exist
if not all([url, user, token]):
    raise ValueError("Missing vars")

# Good:
def validate_environment() -> None:
    """Validate required environment variables are set."""
    required_vars = ['JIRA_URL', 'JIRA_USER', 'JIRA_API_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    # Function name and structure make intent clear
```

## Available Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `jira_get_issue` | Get issue details | `issue_key` |
| `jira_add_comment` | Add comment | `issue_key`, `comment_text` |
| `jira_upload_attachment` | Upload file | `issue_key`, `file_path` |
| `jira_download_attachments` | Download files | `issue_key`, `download_dir?` |
| `jira_search_issues` | Search with JQL | `jql`, `max_results?` |

## Example Usage

### From Command Line

```bash
# Start the server
python3 src/jira_mcp_server.py
```

The server uses stdio for communication, so it's designed to be invoked by MCP clients (like VS Code).

### From VS Code AI Agent

Just ask natural language questions:

```
"Get me details for SCRUM-5"
"Add a comment to SCRUM-5: Analysis complete"
"Search for all bugs in project SCRUM"
"Download attachments from SCRUM-5"
```

The AI agent will automatically invoke the appropriate MCP tools.

## Error Handling

### Environment Validation
```bash
$ python3 src/jira_mcp_server.py
Error: Missing required environment variables: JIRA_API_TOKEN

Please set the following environment variables:
  JIRA_URL - Your JIRA instance URL
  JIRA_USER - Your JIRA username/email
  JIRA_API_TOKEN - Your JIRA API token
```

### Authentication Errors
```json
{
  "error": "Authentication failed. Check credentials.",
  "tool": "jira_get_issue",
  "arguments": {"issue_key": "SCRUM-5"}
}
```

### Not Found Errors
```json
{
  "error": "Not found: Issue SCRUM-999",
  "tool": "jira_get_issue",
  "arguments": {"issue_key": "SCRUM-999"}
}
```

## Development

### Run Tests

```bash
./script/test_jira_mcp.sh
```

### Test Individual Functions

```python
import asyncio
from jira_mcp_server import JiraClientAsync
import os

async def test_get_issue():
    client = JiraClientAsync(
        os.getenv('JIRA_URL'),
        os.getenv('JIRA_USER'),
        os.getenv('JIRA_API_TOKEN')
    )
    issue = await client.get_issue('SCRUM-5')
    print(issue)

asyncio.run(test_get_issue())
```

### Add New Tools

1. **Define tool** in `_handle_list_tools()`:
```python
Tool(
    name="jira_transition_issue",
    description="Transition issue to new status",
    inputSchema={
        "type": "object",
        "properties": {
            "issue_key": {"type": "string"},
            "transition": {"type": "string"}
        },
        "required": ["issue_key", "transition"]
    }
)
```

2. **Create handler** method:
```python
async def _tool_transition_issue(self, arguments: dict) -> dict:
    issue_key = arguments["issue_key"]
    transition = arguments["transition"]
    
    result = await self.jira_client.transition_issue(issue_key, transition)
    
    return {
        "success": True,
        "issue_key": issue_key,
        "transition": transition
    }
```

3. **Map handler** in `_handle_call_tool()`:
```python
handlers = {
    ...
    "jira_transition_issue": self._tool_transition_issue
}
```

4. **Implement API call** in `JiraClientAsync`:
```python
async def transition_issue(self, issue_key: str, transition: str) -> dict:
    endpoint = f"{self.url}/rest/api/3/issue/{issue_key}/transitions"
    
    payload = {"transition": {"name": transition}}
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: requests.post(
            endpoint,
            auth=self.auth,
            headers=self.headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
    )
    
    response.raise_for_status()
    return response.json()
```

## Files

```
src/
  jira_mcp_server.py       # Main MCP server implementation
  jira_help.py             # Original CLI helper (reference)
  README_JIRA_MCP.md       # This file

.vscode/
  mcp.json                 # VS Code MCP configuration

doc/
  jira_mcp_vscode_setup.md # Detailed setup guide
  jira_mcp_server.md       # Full documentation
  jira_mcp_example.py      # Usage examples

script/
  test_jira_mcp.sh         # Test script
```

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [JIRA REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

## License

See repository LICENSE file.
