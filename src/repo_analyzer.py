#!/usr/bin/env python3
"""
Repository Test Analysis Tool
Uses GitHub Copilot SDK for intelligent code analysis and test coverage metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile
import shutil

import pandas as pd
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# GitHub Copilot SDK imports
try:
    from github_copilot_sdk import CopilotClient, CodeAnalyzer
    COPILOT_SDK_AVAILABLE = True
except ImportError:
    print("⚠️  GitHub Copilot SDK not available. Install with: pip install github-copilot-sdk")
    COPILOT_SDK_AVAILABLE = False


@dataclass
class TestMetrics:
    """Test metrics for a repository"""
    repo_name: str
    repo_url: str
    last_analyzed: str
    
    # Unit tests
    unit_test_count: int = 0
    unit_test_coverage_pct: float = 0.0
    unit_test_lines_covered: int = 0
    unit_test_lines_total: int = 0
    
    # Feature/BDD tests
    feature_test_scenarios: int = 0
    feature_test_files: int = 0
    
    # Performance tests
    performance_test_count: int = 0
    performance_test_files: int = 0
    
    # E2E tests
    e2e_test_count: int = 0
    e2e_test_files: int = 0
    
    # Smoke tests
    smoke_test_count: int = 0
    smoke_test_files: int = 0
    
    # Overall metrics
    total_test_files: int = 0
    test_frameworks: List[str] = None
    languages: List[str] = None
    
    # Status
    analysis_status: str = "pending"  # pending, success, partial, failed
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.test_frameworks is None:
            self.test_frameworks = []
        if self.languages is None:
            self.languages = []


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
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Clone failed: {e}")
            return False


class RepositoryAnalyzer:
    """Analyzes repository test structure and coverage"""
    
    def __init__(self, copilot_client: Optional[Any] = None):
        self.copilot_client = copilot_client
    
    async def analyze_repository(self, repo_path: Path, repo_name: str, repo_url: str) -> TestMetrics:
        """Analyze a repository and return test metrics"""
        print(f"\n📊 Analyzing: {repo_name}")
        
        metrics = TestMetrics(
            repo_name=repo_name,
            repo_url=repo_url,
            last_analyzed=datetime.now().isoformat()
        )
        
        try:
            # Detect languages and frameworks
            metrics.languages = self._detect_languages(repo_path)
            metrics.test_frameworks = self._detect_test_frameworks(repo_path)
            
            print(f"   Languages: {', '.join(metrics.languages)}")
            print(f"   Frameworks: {', '.join(metrics.test_frameworks)}")
            
            # Analyze test files
            await self._analyze_test_files(repo_path, metrics)
            
            # Extract coverage metrics
            await self._extract_coverage(repo_path, metrics)
            
            metrics.analysis_status = "success"
            print(f"   ✅ Analysis complete")
            
        except Exception as e:
            metrics.analysis_status = "failed"
            metrics.error_message = str(e)
            print(f"   ❌ Analysis failed: {e}")
        
        return metrics
    
    def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages in repository"""
        languages = []
        
        # Python
        if list(repo_path.rglob("*.py")):
            languages.append("Python")
        
        # JavaScript/TypeScript
        if list(repo_path.rglob("*.js")) or list(repo_path.rglob("*.jsx")):
            languages.append("JavaScript")
        if list(repo_path.rglob("*.ts")) or list(repo_path.rglob("*.tsx")):
            languages.append("TypeScript")
        
        # Java
        if list(repo_path.rglob("*.java")):
            languages.append("Java")
        
        # Go
        if list(repo_path.rglob("*.go")):
            languages.append("Go")
        
        return languages
    
    def _detect_test_frameworks(self, repo_path: Path) -> List[str]:
        """Detect test frameworks in use"""
        frameworks = []
        
        # Check package files
        if (repo_path / "requirements.txt").exists():
            req_content = (repo_path / "requirements.txt").read_text()
            if "pytest" in req_content:
                frameworks.append("pytest")
            if "unittest" in req_content:
                frameworks.append("unittest")
            if "pytest-bdd" in req_content:
                frameworks.append("pytest-bdd")
        
        if (repo_path / "package.json").exists():
            try:
                pkg = json.loads((repo_path / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "jest" in deps:
                    frameworks.append("Jest")
                if "vitest" in deps:
                    frameworks.append("Vitest")
                if "playwright" in deps:
                    frameworks.append("Playwright")
                if "cypress" in deps:
                    frameworks.append("Cypress")
            except:
                pass
        
        return frameworks
    
    async def _analyze_test_files(self, repo_path: Path, metrics: TestMetrics):
        """Analyze test files using Copilot SDK or pattern matching"""
        
        # Find all test files
        test_patterns = [
            "test_*.py", "*_test.py", "test*.py",  # Python
            "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js",  # JS/TS
            "*Test.java",  # Java
            "*_test.go",  # Go
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(repo_path.rglob(pattern))
        
        # Remove duplicates
        test_files = list(set(test_files))
        metrics.total_test_files = len(test_files)
        
        if COPILOT_SDK_AVAILABLE and self.copilot_client:
            await self._analyze_with_copilot(test_files, metrics)
        else:
            self._analyze_with_patterns(test_files, metrics)
        
        # Analyze BDD feature files
        feature_files = list(repo_path.rglob("*.feature"))
        metrics.feature_test_files = len(feature_files)
        metrics.feature_test_scenarios = self._count_bdd_scenarios(feature_files)
    
    async def _analyze_with_copilot(self, test_files: List[Path], metrics: TestMetrics):
        """Use GitHub Copilot SDK to intelligently classify tests"""
        print("   🤖 Using Copilot SDK for intelligent analysis...")
        
        for test_file in test_files:
            try:
                code = test_file.read_text()
                
                # Use Copilot to classify test type
                prompt = f"""Analyze this test file and classify it:
                
File: {test_file.name}
Code:
```
{code[:2000]}  # First 2000 chars
```

Classify as one of: unit, integration, e2e, performance, smoke
Also count the number of test cases.
Response format: {{"type": "unit|integration|e2e|performance|smoke", "count": <number>}}
"""
                
                # Call Copilot SDK (async)
                response = await self.copilot_client.analyze(prompt)
                result = json.loads(response)
                
                test_type = result.get("type", "unit")
                count = result.get("count", 1)
                
                # Update metrics
                if test_type == "unit":
                    metrics.unit_test_count += count
                elif test_type == "e2e":
                    metrics.e2e_test_count += count
                    metrics.e2e_test_files += 1
                elif test_type == "performance":
                    metrics.performance_test_count += count
                    metrics.performance_test_files += 1
                elif test_type == "smoke":
                    metrics.smoke_test_count += count
                    metrics.smoke_test_files += 1
                
            except Exception as e:
                print(f"   ⚠️  Copilot analysis failed for {test_file.name}: {e}")
                # Fallback to pattern matching
                self._classify_by_pattern(test_file, metrics)
    
    def _analyze_with_patterns(self, test_files: List[Path], metrics: TestMetrics):
        """Fallback: Pattern-based test classification"""
        print("   📝 Using pattern-based analysis...")
        
        for test_file in test_files:
            self._classify_by_pattern(test_file, metrics)
    
    def _classify_by_pattern(self, test_file: Path, metrics: TestMetrics):
        """Classify test by file name and content patterns"""
        name_lower = test_file.name.lower()
        content = test_file.read_text().lower()
        
        # Count test functions/methods
        count = content.count("def test_") + content.count("it(") + content.count("test(")
        if count == 0:
            count = 1  # Assume at least 1 test
        
        # Classify by patterns
        if "e2e" in name_lower or "end_to_end" in name_lower or "playwright" in content:
            metrics.e2e_test_count += count
            metrics.e2e_test_files += 1
        elif "performance" in name_lower or "perf" in name_lower or "benchmark" in content:
            metrics.performance_test_count += count
            metrics.performance_test_files += 1
        elif "smoke" in name_lower:
            metrics.smoke_test_count += count
            metrics.smoke_test_files += 1
        elif "integration" in name_lower or "e2e" in str(test_file):
            # Likely integration test - count separately if needed
            metrics.unit_test_count += count
        else:
            # Default to unit test
            metrics.unit_test_count += count
    
    def _count_bdd_scenarios(self, feature_files: List[Path]) -> int:
        """Count BDD scenarios in feature files"""
        total_scenarios = 0
        for feature_file in feature_files:
            content = feature_file.read_text()
            # Count "Scenario:" and "Scenario Outline:"
            total_scenarios += content.count("Scenario:") + content.count("Scenario Outline:")
        return total_scenarios
    
    async def _extract_coverage(self, repo_path: Path, metrics: TestMetrics):
        """Extract coverage from existing reports or run tests"""
        
        # Look for existing coverage reports
        coverage_found = False
        
        # Python: coverage.xml or .coverage
        coverage_xml = repo_path / "coverage.xml"
        if coverage_xml.exists():
            coverage_found = True
            self._parse_python_coverage_xml(coverage_xml, metrics)
        
        # JavaScript: coverage/coverage-summary.json
        coverage_summary = repo_path / "coverage" / "coverage-summary.json"
        if coverage_summary.exists():
            coverage_found = True
            self._parse_js_coverage_json(coverage_summary, metrics)
        
        if not coverage_found:
            print("   ⚠️  No existing coverage reports found")
            # Optionally run tests to generate coverage
            # await self._run_tests_for_coverage(repo_path, metrics)
    
    def _parse_python_coverage_xml(self, coverage_file: Path, metrics: TestMetrics):
        """Parse Python coverage.xml file"""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Get overall coverage
            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get("line-rate", 0))
                metrics.unit_test_coverage_pct = line_rate * 100
                
                lines_covered = int(coverage_elem.get("lines-covered", 0))
                lines_valid = int(coverage_elem.get("lines-valid", 0))
                
                metrics.unit_test_lines_covered = lines_covered
                metrics.unit_test_lines_total = lines_valid
            
            print(f"   📈 Python Coverage: {metrics.unit_test_coverage_pct:.1f}%")
        except Exception as e:
            print(f"   ⚠️  Failed to parse coverage.xml: {e}")
    
    def _parse_js_coverage_json(self, coverage_file: Path, metrics: TestMetrics):
        """Parse JavaScript coverage-summary.json"""
        try:
            data = json.loads(coverage_file.read_text())
            total = data.get("total", {})
            
            lines = total.get("lines", {})
            metrics.unit_test_coverage_pct = lines.get("pct", 0)
            metrics.unit_test_lines_covered = lines.get("covered", 0)
            metrics.unit_test_lines_total = lines.get("total", 0)
            
            print(f"   📈 JS Coverage: {metrics.unit_test_coverage_pct:.1f}%")
        except Exception as e:
            print(f"   ⚠️  Failed to parse coverage-summary.json: {e}")


class ExcelReportGenerator:
    """Generate Excel report from test metrics"""
    
    def generate_report(self, metrics_list: List[TestMetrics], output_file: Path):
        """Generate Excel report with formatting"""
        print(f"\n📊 Generating Excel report: {output_file}")
        
        # Convert to DataFrame
        data = [asdict(m) for m in metrics_list]
        df = pd.DataFrame(data)
        
        # Convert lists to strings for Excel
        df['test_frameworks'] = df['test_frameworks'].apply(lambda x: ', '.join(x) if x else '')
        df['languages'] = df['languages'].apply(lambda x: ', '.join(x) if x else '')
        
        # Reorder columns
        column_order = [
            'repo_name', 'analysis_status', 'last_analyzed',
            'unit_test_count', 'unit_test_coverage_pct', 'unit_test_lines_covered', 'unit_test_lines_total',
            'feature_test_scenarios', 'feature_test_files',
            'performance_test_count', 'performance_test_files',
            'e2e_test_count', 'e2e_test_files',
            'smoke_test_count', 'smoke_test_files',
            'total_test_files', 'test_frameworks', 'languages',
            'repo_url', 'error_message'
        ]
        df = df[column_order]
        
        # Create Excel workbook with formatting
        wb = Workbook()
        ws = wb.active
        ws.title = "Repository Test Analysis"
        
        # Write header with formatting
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        headers = [
            'Repository', 'Status', 'Last Analyzed',
            'Unit Tests', 'Coverage %', 'Lines Covered', 'Total Lines',
            'Feature Scenarios', 'Feature Files',
            'Perf Tests', 'Perf Files',
            'E2E Tests', 'E2E Files',
            'Smoke Tests', 'Smoke Files',
            'Total Test Files', 'Frameworks', 'Languages',
            'Repository URL', 'Error Message'
        ]
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Write data
        for row_idx, row_data in enumerate(dataframe_to_rows(df, index=False, header=False), start=2):
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                
                # Format percentage
                if col_idx == 5:  # Coverage %
                    cell.number_format = '0.00'
                
                # Status color coding
                if col_idx == 2:  # Status
                    if value == "success":
                        cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    elif value == "failed":
                        cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Freeze header row
        ws.freeze_panes = "A2"
        
        # Save workbook
        wb.save(output_file)
        print(f"✅ Report saved: {output_file}")


async def main():
    """Main execution flow"""
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
    
    # Initialize Copilot SDK if available
    copilot_client = None
    if COPILOT_SDK_AVAILABLE:
        try:
            copilot_client = CopilotClient()
            print("✅ GitHub Copilot SDK initialized")
        except Exception as e:
            print(f"⚠️  Copilot SDK initialization failed: {e}")
    
    # Analyze each repository
    github_client = GitHubClient()
    analyzer = RepositoryAnalyzer(copilot_client)
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
