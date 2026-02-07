"""
Test framework detection service.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
from pathlib import Path
from typing import List

from ..constants import FRAMEWORK_INDICATORS


class FrameworkDetector:
    """Detects test frameworks in a repository"""
    
    def detect_frameworks(self, repo_path: Path) -> List[str]:
        """
        Detect test frameworks used in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of detected framework names
        """
        frameworks = []
        
        frameworks.extend(self._detect_from_requirements(repo_path))
        frameworks.extend(self._detect_from_package_json(repo_path))
        
        return frameworks
    
    def _detect_from_requirements(self, repo_path: Path) -> List[str]:
        """Detect Python test frameworks from requirements.txt"""
        frameworks = []
        requirements_file = repo_path / "requirements.txt"
        
        if not requirements_file.exists():
            return frameworks
        
        try:
            content = requirements_file.read_text()
            indicators = FRAMEWORK_INDICATORS["requirements.txt"]
            
            for keyword, framework_name in indicators.items():
                if keyword in content:
                    frameworks.append(framework_name)
        except Exception:
            pass
        
        return frameworks
    
    def _detect_from_package_json(self, repo_path: Path) -> List[str]:
        """Detect JavaScript/TypeScript test frameworks from package.json"""
        frameworks = []
        package_file = repo_path / "package.json"
        
        if not package_file.exists():
            return frameworks
        
        try:
            pkg = json.loads(package_file.read_text())
            dependencies = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {})
            }
            
            indicators = FRAMEWORK_INDICATORS["package.json"]
            
            for keyword, framework_name in indicators.items():
                if keyword in dependencies:
                    frameworks.append(framework_name)
        except Exception:
            pass
        
        return frameworks
