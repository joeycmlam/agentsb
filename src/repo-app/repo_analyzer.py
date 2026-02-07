#!/usr/bin/env python3
"""
Repository Test Analysis Tool - Main Entry Point
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

from models import TestMetrics
from github_client import GitHubClient
from analyzer import RepositoryAnalyzer
from report_generator import ExcelReportGenerator


async def main():
    """Main execution flow"""
    # Load environment variables from .env file
    from utils import load_env_file
    load_env_file()
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze GitHub repositories for test metrics")
    parser.add_argument("--init", action="store_true", help="Initialize repository list from GitHub")
    parser.add_argument("--org", type=str, help="GitHub organization to fetch repos from")
    parser.add_argument("--user", type=str, help="GitHub user to fetch repos from")
    parser.add_argument("--config", type=str, default="repo_list.json", help="Repository list config file")
    parser.add_argument("--output", type=str, default="test_analysis_report.xlsx", help="Output Excel file")
    parser.add_argument("--token", type=str, help="GitHub personal access token")
    
    args = parser.parse_args()
    
    # Set token from environment or arg
    if args.token:
        os.environ["GITHUB_TOKEN"] = args.token
    
    config_file = Path(args.config)
    output_file = Path(args.output)
    
    # Initialize repository list
    if args.init:
        print("🔍 Fetching repository list from GitHub...")
        github_client = GitHubClient()
        
        if args.org:
            repos = github_client.list_org_repos(args.org)
        elif args.user:
            repos = github_client.list_user_repos(args.user)
        else:
            repos = github_client.list_user_repos()
        
        # Create config file
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
        print(f"\n📝 Edit {config_file} to enable/disable specific repositories")
        return
    
    # Load repository list
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print("Run with --init to create repository list")
        sys.exit(1)
    
    config = json.loads(config_file.read_text())
    enabled_repos = [r for r in config["repositories"] if r.get("enabled", True)]
    
    print(f"\n📋 Analyzing {len(enabled_repos)} repositories...")
    
    # Analyze each repository
    github_client = GitHubClient()
    analyzer = RepositoryAnalyzer(use_copilot=True)  # Enable Copilot analysis
    metrics_list = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for idx, repo_config in enumerate(enabled_repos, start=1):
            print(f"\n[{idx}/{len(enabled_repos)}] Processing: {repo_config['name']}")
            
            repo_path = temp_path / repo_config['name'].replace('/', '_')
            
            # Clone repository
            if github_client.clone_repo(repo_config['url'], repo_path):
                # Analyze
                metrics = await analyzer.analyze_repository(
                    repo_path,
                    repo_config['name'],
                    repo_config['url']
                )
                metrics_list.append(metrics)
            else:
                # Failed to clone
                metrics = TestMetrics(
                    repo_name=repo_config['name'],
                    repo_url=repo_config['url'],
                    last_analyzed=datetime.now().isoformat(),
                    analysis_status="failed",
                    error_message="Failed to clone repository"
                )
                metrics_list.append(metrics)
    
    # Clean up Copilot client
    await analyzer._cleanup_copilot()
    
    # Generate Excel report
    report_generator = ExcelReportGenerator()
    report_generator.generate_report(metrics_list, output_file)
    
    # Summary
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total repositories: {len(metrics_list)}")
    print(f"Successful: {sum(1 for m in metrics_list if m.analysis_status == 'success')}")
    print(f"Failed: {sum(1 for m in metrics_list if m.analysis_status == 'failed')}")
    print(f"\n📄 Report: {output_file.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
