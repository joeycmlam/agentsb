"""
Coverage analyzer for extracting test coverage metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
from pathlib import Path

from models import TestMetrics
from logger import get_logger, log_metric


class CoverageAnalyzer:
    """Extracts coverage metrics from coverage reports"""
    
    def extract_coverage(self, repo_path: Path, metrics: TestMetrics):
        """
        Extract coverage from existing reports.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to populate with coverage data
        """
        logger = get_logger()
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
        """
        Parse Python coverage.xml file.
        
        Args:
            coverage_file: Path to coverage.xml
            metrics: TestMetrics object to update
        """
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
        """
        Parse JavaScript coverage-summary.json.
        
        Args:
            coverage_file: Path to coverage-summary.json
            metrics: TestMetrics object to update
        """
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
