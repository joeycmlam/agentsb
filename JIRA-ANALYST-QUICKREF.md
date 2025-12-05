# JIRA Analyst Bot - Quick Reference Card

## 🚀 Quick Commands

```bash
# Analyze any JIRA project
./script/analyze-jira.sh <PROJECT_KEY>

# Save to custom file
./script/analyze-jira.sh <PROJECT_KEY> my-report.md

# Test connection
python3 src/test_jira_connection.py

# Use with Python directly
python3 src/jira_analyst.py <PROJECT_KEY> [output_file]
```

## 📋 Prerequisites

```bash
# Set credentials (one-time setup)
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your@email.com"
export JIRA_API_TOKEN="your_token"

# Or add to ~/.bashrc or ~/.zshrc for persistence
```

## 📊 What It Analyzes

| Category | What It Checks |
|----------|----------------|
| **Health** | Overall score, completion rate, bug ratio |
| **Distribution** | Status, type, priority breakdown |
| **Risks** | Overdue, blockers, stale tickets |
| **Quality** | Descriptions, acceptance criteria |
| **Team** | Workload, contributors, assignments |
| **Trends** | Creation patterns, bug trends |

## 📝 Report Sections

1. **Executive Summary** - Health score, key metrics
2. **Ticket Distribution** - Charts by status/type/priority
3. **Risks & Issues** - Critical items requiring attention
4. **Quality Assessment** - Documentation completeness
5. **Team Insights** - Workload and contributions
6. **Trends** - Historical patterns
7. **Recommendations** - Actionable next steps

## 🎯 Common Use Cases

```bash
# Weekly team health check
./script/analyze-jira.sh MYPROJECT weekly-$(date +%Y%m%d).md

# Sprint retrospective data
./script/analyze-jira.sh SPRINT-42 retrospective.md

# Executive summary
./script/analyze-jira.sh PRODUCT exec-summary.md
```

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| Credentials not found | Set JIRA_USER and JIRA_API_TOKEN |
| No issues found | Check project key (case-sensitive) |
| Connection failed | Verify JIRA_URL and token validity |
| Module not found | Run: `pip3 install jira` |

## 📚 Documentation

- **Full Guide:** `doc/jira-analyst-guide.md`
- **Quick Start:** `README-JIRA-ANALYST.md`
- **Summary:** `JIRA-ANALYST-SUMMARY.md`
- **Agent Config:** `.github/agents/jira-analyst.agent.md`

## 💡 Pro Tips

1. **Automate:** Add to cron for weekly reports
2. **Track History:** Commit reports to Git
3. **Share:** Use in stand-ups and retrospectives
4. **Customize:** Modify thresholds in `src/jira_analyst.py`
5. **Integrate:** Connect to Slack, Confluence, etc.

## 🔐 Security Reminders

- Never commit credentials
- Use environment variables
- Rotate tokens regularly
- Review reports before sharing

## 📞 Support

- Check error messages
- Review documentation
- Verify credentials
- Test connection first

---

**Version:** 1.0.0 | **Status:** ✅ Production Ready
