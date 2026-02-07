#!/usr/bin/env python3
"""
Repository Test Analysis Tool - Main Entry Point (Refactored)
Uses GitHub Copilot SDK for intelligent code analysis and test coverage metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from .models import TestMetrics
from .github_client import GitHubClient
from .analyzer_refactored import RepositoryAnalyzer
from .report_generator_refactored import ExcelReportGenerator


class RepositoryAnalysisOrchestrator:
    """
    Orchestrates the repository analysis workflow.
    
    Follows Single Responsibility Principle - coordinates high-level workflow
    without implementing business logic.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config: Configuration dictionary from command-line args
        """
        self.config = config
        self.github_client = GitHubClient()
        self.analyzer = RepositoryAnalyzer(use_copilot=True)
        self.report_generator = ExcelReportGenerator()
    
    async def run(self):
        """Execute the analysis workflow"""
        if self.config.get("init"):
            await self._initialize_repository_list()
        else:
            await self._analyze_repositories()
    
    async def _initialize_repository_list(self):
        """Fetch and save repository list from GitHub"""
        print("🔍 Fetching repository list from GitHub...")
        
        repos = self._fetch_repositories()
        self._save_repository_config(repos)
        
        print(f"\n📝 Edit {self.config['config_file']} to enable/disable specific repositories")
    
    async def _analyze_repositories(self):
        """Analyze enabled repositories and generate report"""
        # Load repository configuration
        repo_configs = self._load_repository_config()
        enabled_repos = [r for r in repo_configs if r.get("enabled", True)]
        
        print(f"\n📋 Analyzing {len(enabled_repos)} repositories...")
        
        # Analyze each repository
        metrics_list = await self._analyze_all_repositories(enabled_repos)
        
        # Cleanup resources
        await self.analyzer.cleanup()
        
        # Generate report
        self.report_generator.generate_report(
            metrics_list,
            Path(self.config["output_file"])
        )
        
        # Print summary
        self._print_summary(metrics_list)
    
    def _fetch_repositories(self) -> List[Dict]:
        """Fetch repositories from GitHub based on configuration"""
        if self.config.get("org"):
            return self.github_client.list_org_repos(self.config["org"])
        elif self.config.get("user"):
            return self.github_client.list_user_repos(self.config["user"])
        else:
            return self.github_client.list_user_repos()
    
    def _save_repository_config(self, repos: List[Dict]):
        """Save repository configuration to JSON file"""
        config_file = Path(self.config["config_file"])
        
        repo_config = {
            "repositories": [
                {
                    "name": repo["full_name"],
                    "url": repo["clone_url"],
                    "enabled": True,
                    "description": repo.get("description", "")
                }
                for repo in repos
            ]
        }
        
        config_file.write_text(json.dumps(repo_config, indent=2))
        print(f"✅ Saved {len(repos)} repositories to {config_file}")
    
    def _load_repository_config(self) -> List[Dict]:
        """Load repository configuration from JSON file"""
        config_file = Path(self.config["config_file"])
        
        if not config_file.exists():
            print(f"❌ Config file not found: {config_file}")
            print("Run with --init to create repository list")
            sys.exit(1)
        
        config = json.loads(config_file.read_text())
        return config["repositories"]
    
    async def _analyze_all_repositories(self, repo_configs: List[Dict]) -> List[TestMetrics]:
        """Analyze all enabled repositories"""
        metrics_list = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for idx, repo_config in enumerate(repo_configs, start=1):
                print(f"\n[{idx}/{len(repo_configs)}] Processing: {repo_config['name']}")
                
                metrics = await self._analyze_single_repository(
                    repo_config,
                    temp_path,
                    idx,
                    len(repo_configs)
                )
                metrics_list.append(metrics)
        
        return metrics_list
    
    async def _analyze_single_repository(
        self,
        repo_config: Dict,
        temp_path: Path,
        current: int,
        total: int
    ) -> TestMetrics:
        """Analyze a single repository"""
        repo_path = temp_path / repo_config['name'].replace('/', '_')
        
        # Clone repository
        if self.github_client.clone_repo(repo_config['url'], repo_path):
            # Analyze
            return await self.analyzer.analyze_repository(
                repo_path,
                repo_config['name'],
                repo_config['url']
            )
        else:
            # Failed to clone
            return TestMetrics(
                repo_name=repo_config['name'],
                repo_url=repo_config['url'],
                last_analyzed=datetime.now().isoformat(),
                analysis_status="failed",
                error_message="Failed to clone repository"
            )
    
    def _print_summary(self, metrics_list: List[TestMetrics]):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total repositories: {len(metrics_list)}")
        print(f"Successful: {sum(1 for m in metrics_list if m.analysis_status == 'success')}")
        print(f"Failed: {sum(1 for m in metrics_list if m.analysis_status == 'failed')}")
        print(f"\n📄 Report: {Path(self.config['output_file']).absolute()}")


def parse_arguments():
    """Parse command-line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories for test metrics"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize repository list from GitHub"
    )
    parser.add_argument(
        "--org",
        type=str,
        help="GitHub organization to fetch repos from"
    )
    parser.add_argument(
        "--user",
        type=str,
        help="GitHub user to fetch repos from"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="repo_list.json",
        help="Repository list config file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test_analysis_report.xlsx",
        help="Output Excel file"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="GitHub personal access token"
    )
    
    return parser.parse_args()


async def main():
    """Main execution flow"""
    args = parse_arguments()
    
    # Set token from environment or arg
    if args.token:
        os.environ["GITHUB_TOKEN"] = args.token
    
    # Build configuration
    config = {
        "init": args.init,
        "org": args.org,
        "user": args.user,
        "config_file": args.config,
        "output_file": args.output,
    }
    
    # Run orchestrator
    orchestrator = RepositoryAnalysisOrchestrator(config)
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
