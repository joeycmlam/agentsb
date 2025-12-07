# JIRA MCP Server - Refactored Structure

The original monolithic `jira_mcp_server.py` file has been successfully split into multiple modules for better organization and maintainability:

## New File Structure

### Core Modules
- **`jira_client.py`** - Async JIRA API client with all HTTP operations
- **`mcp_server.py`** - MCP server implementation with tool handlers
- **`cli.py`** - Command-line interface functions
- **`utils.py`** - Utility functions (validation, argument parsing)

### Main Entry Point
- **`jira_mcp_server.py`** - Simplified main file that imports and orchestrates the modules

## Benefits of This Refactoring

1. **Modularity**: Each module has a single responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Testability**: Individual modules can be tested in isolation
4. **Readability**: Smaller files are easier to understand
5. **Reusability**: Modules can be imported independently if needed

## File Responsibilities

- `jira_client.py`: All JIRA API interactions (get, update, search, attachments)
- `mcp_server.py`: MCP protocol handling and tool definitions
- `cli.py`: Terminal output formatting and CLI command execution
- `utils.py`: Environment validation and command-line argument parsing
- `jira_mcp_server.py`: Application entry point and mode routing

## Usage

The functionality remains exactly the same. You can run:

```bash
# MCP server mode (default)
python3 jira_mcp_server.py

# CLI mode
python3 jira_mcp_server.py cli get-issue PROJ-123
```

All existing features and command-line options are preserved.