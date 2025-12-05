# JIRA Analyst Bot 🔍

An intelligent agent that analyzes JIRA projects and provides comprehensive insights on project health, risks, quality, and team performance.

## 🚀 Quick Start

### 1. Set up credentials

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your@email.com"
export JIRA_API_TOKEN="your_api_token"
```

### 2. Run analysis

```bash
# Using the shell script (easiest)
./script/analyze-jira.sh YOUR_PROJECT_KEY

# Or directly with Python
python3 src/jira_analyst.py YOUR_PROJECT_KEY report.md
```

### 3. View the report

A comprehensive markdown report will be generated with:
- 📊 Project health metrics
- 📈 Ticket distribution (status, type, priority)
- ⚠️ Risks and blockers
- 💎 Quality assessment
- 👥 Team workload analysis
- 🎯 Actionable recommendations

## 📋 What It Analyzes

### Health Metrics
- Overall project health score (0-10)
- Completion rates
- Bug-to-feature ratio
- Quality indicators

### Ticket Distribution
- Status breakdown (To Do, In Progress, Done, etc.)
- Type distribution (Story, Bug, Task, Epic)
- Priority levels (Blocker, High, Medium, Low)

### Risk Assessment
- ⚠️ Overdue tickets
- 🚫 Blocker/Highest priority items
- 📅 Stale tickets (not updated in 30+ days)
- 🔍 Missing information

### Quality Evaluation
- Ticket description completeness
- Acceptance criteria presence
- Documentation quality
- Definition standards compliance

### Team Insights
- Workload distribution
- Top contributors
- Unassigned tickets
- Collaboration metrics

### Trend Analysis
- Ticket creation patterns
- Bug trends over time
- Resolution patterns
- Sprint velocity indicators

## 📁 Files Created

```
agentsb/
├── .github/agents/
│   └── jira-analyst.agent.md      # Agent definition for Copilot CLI
├── src/
│   └── jira_analyst.py             # Main analysis script
├── script/
│   └── analyze-jira.sh             # Convenience shell script
├── doc/
│   └── jira-analyst-guide.md       # Comprehensive user guide
└── README-JIRA-ANALYST.md          # This file
```

## 🔧 Advanced Usage

### Analyze Specific Sprints

Modify the JQL query in `jira_analyst.py`:

```python
jql = f'project={project_key} AND sprint="Sprint 10"'
```

### Automated Weekly Reports

Set up a cron job:

```bash
0 9 * * MON /path/to/analyze-jira.sh PROJ >> /var/log/jira-analysis.log
```

### GitHub Actions Integration

Use the workflow template in `doc/jira-analyst-guide.md` to:
- Schedule weekly analysis
- Automatically commit reports
- Send notifications

### Use with GitHub Copilot CLI

```bash
gh copilot --agent=jira-analyst \
  --prompt "Analyze project PROJ and identify critical issues"
```

## 📊 Sample Output

```markdown
# JIRA Project Analysis: PROJ

**Analysis Date:** 2025-12-05
**Total Tickets:** 150

## 📊 Executive Summary

### Health Score: 7.5/10

### Key Metrics
- Total Tickets: 150
- Completed: 90 (60.0%)
- In Progress: 30
- To Do: 30
- Bug Ratio: 26.7%
- Health Status: Good

## ⚠️ Risks & Issues

### Critical Items
- 3 Blocker/Highest Priority tickets found
- 5 Overdue tickets
- 12 Stale tickets (not updated in 30+ days)

## 💎 Quality Assessment
- Well-Defined Tickets: 120
- Missing Acceptance Criteria: 15
- Quality Score: 8.0/10

## 👥 Team Insights
- Team Members: 8
- Top Contributors showing balanced workload

## 🎯 Recommendations
1. Address 3 blocker tickets immediately
2. Review 5 overdue tickets and update timelines
3. Add acceptance criteria to 15 tickets
...
```

## 🛠️ Troubleshooting

### "JIRA credentials not provided"
```bash
# Ensure environment variables are set
export JIRA_USER="your@email.com"
export JIRA_API_TOKEN="your_token"
```

### "No issues found"
- Verify project key is correct (case-sensitive)
- Check user permissions for the project
- Ensure project exists

### "Module not found: jira"
```bash
pip3 install jira
```

## 📚 Documentation

See `doc/jira-analyst-guide.md` for:
- Detailed usage instructions
- Customization guide
- Integration examples
- API reference
- Security best practices

## 🎯 Use Cases

### Sprint Planning
- Analyze backlog health
- Identify technical debt
- Balance workload

### Retrospectives
- Review completed work
- Identify bottlenecks
- Track improvement trends

### Project Health Checks
- Executive summaries
- Risk identification
- Quality monitoring

### Team Management
- Workload balancing
- Productivity insights
- Collaboration metrics

## 🔒 Security

- Never commit credentials to Git
- Use environment variables or `.env` files
- Rotate API tokens regularly
- Review reports before sharing publicly

## 🤝 Integration

Works with:
- ✅ GitHub Copilot CLI (as custom agent)
- ✅ GitHub Actions (automated analysis)
- ✅ Slack (notifications)
- ✅ Confluence (publish reports)
- ✅ Email (send summaries)

## 📈 Roadmap

Future enhancements:
- [ ] Visualization generation (charts/graphs)
- [ ] PDF export
- [ ] HTML dashboard
- [ ] Real-time monitoring
- [ ] Predictive analytics
- [ ] Custom field analysis
- [ ] Comparison reports (sprint over sprint)
- [ ] Integration with more tools

## 🙏 Contributing

Contributions welcome! Areas for improvement:
- Additional metrics
- Better visualization
- Performance optimization
- New integrations
- Documentation improvements

## 📄 License

Part of the agentsb project. See LICENSE for details.

---

**Created:** December 2025  
**Author:** Joey Lam  
**Version:** 1.0.0

## 🎓 Example Commands

```bash
# Basic analysis
./script/analyze-jira.sh MYPROJECT

# Save to custom location
./script/analyze-jira.sh MYPROJECT reports/analysis.md

# Analyze and auto-open report (macOS)
./script/analyze-jira.sh MYPROJECT && open jira-analysis-*.md

# Use with specific project
python3 src/jira_analyst.py WEBTEAM team-report.md

# Chain with Git commit
./script/analyze-jira.sh PROJ reports/$(date +%Y%m%d).md && \
  git add reports/ && \
  git commit -m "Add JIRA analysis $(date +%Y-%m-%d)"
```

## 🌟 Key Features

- ✅ **Zero configuration** - Uses environment variables
- ✅ **Comprehensive analysis** - 6 different analysis dimensions
- ✅ **Actionable insights** - Clear recommendations
- ✅ **Beautiful reports** - Well-formatted markdown
- ✅ **Fast execution** - Analyzes 1000+ tickets in seconds
- ✅ **Customizable** - Easy to extend and modify
- ✅ **Secure** - No credential storage in code
- ✅ **Integration ready** - Works with CI/CD, Slack, etc.

---

**Need help?** Check `doc/jira-analyst-guide.md` or open an issue!
