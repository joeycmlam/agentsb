# Doc Agent — `doc.agent`

## Purpose

Automatically inspect a GitHub repository's commit history, compute how many days have passed since the last change, and create or update a documentation file (`DOCS/REPO_STATUS.md` by default) summarising recent activity.

---

## When to Run

| Trigger | Description |
|---------|-------------|
| **Scheduled** | Daily or weekly via GitHub Actions (cron). |
| **Manual** | `workflow_dispatch` from the Actions tab. |
| **On-demand** | Called by another agent or script that needs a doc refresh. |

---

## Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `owner` | string | yes* | — | Repository owner (user or org). Auto-detected in Actions via `GITHUB_REPOSITORY`. |
| `repo` | string | yes* | — | Repository name. Auto-detected in Actions via `GITHUB_REPOSITORY`. |
| `branch` | string | no | default branch | Branch to inspect. |
| `lookback_days` | int | no | `30` | Window (days) for counting recent commits. |
| `target_doc_path` | string | no | `DOCS/REPO_STATUS.md` | Path to the documentation file to create/update. |
| `github_token` | string | yes | — | Token with `repo` (or `contents:write`) permission. |
| `dry_run` | bool | no | `false` | If `true`, print generated content without committing. |

> *Auto-detected when running inside GitHub Actions.

---

## Outputs

The agent produces a Markdown file at `target_doc_path` containing:

- **Last commit date** (ISO 8601, UTC).
- **Days since last change**.
- **Commit count** within the `lookback_days` window.
- **Top changed files** (up to 10, with change counts).
- A footer noting the file is auto-generated.

A commit is created with a message like:

```
docs: update repo status (last change 3 days ago)
```

---

## Algorithm

```text
1. Resolve default branch (if not provided)
   GET /repos/{owner}/{repo} → default_branch

2. Fetch latest commit on branch
   GET /repos/{owner}/{repo}/commits?sha={branch}&per_page=1

3. Compute days_since_last_change
   now (UTC) − commit.author.date

4. Count commits in lookback window
   GET /repos/{owner}/{repo}/commits?sha={branch}&since={ISO_DATE}

5. Aggregate top changed files (optional, rate-limit aware)
   For each commit SHA (limit 200):
     GET /repos/{owner}/{repo}/commits/{sha} → files[]
   Tally file paths, keep top 10.

6. Render Markdown from template

7. Create or update file via Contents API
   PUT /repos/{owner}/{repo}/contents/{path}
   (include existing file SHA if updating)
```

---

## Implementation

### Files

| Path | Purpose |
|------|---------|
| `script/doc_agent.py` | Python CLI that implements the algorithm above. |
| `script/requirements.txt` | Dependencies (`requests`). |
| `.github/workflows/doc-agent.yml` | GitHub Actions workflow (scheduled + manual). |

### Quick Local Run

```bash
export GITHUB_TOKEN="ghp_..."
python script/doc_agent.py --owner joeycmlam --repo agentsb --dry-run
```

### Workflow Behaviour

1. **Scheduled runs** execute the script in `--dry-run` mode only (logs output, no commit).
2. **Manual runs** (`workflow_dispatch`) execute dry-run first, then commit the update.

---

## Example Output (`DOCS/REPO_STATUS.md`)

```markdown
# Repository status — agentsb

- Last commit: 2025-12-05T10:23:45Z (UTC)
- Days since last change: 0
- Commits in last 30 days: 12

Top changed files (last 30 days):
- src/main.py (5 changes)
- script/doc_agent.py (3 changes)
- README.md (2 changes)

_This file is generated automatically by the doc.agent script._
```

---

## Security & Permissions

- Store `GITHUB_TOKEN` as a repository secret; never log it.
- For private repos, use a PAT with `repo` scope or a fine-grained token with `contents:write`.
- The built-in `secrets.GITHUB_TOKEN` in Actions is sufficient for public repos.

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| No commits on branch | Exit gracefully with message; no file written. |
| API rate limit hit | Fail with HTTP 403; retry after reset window or reduce commit fetch limit. |
| File path doesn't exist | Creates the file and any missing directories (API handles this). |
| Token lacks write permission | Commit step fails; dry-run still succeeds. |

---

## Testing

| Method | Command / Steps |
|--------|-----------------|
| **Local dry-run** | `python script/doc_agent.py --dry-run` |
| **CI dry-run** | Push to branch; scheduled workflow logs output. |
| **Full commit** | Trigger workflow manually via GitHub Actions UI. |

---

## Extensions (Future)

- **Badge generator** — output a Shields.io-compatible JSON or SVG with "last updated" info.
- **Per-folder stats** — useful for monorepos; show activity per top-level directory.
- **Ignore list** — honour a `.doc-agent-ignore` file to exclude paths from "top changed" tally.
- **Slack/email alert** — notify if repo inactive for N days.

---

_Last reviewed: 2025-12-05_
