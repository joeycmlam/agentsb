# Implementation Guide: GitHub Actions Documentation Generation

## 📋 Quick Start Checklist

### Phase 1: Repository Setup (15 minutes)

- [ ] **Clone/access your repository**
  ```bash
  git clone https://github.com/YOUR_ORG/YOUR_REPO.git
  cd YOUR_REPO
  ```

- [ ] **Create workflow directory**
  ```bash
  mkdir -p .github/workflows
  mkdir -p .copilot
  mkdir -p docs/{api,architecture,changelog,examples}
  ```

- [ ] **Copy workflow file**
  ```bash
  # Copy the doc-generation.yml file to .github/workflows/
  cp doc-generation.yml .github/workflows/
  ```

- [ ] **Create Copilot configuration**
  ```bash
  # Create .copilot/config.json
  cat > .copilot/config.json << 'EOF'
  {
    "documentation": {
      "enabled": true,
      "types": ["api", "architecture", "changelog", "examples"],
      "outputDir": "./docs",
      "excludePaths": ["node_modules", "dist", ".git", ".next"],
      "language": "en",
      "style": "professional"
    }
  }
  EOF
  ```

### Phase 2: GitHub Configuration (10 minutes)

- [ ] **Set up GitHub Secrets**
  - Go to: **Settings → Secrets and variables → Actions**
  - Click **New repository secret**
  - Add secrets:
    ```
    Name: COPILOT_CLI_TOKEN
    Value: [Your GitHub Copilot CLI Token]
    ```
  - Add secrets:
    ```
    Name: ACTIONS_PAT (optional)
    Value: [Personal Access Token with repo, workflow scopes]
    ```

- [ ] **Verify GitHub App Permissions**
  - Settings → Actions → General
  - Under "Workflow permissions", select:
    - ✓ Read and write permissions
    - ✓ Allow GitHub Actions to create and approve pull requests

- [ ] **Configure branch protection (recommended)**
  - Settings → Branches → Add rule
  - Pattern: `main`
  - Requirements:
    - ✓ Require pull request reviews (1-2 reviewers)
    - ✓ Dismiss stale PR approvals
    - ✓ Require branches to be up to date before merging
    - ✓ Require status checks to pass (if CI/CD configured)

### Phase 3: Workflow Verification (10 minutes)

- [ ] **Commit files to repository**
  ```bash
  git add .github/workflows/doc-generation.yml
  git add .copilot/config.json
  git add docs/
  git commit -m "feat: add automated documentation generation workflow"
  git push origin main
  ```

- [ ] **Verify workflow appears in GitHub UI**
  - Go to: **Actions → Workflows**
  - Look for: "Automated Documentation Generation with Copilot CLI"
  - Should show: "✓ Active"

- [ ] **Test workflow manually**
  - Click on workflow name
  - Click **Run workflow**
  - Select: Branch: `main`
  - Check: `force_run`: `true` (to test without waiting for commits)
  - Click **Run workflow**

- [ ] **Monitor first run**
  - Watch execution in Actions tab
  - Check logs for any errors
  - Verify feature branch is created
  - Verify PR is opened

---

## 🔧 Configuration Details

### Environment Variables (Customizable)

Edit these in the workflow file under `env:` section:

```yaml
env:
  BRANCH_PREFIX: 'feature/doc'           # Change to 'docs/auto-' or similar
  DEFAULT_REVIEWERS: 'tech-lead,docs-team'  # Your team members
```

### Workflow Triggers (Adjust as Needed)

**Current schedule: 1st of each month at 00:00 UTC**

To change schedule:
```yaml
schedule:
  - cron: '0 0 1 * *'    # 1st of month
  # Alternative examples:
  # - cron: '0 0 15 * *'  # 15th of month
  # - cron: '0 3 * * 0'   # Every Sunday at 3 AM UTC
  # - cron: '0 */6 * * *' # Every 6 hours
```

### Documentation Types (Customize Generation)

Modify the jobs in the workflow:
- `api-docs`: Generate API endpoint documentation
- `arch-docs`: Generate architecture documentation
- `changelog`: Generate changelog from commits
- `examples`: Generate code examples documentation

To add custom documentation type:
```yaml
- name: Generate custom documentation
  id: custom-docs
  shell: bash
  continue-on-error: true
  run: |
    echo "🔄 Generating custom documentation..."
    # Your custom generation script here
    echo "✓ Custom documentation generated"
    echo "status=success" >> $GITHUB_OUTPUT
```

---

## 📝 Detailed Workflow Breakdown

### Job 1: Check for Recent Commits

**Purpose**: Determine if documentation generation should proceed

**Logic**:
```
IF scheduled trigger AND no commits in past 30 days
  → Skip workflow (no PR created)
ELSE IF manual dispatch with force_run=true
  → Proceed regardless of commits
ELSE IF commits found
  → Proceed with generation
```

**Output Variables**:
- `commits_found`: true/false
- `commit_count`: number of commits
- `should_proceed`: true/false

**Why this matters**: Avoids creating unnecessary PRs when nothing has changed.

### Job 2: Generate Documentation

**Purpose**: Use GitHub Copilot CLI to create/update documentation

**Steps**:
1. Checkout repository with full history
2. Configure Git for automated commits
3. Install GitHub CLI and Copilot extension
4. Create feature branch (format: `feature/doc-20260125`)
5. Generate documentation:
   - API docs
   - Architecture docs
   - Changelog
   - Code examples
6. Validate generated files
7. Commit changes with detailed message
8. Push branch to remote

**Key Features**:
- Error handling: `continue-on-error: true` allows partial generation
- Unique branch naming: Prevents conflicts on repeated runs
- Validation: Checks file sizes and integrity
- Atomic commits: All docs committed together

### Job 3: Create Pull Request

**Purpose**: Open PR for team review

**Steps**:
1. Check for existing PR (prevents duplicates)
2. Create PR with detailed description
3. Add labels: `documentation, automated, review-required, generated`
4. Request reviewers from `DEFAULT_REVIEWERS` list
5. Add to project board (if exists)
6. Comment with generation summary

**PR Details**:
- Title: `docs: automated documentation update - feature/doc-yyyymmdd`
- Description: Includes checklist, related links, auto-generated notice
- Status: Draft=false (ready for review)

### Job 4: Notify Status

**Purpose**: Report workflow execution summary

**Outputs**:
- GitHub Actions summary
- Execution status: success/skipped/failed
- Links to PR and workflow run

---

## 🔐 Security Best Practices

### Token Management

**Use minimal-scope tokens**:
```yaml
# ✅ RECOMMENDED: Use GitHub Token (auto-scoped)
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# ⚠️ FALLBACK: Custom PAT for advanced needs
env:
  ACTIONS_PAT: ${{ secrets.ACTIONS_PAT }}
```

**Token rotation policy**:
- Review tokens quarterly
- Rotate every 90 days
- Implement least-privilege scope

### Code Security

**Apply branch protection to main**:
```
Settings → Branches → Add rule
- Pattern: main
- ✓ Require pull request reviews (minimum 1)
- ✓ Require status checks before merge
- ✓ Require branches to be up to date
- ✓ Enforce to admins
```

**Require approval before merge**:
- At least 1-2 reviewers must approve
- Reviewers can be tech leads or documentation owners
- Auto-merge disabled for generated docs

**Sign commits** (advanced):
```yaml
- name: Setup GPG signing
  uses: crazy-max/ghaction-import-gpg@v5
  with:
    gpg_private_key: ${{ secrets.GPG_PRIVATE_KEY }}
    git_user_signingkey: true
```

---

## 🐛 Troubleshooting Guide

### Issue: Workflow not triggering on schedule

**Symptoms**: 
- Scheduled job doesn't run on 1st of month
- Manual dispatch works fine

**Solution**:
1. Verify workflow file is on `main` branch (not feature branch)
2. Check cron expression: `0 0 1 * *` is correct
3. GitHub Actions may have slight delay (up to 10 minutes)
4. Test with manual dispatch to verify setup

```bash
# Verify workflow syntax
gh workflow view doc-generation.yml
```

### Issue: Copilot CLI authentication fails

**Symptoms**:
```
Error: gh: extension not found: github/gh-copilot
Error: unauthenticated
```

**Solution**:
1. Verify `COPILOT_CLI_TOKEN` secret exists
2. Ensure token has correct scopes: `repo, read:user, gist`
3. Test token locally:
   ```bash
   export GH_TOKEN=your_token
   gh copilot --help
   ```
4. Update Copilot CLI:
   ```bash
   gh extension upgrade github/gh-copilot
   ```

### Issue: PR creation fails

**Symptoms**:
```
Error: pull request already exists
Error: no commits between branches
```

**Solution**:
1. Check for existing open PRs with same branch
2. Verify branch has commits (not empty)
3. Ensure base branch is `main` (not protected with strict rules)
4. Check token has `pull-requests: write` permission

```bash
# List existing PRs for branch
gh pr list --head feature/doc-20260125

# Check branch commits
git log origin/main..origin/feature/doc-20260125
```

### Issue: No files generated

**Symptoms**:
- Workflow succeeds but docs/ directory is empty
- PR created but with no content

**Solution**:
1. Check for errors in job logs
2. Verify source code directories exist (`src/`, `api/`, etc.)
3. Manually test Copilot CLI:
   ```bash
   gh copilot explain --help
   ```
4. Check file permissions in runner

### Issue: Merge conflicts when merging PR

**Symptoms**:
```
This branch has conflicts that must be resolved
```

**Solution**:
1. Fetch latest from main: `git fetch origin main`
2. Rebase feature branch:
   ```bash
   git checkout feature/doc-20260125
   git rebase origin/main
   ```
3. Resolve conflicts if any
4. Force push to update PR:
   ```bash
   git push origin feature/doc-20260125 --force-with-lease
   ```
5. Re-request review if needed

---

## 📊 Monitoring & Maintenance

### Weekly Maintenance Checklist

- [ ] Check workflow execution history
  - Settings → Actions → Workflows → doc-generation
  - Review success/failure patterns
  
- [ ] Review generated PRs
  - Check if PRs are being merged or closed
  - Validate documentation quality
  
- [ ] Monitor run duration
  - Should complete in 5-15 minutes
  - Optimize if taking longer

### Monthly Review

- [ ] Audit generated documentation
  - Accuracy of API docs
  - Completeness of architecture docs
  - Changelog quality
  
- [ ] Update documentation templates
  - Review user feedback
  - Enhance templates if needed
  
- [ ] Review team feedback
  - Discuss documentation usefulness
  - Adjust frequency/content as needed

### Metrics to Track

| Metric | Target | How to Check |
|--------|--------|------------|
| **Execution Success Rate** | >95% | Actions → Workflow runs |
| **PR Merge Rate** | >80% | Pull Requests → Closed |
| **Avg Execution Time** | <15 min | Actions → Run logs |
| **Documentation Quality** | All approved | PR reviews |

---

## 🚀 Advanced Customizations

### Add Slack Notification

Add to workflow after `notify-status` job:

```yaml
- name: Send Slack notification
  if: always()
  uses: slackapi/slack-github-action@v1.24.0
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "📚 Documentation Update Status",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Status*: ${{ steps.status.outputs.status }}\n*PR*: ${{ needs.create-pull-request.outputs.pr_url }}"
            }
          }
        ]
      }
```

### Add Commit to Multiple Branches

Generate docs to both `main` and `develop`:

```yaml
- name: Create multiple feature branches
  run: |
    for branch in main develop; do
      git checkout -b "feature/doc-$branch-$(date +%Y%m%d)" origin/$branch
      # Generate docs
      git push origin "feature/doc-$branch-$(date +%Y%m%d)"
    done
```

### Filter Documentation Generation by File Changes

Only generate certain docs if specific files changed:

```yaml
- name: Detect changed files
  uses: dorny/paths-filter@v2
  id: changes
  with:
    filters: |
      api:
        - 'src/api/**'
      architecture:
        - 'src/**'
        - 'package.json'

- name: Generate only changed docs
  run: |
    if [ "${{ steps.changes.outputs.api }}" == "true" ]; then
      echo "🔄 Generating API docs..."
    fi
    if [ "${{ steps.changes.outputs.architecture }}" == "true" ]; then
      echo "🔄 Generating architecture docs..."
    fi
```

### Auto-Merge Documentation PR

Add auto-merge for documentation PRs:

```yaml
- name: Auto-merge PR (optional)
  if: steps.create-pr.outputs.pr_number != ''
  shell: bash
  run: |
    gh pr merge "${{ steps.create-pr.outputs.pr_number }}" \
      --auto \
      --merge \
      --delete-branch
```

**⚠️ Warning**: Enable only if you have strong confidence in generated content.

---

## 📚 GitHub Copilot CLI Reference

### Common Commands

```bash
# Explain code
gh copilot explain --source-language typescript "SELECT * FROM users"

# Get suggestions
gh copilot suggest "how to implement caching"

# Generate documentation
gh copilot explain --context src/api --output-format markdown

# Interactive mode
gh copilot suggest -i
```

### Authentication

```bash
# Login
gh auth login --scopes repo,read:user,gist

# Check status
gh auth status

# Switch account
gh auth login --hostname github.com
```

---

## ❓ FAQ

**Q: Can I customize the documentation templates?**
A: Yes! Create `.copilot/doc-templates/` directory with Markdown files. Reference in generation scripts.

**Q: What if I don't have Copilot subscription?**
A: The workflow can still generate basic documentation. Replace Copilot CLI commands with simple file generation/analysis scripts.

**Q: How do I skip the monthly run for a specific month?**
A: Manually disable the workflow in Actions tab → Disable, then re-enable after the scheduled date.

**Q: Can multiple teams use this workflow?**
A: Yes! Customize `DEFAULT_REVIEWERS` and labels per team needs.

**Q: How do I test the workflow before production?**
A: Use `force_run: true` in manual dispatch to test without waiting for commits.

---

## 📞 Support & Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **GitHub Copilot CLI**: https://github.com/github/gh-copilot
- **Cron Expression Helper**: https://crontab.guru
- **Community**: GitHub Discussions / Issues

