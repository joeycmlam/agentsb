# Copilot Instructions for JIRA MCP Server

## Project Overview

This project is a **Model Context Protocol (MCP) server** that bridges AI agents with JIRA, supporting both:
1. **MCP Server Mode**: Exposes JIRA operations as tools for AI agents (default)
2. **CLI Mode**: Direct command-line JIRA operations

The codebase was recently refactored from a monolithic architecture into modular components (see `REFACTORING_SUMMARY.md`).

## Architecture

### Core Module Separation

```
src/
├── jira_mcp_server_v2.py    # Entry point - routes between MCP/CLI modes
├── mcp_server.py             # MCP protocol handlers & tool definitions
├── jira_client.py            # Async JIRA API client (all HTTP operations)
├── cli.py                    # CLI terminal formatting & commands
└── utils.py                  # Environment validation & arg parsing
```

**Key Architectural Decision**: Each module has a single responsibility. When modifying JIRA API interactions, edit `jira_client.py`. For MCP tool definitions, edit `mcp_server.py`. Never mix concerns.

### Entry Point Flow

`jira_mcp_server_v2.py` determines execution mode:
- **No args or no 'cli' subcommand** → MCP server mode via `run_mcp_mode()`
- **Args include 'cli' subcommand** → CLI mode via `run_cli_mode()`

### Environment Configuration

Required environment variables (validated by `utils.py::validate_environment()`):
- `JIRA_URL` - Instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_USER` - Username/email
- `JIRA_API_TOKEN` - API token

The wrapper script `script/run_jira_mcp.sh` loads these from `.env` or shell profiles before launching.

## Critical Patterns

### 1. Atlassian Document Format (ADF)

JIRA Cloud uses ADF for rich text fields. **Always** construct payloads using helper methods:
```python
# In jira_client.py
def _create_description_payload(self, description_text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": description_text}]
        }]
    }
```

When extracting text from responses, use `_extract_description_text()` to parse ADF structure.

### 2. Async Pattern with Blocking HTTP

Since `requests` library is synchronous but MCP requires async, we use:
```python
loop = asyncio.get_event_loop()
response = await loop.run_in_executor(None, lambda: requests.get(...))
```

**Do not** use `requests` directly in async functions without wrapping in `run_in_executor`.

### 3. Error Handling Convention

HTTP errors are centralized in `jira_client.py::_raise_http_error()`:
- 404 → "Not found: {context}"
- 401 → "Authentication failed. Check credentials."
- 403 → "Permission denied. Check access rights."

Always call this method after unsuccessful HTTP responses for consistent error messages.

### 4. MCP Tool Response Format

MCP tools must return `list[TextContent]`. Pattern in `mcp_server.py`:
```python
async def _handle_call_tool(self, name: str, arguments: Any) -> list[TextContent]:
    try:
        result = await handler(arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        error_result = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
```

Always return JSON-serialized results, never raw Python objects.

## Developer Workflows

### Running the MCP Server

```bash
# Via wrapper (recommended - loads .env)
./script/run_jira_mcp.sh

# Direct execution (ensure env vars set)
python3 src/jira_mcp_server_v2.py
```

The server runs on stdio transport and registers 6 tools (see `_handle_list_tools()` in `mcp_server.py`).

### CLI Testing

Test JIRA operations without AI agent integration:
```bash
python3 src/jira_mcp_server_v2.py cli get-issue PROJ-123
python3 src/jira_mcp_server_v2.py cli search "project = PROJ AND status = Open"
```

Use `--download` flag with `get-issue` to test attachment downloading.

### Adding New JIRA Operations

1. Add async method to `JiraClientAsync` in `jira_client.py`
2. Add tool definition in `mcp_server.py::_handle_list_tools()`
3. Add handler method `_tool_<operation>()` in `mcp_server.py`
4. Add handler mapping in `_handle_call_tool()`
5. (Optional) Add CLI command in `cli.py` and update parser in `utils.py`

### Dependencies

From `script/requirements.txt`:
- `requests>=2.0` - HTTP client for JIRA API
- `mcp>=0.1.0` - Model Context Protocol SDK
- `deepdiff>=6.0.0` - Not actively used in core modules (legacy?)

No virtual environment management in codebase - assumes system Python 3.

## Project-Specific Conventions

### Import Organization

Follow standard library → third-party → local pattern:
```python
import os
import json
import asyncio
from typing import Any, Optional
from pathlib import Path

import requests

from jira_client import JiraClientAsync
from utils import validate_environment
```

### Naming Conventions

- Module-level constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `CONTENT_TYPE_JSON`)
- Private methods: Prefix with underscore `_method_name()`
- MCP tool handlers: `_tool_<operation>()`
- CLI functions: `cli_<operation>()`

### File Organization

- Scripts: `script/` directory (bash wrappers, requirements.txt)
- Source: `src/` directory (no subdirectories - flat structure)
- Tests: `tests/` directory (currently empty - add tests when requested)
- Documentation: `doc/` directory (architecture, design subdirs exist)
- Temp files: `tmp/` directory (gitignored)

## Integration Points

### MCP Protocol

Server implements two core handlers:
- `list_tools()` - Returns available JIRA operations
- `call_tool()` - Executes requested operation

Registered via `_register_handlers()` in `__init__`. Transport is stdio via `mcp.server.stdio.stdio_server()`.

### JIRA REST API v3

Base URL pattern: `{JIRA_URL}/rest/api/3/{endpoint}`

Authentication: HTTP Basic Auth with `(username, api_token)`

Common endpoints in use:
- `/issue/{issueKey}` - GET (retrieve), PUT (update)
- `/issue/{issueKey}/comment` - POST (add comment)
- `/issue/{issueKey}/attachments` - POST (upload), GET (download)
- `/search` - GET with JQL query

## Agent Ecosystem

The `.github/agents/` directory contains role-specific agent definitions:
- `developer.agent.md` - Full-cycle development with TDD, includes JIRA integration workflows
- `ba-mcp.agent.md` - Business analysis with MCP tool usage
- `architect.agent.md` - Architecture decisions and system design

These agents expect MCP tools to be available. When adding new JIRA operations, consider updating relevant agent definitions.

## Common Pitfalls

1. **Forgetting ADF format**: Always use `_create_description_payload()` and `_create_comment_payload()`
2. **Blocking async**: Wrap `requests` calls in `run_in_executor()`
3. **Missing env validation**: CLI mode calls `validate_environment()` - don't skip this
4. **Hardcoded URLs**: Use `self.url` from client initialization
5. **Large files**: Use `UPLOAD_TIMEOUT` (60s) instead of `DEFAULT_TIMEOUT` (30s) for attachments

## Testing Strategy

Currently no automated tests exist. When adding tests:
- Unit tests for `jira_client.py` - mock HTTP responses
- Integration tests for `mcp_server.py` - test tool handlers
- CLI tests for `cli.py` - capture stdout/stderr

Use `pytest` framework (not explicitly in requirements but standard Python practice).

## Version History

- **v1**: Monolithic `jira_mcp_server_v1.py` (34KB, ~600 lines)
- **v2**: Current modular architecture (see `REFACTORING_SUMMARY.md` for migration details)

The v1 file still exists in `src/` but is deprecated. Use `jira_mcp_server_v2.py`.
