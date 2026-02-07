"""
Test file analyzer for detecting and classifying test files.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from models import TestMetrics
from logger import get_logger
from constants import FILE_PREVIEW_LENGTH


class TestFileAnalyzer:
    """Analyzes and classifies test files in a repository"""
    
    def __init__(self, copilot_service=None):
        """
        Initialize test analyzer.
        
        Args:
            copilot_service: Optional CopilotService for intelligent classification
        """
        self.copilot_service = copilot_service
    
    async def analyze_test_files(self, repo_path: Path, metrics: TestMetrics):
        """
        Analyze test files using Copilot SDK or pattern matching.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to populate with results
        """
        # Find all test files
        test_files = self._find_test_files(repo_path)
        metrics.total_test_files = len(test_files)
        
        # Classify tests using Copilot or patterns
        if self.copilot_service and self.copilot_service.is_available():
            await self._analyze_with_copilot(test_files, metrics)
        else:
            self._analyze_with_patterns(test_files, metrics)
        
        # Analyze BDD feature files
        feature_files = list(repo_path.rglob("*.feature"))
        metrics.feature_test_files = len(feature_files)
        metrics.feature_test_scenarios = self._count_bdd_scenarios(feature_files)
    
    def _find_test_files(self, repo_path: Path) -> List[Path]:
        """
        Find all test files in repository.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            List of test file paths
        """
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
        return list(set(test_files))
    
    async def _analyze_with_copilot(self, test_files: List[Path], metrics: TestMetrics):
        """Use GitHub Copilot SDK to intelligently classify tests"""
        logger = get_logger()
        logger.info("   🤖 Using Copilot SDK for intelligent test classification")
        
        try:
            # Process files in batches
            batch_size = 10
            for i in range(0, len(test_files), batch_size):
                batch = test_files[i:i+batch_size]
                await self._classify_batch_with_copilot(batch, metrics)
                
        except Exception as e:
            logger.warning(f"Copilot analysis failed: {e}")
            logger.debug("Falling back to pattern-based analysis")
            self._analyze_with_patterns(test_files, metrics)
    
    async def _classify_batch_with_copilot(self, test_files: List[Path], metrics: TestMetrics):
        """Classify a batch of test files using Copilot"""
        if not self.copilot_service:
            return
        
        # Prepare file information
        file_info = self._prepare_file_info(test_files)
        if not file_info:
            return
        
        try:
            # Get classifications from Copilot
            prompt = self._build_classification_prompt(file_info)
            classifications = await self.copilot_service.classify_tests(prompt)
            
            # Apply classifications to metrics
            self._apply_classifications(classifications, metrics)
            
            # Handle unclassified files with pattern matching
            self._classify_unmatched_files(test_files, classifications, metrics)
        
        except Exception as e:
            logger = get_logger()
            logger.warning(f"Copilot classification failed: {e}")
            for test_file in test_files:
                self._classify_by_pattern(test_file, metrics)
    
    def _prepare_file_info(self, test_files: List[Path]) -> List[dict]:
        """Prepare file information for Copilot analysis"""
        file_info = []
        for test_file in test_files:
            try:
                content = test_file.read_text(encoding='utf-8', errors='ignore')[:FILE_PREVIEW_LENGTH]
                file_info.append({
                    "path": str(test_file),
                    "name": test_file.name,
                    "preview": content
                })
            except Exception as e:
                get_logger().debug(f"Failed to read {test_file.name}: {e}")
                continue
        return file_info
    
    def _build_classification_prompt(self, file_info: List[dict]) -> str:
        """Build prompt for Copilot test classification"""
        return f"""Analyze these test files and classify each as one of: unit, integration, e2e, performance, or smoke test.

For each file, respond with the format: "filename: type"

Files to analyze:
{json.dumps(file_info, indent=2)}

Classifications:"""
    
    def _apply_classifications(self, classifications: List[dict], metrics: TestMetrics):
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
                metrics.unit_test_count += count
            else:  # unit
                metrics.unit_test_count += count
    
    def _classify_unmatched_files(self, test_files: List[Path], 
                                   classifications: List[dict], metrics: TestMetrics):
        """Classify files not matched by Copilot using pattern matching"""
        classified_files = {c["file"] for c in classifications}
        
        for test_file in test_files:
            if str(test_file) not in classified_files and test_file.name not in classified_files:
                self._classify_by_pattern(test_file, metrics)
    
    def _analyze_with_patterns(self, test_files: List[Path], metrics: TestMetrics):
        """Fallback: Pattern-based test classification"""
        logger = get_logger()
        logger.debug("Using pattern-based analysis")
        
        for test_file in test_files:
            self._classify_by_pattern(test_file, metrics)
    
    def _classify_by_pattern(self, test_file: Path, metrics: TestMetrics):
        """
        Classify test by file name and content patterns.
        
        Args:
            test_file: Path to test file
            metrics: TestMetrics object to update
        """
        try:
            name_lower = test_file.name.lower()
            content = test_file.read_text(encoding='utf-8', errors='ignore').lower()
            
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
                metrics.unit_test_count += count
            else:
                # Default to unit test
                metrics.unit_test_count += count
                
        except Exception as e:
            get_logger().debug(f"Failed to classify {test_file}: {e}")
    
    def _count_bdd_scenarios(self, feature_files: List[Path]) -> int:
        """
        Count BDD scenarios in feature files.
        
        Args:
            feature_files: List of .feature file paths
            
        Returns:
            Total number of scenarios
        """
        total_scenarios = 0
        for feature_file in feature_files:
            try:
                content = feature_file.read_text(encoding='utf-8', errors='ignore')
                # Count "Scenario:" and "Scenario Outline:"
                total_scenarios += content.count("Scenario:") + content.count("Scenario Outline:")
            except Exception as e:
                get_logger().debug(f"Failed to count scenarios in {feature_file}: {e}")
        return total_scenarios
