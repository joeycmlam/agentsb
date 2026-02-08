"""
Test coverage report saving functionality.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
import pytest
import shutil

# Add src/repo-app to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "repo-app"))

from analyzers.coverage_analyzer import CoverageAnalyzer
from models import TestMetrics


class TestCoverageReportSaving:
    """Test coverage report saving to persistent location"""
    
    def test_save_python_coverage_report(self, tmp_path):
        """Test saving Python coverage.xml to persistent location"""
        # Create a mock coverage.xml
        coverage_content = """<?xml version="1.0" ?>
<coverage version="7.0" timestamp="1706400000000" lines-valid="100" lines-covered="75" line-rate="0.75">
    <packages>
        <package name="mypackage" line-rate="0.75" branch-rate="0.8">
        </package>
    </packages>
</coverage>"""
        
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text(coverage_content)
        
        # Test saving
        analyzer = CoverageAnalyzer()
        saved_path = analyzer._save_coverage_report(coverage_file, "test/repo")
        
        assert saved_path is not None
        assert saved_path.exists()
        assert saved_path.name == "test_repo_coverage.xml"
        assert saved_path.parent.name == "coverage"
        
        # Verify content was copied
        assert saved_path.read_text() == coverage_content
        
        # Cleanup
        if saved_path.exists():
            saved_path.unlink()
        if saved_path.parent.exists():
            shutil.rmtree(saved_path.parent.parent)
    
    def test_save_javascript_coverage_report(self, tmp_path):
        """Test saving JavaScript coverage-summary.json to persistent location"""
        # Create a mock coverage-summary.json
        coverage_content = {
            "total": {
                "lines": {"total": 100, "covered": 80, "pct": 80.0},
                "statements": {"total": 100, "covered": 80, "pct": 80.0},
                "functions": {"total": 20, "covered": 15, "pct": 75.0},
                "branches": {"total": 30, "covered": 24, "pct": 80.0}
            }
        }
        
        coverage_file = tmp_path / "coverage-summary.json"
        coverage_file.write_text(json.dumps(coverage_content))
        
        # Test saving
        analyzer = CoverageAnalyzer()
        saved_path = analyzer._save_coverage_report(coverage_file, "user/project")
        
        assert saved_path is not None
        assert saved_path.exists()
        assert saved_path.name == "user_project_coverage_summary.json"
        assert saved_path.parent.name == "coverage"
        
        # Verify content was copied
        assert json.loads(saved_path.read_text()) == coverage_content
        
        # Cleanup
        if saved_path.exists():
            saved_path.unlink()
        if saved_path.parent.exists():
            shutil.rmtree(saved_path.parent.parent)
    
    def test_extract_coverage_saves_report_path(self, tmp_path):
        """Test that extract_coverage saves the coverage report path to metrics"""
        # Create a mock coverage.xml with correct structure
        coverage_content = """<?xml version="1.0" ?>
<coverage version="7.0" timestamp="1706400000000" lines-valid="100" lines-covered="75" line-rate="0.75">
    <packages>
        <package name="test" line-rate="0.75" branch-rate="0.8">
            <classes>
                <class name="test_module.py" filename="test_module.py" line-rate="0.75">
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text(coverage_content)
        
        # Create metrics
        metrics = TestMetrics(
            repo_name="test/repo",
            repo_url="https://github.com/test/repo",
            last_analyzed=datetime.now().isoformat()
        )
        
        # Extract coverage
        analyzer = CoverageAnalyzer()
        analyzer.extract_coverage(tmp_path, metrics)
        
        # Verify coverage was extracted
        assert metrics.unit_test_coverage_pct == 75.0
        assert metrics.unit_test_lines_covered == 75
        assert metrics.unit_test_lines_total == 100
        
        # Verify coverage report path was saved
        assert metrics.coverage_report_path is not None
        assert "test_repo_coverage.xml" in metrics.coverage_report_path
        
        # Verify file exists at that path
        saved_file = Path(metrics.coverage_report_path)
        assert saved_file.exists()
        
        # Cleanup
        if saved_file.exists():
            saved_file.unlink()
        if saved_file.parent.exists():
            shutil.rmtree(saved_file.parent.parent)
    
    def test_model_has_coverage_report_path_field(self):
        """Test that TestMetrics model has coverage_report_path field"""
        metrics = TestMetrics(
            repo_name="test",
            repo_url="https://github.com/test",
            last_analyzed=datetime.now().isoformat()
        )
        
        # Verify field exists and is None by default
        assert hasattr(metrics, 'coverage_report_path')
        assert metrics.coverage_report_path is None
        
        # Verify field can be set
        metrics.coverage_report_path = "/path/to/coverage.xml"
        assert metrics.coverage_report_path == "/path/to/coverage.xml"
        
        # Verify field is included in to_dict()
        data = metrics.to_dict()
        assert 'coverage_report_path' in data
        assert data['coverage_report_path'] == "/path/to/coverage.xml"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
