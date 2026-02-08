"""
GitHub API client for repository operations.

Author: Automated Software Engineering Team
Date: February 2026
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from logger import get_logger


class GitHubClient:
    """GitHub API client for repository operations"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def list_user_repos(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """List repositories for authenticated user or specific username"""
        if username:
            url = f"{self.base_url}/users/{username}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        
        repos = []
        page = 1
        while True:
            response = requests.get(
                url,
                headers=self.headers,
                params={"per_page": 100, "page": page, "sort": "updated"}
            )
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            repos.extend(page_repos)
            page += 1
            
            if len(page_repos) < 100:
                break
        
        return repos
    
    def list_org_repos(self, org: str) -> List[Dict[str, Any]]:
        """List repositories for an organization"""
        url = f"{self.base_url}/orgs/{org}/repos"
        
        repos = []
        page = 1
        while True:
            response = requests.get(
                url,
                headers=self.headers,
                params={"per_page": 100, "page": page, "sort": "updated"}
            )
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            repos.extend(page_repos)
            page += 1
            
            if len(page_repos) < 100:
                break
        
        return repos
    
    def clone_repo(self, repo_url: str, target_dir: Path) -> bool:
        """Clone a repository to target directory"""
        logger = get_logger()
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.debug(f"Successfully cloned {repo_url}")
            else:
                logger.error(f"Clone failed: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Clone failed: {e}")
            return False
