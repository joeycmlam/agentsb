# JIRA Helper Tool

A simple Python command-line tool to interact with JIRA - read issue details and add comments.

## Prerequisites

- Python 3.6 or higher
- `requests` library (`pip install requests`)
- JIRA account with API token

## Setup

1. Set the following environment variables:

```bash
export JIRA_URL="https://your-domain.atlassian.net/"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or create a `.env` file with:

```bash
JIRA_URL="https://your-domain.atlassian.net/"
JIRA_USER="your-email@example.com"
JIRA_API_TOKEN="your-api-token"
```

Then source it: `source .env`

### Getting a JIRA API Token

1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and click "Create"
4. Copy the token immediately (it won't be shown again)

## Usage

### Read JIRA Issue Details

```bash
python3 jira_help.py [JIRA-NUMBER]
```

**Example:**
```bash
python3 jira_help.py SCRUM-1
```

**Output:**
```
Fetching details for SCRUM-1...

============================================================
JIRA Issue: SCRUM-1
============================================================
Summary:     Task 1
Type:        Task
Status:      To Do
Priority:    Medium
Assignee:    John Doe
Reporter:    Jane Smith
Created:     2025-11-07T23:38:17.670+0800
Updated:     2025-11-07T23:38:20.557+0800

Description:
    This is the task description...
============================================================
```

### Add Comment to JIRA Issue

```bash
python3 jira_help.py [JIRA-NUMBER] [update-info]
```

**Example:**
```bash
python3 jira_help.py SCRUM-1 "This is my comment"
```

**Multi-word comments:**
```bash
python3 jira_help.py SCRUM-1 "This is a longer comment with multiple words"
```

**Output:**
```
Adding comment to SCRUM-1...
✓ Comment added successfully to SCRUM-1
```

## Features

- **Read Issue Details**: Fetches and displays key information about a JIRA issue including summary, type, status, priority, assignee, reporter, dates, and description
- **Add Comments**: Adds text comments to JIRA issues
- **Error Handling**: Provides clear error messages for authentication failures, missing issues, and connection problems
- **Environment Variables**: Securely manages credentials through environment variables

## Error Handling

The tool provides helpful error messages:

- **Issue not found**: `Error: Issue 'PROJ-123' not found`
- **Authentication failed**: `Error: Authentication failed. Check your credentials.`
- **Connection issues**: `Error: Failed to connect to JIRA - [details]`
- **Missing credentials**: `Error: Missing JIRA credentials in environment variables.`

## Technical Details

- Uses JIRA REST API v3
- Supports JIRA Cloud instances
- Handles Atlassian Document Format (ADF) for comments
- Timeout: 30 seconds per request

## Troubleshooting

1. **Authentication errors**: Verify your API token is correct and hasn't expired
2. **Issue not found**: Check the issue key format (e.g., PROJECT-123)
3. **Connection timeout**: Check your internet connection and JIRA URL
4. **Missing fields**: Some fields may show "N/A" if not set in JIRA

## License

Free to use and modify.
