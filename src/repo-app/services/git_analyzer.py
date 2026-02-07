"""
Git repository analysis service.

Author: Automated Software Engineering Team
Date: February 2026
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict

from ..constants import GIT_TIMEFRAMES, GIT_COMMAND_TIMEOUT


class GitAnalyzer:
    """Analyzes git repository commit history and activity"""
    
    async def analyze_commit_activity(self, repo_path: Path) -> Dict[str, int | float]:
        """
        Analyze git commit activity metrics.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            Dictionary with commit metrics
        """
        metrics = {
            "total_commits": 0,
            "commits_last_30_days": 0,
            "commits_last_90_days": 0,
            "commits_last_year": 0,
            "avg_commits_per_week": 0.0,
            "active_contributors": 0,
        }
        
        try:
            # Get total commits
            metrics["total_commits"] = await self._count_commits(repo_path)
            
            # Get commits by timeframe
            for name, days in GIT_TIMEFRAMES.items():
                count = await self._count_commits_since(repo_path, days)
                metrics[f"commits_last_{name if name != 'quarter' else '90_days'}"] = count
            
            # Calculate average commits per week (based on last 90 days)
            if metrics["commits_last_90_days"] > 0:
                weeks = GIT_TIMEFRAMES["quarter"] / 7
                metrics["avg_commits_per_week"] = round(
                    metrics["commits_last_90_days"] / weeks, 2
                )
            
            # Count active contributors
            metrics["active_contributors"] = await self._count_active_contributors(
                repo_path,
                GIT_TIMEFRAMES["quarter"]
            )
            
        except Exception:
            pass  # Return zero metrics on failure
        
        return metrics
    
    async def _count_commits(self, repo_path: Path, since: Optional[str] = None) -> int:
        """Count commits in repository"""
        cmd = ["git", "rev-list", "--count"]
        if since:
            cmd.extend(["--since", since])
        cmd.append("HEAD")
        
        result = await self._run_git_command(repo_path, cmd)
        return int(result.strip()) if result else 0
    
    async def _count_commits_since(self, repo_path: Path, days: int) -> int:
        """Count commits since N days ago"""
        return await self._count_commits(repo_path, f"{days}.days.ago")
    
    async def _count_active_contributors(self, repo_path: Path, days: int) -> int:
        """Count active contributors in the last N days"""
        cmd = ["git", "shortlog", "-sn", f"--since={days}.days.ago", "HEAD"]
        
        result = await self._run_git_command(repo_path, cmd)
        if not result:
            return 0
        
        contributors = [line.strip() for line in result.split('\n') if line.strip()]
        return len(contributors)
    
    async def _run_git_command(self, repo_path: Path, cmd: list[str]) -> Optional[str]:
        """Run git command asynchronously"""
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=GIT_COMMAND_TIMEOUT
                )
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None


# Type hint for optional import
from typing import Optional
