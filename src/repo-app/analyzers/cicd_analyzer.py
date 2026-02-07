"""
CI/CD analyzer for detecting pipeline configurations and capabilities.

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from typing import List

from models import TestMetrics
from logger import get_logger, log_metric


class CICDAnalyzer:
    """Detects CI/CD pipeline configuration and capabilities"""
    
    # CI/CD capability keywords
    TEST_KEYWORDS = ['test', 'pytest', 'jest', 'npm test', 'npm run test', 'mvn test', 'go test']
    SECURITY_KEYWORDS = [
        'codeql', 'snyk', 'trivy', 'security', 'vulnerability', 'scan',
        'dependabot', 'npm audit', 'safety check', 'bandit', 'sast',
        'dependency_scanning', 'container_scanning', 'sonar', 'owasp'
    ]
    DEPLOY_KEYWORDS = [
        'deploy', 'deployment', 'publish', 'release', 'docker push',
        'kubectl apply', 'terraform apply', 'aws deploy', 'azure deploy',
        'gcloud deploy', 'heroku', 'vercel', 'netlify', 'production', 'staging'
    ]
    
    def detect_cicd_pipeline(self, repo_path: Path, metrics: TestMetrics):
        """
        Detect CI/CD pipeline configuration and capabilities.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to populate with CI/CD data
        """
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
    
    def _detect_capabilities(self, content: str) -> dict:
        """
        Detect CI/CD capabilities from config file content.
        
        Args:
            content: Configuration file content (lowercase)
            
        Returns:
            Dict with boolean flags for testing, security, deployment
        """
        return {
            "testing": any(keyword in content for keyword in self.TEST_KEYWORDS),
            "security": any(keyword in content for keyword in self.SECURITY_KEYWORDS),
            "deployment": any(keyword in content for keyword in self.DEPLOY_KEYWORDS)
        }
    
    def _analyze_github_workflows(self, workflow_files: List[Path], metrics: TestMetrics):
        """Analyze GitHub Actions workflow files"""
        for workflow_file in workflow_files:
            try:
                content = workflow_file.read_text(encoding='utf-8', errors='ignore').lower()
                workflow_name = workflow_file.stem
                metrics.cicd_workflows.append(workflow_name)
                
                capabilities = self._detect_capabilities(content)
                if capabilities["testing"]:
                    metrics.has_automated_testing = True
                if capabilities["security"]:
                    metrics.has_security_scanning = True
                if capabilities["deployment"]:
                    metrics.has_deployment_automation = True
                
            except Exception as e:
                get_logger().debug(f"Failed to analyze workflow {workflow_file.name}: {e}")
    
    def _analyze_gitlab_ci(self, config_file: Path, metrics: TestMetrics):
        """Analyze GitLab CI configuration"""
        try:
            content = config_file.read_text(encoding='utf-8', errors='ignore').lower()
            metrics.cicd_workflows.append(".gitlab-ci.yml")
            
            # Detect test stage
            if 'test:' in content or 'stages:' in content:
                metrics.has_automated_testing = True
            
            capabilities = self._detect_capabilities(content)
            if capabilities["security"]:
                metrics.has_security_scanning = True
            if capabilities["deployment"] or 'deploy:' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze GitLab CI: {e}")
    
    def _analyze_jenkinsfile(self, jenkinsfile: Path, metrics: TestMetrics):
        """Analyze Jenkinsfile"""
        try:
            content = jenkinsfile.read_text(encoding='utf-8', errors='ignore').lower()
            metrics.cicd_workflows.append("Jenkinsfile")
            
            capabilities = self._detect_capabilities(content)
            if capabilities["testing"] or 'stage(\'test\')' in content or 'stage("test")' in content:
                metrics.has_automated_testing = True
            if capabilities["security"]:
                metrics.has_security_scanning = True
            if capabilities["deployment"] or 'stage(\'deploy\')' in content or 'stage("deploy")' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze Jenkinsfile: {e}")
    
    def _analyze_circleci_config(self, config_file: Path, metrics: TestMetrics):
        """Analyze CircleCI configuration"""
        try:
            content = config_file.read_text(encoding='utf-8', errors='ignore').lower()
            metrics.cicd_workflows.append(".circleci/config.yml")
            
            capabilities = self._detect_capabilities(content)
            if capabilities["testing"]:
                metrics.has_automated_testing = True
            if capabilities["security"]:
                metrics.has_security_scanning = True
            if capabilities["deployment"]:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze CircleCI config: {e}")
    
    def _analyze_travis_config(self, config_file: Path, metrics: TestMetrics):
        """Analyze Travis CI configuration"""
        try:
            content = config_file.read_text(encoding='utf-8', errors='ignore').lower()
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
            content = config_file.read_text(encoding='utf-8', errors='ignore').lower()
            metrics.cicd_workflows.append("azure-pipelines.yml")
            
            capabilities = self._detect_capabilities(content)
            if capabilities["testing"]:
                metrics.has_automated_testing = True
            if capabilities["security"]:
                metrics.has_security_scanning = True
            if capabilities["deployment"] or 'deployment:' in content:
                metrics.has_deployment_automation = True
                
        except Exception as e:
            get_logger().debug(f"Failed to analyze Azure Pipelines: {e}")
