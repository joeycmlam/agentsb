"""
Repository analyzer orchestrator (refactored for CLEAN code principles).

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from datetime import datetime

from .models import TestMetrics
from .services import (
    LanguageDetector,
    FrameworkDetector,
    TestFileClassifier,
    CoverageExtractor,
    GitAnalyzer,
    CICDDetector,
)
from .copilot_service import CopilotTestAnalyzer


class RepositoryAnalyzer:
    """
    Orchestrates repository analysis using specialized service classes.
    
    Follows Single Responsibility Principle by delegating specific tasks
    to focused service classes.
    """
    
    def __init__(self, use_copilot: bool = True):
        """
        Initialize analyzer with dependency injection.
        
        Args:
            use_copilot: Enable GitHub Copilot SDK for intelligent analysis
        """
        # Core services (always available)
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()
        self.test_classifier = TestFileClassifier()
        self.coverage_extractor = CoverageExtractor()
        self.git_analyzer = GitAnalyzer()
        self.cicd_detector = CICDDetector()
        
        # Optional Copilot service
        self.copilot_analyzer = CopilotTestAnalyzer(enabled=use_copilot)
    
    async def analyze_repository(
        self,
        repo_path: Path,
        repo_name: str,
        repo_url: str
    ) -> TestMetrics:
        """
        Analyze a repository and return comprehensive test metrics.
        
        Args:
            repo_path: Path to cloned repository
            repo_name: Repository name
            repo_url: Repository URL
            
        Returns:
            TestMetrics object with analysis results
        """
        print(f"\n📊 Analyzing: {repo_name}")
        
        # Initialize Copilot if enabled
        await self.copilot_analyzer.initialize()
        
        metrics = TestMetrics(
            repo_name=repo_name,
            repo_url=repo_url,
            last_analyzed=datetime.now().isoformat()
        )
        
        try:
            # Detect languages and frameworks
            await self._analyze_tech_stack(repo_path, metrics)
            
            # Analyze test files
            await self._analyze_tests(repo_path, metrics)
            
            # Extract coverage metrics
            await self._analyze_coverage(repo_path, metrics)
            
            # Analyze commit activity
            await self._analyze_git_activity(repo_path, metrics)
            
            # Detect CI/CD pipeline
            await self._analyze_cicd(repo_path, metrics)
            
            metrics.analysis_status = "success"
            print(f"   ✅ Analysis complete")
            
        except Exception as e:
            metrics.analysis_status = "failed"
            metrics.error_message = str(e)
            print(f"   ❌ Analysis failed: {e}")
        
        return metrics
    
    async def cleanup(self):
        """Cleanup resources (Copilot client, etc.)"""
        await self.copilot_analyzer.cleanup()
    
    # Private helper methods (keep methods focused and small)
    
    async def _analyze_tech_stack(self, repo_path: Path, metrics: TestMetrics):
        """Detect languages and test frameworks"""
        metrics.languages = self.language_detector.detect_languages(repo_path)
        metrics.test_frameworks = self.framework_detector.detect_frameworks(repo_path)
        
        print(f"   Languages: {', '.join(metrics.languages)}")
        print(f"   Frameworks: {', '.join(metrics.test_frameworks)}")
    
    async def _analyze_tests(self, repo_path: Path, metrics: TestMetrics):
        """Analyze test files and classify them"""
        # Find all test files
        test_files = self.test_classifier.find_test_files(repo_path)
        metrics.total_test_files = len(test_files)
        
        # Classify tests (with Copilot if available, otherwise pattern-based)
        if self.copilot_analyzer.is_available():
            await self._classify_tests_with_copilot(test_files, metrics)
        else:
            self._classify_tests_with_patterns(test_files, metrics)
        
        # Analyze BDD feature files
        feature_files = self.test_classifier.find_feature_files(repo_path)
        metrics.feature_test_files = len(feature_files)
        metrics.feature_test_scenarios = self.test_classifier.count_bdd_scenarios(feature_files)
    
    async def _classify_tests_with_copilot(self, test_files: list[Path], metrics: TestMetrics):
        """Use Copilot SDK for intelligent test classification"""
        print("   🤖 Using Copilot SDK for intelligent test classification...")
        
        try:
            # Delegate to Copilot service
            classifications = await self.copilot_analyzer.classify_tests(test_files)
            
            # Update metrics from classifications
            for classification in classifications:
                self._update_metrics_from_classification(classification, metrics)
            
            # Fallback to patterns for unclassified files
            classified_files = {c["file"] for c in classifications}
            for test_file in test_files:
                if str(test_file) not in classified_files:
                    self._classify_single_test(test_file, metrics)
        
        except Exception as e:
            print(f"   ⚠️  Copilot classification failed: {e}")
            print("   📝 Falling back to pattern-based analysis...")
            self._classify_tests_with_patterns(test_files, metrics)
    
    def _classify_tests_with_patterns(self, test_files: list[Path], metrics: TestMetrics):
        """Fallback: pattern-based test classification"""
        print("   📝 Using pattern-based analysis...")
        
        for test_file in test_files:
            self._classify_single_test(test_file, metrics)
    
    def _classify_single_test(self, test_file: Path, metrics: TestMetrics):
        """Classify a single test file and update metrics"""
        classification = self.test_classifier.classify_test_file(test_file)
        
        for test_type, count in classification.items():
            if test_type == "e2e":
                metrics.e2e_test_count += count
                metrics.e2e_test_files += 1
            elif test_type == "performance":
                metrics.performance_test_count += count
                metrics.performance_test_files += 1
            elif test_type == "smoke":
                metrics.smoke_test_count += count
                metrics.smoke_test_files += 1
            else:  # unit or integration
                metrics.unit_test_count += count
    
    def _update_metrics_from_classification(self, classification: dict, metrics: TestMetrics):
        """Update metrics from a single Copilot classification result"""
        test_type = classification.get("type", "unit")
        count = classification.get("count", 1)
        
        if test_type == "e2e":
            metrics.e2e_test_count += count
            metrics.e2e_test_files += 1
        elif test_type == "performance":
            metrics.performance_test_count += count
            metrics.performance_test_files += 1
        elif test_type == "smoke":
            metrics.smoke_test_count += count
            metrics.smoke_test_files += 1
        else:  # unit or integration
            metrics.unit_test_count += count
    
    async def _analyze_coverage(self, repo_path: Path, metrics: TestMetrics):
        """Extract coverage metrics from existing reports"""
        coverage_data = self.coverage_extractor.extract_coverage(repo_path)
        
        if coverage_data:
            metrics.unit_test_coverage_pct = coverage_data["coverage_pct"]
            metrics.unit_test_lines_covered = coverage_data["lines_covered"]
            metrics.unit_test_lines_total = coverage_data["lines_total"]
            print(f"   📈 Coverage: {metrics.unit_test_coverage_pct:.1f}%")
        else:
            print("   ⚠️  No existing coverage reports found")
    
    async def _analyze_git_activity(self, repo_path: Path, metrics: TestMetrics):
        """Analyze git commit activity"""
        git_metrics = await self.git_analyzer.analyze_commit_activity(repo_path)
        
        # Update metrics object
        metrics.total_commits = git_metrics["total_commits"]
        metrics.commits_last_30_days = git_metrics["commits_last_30_days"]
        metrics.commits_last_90_days = git_metrics["commits_last_90_days"]
        metrics.commits_last_year = git_metrics["commits_last_year"]
        metrics.avg_commits_per_week = git_metrics["avg_commits_per_week"]
        metrics.active_contributors = git_metrics["active_contributors"]
        
        print(f"   📊 Commits: {metrics.total_commits} total, "
              f"{metrics.commits_last_30_days} (30d), "
              f"{metrics.avg_commits_per_week}/week avg, "
              f"{metrics.active_contributors} contributors")
    
    async def _analyze_cicd(self, repo_path: Path, metrics: TestMetrics):
        """Detect CI/CD pipeline and capabilities"""
        cicd_data = self.cicd_detector.detect_cicd(repo_path)
        
        # Update metrics
        metrics.has_cicd_pipeline = cicd_data["has_cicd_pipeline"]
        metrics.cicd_platform = cicd_data["cicd_platform"]
        metrics.has_automated_testing = cicd_data["has_automated_testing"]
        metrics.has_security_scanning = cicd_data["has_security_scanning"]
        metrics.has_deployment_automation = cicd_data["has_deployment_automation"]
        metrics.cicd_workflows = cicd_data["cicd_workflows"]
        
        if metrics.has_cicd_pipeline:
            print(f"   🔧 CI/CD: {metrics.cicd_platform}")
            print(f"      - Automated Testing: {'✅' if metrics.has_automated_testing else '❌'}")
            print(f"      - Security Scanning: {'✅' if metrics.has_security_scanning else '❌'}")
            print(f"      - Deployment: {'✅' if metrics.has_deployment_automation else '❌'}")
        else:
            print("   🔧 CI/CD: Not detected")
