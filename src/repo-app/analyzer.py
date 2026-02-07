"""
Repository analyzer for test coverage and CI/CD metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
import logging
import re
import asyncio
import subprocess
from pathlib import Path
from typing import List
from datetime import datetime

from models import TestMetrics
from logger import get_logger, log_repo_analysis_start, log_repo_analysis_end, log_metric, log_section

# GitHub Copilot SDK imports
try:
    from copilot import CopilotClient
    COPILOT_SDK_AVAILABLE = True
except ImportError:
    COPILOT_SDK_AVAILABLE = False
    CopilotClient = None


class RepositoryAnalyzer:
    """Analyzes repository test structure and coverage"""
    
    def __init__(self, use_copilot: bool = True):
        self.use_copilot = use_copilot and COPILOT_SDK_AVAILABLE
        self.copilot_client = None
        self.copilot_session = None
        self._copilot_started = False
    
    async def _init_copilot(self):
        """Async initialization of Copilot client"""
        logger = get_logger()
        if self.use_copilot and not self._copilot_started:
            try:
                self.copilot_client = CopilotClient()
                await self.copilot_client.start()
                self._copilot_started = True
                logger.info("   🤖 GitHub Copilot SDK initialized")
            except Exception as e:
                logger.warning(f"Copilot SDK initialization failed: {e}")
                self.use_copilot = False
                self.copilot_client = None
    
    async def _cleanup_copilot(self):
        """Async cleanup of Copilot client"""
        logger = get_logger()
        if self.copilot_client and self._copilot_started:
            try:
                if self.copilot_session:
                    await self.copilot_session.destroy()
                    self.copilot_session = None
                await self.copilot_client.stop()
                self._copilot_started = False
            except Exception as e:
                logger.warning(f"Copilot cleanup error: {e}")
    
    async def analyze_repository(self, repo_path: Path, repo_name: str, repo_url: str) -> TestMetrics:
        """Analyze a repository and return test metrics"""
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
            
            # Analyze test files
            await self._analyze_test_files(repo_path, metrics)
            
            # Extract coverage metrics
            self._extract_coverage(repo_path, metrics)
            
            # Analyze commit activity
            await self._analyze_commit_activity(repo_path, metrics)
            
            # Detect CI/CD pipeline
            self._detect_cicd_pipeline(repo_path, metrics)
            
            metrics.analysis_status = "success"
            log_repo_analysis_end(repo_name, True)
            
        except Exception as e:
            metrics.analysis_status = "failed"
            metrics.error_message = str(e)
            logger.error(f"Analysis failed: {e}", exc_info=True)
            log_repo_analysis_end(repo_name, False)
        
        return metrics
    
    def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages in repository with optimized single scan"""
        from collections import defaultdict
        
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
            except (json.JSONDecodeError, KeyError, IOError) as e:
                get_logger().debug(f"Failed to parse package.json: {e}")
        
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
        logger = get_logger()
        if not self.copilot_client:
            logger.debug("Copilot not available, using pattern-based analysis")
            self._analyze_with_patterns(test_files, metrics)
            return
        
        logger.info("   🤖 Using Copilot SDK for intelligent test classification")
        
        try:
            # Create a new session for this analysis
            self.copilot_session = await self.copilot_client.create_session()
            
            # Process files in batches to avoid overwhelming the model
            batch_size = 10
            for i in range(0, len(test_files), batch_size):
                batch = test_files[i:i+batch_size]
                await self._classify_batch_with_copilot(batch, metrics)
            
            # Clean up session
            if self.copilot_session:
                await self.copilot_session.destroy()
                self.copilot_session = None
                
        except Exception as e:
            logger = get_logger()
            logger.warning(f"Copilot analysis failed: {e}")
            logger.debug("Falling back to pattern-based analysis")
            self._analyze_with_patterns(test_files, metrics)
    
    def _prepare_file_info_for_copilot(self, test_files: List[Path]) -> List[dict]:
        """Prepare file information for Copilot analysis"""
        file_info = []
        for test_file in test_files:
            try:
                content = test_file.read_text()[:500]  # First 500 chars
                file_info.append({
                    "path": str(test_file),
                    "name": test_file.name,
                    "preview": content
                })
            except Exception as e:
                get_logger().debug(f"Failed to read {test_file.name}: {e}")
                continue
        return file_info
    
    def _build_copilot_classification_prompt(self, file_info: List[dict]) -> str:
        """Build prompt for Copilot test classification"""
        return f"""Analyze these test files and classify each as one of: unit, integration, e2e, performance, or smoke test.

For each file, respond with the format: "filename: type"

Files to analyze:
{json.dumps(file_info, indent=2)}

Classifications:"""
    
    def _log_copilot_response_debug(self, response):
        """Log Copilot response details for debugging"""
        logger = get_logger()
        if not logger.isEnabledFor(logging.DEBUG):
            return
        
        logger.debug("="*80)
        logger.debug("COPILOT RESPONSE DEBUG INFO")
        logger.debug("="*80)
        logger.debug(f"Response Type: {type(response)}")
        logger.debug(f"Response: {response}")
        
        if response:
            logger.debug(f"Response Attributes: {dir(response)}")
            
            if hasattr(response, 'data'):
                logger.debug(f"Response.data Type: {type(response.data)}")
                logger.debug(f"Response.data: {response.data}")
                
                if hasattr(response.data, 'content'):
                    content_len = len(response.data.content) if response.data.content else 0
                    logger.debug(f"Response.data.content Length: {content_len}")
                    logger.debug(f"Response.data.content: {response.data.content}")
        else:
            logger.debug("Response is None or falsy")
        
        logger.debug("="*80)
    
    def _parse_copilot_classifications(self, response) -> List[dict]:
        """Parse test classifications from Copilot response"""
        classifications = []
        
        if not response:
            return classifications
        
        if not hasattr(response, 'data') or not hasattr(response.data, 'content'):
            return classifications
        
        content = response.data.content
        if not content:
            return classifications
        
        # Extract classifications from response
        for line in content.split('\n'):
            # Look for patterns like "file.py: unit" or "file.py -> e2e"
            match = re.search(r'([^:]+):\s*(unit|integration|e2e|performance|smoke)', line, re.IGNORECASE)
            if match:
                classifications.append({
                    "file": match.group(1).strip(),
                    "type": match.group(2).lower()
                })
        
        return classifications
    
    def _apply_classifications_to_metrics(self, classifications: List[dict], metrics: TestMetrics):
        """Apply test classifications to metrics object"""
        for classification in classifications:
            test_type = classification["type"]
            count = 1  # Assume 1 test per file
            
            if test_type == "e2e":
                metrics.e2e_test_count += count
                metrics.e2e_test_files += 1
            elif test_type == "performance":
                metrics.performance_test_count += count
                metrics.performance_test_files += 1
            elif test_type == "smoke":
                metrics.smoke_test_count += count
                metrics.smoke_test_files += 1
            elif test_type == "integration":
                metrics.unit_test_count += count  # Count as unit for now
            else:  # unit
                metrics.unit_test_count += count
    
    def _classify_unmatched_files(self, test_files: List[Path], classifications: List[dict], metrics: TestMetrics):
        """Classify files not matched by Copilot using pattern matching"""
        classified_files = {c["file"] for c in classifications}
        
        for test_file in test_files:
            if str(test_file) not in classified_files and test_file.name not in classified_files:
                self._classify_by_pattern(test_file, metrics)
    
    async def _classify_batch_with_copilot(self, test_files: List[Path], metrics: TestMetrics):
        """Classify a batch of test files using Copilot (refactored for lower complexity)"""
        if not self.copilot_session:
            return
        
        # Step 1: Prepare file information
        file_info = self._prepare_file_info_for_copilot(test_files)
        if not file_info:
            return
        
        # Step 2: Send request to Copilot
        try:
            from copilot.types import MessageOptions
            
            prompt = self._build_copilot_classification_prompt(file_info)
            message_options: MessageOptions = {"prompt": prompt}
            
            response = await self.copilot_session.send_and_wait(message_options, timeout=30.0)
            
            # Step 3: Log response for debugging
            self._log_copilot_response_debug(response)
            
            # Step 4: Parse classifications
            classifications = self._parse_copilot_classifications(response)
            
            # Step 5: Apply classifications to metrics
            self._apply_classifications_to_metrics(classifications, metrics)
            
            # Step 6: Handle unclassified files
            self._classify_unmatched_files(test_files, classifications, metrics)
        
        except Exception as e:
            # If Copilot fails, fall back to pattern matching for all files
            logger = get_logger()
            logger.warning(f"Copilot classification failed: {e}")
            for test_file in test_files:
                self._classify_by_pattern(test_file, metrics)
    
    def _analyze_with_patterns(self, test_files: List[Path], metrics: TestMetrics):
        """Fallback: Pattern-based test classification"""
        logger = get_logger()
        logger.debug("Using pattern-based analysis")
        
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
    
    def _extract_coverage(self, repo_path: Path, metrics: TestMetrics):
        """Extract coverage from existing reports or run tests"""
        logger = get_logger()
        
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
            logger.debug("No existing coverage reports found")
    
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
            
            log_metric("Python Coverage", f"{metrics.unit_test_coverage_pct:.1f}%")
        except Exception as e:
            get_logger().warning(f"Failed to parse coverage.xml: {e}")
    
    def _parse_js_coverage_json(self, coverage_file: Path, metrics: TestMetrics):
        """Parse JavaScript coverage-summary.json"""
        try:
            data = json.loads(coverage_file.read_text())
            total = data.get("total", {})
            
            lines = total.get("lines", {})
            metrics.unit_test_coverage_pct = lines.get("pct", 0)
            metrics.unit_test_lines_covered = lines.get("covered", 0)
            metrics.unit_test_lines_total = lines.get("total", 0)
            
            log_metric("JS Coverage", f"{metrics.unit_test_coverage_pct:.1f}%")
        except Exception as e:
            get_logger().warning(f"Failed to parse coverage-summary.json: {e}")
    
    async def _analyze_commit_activity(self, repo_path: Path, metrics: TestMetrics):
        """Analyze git commit history for activity metrics"""
        try:
            # Total commits
            process = await asyncio.create_subprocess_exec(
                "git", "rev-list", "--count", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                metrics.total_commits = int(stdout.decode().strip())
            
            # Commits in last 30 days
            process = await asyncio.create_subprocess_exec(
                "git", "rev-list", "--count", "--since=30.days.ago", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                metrics.commits_last_30_days = int(stdout.decode().strip())
            
            # Commits in last 90 days
            process = await asyncio.create_subprocess_exec(
                "git", "rev-list", "--count", "--since=90.days.ago", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                metrics.commits_last_90_days = int(stdout.decode().strip())
            
            # Commits in last year
            process = await asyncio.create_subprocess_exec(
                "git", "rev-list", "--count", "--since=1.year.ago", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                metrics.commits_last_year = int(stdout.decode().strip())
            
            # Average commits per week (based on last 90 days)
            if metrics.commits_last_90_days > 0:
                metrics.avg_commits_per_week = round(metrics.commits_last_90_days / (90 / 7), 2)
            
            # Active contributors (last 90 days)
            process = await asyncio.create_subprocess_exec(
                "git", "shortlog", "-sn", "--since=90.days.ago", "HEAD",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                contributors = [line.strip() for line in stdout.decode().strip().split('\n') if line.strip()]
                metrics.active_contributors = len(contributors)
            
            log_metric("Commits", f"{metrics.total_commits} total, {metrics.commits_last_30_days} (30d), "
                       f"{metrics.avg_commits_per_week}/week avg, {metrics.active_contributors} contributors")
            
        except Exception as e:
            get_logger().warning(f"Commit analysis failed: {e}")
    
    def _detect_cicd_pipeline(self, repo_path: Path, metrics: TestMetrics):
        """Detect CI/CD pipeline configuration and capabilities"""
        try:
            platforms_detected = []
            
            # GitHub Actions
            gh_workflows = repo_path / ".github" / "workflows"
            if gh_workflows.exists():
                workflow_files = list(gh_workflows.glob("*.yml")) + list(gh_workflows.glob("*.yaml"))
                if workflow_files:
                    platforms_detected.append("GitHub Actions")
                    self._analyze_github_workflows(workflow_files, metrics)
            
            # GitLab CI
            gitlab_ci = repo_path / ".gitlab-ci.yml"
            if gitlab_ci.exists():
                platforms_detected.append("GitLab CI")
                self._analyze_gitlab_ci(gitlab_ci, metrics)
            
            # Jenkins
            jenkinsfile = repo_path / "Jenkinsfile"
            if jenkinsfile.exists():
                platforms_detected.append("Jenkins")
                self._analyze_jenkinsfile(jenkinsfile, metrics)
            
            # CircleCI
            circleci_config = repo_path / ".circleci" / "config.yml"
            if circleci_config.exists():
                platforms_detected.append("CircleCI")
                self._analyze_circleci_config(circleci_config, metrics)
            
            # Travis CI
            travis_config = repo_path / ".travis.yml"
            if travis_config.exists():
                platforms_detected.append("Travis CI")
                self._analyze_travis_config(travis_config, metrics)
            
            # Azure Pipelines
            azure_pipelines = repo_path / "azure-pipelines.yml"
            if azure_pipelines.exists():
                platforms_detected.append("Azure Pipelines")
                self._analyze_azure_pipelines(azure_pipelines, metrics)
            
            # Set CI/CD status
            logger = get_logger()
            if platforms_detected:
                metrics.has_cicd_pipeline = True
                metrics.cicd_platform = ", ".join(platforms_detected)
                log_metric("CI/CD", metrics.cicd_platform)
                logger.info(f"      - Automated Testing: {'✅' if metrics.has_automated_testing else '❌'}")
                logger.info(f"      - Security Scanning: {'✅' if metrics.has_security_scanning else '❌'}")
                logger.info(f"      - Deployment: {'✅' if metrics.has_deployment_automation else '❌'}")
            else:
                log_metric("CI/CD", "Not detected")
            
        except Exception as e:
            get_logger().warning(f"CI/CD detection failed: {e}")
    
    def _analyze_github_workflows(self, workflow_files: List[Path], metrics: TestMetrics):
        """Analyze GitHub Actions workflow files"""
        for workflow_file in workflow_files:
            try:
                content = workflow_file.read_text().lower()
                workflow_name = workflow_file.stem
                metrics.cicd_workflows.append(workflow_name)
                
                # Detect automated testing
                test_keywords = ['test', 'pytest', 'jest', 'npm test', 'npm run test', 'mvn test', 'go test']
                if any(keyword in content for keyword in test_keywords):
                    metrics.has_automated_testing = True
                
                # Detect security scanning
                security_keywords = [
                    'codeql', 'snyk', 'trivy', 'security', 'vulnerability', 'scan',
                    'dependabot', 'npm audit', 'safety check', 'bandit'
                ]
                if any(keyword in content for keyword in security_keywords):
                    metrics.has_security_scanning = True
                
                # Detect deployment
                deploy_keywords = [
                    'deploy', 'deployment', 'publish', 'release', 'docker push',
                    'kubectl apply', 'terraform apply', 'aws deploy', 'azure deploy',
                    'gcloud deploy', 'heroku', 'vercel', 'netlify'
                ]
                if any(keyword in content for keyword in deploy_keywords):
                    metrics.has_deployment_automation = True
                
            except Exception as e:
                get_logger().debug(f"Failed to analyze workflow {workflow_file.name}: {e}")
    
    def _analyze_gitlab_ci(self, config_file: Path, metrics: TestMetrics):
        """Analyze GitLab CI configuration"""
        try:
            content = config_file.read_text().lower()
            metrics.cicd_workflows.append(".gitlab-ci.yml")
            
            # Detect test stage
            if 'test:' in content or 'stages:' in content:
                metrics.has_automated_testing = True
            
            # Detect security scanning
            if any(keyword in content for keyword in ['sast', 'dependency_scanning', 'security', 'container_scanning']):
                metrics.has_security_scanning = True
            
            # Detect deployment
            if any(keyword in content for keyword in ['deploy:', 'production:', 'staging:']):
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze GitLab CI: {e}")
    
    def _analyze_jenkinsfile(self, jenkinsfile: Path, metrics: TestMetrics):
        """Analyze Jenkinsfile"""
        try:
            content = jenkinsfile.read_text().lower()
            metrics.cicd_workflows.append("Jenkinsfile")
            
            # Detect test stage
            if any(keyword in content for keyword in ['test', 'stage(\'test\')', 'stage("test")']):
                metrics.has_automated_testing = True
            
            # Detect security scanning
            if any(keyword in content for keyword in ['sonar', 'security', 'owasp']):
                metrics.has_security_scanning = True
            
            # Detect deployment
            if any(keyword in content for keyword in ['deploy', 'stage(\'deploy\')', 'stage("deploy")']):
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze Jenkinsfile: {e}")
    
    def _analyze_circleci_config(self, config_file: Path, metrics: TestMetrics):
        """Analyze CircleCI configuration"""
        try:
            content = config_file.read_text().lower()
            metrics.cicd_workflows.append(".circleci/config.yml")
            
            # Detect testing
            if 'test' in content:
                metrics.has_automated_testing = True
            
            # Detect security
            if any(keyword in content for keyword in ['security', 'vulnerability', 'scan']):
                metrics.has_security_scanning = True
            
            # Detect deployment
            if 'deploy' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze CircleCI config: {e}")
    
    def _analyze_travis_config(self, config_file: Path, metrics: TestMetrics):
        """Analyze Travis CI configuration"""
        try:
            content = config_file.read_text().lower()
            metrics.cicd_workflows.append(".travis.yml")
            
            # Detect testing (usually in script section)
            if 'script:' in content:
                metrics.has_automated_testing = True
            
            # Detect deployment
            if 'deploy:' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze Travis CI config: {e}")
    
    def _analyze_azure_pipelines(self, config_file: Path, metrics: TestMetrics):
        """Analyze Azure Pipelines configuration"""
        try:
            content = config_file.read_text().lower()
            metrics.cicd_workflows.append("azure-pipelines.yml")
            
            # Detect testing
            if 'test' in content:
                metrics.has_automated_testing = True
            
            # Detect security
            if any(keyword in content for keyword in ['security', 'vulnerability']):
                metrics.has_security_scanning = True
            
            # Detect deployment
            if 'deployment:' in content or 'deploy' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze Azure Pipelines: {e}")
