"""
Data models for repository test analysis.

Author: Automated Software Engineering Team
Date: February 2026
"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


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
    test_frameworks: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    
    # Commit activity metrics
    total_commits: int = 0
    commits_last_30_days: int = 0
    commits_last_90_days: int = 0
    commits_last_year: int = 0
    avg_commits_per_week: float = 0.0
    active_contributors: int = 0
    
    # CI/CD pipeline detection
    has_cicd_pipeline: bool = False
    cicd_platform: str = "None"
    has_automated_testing: bool = False
    has_security_scanning: bool = False
    has_deployment_automation: bool = False
    cicd_workflows: Optional[List[str]] = None
    
    # Status
    analysis_status: str = "pending"  # pending, success, partial, failed
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.test_frameworks is None:
            self.test_frameworks = []
        if self.languages is None:
            self.languages = []
        if self.cicd_workflows is None:
            self.cicd_workflows = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
