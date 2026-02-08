"""
Coverage analyzer for extracting test coverage metrics.

Author: Automated Software Engineering Team
Date: February 2026
"""

import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

from models import TestMetrics
from logger import get_logger, log_metric
from services.copilot_service import CopilotService

# Constants
TEST_TIMEOUT = 300  # 5 minutes for test execution
COVERAGE_TIMEOUT = 60  # 1 minute for coverage collection
STALE_THRESHOLD_HOURS = 24  # Report older than this triggers regeneration

# Log metric keys
COVERAGE_SOURCE_METRIC = "Coverage Source"
COVERAGE_STATUS_METRIC = "Coverage Status"


class CoverageAnalyzer:
    """Extracts coverage metrics from coverage reports"""
    
    def __init__(self, copilot_service: Optional[CopilotService] = None):
        """
        Initialize coverage analyzer.
        
        Args:
            copilot_service: Optional Copilot service for intelligent command generation
        """
        self.copilot_service = copilot_service
    
    async def generate_coverage_if_needed(self, repo_path: Path, metrics: TestMetrics) -> bool:
        """
        Generate coverage report if missing or stale.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to update
            
        Returns:
            True if new coverage was generated, False otherwise
        """
        logger = get_logger()
        
        # Check for existing coverage files in common locations
        coverage_files = [
            repo_path / "coverage.xml",
            repo_path / "coverage" / "coverage-final.json",
            repo_path / "htmlcov" / "index.html",
            repo_path / "coverage" / "coverage-summary.json"
        ]
        
        existing_coverage = None
        for coverage_file in coverage_files:
            if coverage_file.exists():
                existing_coverage = coverage_file
                break
        
        # Check if coverage is stale
        is_stale = self._is_coverage_stale(existing_coverage)
        
        if not is_stale:
            logger.debug("Coverage report is fresh, skipping generation")
            log_metric(COVERAGE_SOURCE_METRIC, "Existing (Fresh)")
            return False
        
        # Check if we have test frameworks detected
        if not metrics.test_frameworks:
            logger.debug("No test frameworks detected, cannot generate coverage")
            return False
        
        logger.info("   📊 Generating coverage report...")
        
        try:
            # Determine coverage command using Copilot or defaults
            command = await self._determine_coverage_command(repo_path, metrics)
            if not command:
                logger.warning("Could not determine coverage command")
                return False
            
            logger.debug(f"Coverage command: {command}")
            
            # Install dependencies if needed
            await self._install_dependencies(repo_path, metrics)
            
            # Execute coverage command
            success, _, stderr = await self._execute_coverage_command(command, repo_path)
            
            if success:
                logger.info("   ✅ Coverage generated successfully")
                log_metric(COVERAGE_SOURCE_METRIC, "Generated")
                metrics.coverage_generated = True
                return True
            else:
                logger.warning(f"Coverage generation failed: {stderr}")
                if existing_coverage:
                    logger.info("   ⚠️  Falling back to stale coverage report")
                    log_metric(COVERAGE_SOURCE_METRIC, "Existing (Stale)")
                return False
                
        except Exception as e:
            logger.warning(f"Coverage generation error: {e}")
            if existing_coverage:
                logger.info("   ⚠️  Falling back to stale coverage report")
                log_metric(COVERAGE_SOURCE_METRIC, "Existing (Stale)")
            return False
    
    def _is_coverage_stale(self, coverage_file: Optional[Path]) -> bool:
        """
        Check if coverage report is stale or missing.
        
        Args:
            coverage_file: Path to coverage file (None if doesn't exist)
            
        Returns:
            True if file doesn't exist or is older than threshold
        """
        logger = get_logger()
        
        if not coverage_file or not coverage_file.exists():
            logger.debug("Coverage report not found")
            log_metric(COVERAGE_STATUS_METRIC, "Missing")
            return True
        
        try:
            file_mtime = coverage_file.stat().st_mtime
            current_time = datetime.now().timestamp()
            age_hours = (current_time - file_mtime) / 3600
            
            if age_hours > STALE_THRESHOLD_HOURS:
                logger.debug(f"Coverage report is {age_hours:.1f} hours old (threshold: {STALE_THRESHOLD_HOURS}h)")
                log_metric(COVERAGE_STATUS_METRIC, f"Stale ({age_hours:.0f}h old)")
                return True
            else:
                logger.debug(f"Coverage report is {age_hours:.1f} hours old (fresh)")
                log_metric(COVERAGE_STATUS_METRIC, f"Fresh ({age_hours:.0f}h old)")
                return False
                
        except Exception as e:
            logger.debug(f"Error checking coverage staleness: {e}")
            return True
    
    async def _determine_coverage_command(self, repo_path: Path, metrics: TestMetrics) -> Optional[str]:
        """
        Determine coverage command using Copilot or predefined patterns.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics with detected frameworks and languages
            
        Returns:
            Coverage command string or None
        """
        logger = get_logger()
        
        # Try Copilot first if available
        if self.copilot_service and self.copilot_service.is_available():
            try:
                prompt = f"""
Generate a command to run tests with coverage collection for this repository.

Detected Languages: {', '.join(metrics.languages or [])}
Detected Test Frameworks: {', '.join(metrics.test_frameworks or [])}

Repository structure:
- Has package.json: {(repo_path / 'package.json').exists()}
- Has requirements.txt: {(repo_path / 'requirements.txt').exists()}
- Has pytest.ini: {(repo_path / 'pytest.ini').exists()}
- Has jest.config: {(repo_path / 'jest.config.js').exists() or (repo_path / 'jest.config.ts').exists()}

Provide ONLY the exact shell command to run (no explanations, no markdown).
Examples:
- Python: coverage run -m pytest -o asyncio_default_fixture_loop_scope=function && coverage xml
- JavaScript: npm test -- --coverage
"""
                response = await self.copilot_service.send_prompt(prompt)
                if response:
                    # Extract command from response (strip markdown, explanations)
                    command = response.strip()
                    # Remove markdown code blocks if present
                    if "```" in command:
                        import re
                        match = re.search(r'```(?:bash|shell)?\s*(.+?)```', command, re.DOTALL)
                        if match:
                            command = match.group(1).strip()
                    command = command.split('\n')[0].strip()  # Take first line only
                    if command:
                        logger.debug(f"Copilot suggested command: {command}")
                        return command
            except Exception as e:
                logger.debug(f"Copilot command generation failed: {e}")
        
        # Fall back to predefined patterns
        frameworks_lower = [f.lower() for f in (metrics.test_frameworks or [])]
        
        # Python patterns
        if 'pytest' in frameworks_lower:
            return "coverage run -m pytest -o asyncio_default_fixture_loop_scope=function && coverage xml"
        elif any(f in frameworks_lower for f in ['unittest', 'python']):
            return "coverage run -m unittest discover && coverage xml"
        
        # JavaScript/TypeScript patterns
        if 'jest' in frameworks_lower:
            return "npm test -- --coverage"
        elif 'vitest' in frameworks_lower:
            return "npm run test:coverage"
        
        logger.warning("Could not determine coverage command from frameworks")
        return None
    
    async def _install_dependencies(self, repo_path: Path, metrics: TestMetrics):
        """
        Install coverage dependencies if needed.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics with detected frameworks
        """
        logger = get_logger()
        
        # Check what tools are needed
        missing_tools = self._validate_tools_installed(metrics)
        if not missing_tools:
            logger.debug("All required tools already installed")
            return
        
        logger.info(f"   📦 Installing dependencies: {', '.join(missing_tools)}")
        
        try:
            # Python dependencies
            if any(tool in missing_tools for tool in ['pytest', 'coverage']):
                requirements_file = repo_path / "requirements.txt"
                if requirements_file.exists():
                    cmd = ["pip", "install", "-q", "coverage", "pytest"]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await asyncio.wait_for(process.communicate(), timeout=120)
                    if process.returncode == 0:
                        logger.debug("Python coverage tools installed")
            
            # JavaScript dependencies
            if 'npm' not in missing_tools and (repo_path / "package.json").exists():
                # npm install should already install coverage tools from package.json
                cmd = ["npm", "install"]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.communicate(), timeout=120)
                if process.returncode == 0:
                    logger.debug("JavaScript dependencies installed")
                    
        except asyncio.TimeoutError:
            logger.warning("Dependency installation timed out")
        except Exception as e:
            logger.warning(f"Dependency installation failed: {e}")
    
    def _validate_tools_installed(self, metrics: TestMetrics) -> List[str]:
        """
        Check which required tools are missing.
        
        Args:
            metrics: TestMetrics with detected frameworks
            
        Returns:
            List of missing tool names
        """
        missing = []
        frameworks_lower = [f.lower() for f in (metrics.test_frameworks or [])]
        
        # Check Python tools
        if any(f in frameworks_lower for f in ['pytest', 'unittest']):
            if not shutil.which('pytest'):
                missing.append('pytest')
            if not shutil.which('coverage'):
                missing.append('coverage')
        
        # Check JavaScript tools
        if any(f in frameworks_lower for f in ['jest', 'vitest']):
            if not shutil.which('npm'):
                missing.append('npm')
        
        return missing
    
    async def _execute_coverage_command(self, command: str, repo_path: Path) -> Tuple[bool, str, str]:
        """
        Execute coverage command.
        
        Args:
            command: Shell command to execute
            repo_path: Path to repository root
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        logger = get_logger()
        
        try:
            # Split command for subprocess
            cmd_parts = command.split()
            
            # Handle shell operators like && by using shell
            if '&&' in command or '|' in command:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=TEST_TIMEOUT
            )
            
            success = process.returncode == 0
            return success, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            logger.warning(f"Coverage command timed out after {TEST_TIMEOUT}s")
            return False, "", "Timeout"
        except Exception as e:
            logger.warning(f"Coverage command execution failed: {e}")
            return False, "", str(e)
    
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
            logger.debug(f"Found coverage report: {coverage_xml.name}")
            self._parse_python_coverage_xml(coverage_xml, metrics)
        
        # JavaScript: coverage/coverage-summary.json
        coverage_summary = repo_path / "coverage" / "coverage-summary.json"
        if coverage_summary.exists():
            coverage_found = True
            logger.debug(f"Found coverage report: {coverage_summary.relative_to(repo_path)}")
            self._parse_js_coverage_json(coverage_summary, metrics)
        
        if coverage_found:
            source = "Generated" if getattr(metrics, 'coverage_generated', False) else "Existing"
            logger.info(f"   📊 Using {source.lower()} coverage report")
        else:
            logger.debug("No coverage reports found")
            log_metric(COVERAGE_SOURCE_METRIC, "None")
    
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
