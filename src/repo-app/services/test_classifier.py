"""
Test file classification service.

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from typing import List, Dict

from ..constants import TEST_PATTERNS, TEST_KEYWORDS, FEATURE_FILE_PATTERN


class TestFileClassifier:
    """Classifies test files by type (unit, e2e, performance, etc.)"""
    
    def find_test_files(self, repo_path: Path) -> List[Path]:
        """
        Find all test files in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of unique test file paths
        """
        test_files = []
        
        for pattern in TEST_PATTERNS:
            test_files.extend(repo_path.rglob(pattern))
        
        return list(set(test_files))
    
    def classify_test_file(self, test_file: Path) -> Dict[str, int]:
        """
        Classify a single test file by type.
        
        Args:
            test_file: Path to test file
            
        Returns:
            Dictionary with test type as key and count as value
        """
        try:
            name_lower = test_file.name.lower()
            content = test_file.read_text().lower()
            
            # Count test functions/methods
            test_count = self._count_tests(content)
            
            # Classify by keywords
            test_type = self._determine_test_type(name_lower, content, test_file)
            
            return {test_type: test_count}
        except Exception:
            return {"unit": 1}  # Default fallback
    
    def find_feature_files(self, repo_path: Path) -> List[Path]:
        """Find BDD feature files"""
        return list(repo_path.rglob(FEATURE_FILE_PATTERN))
    
    def count_bdd_scenarios(self, feature_files: List[Path]) -> int:
        """Count BDD scenarios in feature files"""
        total_scenarios = 0
        
        for feature_file in feature_files:
            try:
                content = feature_file.read_text()
                total_scenarios += content.count("Scenario:")
                total_scenarios += content.count("Scenario Outline:")
            except Exception:
                continue
        
        return total_scenarios
    
    def _count_tests(self, content: str) -> int:
        """Count test functions/methods in file content"""
        count = (
            content.count("def test_") +
            content.count("it(") +
            content.count("test(")
        )
        return max(count, 1)  # Assume at least 1 test if file exists
    
    def _determine_test_type(self, filename: str, content: str, file_path: Path) -> str:
        """Determine test type based on keywords"""
        
        # Check keywords in order of specificity
        for test_type, keywords in TEST_KEYWORDS.items():
            if self._matches_keywords(filename, content, file_path, keywords):
                return test_type
        
        return "unit"  # Default to unit test
    
    def _matches_keywords(
        self,
        filename: str,
        content: str,
        file_path: Path,
        keywords: List[str]
    ) -> bool:
        """Check if filename or content matches any keywords"""
        for keyword in keywords:
            if keyword in filename or keyword in content or keyword in str(file_path):
                return True
        return False
