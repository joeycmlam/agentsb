"""
CI/CD pipeline detection service.

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from typing import Dict, List

from ..constants import CICD_PLATFORMS, CICD_KEYWORDS


class CICDDetector:
    """Detects CI/CD platforms and capabilities"""
    
    def detect_cicd(self, repo_path: Path) -> Dict[str, bool | str | List[str]]:
        """
        Detect CI/CD configuration and capabilities.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            Dictionary with CI/CD detection results
        """
        result = {
            "has_cicd_pipeline": False,
            "cicd_platform": "None",
            "has_automated_testing": False,
            "has_security_scanning": False,
            "has_deployment_automation": False,
            "cicd_workflows": [],
        }
        
        platforms_detected = []
        all_workflows = []
        
        # Detect each CI/CD platform
        for platform_name, config_path in CICD_PLATFORMS.items():
            detected, workflows, capabilities = self._detect_platform(
                repo_path,
                platform_name,
                config_path
            )
            
            if detected:
                platforms_detected.append(platform_name)
                all_workflows.extend(workflows)
                
                # Aggregate capabilities
                result["has_automated_testing"] |= capabilities["testing"]
                result["has_security_scanning"] |= capabilities["security"]
                result["has_deployment_automation"] |= capabilities["deployment"]
        
        # Update results
        if platforms_detected:
            result["has_cicd_pipeline"] = True
            result["cicd_platform"] = ", ".join(platforms_detected)
            result["cicd_workflows"] = all_workflows
        
        return result
    
    def _detect_platform(
        self,
        repo_path: Path,
        platform_name: str,
        config_path: str
    ) -> tuple[bool, List[str], Dict[str, bool]]:
        """
        Detect a specific CI/CD platform.
        
        Returns:
            Tuple of (detected, workflow_names, capabilities)
        """
        full_path = repo_path / config_path
        
        # Handle directory-based platforms (GitHub Actions)
        if full_path.is_dir():
            return self._detect_workflow_directory(full_path)
        
        # Handle file-based platforms
        if full_path.is_file():
            return self._detect_workflow_file(full_path, config_path)
        
        return False, [], {"testing": False, "security": False, "deployment": False}
    
    def _detect_workflow_directory(self, workflow_dir: Path) -> tuple[bool, List[str], Dict[str, bool]]:
        """Detect workflows in a directory (e.g., GitHub Actions)"""
        workflow_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
        
        if not workflow_files:
            return False, [], {"testing": False, "security": False, "deployment": False}
        
        workflows = [f.stem for f in workflow_files]
        capabilities = {
            "testing": False,
            "security": False,
            "deployment": False,
        }
        
        # Analyze all workflow files
        for workflow_file in workflow_files:
            file_capabilities = self._analyze_workflow_content(workflow_file)
            capabilities["testing"] |= file_capabilities["testing"]
            capabilities["security"] |= file_capabilities["security"]
            capabilities["deployment"] |= file_capabilities["deployment"]
        
        return True, workflows, capabilities
    
    def _detect_workflow_file(
        self,
        workflow_file: Path,
        config_name: str
    ) -> tuple[bool, List[str], Dict[str, bool]]:
        """Detect single workflow file"""
        capabilities = self._analyze_workflow_content(workflow_file)
        return True, [config_name], capabilities
    
    def _analyze_workflow_content(self, workflow_file: Path) -> Dict[str, bool]:
        """Analyze workflow file content for capabilities"""
        capabilities = {
            "testing": False,
            "security": False,
            "deployment": False,
        }
        
        try:
            content = workflow_file.read_text().lower()
            
            for capability, keywords in CICD_KEYWORDS.items():
                if self._content_has_keywords(content, keywords):
                    capabilities[capability] = True
        except Exception:
            pass
        
        return capabilities
    
    def _content_has_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains any of the keywords"""
        return any(keyword in content for keyword in keywords)
