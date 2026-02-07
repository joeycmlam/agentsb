#!/bin/bash
# Wrapper script to run Repository Analyzer with proper PYTHONPATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env if it exists
if [ -f "$REPO_ROOT/.env" ]; then
    set -a  # Automatically export all variables
    source "$REPO_ROOT/.env"
    set +a  # Disable automatic export
fi

# Add both src (for utils) and src/repo-app directories to PYTHONPATH
export PYTHONPATH="$REPO_ROOT/src/repo-app:$REPO_ROOT/src:$PYTHONPATH"

# Execute the repository analyzer with all passed arguments
python3 "$REPO_ROOT/src/repo-app/repo_analyzer.py" "$@"
