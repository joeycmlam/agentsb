# JIRA Analyst API Documentation

Enhanced `jira_analyst.py` with support for reading individual issues and updating them with analysis.

## Features

### 1. Read Individual JIRA Issues
Retrieve detailed information about a specific JIRA ticket including description, comments, links, and metadata.

### 2. Update JIRA Issues
Add analysis comments to JIRA tickets programmatically.

### 3. Project Analysis
Comprehensive analysis of entire JIRA projects (original feature).

## Command-Line Usage

### Read a JIRA Issue

**Human-readable format:**
```bash
python src/jira_analyst.py --issue PROJ-123
```

**JSON format (for parsing):**
```bash
python src/jira_analyst.py --issue PROJ-123 --json
```

**JSON output structure:**
```json
{
  "key": "PROJ-123",
  "summary": "Issue title",
  "description": "Full description text",
  "status": "In Progress",
  "priority": "High",
  "issue_type": "Story",
  "assignee": "John Doe",
  "reporter": "Jane Smith",
  "created": "2024-01-01T10:00:00.000+0000",
  "updated": "2024-01-15T14:30:00.000+0000",
  "due_date": "2024-02-01",
  "labels": ["backend", "api"],
  "components": ["Authentication"],
  "fix_versions": ["v1.2.0"],
  "comments": [...],
  "subtasks": [...],
  "links": [...]
}
```

### Update a JIRA Issue

**Single-line comment:**
```bash
python src/jira_analyst.py --update PROJ-123 --comment "Analysis complete"
```

**Multi-line comment from file:**
```bash
python src/jira_analyst.py --update PROJ-123 --comment "$(cat analysis.txt)"
```

**Multi-line comment via stdin:**
```bash
cat analysis.txt | python src/jira_analyst.py --update PROJ-123
```

### Analyze Entire Project

```bash
python src/jira_analyst.py PROJECT_KEY [output_file.md]
```

## Programmatic API Usage

### Python API

```python
from jira_analyst import JiraAnalyst

# Initialize
analyst = JiraAnalyst()

# Read an issue
issue_data = analyst.get_issue('PROJ-123')
print(f"Summary: {issue_data['summary']}")
print(f"Description: {issue_data['description']}")
print(f"Status: {issue_data['status']}")

# Update an issue
analysis_text = """
## Business Analysis

### Assumptions:
1. Users must be authenticated
2. Data is validated server-side

### Recommendations:
- Add unit tests
- Update documentation
"""

result = analyst.update_issue_with_analysis(
    'PROJ-123',
    analysis_text,
    comment_prefix="BA Analysis"
)

if result['success']:
    print(f"Updated {result['issue_key']}")
else:
    print(f"Error: {result['error']}")

# Analyze project
report = analyst.analyze_project('PROJ')
print(report)
```

## BA Agent Integration

The enhanced features are designed for the BA Agent workflow:

### Workflow Steps

1. **Read JIRA Ticket**
   ```bash
   python src/jira_analyst.py --issue PROJ-123 --json > ticket.json
   ```

2. **Analyze Requirements**
   - Extract business requirements
   - Identify assumptions
   - List edge cases

3. **Generate Cucumber Scenarios**
   - Create feature files
   - Write test scenarios

4. **Update JIRA**
   ```bash
   python src/jira_analyst.py --update PROJ-123 --comment "
   ## BA Analysis Complete
   
   ### Assumptions:
   - User authentication required
   - Real-time inventory checks
   
   ### Feature File:
   features/PROJ-123-checkout.feature
   "
   ```

## Environment Setup

Required environment variables:
```bash
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USER="your.email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

## Return Values

### get_issue()
Returns a dictionary with:
- `key`: Issue key (e.g., "PROJ-123")
- `summary`: Issue title
- `description`: Full description text
- `status`: Current status
- `priority`: Priority level
- `issue_type`: Type (Story, Bug, etc.)
- `assignee`: Assigned person
- `reporter`: Reporter name
- `created`: Creation timestamp
- `updated`: Last update timestamp
- `due_date`: Due date (if set)
- `labels`: List of labels
- `components`: List of components
- `fix_versions`: Target versions
- `comments`: List of comment objects
- `subtasks`: List of subtask objects
- `links`: List of linked issues

### update_issue_with_analysis()
Returns a dictionary with:
- `success`: Boolean success flag
- `issue_key`: The issue key
- `message`: Success message (if success=True)
- `error`: Error message (if success=False)

## Error Handling

All methods handle errors gracefully:
- Missing credentials → ValueError
- Invalid issue key → Exception with details
- API errors → Exception with error message

## Examples

See `src/ba_agent_example.py` for a complete workflow example:
```bash
python src/ba_agent_example.py PROJ-123
```

## Dependencies

- `jira` - Python JIRA library
- Environment variables for authentication

## See Also

- [BA Agent Documentation](.github/agents/ba.agent.md)
- [JIRA Analyst Summary](JIRA-ANALYST-SUMMARY.md)
- [JIRA Analyst Quick Reference](JIRA-ANALYST-QUICKREF.md)
