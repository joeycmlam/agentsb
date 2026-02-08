"""
Git analyzer for extracting commit activity metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import asyncio
from pathlib import Path

from models import TestMetrics
from logger import get_logger, log_metric


class GitAnalyzer:
    """Analyzes git commit history for activity metrics"""
    
    async def analyze_commit_activity(self, repo_path: Path, metrics: TestMetrics):
        """
        Analyze git commit history for activity metrics.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to populate with commit data
        """
        try:
            # Run git commands in parallel for efficiency
            results = await asyncio.gather(
                self._get_commit_count(repo_path, "HEAD"),
                self._get_commit_count(repo_path, "--since=30.days.ago", "HEAD"),
                self._get_commit_count(repo_path, "--since=90.days.ago", "HEAD"),
                self._get_commit_count(repo_path, "--since=1.year.ago", "HEAD"),
                self._get_contributors(repo_path),
                return_exceptions=True
            )
            
            # Unpack results
            if not isinstance(results[0], Exception):
                metrics.total_commits = results[0]
            if not isinstance(results[1], Exception):
                metrics.commits_last_30_days = results[1]
            if not isinstance(results[2], Exception):
                metrics.commits_last_90_days = results[2]
            if not isinstance(results[3], Exception):
                metrics.commits_last_year = results[3]
            if not isinstance(results[4], Exception):
                metrics.active_contributors = results[4]
            
            # Calculate average commits per week (based on last 90 days)
            if metrics.commits_last_90_days > 0:
                metrics.avg_commits_per_week = round(metrics.commits_last_90_days / (90 / 7), 2)
            
            log_metric("Commits", 
                      f"{metrics.total_commits} total, {metrics.commits_last_30_days} (30d), "
                      f"{metrics.avg_commits_per_week}/week avg, {metrics.active_contributors} contributors")
            
        except Exception as e:
            get_logger().warning(f"Commit analysis failed: {e}")
    
    async def _get_commit_count(self, repo_path: Path, *args) -> int:
        """
        Get commit count for given git arguments.
        
        Args:
            repo_path: Path to repository root
            *args: Additional git rev-list arguments
            
        Returns:
            Number of commits
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "rev-list", "--count", *args,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return int(stdout.decode().strip())
            return 0
        except Exception as e:
            get_logger().debug(f"Failed to get commit count: {e}")
            return 0
    
    async def _get_contributors(self, repo_path: Path) -> int:
        """
        Get number of active contributors (last 90 days).
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            Number of contributors
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "shortlog", "-sn", "--since=90.days.ago", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                contributors = [line.strip() for line in stdout.decode().strip().split('\n') if line.strip()]
                return len(contributors)
            return 0
        except Exception as e:
            get_logger().debug(f"Failed to get contributors: {e}")
            return 0
