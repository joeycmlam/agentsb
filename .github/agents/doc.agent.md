# Doc Agent — `doc.agent`

Purpose
- Provide an automated specification for a GitHub agent that reads a repository, determines how many days have passed since recent changes (commit activity), and creates or updates a repository-level documentation file with an up-to-date "last changed" summary.

When to run
- Scheduled (e.g., daily or weekly) via GitHub Actions.
- Manual run via workflow_dispatch or by another agent that requests doc refresh.

Inputs
- `owner` (string): repository owner (org or user).
- `repo` (string): repository name.
- `branch` (string, optional): branch to inspect (default: default branch).
- `lookback_days` (int, optional): window to count recent changes (default: 30).
- `target_doc_path` (string, optional): path to update/create doc (default: `DOCS/REPO_STATUS.md`).
- `github_token` (string): token with `repo` permission to read commits and update files.

Outputs
- Updated or created documentation file at `target_doc_path` with:
  - Last commit date in the repo (ISO8601).
  - Number of days since the last change.
  - Count of commits within `lookback_days`.
  - List of top changed files (optional truncated list).
  - Recommended next steps (if no activity for X days).
- Commit to the repo with a clear message like `docs: update repo status (last change X days ago)`.

Behavior / Algorithm
1. Resolve default branch if `branch` not provided using GitHub API: `GET /repos/{owner}/{repo}` (field `default_branch`).
2. Query the most recent commit on the branch: `GET /repos/{owner}/{repo}/commits?sha={branch}&per_page=1`.
3. Parse `commit.commit.author.date` to compute the difference in days between now and that date -> `days_since_last_change`.
4. For `lookback_days` window: fetch commits since `now - lookback_days` using `GET /repos/{owner}/{repo}/commits?since={ISO_DATE}` and count them.
5. Optionally aggregate changed files by calling `GET /repos/{owner}/{repo}/commits/{sha}` for each commit (or call once for the latest N commits) and tally file paths.
6. Render documentation content using a small template including a badge-like header, metrics, and the short file list.
7. Update or create `target_doc_path` using GitHub Contents API (`PUT /repos/{owner}/{repo}/contents/{path}`) with a commit message and the file content. If file exists, pass the `sha` to update.

Implementation notes
- Use the GitHub REST API and `Authorization: Bearer <token>` header. Keep rate limits in mind (authenticate to increase limits).
- If the repo is large, prefer counting commits by using the commits listing endpoints with `since` rather than enumerating every commit.
- For robust scheduling, implement as a small GitHub Action workflow that invokes a script (Python/Node) in the repo.
- If updating many repos, add a dry-run mode that prints the planned doc content without committing.

Example `DOCS/REPO_STATUS.md` template
```
# Repository status — {repo}

- Last commit: {last_commit_date} (UTC)
- Days since last change: {days_since_last_change}
- Commits in last {lookback_days} days: {commit_count}

Top changed files (last {lookback_days} days):
{top_files_list}

_This file is generated automatically by the `doc.agent`._
```

Example Python implementation (concise)
```python
import os, requests, datetime

token = os.environ.get('GITHUB_TOKEN')
owner='OWNER'
repo='REPO'
branch=None
lookback_days=30

def api_get(path, params=None):
    url=f'https://api.github.com{path}'
    headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json'}
    r=requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()

# 1. resolve repo default branch
repo_meta=api_get(f'/repos/{owner}/{repo}')
branch = branch or repo_meta['default_branch']

# 2. latest commit
latest=api_get(f'/repos/{owner}/{repo}/commits', params={'sha':branch,'per_page':1})[0]
last_date=latest['commit']['author']['date']
last_dt=datetime.datetime.fromisoformat(last_date.replace('Z','+00:00'))

# 3. compute days difference
now=datetime.datetime.now(datetime.timezone.utc)
days_since=(now-last_dt).days

# 4. commits in window
since_iso=(now-datetime.timedelta(days=lookback_days)).isoformat()
commits_window=api_get(f'/repos/{owner}/{repo}/commits', params={'sha':branch,'since':since_iso})
commit_count=len(commits_window)

# 5. prepare doc content (truncated)
content=f"""# Repository status — {repo}\n\n- Last commit: {last_date} (UTC)\n- Days since last change: {days_since}\n- Commits in last {lookback_days} days: {commit_count}\n\n_This file is generated automatically by the `doc.agent`._\n"""

# 6. create/update via Contents API (omitted here for brevity)
```

Security & Permissions
- The agent requires a `GITHUB_TOKEN` (or PAT with repo scope for private repos).
- Keep the token out of logs. Use encrypted secrets in Actions.

Testing
- Manual: run locally with a PAT and `owner`, `repo` env vars.
- CI: Add an Action that runs in dry-run mode first, then commit on success.

Extensions and suggestions
- Add a small badge generator that writes a shield-style SVG with the last-updated date.
- Extend to track activity per package/folder for mono-repos.
- Add an opt-in file `.doc-agent-ignore` to skip files or paths when computing top changed files.


---

Generated by automation on branch: feat/SCRUM-5-requirements
