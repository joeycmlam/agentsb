#!/bin/bash
# Launcher script for JIRA MCP Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting JIRA MCP Server..."
echo ""

# Check environment variables
if [ -z "$JIRA_URL" ] || [ -z "$JIRA_USER" ] || [ -z "$JIRA_API_TOKEN" ]; then
    echo "Error: Missing JIRA credentials"
    echo ""
    echo "Please set environment variables:"
    echo "  export JIRA_URL='https://your-domain.atlassian.net'"
    echo "  export JIRA_USER='your-email@example.com'"
    echo "  export JIRA_API_TOKEN='your-api-token'"
    echo ""
    exit 1
fi

echo "Configuration:"
echo "  JIRA URL: $JIRA_URL"
echo "  JIRA User: $JIRA_USER"
echo "  API Token: ${JIRA_API_TOKEN:0:4}****"
echo ""
echo "Server ready. Waiting for MCP client connections..."
echo "(Press Ctrl+C to stop)"
echo ""

# Start the server
exec python3 "$PROJECT_ROOT/src/jira_mcp_server.py"
