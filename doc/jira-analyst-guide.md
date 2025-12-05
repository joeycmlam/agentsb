# JIRA Analyst Bot - User Guide

## Overview

The JIRA Analyst Bot is an intelligent agent that reads JIRA projects and provides comprehensive analysis including:

- 📊 Project health metrics
- 📈 Ticket distribution and trends
- ⚠️ Risk assessment and blockers
- 💎 Quality evaluation
- 👥 Team workload analysis
- 🎯 Actionable recommendations

## Quick Start

### Prerequisites

1. **JIRA Account** with API access
2. **Python 3.7+** installed
3. **JIRA API Token** ([How to get one](https://id.atlassian.com/manage-profile/security/api-tokens))

### Installation

```bash
# Install required Python package
pip3 install jira

# Or use requirements.txt if available
pip3 install -r requirements.txt
```

### Configuration

Set your JIRA credentials as environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc for persistence
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your@email.com"
export JIRA_API_TOKEN="your_api_token_here"
```

**Security Note:** Never commit credentials to Git. Use `.env` file or environment variables.

## Usage

### Method 1: Using the Shell Script (Recommended)

```bash
# Basic usage - analyze a project
./script/analyze-jira.sh PROJ

# Specify custom output file
./script/analyze-jira.sh PROJ my-analysis.md

# The script will:
# - Validate credentials
# - Install dependencies if needed
# - Run analysis
# - Save report with timestamp
```

### Method 2: Direct Python Execution

```bash
# Analyze project and print to console
python3 src/jira_analyst.py PROJ

# Save to specific file
python3 src/jira_analyst.py PROJ output/report.md
```

### Method 3: Using GitHub Copilot CLI Agent

```bash
# Use the JIRA Analyst agent through Copilot CLI
gh copilot --agent=jira-analyst \
  --prompt "Analyze JIRA project PROJ and provide insights"
```

## Sample Output

The bot generates a comprehensive markdown report with:

```markdown
# JIRA Project Analysis: PROJ

## Executive Summary
- Total Tickets: 150
- Completed: 90 (60%)
- Health Score: 7.5/10

## Ticket Distribution
- By Status: To Do (30), In Progress (30), Done (90)
- By Type: Story (80), Bug (40), Task (30)
- By Priority: High (20), Medium (80), Low (50)

## Risks & Issues
- 5 Overdue tickets requiring attention
- 3 Blocker priority items
- 12 Stale tickets (not updated in 30+ days)

## Quality Assessment
- 120 well-defined tickets
- 15 missing acceptance criteria
- 15 need better descriptions

## Team Insights
- Team Members: 8
- Top Contributor: John Doe (45 tickets)
- Workload distribution: Balanced

## Recommendations
1. Address 3 blocker tickets immediately
2. Add acceptance criteria to 15 tickets
3. Review 12 stale tickets
...
```

## Analysis Features

### 1. Project Health Metrics

Provides overall health score (0-10) based on:
- Ticket completion rate
- Quality of documentation
- Bug-to-feature ratio
- Overdue and blocked items

### 2. Ticket Distribution Analysis

**By Status:**
- Open/To Do
- In Progress
- Done/Closed
- Custom statuses

**By Type:**
- Story
- Bug
- Task
- Epic
- Sub-task

**By Priority:**
- Blocker/Highest
- Critical/High
- Medium
- Low

### 3. Risk Assessment

Identifies:
- **Overdue tickets** - Past due date and still open
- **Blockers** - Highest priority items
- **Stale tickets** - Not updated in 30+ days
- **Missing information** - Incomplete descriptions
- **High priority backlog** - Critical items not started

### 4. Quality Evaluation

Measures:
- Completeness of ticket descriptions
- Presence of acceptance criteria
- Documentation quality
- Comment activity
- Ticket definition standards

### 5. Team Workload Analysis

Analyzes:
- Distribution of work across team members
- Individual workload (open, in progress, done)
- Top contributors and reporters
- Unassigned ticket count
- Workload balance

### 6. Trend Analysis

Tracks:
- Ticket creation over time
- Bug vs feature ratio
- Resolution patterns
- Sprint velocity indicators
- Seasonal patterns

## Advanced Usage

### Filtering by Sprint

```python
# In src/jira_analyst.py, modify the JQL query:
jql = f'project={project_key} AND sprint="Sprint 10"'
```

### Analyzing Specific Issue Types

```bash
# For bugs only (modify jira_analyst.py):
jql = f'project={project_key} AND type=Bug'
```

### Custom Date Ranges

```python
# Last 30 days only:
jql = f'project={project_key} AND created >= -30d'
```

### Export to JSON

```python
# Add to jira_analyst.py:
import json
with open('analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)
```

## Integration with Workflow

### Automated Weekly Analysis

Create a cron job or GitHub Action:

```bash
# crontab -e
0 9 * * MON cd /path/to/agentsb && ./script/analyze-jira.sh PROJ weekly-report.md
```

### GitHub Actions Integration

```yaml
# .github/workflows/jira-analysis.yml
name: Weekly JIRA Analysis

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install jira
      
      - name: Run Analysis
        env:
          JIRA_USER: ${{ secrets.JIRA_USER }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
        run: ./script/analyze-jira.sh PROJ
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: jira-analysis
          path: jira-analysis-*.md
```

### Slack Notifications

Add to analysis script:

```bash
# Send to Slack after analysis
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"JIRA Analysis Complete: $OUTPUT_FILE\"}" \
  $SLACK_WEBHOOK_URL
```

## Troubleshooting

### Authentication Issues

```
❌ Error: JIRA credentials not provided
```

**Solution:** Ensure environment variables are set:
```bash
echo $JIRA_USER
echo $JIRA_API_TOKEN
```

### Connection Errors

```
❌ Error: Cannot connect to JIRA
```

**Solutions:**
1. Check JIRA URL is correct (include https://)
2. Verify API token is still valid
3. Check network/firewall settings
4. Ensure JIRA Cloud vs Server URL format

### No Issues Found

```
⚠️ No issues found in project PROJ
```

**Solutions:**
1. Verify project key is correct (case-sensitive)
2. Check user has permission to view project
3. Confirm project exists and has issues

### Rate Limiting

```
❌ Error: Rate limit exceeded
```

**Solution:** JIRA API has rate limits. Wait and retry, or reduce `maxResults`.

### Import Errors

```
ModuleNotFoundError: No module named 'jira'
```

**Solution:**
```bash
pip3 install jira
```

## Best Practices

### 1. Regular Analysis

Run analysis weekly or bi-weekly to:
- Track progress trends
- Identify issues early
- Maintain project health

### 2. Actionable Insights

Focus on:
- High-priority blockers first
- Quality improvements for future tickets
- Workload balancing across team

### 3. Team Collaboration

- Share reports with team in stand-ups
- Discuss recommendations in retrospectives
- Use insights for sprint planning

### 4. Customize for Your Needs

Modify the bot to:
- Add custom fields analysis
- Include team-specific metrics
- Adjust quality criteria
- Add visualization generation

### 5. Version Control Reports

```bash
# Save reports in a dedicated directory
mkdir -p reports/jira-analysis
./script/analyze-jira.sh PROJ reports/jira-analysis/$(date +%Y-%m-%d).md

# Commit to Git for historical tracking
git add reports/
git commit -m "Add JIRA analysis for $(date +%Y-%m-%d)"
```

## Customization Guide

### Adding Custom Metrics

Edit `src/jira_analyst.py`:

```python
def _analyze_custom_metrics(self, issues):
    """Add your custom analysis"""
    # Example: Track story points
    total_points = sum(
        int(issue.fields.customfield_10016 or 0) 
        for issue in issues
    )
    return {'total_story_points': total_points}
```

### Custom Report Format

Modify `_generate_report()` method to:
- Change markdown formatting
- Add charts/graphs
- Export to HTML/PDF
- Include custom sections

### Integration with Other Tools

```python
# Send to Confluence
from atlassian import Confluence
confluence = Confluence(url=CONF_URL, username=USER, password=TOKEN)
confluence.create_page(space='DOCS', title='JIRA Analysis', body=report)

# Send via email
import smtplib
# ... email sending logic
```

## API Reference

### JiraAnalyst Class

```python
from jira_analyst import JiraAnalyst

# Initialize
analyst = JiraAnalyst(
    server='https://your.atlassian.net',
    user='your@email.com',
    token='your_token'
)

# Analyze project
report = analyst.analyze_project('PROJ', max_results=1000)

# Individual analysis methods
overview = analyst._analyze_overview(issues)
distribution = analyst._analyze_distribution(issues)
quality = analyst._analyze_quality(issues)
risks = analyst._analyze_risks(issues)
team = analyst._analyze_team(issues)
trends = analyst._analyze_trends(issues)
```

## Support & Contributing

### Getting Help

1. Check this documentation
2. Review error messages carefully
3. Check JIRA API documentation
4. Open an issue in the repository

### Contributing

Contributions welcome! Areas for improvement:
- Additional analysis metrics
- Visualization generation
- Export formats (PDF, HTML)
- Integration with more tools
- Performance optimizations

## Security Considerations

### Credential Management

✅ **DO:**
- Use environment variables
- Use `.env` files (gitignored)
- Use secret management tools
- Rotate tokens regularly

❌ **DON'T:**
- Commit credentials to Git
- Share tokens in chat/email
- Use production credentials for testing
- Hard-code credentials in scripts

### Data Privacy

- Be mindful of sensitive information in tickets
- Don't share reports publicly without review
- Respect team member privacy
- Follow company data policies

## License

This tool is part of the agentsb project. See main LICENSE file for details.

---

**Last Updated:** December 2025  
**Version:** 1.0.0  
**Maintainer:** Joey Lam
