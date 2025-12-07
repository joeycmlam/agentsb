# JIRA MCP Server - Dual Mode Guide

## Overview

The `jira_mcp_server.py` now supports **two operational modes**:

1. **MCP Service Mode** (default): Runs as a Model Context Protocol server for AI agents
2. **Command-Line Mode**: Direct CLI operations for manual JIRA interactions

This eliminates the need for separate `jira_help.py` script while maintaining backward compatibility.

## Architecture Changes

### Before
- `jira_help.py`: Synchronous CLI tool with `JiraClient` class
- `jira_mcp_server.py`: Async MCP server with `JiraClientAsync` class
- Code duplication between the two files

### After
- `jira_mcp_server.py`: Unified solution supporting both modes
- Single `JiraClientAsync` class used for all operations
- CLI mode functions built on top of the async client
- Automatic mode detection based on command-line arguments

## Usage

### MCP Service Mode (Default)

Run without arguments to start the MCP server:

```bash
python3 src/jira_mcp_server.py
```

The server will:
- Listen on stdio for MCP protocol messages
- Expose JIRA operations as tools for AI agents
- Support all MCP tools: `jira_get_issue`, `jira_add_comment`, etc.

### Command-Line Mode

Run with `cli` subcommand for direct operations:

#### Get Issue Details

```bash
# Basic issue details
python3 src/jira_mcp_server.py cli get-issue PROJ-123

# Get issue details and download attachments
python3 src/jira_mcp_server.py cli get-issue PROJ-123 --download
```

#### Add Comment

```bash
python3 src/jira_mcp_server.py cli add-comment PROJ-123 "Bug fixed in commit abc123"
```

#### Upload Attachment

```bash
python3 src/jira_mcp_server.py cli upload-attachment PROJ-123 report.pdf
```

#### Update Description

```bash
python3 src/jira_mcp_server.py cli update-description PROJ-123 "Updated requirements based on feedback"
```

#### Search Issues

```bash
# Basic search
python3 src/jira_mcp_server.py cli search "project = PROJ AND status = Open"

# Limit results
python3 src/jira_mcp_server.py cli search "assignee = currentUser()" --max-results 10
```

## Help

```bash
# General help
python3 src/jira_mcp_server.py --help

# CLI mode help
python3 src/jira_mcp_server.py cli --help

# Specific command help
python3 src/jira_mcp_server.py cli get-issue --help
python3 src/jira_mcp_server.py cli search --help
```

## Environment Variables

Both modes require the same environment variables:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or source the environment script:

```bash
source script/env.sh
```

## Implementation Details

### Mode Detection

The `main()` function automatically detects the mode:

```python
async def main() -> None:
    """Main entry point - routes to MCP server or CLI mode."""
    # No arguments → MCP server mode
    if len(sys.argv) == 1:
        await run_mcp_mode()
        return
    
    # Parse arguments
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Route to appropriate mode
    if args.mode == 'cli':
        await run_cli_mode(args)
    else:
        await run_mcp_mode()
```

### CLI Functions

All CLI commands are async functions that use `JiraClientAsync`:

- `cli_get_issue()` - Fetch and display issue details
- `cli_add_comment()` - Add comment to issue
- `cli_upload_attachment()` - Upload file to issue
- `cli_update_description()` - Update issue description
- `cli_search_issues()` - Search issues with JQL

### Code Organization

```
jira_mcp_server.py
├── Constants (CONTENT_TYPE_JSON, DEFAULT_TIMEOUT, etc.)
├── JiraClientAsync (shared async JIRA client)
├── CLI Mode Functions (cli_get_issue, cli_add_comment, etc.)
├── MCP Server Mode (JiraMcpServer class)
└── Main Entry Point (mode routing)
```

## Benefits

1. **Single Source of Truth**: All JIRA logic in one file
2. **No Code Duplication**: Shared async client for both modes
3. **Consistent Behavior**: Same API interactions in both modes
4. **Easy Maintenance**: Update logic once, applies to both modes
5. **Backward Compatible**: Existing MCP integrations continue working
6. **Developer Friendly**: Direct CLI for testing and debugging

## Migration from jira_help.py

If you were using `jira_help.py`, replace it with the CLI mode:

### Before (jira_help.py)
```bash
python3 src/jira_help.py PROJ-123
python3 src/jira_help.py PROJ-123 --download
python3 src/jira_help.py PROJ-123 "comment text"
```

### After (jira_mcp_server.py CLI mode)
```bash
python3 src/jira_mcp_server.py cli get-issue PROJ-123
python3 src/jira_mcp_server.py cli get-issue PROJ-123 --download
python3 src/jira_mcp_server.py cli add-comment PROJ-123 "comment text"
```

## Testing Both Modes

### Test MCP Mode

```bash
# In one terminal, start the server
python3 src/jira_mcp_server.py

# In another terminal, test with VS Code Copilot or MCP client
# The AI agent should be able to call JIRA tools
```

### Test CLI Mode

```bash
# Get issue
python3 src/jira_mcp_server.py cli get-issue PROJ-123

# Search
python3 src/jira_mcp_server.py cli search "project = PROJ" --max-results 5

# Add comment
python3 src/jira_mcp_server.py cli add-comment PROJ-123 "Test comment from CLI"
```

## Error Handling

Both modes provide consistent error handling:

- **Missing credentials**: Clear error message with instructions
- **Invalid issue key**: HTTP 404 error with context
- **Permission issues**: HTTP 403 error
- **Network errors**: Connection failure messages
- **File not found**: Clear file path error for uploads

## Future Enhancements

Possible additions:
- Batch operations in CLI mode
- Interactive mode with prompts
- Output format options (JSON, table, etc.)
- Configuration file support
- Transition issue status
- Update custom fields
- Manage issue labels and components
