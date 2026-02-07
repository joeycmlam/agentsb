"""
Test coverage extraction service.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict

from ..constants import COVERAGE_FILES


class CoverageExtractor:
    """Extracts coverage metrics from coverage reports"""
    
    def extract_coverage(self, repo_path: Path) -> Optional[Dict[str, float | int]]:
        """
        Extract coverage metrics from existing reports.
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            Dictionary with coverage metrics or None if not found
        """
        # Try Python coverage
        python_coverage = self._extract_python_coverage(repo_path)
        if python_coverage:
            return python_coverage
        
        # Try JavaScript coverage
        js_coverage = self._extract_js_coverage(repo_path)
        if js_coverage:
            return js_coverage
        
        return None
    
    def _extract_python_coverage(self, repo_path: Path) -> Optional[Dict[str, float | int]]:
        """Extract Python coverage from coverage.xml"""
        coverage_file = repo_path / COVERAGE_FILES["python"]
        
        if not coverage_file.exists():
            return None
        
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            coverage_elem = root.find(".//coverage")
            if coverage_elem is None:
                return None
            
            line_rate = float(coverage_elem.get("line-rate", 0))
            lines_covered = int(coverage_elem.get("lines-covered", 0))
            lines_valid = int(coverage_elem.get("lines-valid", 0))
            
            return {
                "coverage_pct": line_rate * 100,
                "lines_covered": lines_covered,
                "lines_total": lines_valid
            }
        except Exception:
            return None
    
    def _extract_js_coverage(self, repo_path: Path) -> Optional[Dict[str, float | int]]:
        """Extract JavaScript coverage from coverage-summary.json"""
        coverage_file = repo_path / COVERAGE_FILES["javascript"]
        
        if not coverage_file.exists():
            return None
        
        try:
            data = json.loads(coverage_file.read_text())
            total = data.get("total", {})
            lines = total.get("lines", {})
            
            return {
                "coverage_pct": lines.get("pct", 0),
                "lines_covered": lines.get("covered", 0),
                "lines_total": lines.get("total", 0)
            }
        except Exception:
            return None
