"""
Test coverage generation functionality.

Author: Automated Software Engineering Team
Date: February 2026
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest

# Add src/repo-app to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "repo-app"))

from analyzers.coverage_analyzer import CoverageAnalyzer, STALE_THRESHOLD_HOURS
from models import TestMetrics


class TestCoverageGeneration:
    """Test coverage generation functionality"""
    
    def test_is_coverage_stale_missing_file(self):
        """Test staleness check for missing file"""
        analyzer = CoverageAnalyzer()
        assert analyzer._is_coverage_stale(None) is True
        assert analyzer._is_coverage_stale(Path("/nonexistent/file.xml")) is True
    
    def test_is_coverage_stale_fresh_file(self, tmp_path):
        """Test staleness check for fresh file"""
        # Create a fresh file
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text("<coverage></coverage>")
        
        analyzer = CoverageAnalyzer()
        assert analyzer._is_coverage_stale(coverage_file) is False
    
    def test_is_coverage_stale_old_file(self, tmp_path):
        """Test staleness check for old file"""
        # Create a file and manually set old timestamp
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text("<coverage></coverage>")
        
        # Set file modification time to 48 hours ago
        old_time = (datetime.now() - timedelta(hours=48)).timestamp()
        import os
        os.utime(coverage_file, (old_time, old_time))
        
        analyzer = CoverageAnalyzer()
        assert analyzer._is_coverage_stale(coverage_file) is True
    
    def test_validate_tools_installed_python(self):
        """Test tool validation for Python projects"""
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            test_frameworks=["pytest"]
        )
        
        # This will return actual missing tools or empty list
        missing = analyzer._validate_tools_installed(metrics)
        assert isinstance(missing, list)
    
    def test_validate_tools_installed_javascript(self):
        """Test tool validation for JavaScript projects"""
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            test_frameworks=["Jest"]
        )
        
        missing = analyzer._validate_tools_installed(metrics)
        assert isinstance(missing, list)
    
    @pytest.mark.asyncio
    async def test_determine_coverage_command_python(self):
        """Test coverage command determination for Python"""
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            languages=["Python"],
            test_frameworks=["pytest"]
        )
        
        command = await analyzer._determine_coverage_command(Path("/tmp"), metrics)
        assert command is not None
        assert "pytest" in command or "coverage" in command
    
    @pytest.mark.asyncio
    async def test_determine_coverage_command_javascript(self):
        """Test coverage command determination for JavaScript"""
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            languages=["JavaScript"],
            test_frameworks=["Jest"]
        )
        
        command = await analyzer._determine_coverage_command(Path("/tmp"), metrics)
        assert command is not None
        assert "npm" in command or "jest" in command
    
    @pytest.mark.asyncio
    async def test_determine_coverage_command_with_copilot(self):
        """Test coverage command determination with Copilot service"""
        # Mock Copilot service
        mock_copilot = Mock()
        mock_copilot.is_available.return_value = True
        mock_copilot.send_prompt = AsyncMock(return_value="coverage run -m pytest && coverage xml")
        
        analyzer = CoverageAnalyzer(copilot_service=mock_copilot)
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            languages=["Python"],
            test_frameworks=["pytest"]
        )
        
        command = await analyzer._determine_coverage_command(Path("/tmp"), metrics)
        assert command == "coverage run -m pytest && coverage xml"
        mock_copilot.send_prompt.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_coverage_if_needed_no_frameworks(self, tmp_path):
        """Test that coverage generation is skipped when no frameworks detected"""
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            test_frameworks=[]
        )
        
        result = await analyzer.generate_coverage_if_needed(tmp_path, metrics)
        assert result is False
        assert metrics.coverage_generated is False
    
    @pytest.mark.asyncio
    async def test_generate_coverage_if_needed_fresh_coverage(self, tmp_path):
        """Test that coverage generation is skipped for fresh reports"""
        # Create fresh coverage file
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text("<coverage></coverage>")
        
        analyzer = CoverageAnalyzer()
        metrics = TestMetrics(
            repo_name="test",
            repo_url="http://test",
            last_analyzed=datetime.now().isoformat(),
            test_frameworks=["pytest"],
            languages=["Python"]
        )
        
        result = await analyzer.generate_coverage_if_needed(tmp_path, metrics)
        assert result is False  # Skipped because fresh
        assert metrics.coverage_generated is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
