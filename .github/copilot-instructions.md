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
├── document_converter.py     # Document format conversion (PDF, Word, Excel, etc.)
├── cli.py                    # CLI terminal formatting & commands
└── utils.py                  # Environment validation & arg parsing
```

**Key Architectural Decision**: Each module has a single responsibility. When modifying JIRA API interactions, edit `jira_client.py`. For MCP tool definitions, edit `mcp_server.py`. For document conversion, edit `document_converter.py`. Never mix concerns.

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

### 5. Document Reading & Conversion

The server provides powerful document reading capabilities through `document_converter.py` using the MarkItDown library. This allows AI agents to read and understand various document formats.

**Supported Document Formats:**
- **PDF** - Portable Document Format
- **Word** - `.docx`, `.doc` (Microsoft Word)
- **Excel** - `.xlsx`, `.xls` (spreadsheets)
- **PowerPoint** - `.pptx`, `.ppt` (presentations)
- **Images** - `.jpg`, `.png`, `.bmp`, `.gif` (with OCR capabilities)
- **Web** - `.html`, `.htm`
- **Data** - `.csv`, `.json`, `.xml`
- **Text** - `.txt`, `.md`, `.log`

**Two Document Reading Modes:**

1. **JIRA Attachment Reading** (`jira_read_attachment_content`):
   - Reads attachments directly from JIRA issues
   - Downloads and converts on-the-fly
   - Returns markdown-formatted content
   - Ideal for analyzing requirements, specs, mockups attached to tickets

2. **Local File Reading** (`read_file`):
   - Reads any local file from the filesystem
   - Standalone document conversion service
   - Works independently of JIRA
   - Useful for analyzing local documentation, reports, designs

**Document Converter Pattern:**
```python
# In document_converter.py
class DocumentConverter:
    def convert_to_markdown(self, file_source: Union[str, Path, BinaryIO], 
                          file_extension: Optional[str] = None) -> str:
        """
        Convert document to markdown using MarkItDown.
        
        Args:
            file_source: File path, Path object, or binary stream
            file_extension: Optional extension hint for binary streams
        
        Returns:
            Markdown-formatted text content
        """
```

**Usage in MCP Tools:**
```python
# Read JIRA attachment
async def _tool_read_attachment_content(self, arguments: dict) -> dict:
    result = await self.jira_client.read_attachment_content(
        issue_key=arguments["issue_key"],
        filename=arguments["filename"],
        attachment_id=arguments.get("attachment_id")
    )
    return result

# Read local file
async def _tool_read_file(self, arguments: dict) -> dict:
    converter = get_converter()
    markdown = await converter.convert_to_markdown_async(
        file_path=arguments["file_path"]
    )
    return {
        "file_path": arguments["file_path"],
        "content": markdown,
        "format": "markdown"
    }
```

**Graceful Fallback:**
If MarkItDown library is not installed, document conversion features are disabled gracefully. The server still functions for JIRA operations, but document reading tools return appropriate error messages.

**Installation:**
```bash
# Install with document conversion support
pip install markitdown

# Optional: For enhanced image OCR
pip install pytesseract
```

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
- `markitdown>=0.1.0` - Document conversion to markdown (PDF, Word, Excel, etc.)
- `deepdiff>=6.0.0` - Not actively used in core modules (legacy?)

**Optional Dependencies for Enhanced Features:**
- `pytesseract` - OCR for images (improves image-to-text extraction)
- `Pillow` - Image processing (usually included with markitdown)

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

### Document Conversion Service

The `document_converter.py` module uses MarkItDown library to convert various document formats to markdown:

**Conversion Flow:**
1. Accept file input (path, Path object, or binary stream)
2. Detect file type from extension or MIME type
3. Use appropriate converter (PDF, Word, Excel, etc.)
4. Extract text, tables, images (with OCR if available)
5. Return markdown-formatted content

**Async Wrapper:**
```python
async def convert_to_markdown_async(self, file_path: Union[str, Path]) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: self.convert_to_markdown(file_path)
    )
```

**Integration with JIRA Client:**
The `JiraClientAsync` class integrates document conversion to provide seamless attachment reading:
```python
async def read_attachment_content(self, issue_key: str, filename: str, 
                                  attachment_id: Optional[str] = None) -> dict:
    # 1. Download attachment binary
    # 2. Convert to markdown using DocumentConverter
    # 3. Return structured result with content and metadata
```

## Agent Ecosystem

The `.github/agents/` directory contains role-specific agent definitions:
- `developer.agent.md` - Full-cycle development with TDD, includes JIRA integration workflows
## Common Pitfalls

1. **Forgetting ADF format**: Always use `_create_description_payload()` and `_create_comment_payload()`
2. **Blocking async**: Wrap `requests` calls in `run_in_executor()`
3. **Missing env validation**: CLI mode calls `validate_environment()` - don't skip this
4. **Hardcoded URLs**: Use `self.url` from client initialization
5. **Large files**: Use `UPLOAD_TIMEOUT` (60s) instead of `DEFAULT_TIMEOUT` (30s) for attachments
6. **Document conversion errors**: Check if MarkItDown is installed before attempting conversions
7. **Binary vs text mode**: Always open files in binary mode (`'rb'`) when reading for conversion
8. **Large document memory**: Document conversion loads entire file into memory - be mindful of file sizes
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
