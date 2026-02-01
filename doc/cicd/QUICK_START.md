# Quick Copy-Paste Setup Guide

## 📋 Step-by-Step Copy-Paste Instructions

### Step 1: Create Directory Structure
```bash
# Run this in your repository root
mkdir -p .github/workflows
mkdir -p .copilot
mkdir -p docs/{api,architecture,changelog,examples}
```

### Step 2: Create GitHub Secrets

**Go to GitHub UI:**
1. Navigate to your repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"

**Add these secrets:**

**Secret 1: COPILOT_CLI_TOKEN**
```
Name: COPILOT_CLI_TOKEN
Value: [Your GitHub personal access token with repo + read:user + gist scopes]

How to generate:
1. github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Check: repo, read:user, gist
4. Copy token and paste above
```

**Secret 2 (Optional): ACTIONS_PAT**
```
Name: ACTIONS_PAT
Value: [Another PAT if you need it for additional API calls]
```

### Step 3: Configure Workflow Permissions

**In GitHub UI:**
1. Repository → Settings → Actions → General
2. Under "Workflow permissions":
   - Select: "Read and write permissions"
   - Check: "Allow GitHub Actions to create and approve pull requests"
3. Save

### Step 4: Copy Workflow File

**Create/edit:** `.github/workflows/doc-generation.yml`

Copy the COMPLETE workflow YAML from below (scroll to end of this file).

### Step 5: Create Copilot Configuration

**Create file:** `.copilot/config.json`

```json
{
  "documentation": {
    "enabled": true,
    "types": ["api", "architecture", "changelog", "examples"],
    "outputDir": "./docs",
    "excludePaths": ["node_modules", "dist", ".git", ".next", "target", "build"],
    "language": "en",
    "style": "professional"
  },
  "copilot": {
    "model": "gpt-4",
    "temperature": 0.3,
    "maxTokens": 2000
  }
}
```

### Step 6: Commit and Push

```bash
git add .github/workflows/doc-generation.yml
git add .copilot/config.json
git add docs/  # Add gitkeep files if empty
git commit -m "feat: add automated documentation generation workflow"
git push origin main
```

### Step 7: Verify Workflow Appears

1. Go to your repository → Actions
2. Look for "Automated Documentation Generation with Copilot CLI"
3. Should show "✓ Active"

### Step 8: Test with Manual Dispatch

1. Click on the workflow name
2. Click "Run workflow" button
3. Ensure branch is set to `main`
4. In "force_run" check the checkbox (to test without waiting for commits)
5. Click "Run workflow"
6. Watch it execute in real-time

**Expected outcome**: Takes 5-15 minutes, creates feature branch + opens PR

### Step 9: Monitor First Run

1. Go to Actions → Click the running workflow
2. Watch logs in real-time
3. Verify all jobs succeed (Check commits → Generate Docs → Create PR → Notify)
4. Check feature branch is created
5. Check PR is opened with documentation

### Step 10: Configure Team

**Edit the workflow file:**

Find this line (around line 20):
```yaml
env:
  ...
  DEFAULT_REVIEWERS: 'tech-lead,documentation-team'
```

Replace with your actual team members (comma-separated, no @ symbol):
```yaml
DEFAULT_REVIEWERS: 'alice,bob,charlie'  # GitHub usernames
```

---

## 🧪 Testing Checklist

Before enabling the monthly schedule, verify:

- [ ] Manual dispatch works (creates PR successfully)
- [ ] PR description is clear and informative
- [ ] Documentation files are generated properly
- [ ] Labels are applied correctly
- [ ] Team receives reviewer notification
- [ ] Merge conflict resolution works (if applicable)
- [ ] Cleanup happens after PR merge (feature branch deleted)

---

## ⚙️ Customization Reference

### Change Monthly Schedule

**Find this section** (around line 5):
```yaml
schedule:
  - cron: '0 0 1 * *'
```

**Use these cron expressions:**
- `0 0 1 * *` = 1st of month, 00:00 UTC (DEFAULT)
- `0 0 15 * *` = 15th of month
- `0 3 * * 0` = Every Sunday, 3 AM UTC
- `0 0 * * MON-FRI` = Every weekday
- `0 */6 * * *` = Every 6 hours (for testing)

**Cron cheat sheet**: https://crontab.guru

### Change Branch Prefix

**Find this line** (around line 20):
```yaml
BRANCH_PREFIX: 'feature/doc'
```

**Change to:**
```yaml
BRANCH_PREFIX: 'docs/auto'          # Results in: docs/auto-20260125
BRANCH_PREFIX: 'chore/docs'         # Results in: chore/docs-20260125
BRANCH_PREFIX: 'automation/doc'     # Results in: automation/doc-20260125
```

### Change Documentation Types

**Find the jobs section** and remove/add doc generation jobs:

```yaml
- name: Generate API documentation
  # Keep or remove this block

- name: Generate architecture documentation
  # Keep or remove this block

- name: Generate changelog
  # Keep or remove this block

- name: Generate code examples documentation
  # Keep or remove this block
```

Each job can be disabled by commenting it out or removing it entirely.

### Add Slack Notification

**Find line ~280** (search for `notify-status` job)

Add this step:
```yaml
- name: Send Slack notification
  if: always()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "📚 Docs Update: ${{ needs.check-commits.result }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Documentation Update*\n*Status*: ${{ job.status }}\n*PR*: ${{ needs.create-pull-request.outputs.pr_url }}"
            }
          }
        ]
      }
```

Then add this secret in GitHub UI:
```
SLACK_WEBHOOK = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🔍 Verification Commands

**Run these in your repository to verify setup:**

```bash
# Check if workflow file exists and is valid YAML
cat .github/workflows/doc-generation.yml | head -20

# Verify directory structure
ls -la .github/workflows/
ls -la .copilot/
ls -la docs/

# Check Git status
git status

# Verify secrets exist (won't show values, just that they exist)
gh secret list
```

---

## 🚨 Troubleshooting: If Something Doesn't Work

### Workflow doesn't appear in GitHub UI
```bash
# Solution 1: Verify file is on main branch
git status
git push origin main

# Solution 2: Clear GitHub cache
# Go to Settings → Actions → Clear all actions cache

# Solution 3: Check YAML syntax
gh workflow view doc-generation.yml
```

### Manual dispatch fails with "no commits"
```bash
# This is expected if force_run is not checked
# Just check the force_run checkbox when manually running
```

### Copilot CLI authentication fails
```bash
# Verify token is valid
export GH_TOKEN=your_token_value
gh copilot --help

# If fails, regenerate token:
# 1. github.com → Settings → Developer settings → Personal access tokens
# 2. Generate new token with repo, read:user, gist scopes
# 3. Update COPILOT_CLI_TOKEN secret in GitHub
```

### PR not created
```bash
# Check for existing PR
gh pr list --head feature/doc-20260125

# Check branch exists
git branch -r | grep feature/doc

# View workflow logs
gh workflow view doc-generation.yml --ref main
```

---

## 📞 Need Help?

**Check these resources:**
- GitHub Actions docs: https://docs.github.com/en/actions
- Copilot CLI: https://github.com/github/gh-copilot
- Cron expressions: https://crontab.guru
- YAML syntax: https://yaml.org

---

## ✅ You're Ready!

Once you've completed all 10 steps above, your automated documentation workflow is active and ready to:

✅ Check for commits monthly  
✅ Generate documentation with Copilot CLI  
✅ Create feature branches automatically  
✅ Open PRs for team review  
✅ Notify your team  

**That's it! The workflow will run automatically on the 1st of each month (or whenever you manually trigger it).**

---

## 📁 File Checklist

Verify these files exist in your repository:

- [ ] `.github/workflows/doc-generation.yml` - Main workflow (400+ lines)
- [ ] `.copilot/config.json` - Configuration file (15 lines)
- [ ] `docs/api/` - Directory for API docs
- [ ] `docs/architecture/` - Directory for architecture docs
- [ ] `docs/changelog/` - Directory for changelog
- [ ] `docs/examples/` - Directory for examples

---

## 🎯 First Run Expectations

When you manually dispatch or it runs on schedule for the first time:

**Timeline:**
- Start: ~2 min to setup
- Execution: ~5-10 min for docs generation
- PR creation: ~1-2 min
- Total: ~10-15 minutes

**Outputs:**
- ✅ Feature branch: `feature/doc-20260125` (or your custom prefix)
- ✅ PR: With detailed description and checklist
- ✅ Labels: `documentation`, `automated`, `review-required`, `generated`
- ✅ Reviewers: Added based on `DEFAULT_REVIEWERS`
- ✅ Documentation files: Generated in `/docs` directory

**Next step:** Team reviews the PR, approves/requests changes, then merges.

---

**You're all set! Start with manual dispatch to test everything works, then let it run automatically on schedule. 🚀**

