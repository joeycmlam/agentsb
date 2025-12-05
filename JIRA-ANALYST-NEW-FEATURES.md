# JIRA Analyst - New Features Quick Start

## Two New Features for BA Agent

### Feature 1: Read JIRA Ticket
Pass in the JIRA number to read it from the JIRA project so that the agent can provide analysis.

**Command Line:**
```bash
# Human-readable format
python src/jira_analyst.py --issue PROJ-123

# JSON format (for programmatic use)
python src/jira_analyst.py --issue PROJ-123 --json
```

**Python API:**
```python
from jira_analyst import JiraAnalyst

analyst = JiraAnalyst()
issue_data = analyst.get_issue('PROJ-123')

print(f"Title: {issue_data['summary']}")
print(f"Description: {issue_data['description']}")
print(f"Status: {issue_data['status']}")
```

**What You Get:**
- Issue key, summary, description
- Status, priority, type
- Assignee, reporter
- Created/updated dates
- Labels, components, versions
- Comments, subtasks, linked issues

### Feature 2: Update JIRA Ticket
Allow BA agent to update the JIRA ticket in the JIRA project with its analysis.

**Command Line:**
```bash
# Simple comment
python src/jira_analyst.py --update PROJ-123 --comment "Analysis complete"

# Multi-line analysis
python src/jira_analyst.py --update PROJ-123 --comment "
## Business Analysis

### Assumptions:
1. Users must authenticate first
2. Data validated server-side

### Next Steps:
- Create feature file
- Review with stakeholders
"
```

**Python API:**
```python
from jira_analyst import JiraAnalyst

analyst = JiraAnalyst()

analysis = """
## BA Analysis Complete

### Business Assumptions:
1. System operates 24/7
2. API rate limit: 100 req/min

### Feature File:
features/PROJ-123-checkout.feature
"""

result = analyst.update_issue_with_analysis(
    'PROJ-123',
    analysis,
    comment_prefix="BA Analysis"
)

if result['success']:
    print("✅ Updated successfully")
```

## Complete BA Workflow Example

```bash
#!/bin/bash
ISSUE_KEY="PROJ-123"

# Step 1: Read the ticket
echo "Reading ticket $ISSUE_KEY..."
python src/jira_analyst.py --issue $ISSUE_KEY --json > ticket.json

# Step 2: Extract key information (example with jq)
SUMMARY=$(jq -r '.summary' ticket.json)
DESCRIPTION=$(jq -r '.description' ticket.json)

echo "Ticket: $SUMMARY"

# Step 3: Generate analysis
cat > analysis.md << EOF
## Business Analysis for $ISSUE_KEY

### Summary
$SUMMARY

### Business Assumptions:
1. User authentication is required
2. Input validation on client and server
3. Real-time data synchronization
4. API versioning follows semantic versioning

### Cucumber Scenarios Created:
See features/$ISSUE_KEY-feature.feature

### Recommendations:
- Add integration tests
- Document API endpoints
- Review security requirements

---
*Analysis by BA Agent*
EOF

# Step 4: Update JIRA
echo "Updating ticket with analysis..."
python src/jira_analyst.py --update $ISSUE_KEY --comment "$(cat analysis.md)"

# Step 5: Create feature file
mkdir -p features
cat > features/$ISSUE_KEY-feature.feature << 'EOF'
Feature: User Authentication
  As a user
  I want to log in securely
  So that I can access my account

  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should be logged in
EOF

# Step 6: Commit and push
git checkout -b feat/$ISSUE_KEY-requirements
git add features/$ISSUE_KEY-feature.feature analysis.md
git commit -m "feat($ISSUE_KEY): Add BA analysis and scenarios"
git push origin feat/$ISSUE_KEY-requirements

# Step 7: Create PR
gh pr create \
  --title "$ISSUE_KEY: Requirements Analysis" \
  --body "Business analysis complete. See analysis.md for assumptions and features/ for Cucumber scenarios."

echo "✅ Workflow complete!"
```

## Environment Setup

Before using these features, set up JIRA credentials:

```bash
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_USER="your.email@company.com"
export JIRA_API_TOKEN="your-api-token"
```

## Integration with BA Agent

The BA agent (`.github/agents/ba.agent.md`) can now:

1. ✅ **Read JIRA tickets** - Extract requirements, acceptance criteria, links
2. ✅ **Update JIRA tickets** - Add business assumptions and analysis
3. ✅ **Generate feature files** - Create Cucumber scenarios
4. ✅ **Create PRs** - Document requirements in version control

## Error Handling

If credentials are missing:
```
ValueError: JIRA credentials not provided. Set JIRA_USER and JIRA_API_TOKEN environment variables.
```

If issue doesn't exist:
```
❌ Error reading issue PROJ-999: Issue does not exist or you do not have permission to see it.
```

## More Information

- Full API documentation: `README-JIRA-ANALYST-API.md`
- Example script: `src/ba_agent_example.py`
- Enhancement details: `ENHANCEMENT-SUMMARY.md`
- BA Agent workflow: `.github/agents/ba.agent.md`

## Quick Test

Test the features work:

```bash
# Check help (should show new options)
python src/jira_analyst.py

# Test syntax
python3 -m py_compile src/jira_analyst.py

# Run example (requires valid credentials and issue key)
python src/ba_agent_example.py PROJ-123
```

---

**Status:** ✅ Enhancement Complete

Both requested features are now implemented and ready for use by the BA Agent.
