"""
Language detection service.

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from typing import List

from ..constants import LANGUAGE_PATTERNS


class LanguageDetector:
    """Detects programming languages in a repository"""
    
    def detect_languages(self, repo_path: Path) -> List[str]:
        """
        Detect programming languages used in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of detected language names
        """
        languages = []
        
        for language, patterns in LANGUAGE_PATTERNS.items():
            if self._has_files_matching(repo_path, patterns):
                languages.append(language)
        
        return languages
    
    def _has_files_matching(self, repo_path: Path, patterns: str | List[str]) -> bool:
        """Check if repository has files matching pattern(s)"""
        if isinstance(patterns, str):
            patterns = [patterns]
        
        for pattern in patterns:
            if list(repo_path.rglob(pattern)):
                return True
        
        return False
