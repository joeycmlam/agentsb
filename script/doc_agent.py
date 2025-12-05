#!/usr/bin/env python3
"""
Doc Agent script

Usage:
  python script/doc_agent.py [--owner OWNER] [--repo REPO] [--branch BRANCH]
                             [--lookback-days N] [--target-doc-path PATH]
                             [--dry-run]

This script reads commit activity from a GitHub repo, computes days since last change,
counts commits in a lookback window, lists top changed files, and updates a documentation
file (`DOCS/REPO_STATUS.md` by default) via the GitHub Contents API.

It uses the `GITHUB_TOKEN` environment variable for authentication.
"""

import argparse
import base64
import datetime
import os
import sys
import time
from collections import Counter

import requests

API_BASE = "https://api.github.com"


def api_get(url, token, params=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-agent-script",
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp


def api_put(url, token, json_data):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-agent-script",
    }
    resp = requests.put(url, headers=headers, json=json_data)
    resp.raise_for_status()
    return resp


def get_default_branch(owner, repo, token):
    url = f"{API_BASE}/repos/{owner}/{repo}"
    resp = api_get(url, token)
    return resp.json().get("default_branch")


def get_latest_commit(owner, repo, branch, token):
    url = f"{API_BASE}/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "per_page": 1}
    resp = api_get(url, token, params=params)
    items = resp.json()
    if not items:
        return None
    return items[0]


def paginate_commits(owner, repo, branch, since_iso, token):
    url = f"{API_BASE}/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "since": since_iso, "per_page": 100}
    commits = []
    while True:
        resp = api_get(url, token, params=params)
        page_items = resp.json()
        commits.extend(page_items)
        # Pagination via Link header
        link = resp.headers.get("Link")
        if not link or "rel=\"next\"" not in link:
            break
        # extract next URL
        parts = link.split(",")
        next_url = None
        for p in parts:
            if "rel=\"next\"" in p:
                p = p.strip()
                start = p.find("<") + 1
                end = p.find(">", start)
                next_url = p[start:end]
                break
        if not next_url:
            break
        # follow next_url (it's a full URL)
        resp = requests.get(next_url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "doc-agent-script",
        })
        resp.raise_for_status()
        params = None
        page_items = resp.json()
        commits.extend(page_items)
        # continue loop will check Link header on this response
        link = resp.headers.get("Link")
        if not link or "rel=\"next\"" not in link:
            break
    return commits


def get_commit_files(owner, repo, sha, token):
    url = f"{API_BASE}/repos/{owner}/{repo}/commits/{sha}"
    resp = api_get(url, token)
    data = resp.json()
    files = data.get("files", [])
    return [f.get("filename") for f in files if f.get("filename")]


def get_contents_sha(owner, repo, path, branch, token):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch}
    resp = requests.get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-agent-script",
    }, params=params)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json().get("sha")


def create_or_update_file(owner, repo, path, content_str, branch, token, message):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    sha = get_contents_sha(owner, repo, path, branch, token)
    b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": message,
        "content": b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    resp = api_put(url, token, payload)
    return resp.json()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--owner", help="Repository owner (user/org)")
    p.add_argument("--repo", help="Repository name")
    p.add_argument("--branch", help="Branch to inspect (defaults to repo default)")
    p.add_argument("--lookback-days", type=int, default=30, help="Lookback window in days")
    p.add_argument("--target-doc-path", default="DOCS/REPO_STATUS.md", help="Path to create/update")
    p.add_argument("--dry-run", action="store_true", help="Print generated content but do not commit")
    args = p.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required", file=sys.stderr)
        sys.exit(2)

    # derive owner/repo from env if not provided
    if not args.owner or not args.repo:
        repo_env = os.environ.get("GITHUB_REPOSITORY")
        if repo_env and "/" in repo_env:
            env_owner, env_repo = repo_env.split("/", 1)
            owner = args.owner or env_owner
            repo = args.repo or env_repo
        else:
            print("Error: owner and repo must be provided, or run inside GitHub Actions with GITHUB_REPOSITORY set", file=sys.stderr)
            sys.exit(2)
    else:
        owner = args.owner
        repo = args.repo

    branch = args.branch
    lookback_days = args.lookback_days
    target_doc_path = args.target_doc_path

    # resolve default branch
    if not branch:
        branch = get_default_branch(owner, repo, token)
        if not branch:
            print("Error: could not determine default branch", file=sys.stderr)
            sys.exit(2)

    print(f"Inspecting {owner}/{repo} on branch {branch}")

    latest = get_latest_commit(owner, repo, branch, token)
    if not latest:
        print("No commits found on the branch", file=sys.stderr)
        sys.exit(0)

    last_date_str = latest["commit"]["author"]["date"]
    last_dt = datetime.datetime.fromisoformat(last_date_str.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    days_since = (now - last_dt).days

    # commits in lookback window
    since_dt = now - datetime.timedelta(days=lookback_days)
    since_iso = since_dt.isoformat()
    commits = paginate_commits(owner, repo, branch, since_iso, token)
    commit_count = len(commits)

    # collect top changed files
    file_counter = Counter()
    # limit to first 200 commits in window to avoid excessive API usage
    sha_list = [c.get("sha") for c in commits][:200]
    for sha in sha_list:
        try:
            files = get_commit_files(owner, repo, sha, token)
        except Exception:
            # be tolerant of occasional errors
            continue
        file_counter.update(files)
        # be gentle with API
        time.sleep(0.1)

    top_files = file_counter.most_common(10)

    top_files_list = "\n".join([f"- {path} ({count} changes)" for path, count in top_files]) if top_files else "- None"

    content = f"""# Repository status — {repo}\n\n- Last commit: {last_date_str} (UTC)\n- Days since last change: {days_since}\n- Commits in last {lookback_days} days: {commit_count}\n\nTop changed files (last {lookback_days} days):\n{top_files_list}\n\n_This file is generated automatically by the doc.agent script._\n"""

    if args.dry_run:
        print("--- DRY RUN: Generated content ---")
        print(content)
        sys.exit(0)

    commit_message = f"docs: update repo status (last change {days_since} days ago)"
    try:
        resp = create_or_update_file(owner, repo, target_doc_path, content, branch, token, commit_message)
    except Exception as e:
        print(f"Failed to create/update file: {e}", file=sys.stderr)
        sys.exit(1)

    print("Updated documentation at:", resp.get("content", {}).get("html_url"))


if __name__ == "__main__":
    main()
