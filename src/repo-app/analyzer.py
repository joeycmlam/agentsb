"""
Repository analyzer orchestrator - coordinates specialized analyzers.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import List
from datetime import datetime

from models import TestMetrics
from logger import get_logger, log_repo_analysis_start, log_repo_analysis_end, log_metric
from services.copilot_service import CopilotService
from analyzers.test_analyzer import TestFileAnalyzer
from analyzers.coverage_analyzer import CoverageAnalyzer
from analyzers.git_analyzer import GitAnalyzer
from analyzers.cicd_analyzer import CICDAnalyzer


class RepositoryAnalyzer:
    """
    Orchestrates repository analysis using specialized analyzers.
    
    Follows Single Responsibility Principle by delegating to:
    - TestFileAnalyzer: Test file detection and classification
    - CoverageAnalyzer: Coverage metrics extraction
    - GitAnalyzer: Commit activity analysis
    - CICDAnalyzer: CI/CD pipeline detection
    - CopilotService: Copilot SDK integration
    """
    
    def __init__(self, use_copilot: bool = True):
        """
        Initialize repository analyzer with specialized components.
        
        Args:
            use_copilot: Whether to enable Copilot SDK for intelligent analysis
        """
        # Initialize Copilot service
        self.copilot_service = CopilotService(use_copilot=use_copilot)
        
        # Initialize specialized analyzers
        self.test_analyzer = TestFileAnalyzer(copilot_service=self.copilot_service)
        self.coverage_analyzer = CoverageAnalyzer()
        self.git_analyzer = GitAnalyzer()
        self.cicd_analyzer = CICDAnalyzer()
    
    async def _init_copilot(self):
        """Initialize Copilot service"""
        await self.copilot_service.start()
    
    async def _cleanup_copilot(self):
        """Clean up Copilot service"""
        await self.copilot_service.cleanup()
    
    async def analyze_repository(self, repo_path: Path, repo_name: str, repo_url: str) -> TestMetrics:
        """
        Orchestrate complete repository analysis.
        
        Args:
            repo_path: Path to repository root
            repo_name: Repository name
            repo_url: Repository URL
            
        Returns:
            TestMetrics with analysis results
        """
        logger = get_logger()
        log_repo_analysis_start(repo_name)
        
        # Initialize Copilot if needed
        await self._init_copilot()
        
        metrics = TestMetrics(
            repo_name=repo_name,
            repo_url=repo_url,
            last_analyzed=datetime.now().isoformat()
        )
        
        try:
            # Detect languages and frameworks
            metrics.languages = self._detect_languages(repo_path)
            metrics.test_frameworks = self._detect_test_frameworks(repo_path)
            
            log_metric("Languages", ', '.join(metrics.languages))
            log_metric("Frameworks", ', '.join(metrics.test_frameworks))
            
            # Delegate to specialized analyzers
            await self.test_analyzer.analyze_test_files(repo_path, metrics)
            self.coverage_analyzer.extract_coverage(repo_path, metrics)
            await self.git_analyzer.analyze_commit_activity(repo_path, metrics)
            self.cicd_analyzer.detect_cicd_pipeline(repo_path, metrics)
            
            metrics.analysis_status = "success"
            log_repo_analysis_end(repo_name, True)
            
        except Exception as e:
            metrics.analysis_status = "failed"
            metrics.error_message = str(e)
            logger.error(f"Analysis failed: {e}", exc_info=True)
            log_repo_analysis_end(repo_name, False)
        
        return metrics
    
    def _detect_languages(self, repo_path: Path) -> List[str]:
        """
        Detect programming languages in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of detected programming languages
        """
        # Count file extensions in a single filesystem scan
        extension_count = defaultdict(int)
        for file_path in repo_path.rglob("*.*"):
            ext = file_path.suffix.lower()
            extension_count[ext] += 1
        
        # Map extensions to languages
        languages = []
        
        if extension_count['.py'] > 0:
            languages.append("Python")
        
        if extension_count['.js'] > 0 or extension_count['.jsx'] > 0:
            languages.append("JavaScript")
        
        if extension_count['.ts'] > 0 or extension_count['.tsx'] > 0:
            languages.append("TypeScript")
        
        if extension_count['.java'] > 0:
            languages.append("Java")
        
        if extension_count['.go'] > 0:
            languages.append("Go")
        
        return languages
    
    def _detect_test_frameworks(self, repo_path: Path) -> List[str]:
        """
        Detect test frameworks in use.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of detected test frameworks
        """
        frameworks = []
        
        # Check Python requirements
        requirements_file = repo_path / "requirements.txt"
        if requirements_file.exists():
            try:
                req_content = requirements_file.read_text(encoding='utf-8', errors='ignore')
                if "pytest" in req_content:
                    frameworks.append("pytest")
                if "unittest" in req_content:
                    frameworks.append("unittest")
                if "pytest-bdd" in req_content:
                    frameworks.append("pytest-bdd")
            except Exception as e:
                get_logger().debug(f"Failed to read requirements.txt: {e}")
        
        # Check JavaScript/TypeScript packages
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text(encoding='utf-8', errors='ignore'))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "jest" in deps:
                    frameworks.append("Jest")
                if "vitest" in deps:
                    frameworks.append("Vitest")
                if "playwright" in deps:
                    frameworks.append("Playwright")
                if "cypress" in deps:
                    frameworks.append("Cypress")
            except Exception as e:
                get_logger().debug(f"Failed to parse package.json: {e}")
        
        return frameworks
