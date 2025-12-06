#!/bin/bash
# Wrapper script to run JIRA MCP Server with environment variables for VS Code

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

load_environment_variables() {
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            if [[ ! "$key" =~ ^#.*$ ]] && [ -n "$key" ]; then
                export "$key=$value"
            fi
        done < "$ENV_FILE"
    fi
    
    if [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc" 2>/dev/null
    elif [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc" 2>/dev/null
    fi
}

load_environment_variables

exec python3 "$PROJECT_ROOT/src/jira_mcp_server.py"
