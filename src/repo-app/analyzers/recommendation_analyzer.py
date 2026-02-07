"""
Recommendation analyzer for generating intelligent testing recommendations using Copilot.

Author: Automated Software Engineering Team
Date: February 2026
"""

import json
from pathlib import Path
from typing import Optional, Dict

from models import TestMetrics
from logger import get_logger


class RecommendationAnalyzer:
    """Generates testing recommendations using Copilot SDK"""
    
    # Cache for training guide content
    _training_guide_cache: Optional[str] = None
    
    def __init__(self, copilot_service=None):
        """
        Initialize recommendation analyzer.
        
        Args:
            copilot_service: CopilotService for intelligent recommendations
        """
        self.copilot_service = copilot_service
        self.logger = get_logger()
    
    async def generate_recommendations(self, repo_path: Path, metrics: TestMetrics) -> bool:
        """
        Generate testing recommendations and maturity score.
        
        Args:
            repo_path: Path to repository root
            metrics: TestMetrics object to populate with recommendations
            
        Returns:
            True if recommendations generated successfully, False otherwise
        """
        # Check if Copilot service is available
        if not self.copilot_service or not self.copilot_service.is_available():
            self.logger.warning("⚠️  Copilot service unavailable - skipping recommendations")
            return False
        
        try:
            # Calculate maturity score
            metrics.testing_maturity_score = self._calculate_maturity_score(metrics)
            
            # Analyze gaps
            gaps = self._analyze_gaps(metrics)
            
            # Generate recommendations with Copilot
            training_guide = self._load_training_guide()
            copilot_recommendations = await self._generate_with_copilot(
                repo_path, metrics, gaps, training_guide
            )
            
            if copilot_recommendations:
                metrics.recommendations = copilot_recommendations
                self.logger.info(f"   📋 Generated recommendations (Maturity Score: {metrics.testing_maturity_score:.1f}/100)")
                return True
            else:
                self.logger.warning("   ⚠️  Failed to generate Copilot recommendations")
                return False
                
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return False
    
    def _calculate_maturity_score(self, metrics: TestMetrics) -> float:
        """
        Calculate testing maturity score (0-100).
        
        Weighted scoring:
        - Test coverage % (30%)
        - CI/CD presence (20%)
        - Test diversity (20%)
        - Commit activity (15%)
        - BDD adoption (15%)
        
        Args:
            metrics: TestMetrics object
            
        Returns:
            Maturity score between 0 and 100
        """
        score = 0.0
        
        # Coverage score (30 points max)
        coverage_score = min(metrics.unit_test_coverage_pct, 100.0) * 0.3
        score += coverage_score
        
        # CI/CD score (20 points max)
        if metrics.has_cicd_pipeline:
            score += 10.0
        if metrics.has_automated_testing:
            score += 5.0
        if metrics.has_security_scanning:
            score += 3.0
        if metrics.has_deployment_automation:
            score += 2.0
        
        # Test diversity score (20 points max)
        test_types_count = sum([
            1 if metrics.unit_test_count > 0 else 0,
            1 if metrics.feature_test_scenarios > 0 else 0,
            1 if metrics.e2e_test_count > 0 else 0,
            1 if metrics.performance_test_count > 0 else 0,
            1 if metrics.smoke_test_count > 0 else 0,
        ])
        diversity_score = (test_types_count / 5) * 20.0
        score += diversity_score
        
        # Commit activity score (15 points max)
        # Active repo (>4 commits/week) = full points, inactive = proportional
        commits_per_week = metrics.avg_commits_per_week
        activity_score = min(commits_per_week / 4.0, 1.0) * 15.0
        score += activity_score
        
        # BDD adoption score (15 points max)
        if metrics.feature_test_scenarios > 0:
            # Scale based on scenarios: 1-5 = 5pts, 6-20 = 10pts, 21+ = 15pts
            if metrics.feature_test_scenarios >= 21:
                score += 15.0
            elif metrics.feature_test_scenarios >= 6:
                score += 10.0
            else:
                score += 5.0
        
        return round(score, 1)
    
    def _analyze_gaps(self, metrics: TestMetrics) -> Dict[str, str]:
        """
        Identify testing gaps based on test pyramid principles.
        
        Args:
            metrics: TestMetrics object
            
        Returns:
            Dictionary of gap categories and descriptions
        """
        gaps = {}
        
        # Unit test gaps
        if metrics.unit_test_count == 0:
            gaps['unit_tests'] = "No unit tests detected - foundational layer missing"
        elif metrics.unit_test_coverage_pct < 50:
            gaps['unit_coverage'] = f"Low unit test coverage ({metrics.unit_test_coverage_pct:.1f}%) - target ≥80%"
        elif metrics.unit_test_coverage_pct < 80:
            gaps['unit_coverage'] = f"Moderate unit test coverage ({metrics.unit_test_coverage_pct:.1f}%) - room for improvement"
        
        # Integration test gaps
        if metrics.feature_test_scenarios == 0 and metrics.e2e_test_count == 0:
            gaps['integration'] = "No integration or BDD tests - missing middle pyramid layer"
        
        # E2E test gaps
        if metrics.e2e_test_count == 0:
            gaps['e2e_tests'] = "No E2E tests detected - limited user journey validation"
        
        # Performance test gaps
        if metrics.performance_test_count == 0:
            gaps['performance'] = "No performance tests - scalability and responsiveness untested"
        
        # CI/CD gaps
        if not metrics.has_cicd_pipeline:
            gaps['cicd'] = "No CI/CD pipeline detected - missing automated quality gates"
        elif not metrics.has_automated_testing:
            gaps['automated_testing'] = "CI/CD exists but automated testing not configured"
        
        # BDD gaps
        if metrics.feature_test_scenarios == 0:
            gaps['bdd'] = "No BDD scenarios - behavior-driven development not adopted"
        
        # Test diversity gap
        test_types = sum([
            1 if metrics.unit_test_count > 0 else 0,
            1 if metrics.feature_test_scenarios > 0 else 0,
            1 if metrics.e2e_test_count > 0 else 0,
            1 if metrics.performance_test_count > 0 else 0,
        ])
        
        if test_types < 3:
            gaps['diversity'] = "Limited test type diversity - consider expanding test pyramid layers"
        
        return gaps
    
    def _load_training_guide(self) -> str:
        """
        Load testing training guide as context for recommendations.
        
        Returns:
            Training guide content or empty string if not found
        """
        # Use cached content if available
        if RecommendationAnalyzer._training_guide_cache is not None:
            return RecommendationAnalyzer._training_guide_cache
        
        # Try to load from docs/testing/training.md
        training_paths = [
            Path(__file__).parent.parent.parent.parent / "docs" / "testing" / "training.md",
            Path.cwd() / "docs" / "testing" / "training.md",
        ]
        
        for path in training_paths:
            if path.exists():
                try:
                    content = path.read_text(encoding='utf-8')
                    # Cache for future use
                    RecommendationAnalyzer._training_guide_cache = content
                    self.logger.debug(f"Loaded training guide from {path}")
                    return content
                except Exception as e:
                    self.logger.warning(f"Failed to read training guide from {path}: {e}")
        
        self.logger.warning("Training guide not found - recommendations will be based on general best practices")
        RecommendationAnalyzer._training_guide_cache = ""
        return ""
    
    async def _generate_with_copilot(
        self, 
        repo_path: Path, 
        metrics: TestMetrics, 
        gaps: Dict[str, str],
        training_guide: str
    ) -> Optional[Dict]:
        """
        Generate recommendations using Copilot SDK.
        
        Args:
            repo_path: Path to repository root
            metrics: Current test metrics
            gaps: Identified testing gaps
            training_guide: Training guide content for context
            
        Returns:
            Dictionary with recommendations or None if generation failed
        """
        # Extract relevant sections from training guide (first 3000 chars for context)
        training_excerpt = training_guide[:3000] if training_guide else "Use industry best practices for testing."
        
        # Get sample file structure
        file_structure = self._get_file_structure_sample(repo_path, max_depth=3, max_files=30)
        
        # Build comprehensive prompt
        prompt = f"""Analyze this repository's testing maturity and provide actionable recommendations.

**Repository Information:**
- Name: {metrics.repo_name}
- Languages: {', '.join(metrics.languages or ['Unknown'])}
- Test Frameworks: {', '.join(metrics.test_frameworks or ['None detected'])}

**Current Metrics:**
- Unit Tests: {metrics.unit_test_count} tests, {metrics.unit_test_coverage_pct:.1f}% coverage
- BDD Scenarios: {metrics.feature_test_scenarios}
- E2E Tests: {metrics.e2e_test_count}
- Performance Tests: {metrics.performance_test_count}
- Total Test Files: {metrics.total_test_files}
- CI/CD: {metrics.cicd_platform if metrics.has_cicd_pipeline else 'Not configured'}
- Maturity Score: {metrics.testing_maturity_score:.1f}/100

**Identified Gaps:**
{json.dumps(gaps, indent=2)}

**File Structure Sample:**
{file_structure}

**Context from Best Practices Guide:**
{training_excerpt}

**Task:**
Generate structured, actionable testing recommendations in JSON format with these keys:
- "gaps": List of critical testing gaps (max 5 items, each 1-2 sentences)
- "coverage_improvements": Prioritized list of coverage improvement suggestions (max 5 items)
- "maturity_roadmap": Phased improvement plan with phases: "Quick Wins (0-1 month)", "Medium Term (1-3 months)", "Long Term (3-6 months)"
- "tool_recommendations": Specific tools/frameworks to adopt based on detected languages and current setup

Focus on practical, implementable recommendations that address the gaps and improve the maturity score.
Return ONLY valid JSON, no markdown formatting or explanations outside the JSON structure.
"""
        
        try:
            # Query Copilot SDK
            response = await self.copilot_service.send_prompt(prompt, timeout=60.0)
            
            if not response:
                return None
            
            # Try to parse JSON from response
            # Handle potential markdown code blocks
            json_text = response.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            recommendations = json.loads(json_text)
            
            # Validate structure
            required_keys = ['gaps', 'coverage_improvements', 'maturity_roadmap', 'tool_recommendations']
            if not all(key in recommendations for key in required_keys):
                self.logger.warning(f"Copilot response missing required keys: {required_keys}")
                return None
            
            return recommendations
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Copilot response as JSON: {e}")
            self.logger.debug(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            self.logger.error(f"Copilot recommendation generation failed: {e}")
            return None
    
    def _get_file_structure_sample(self, repo_path: Path, max_depth: int = 3, max_files: int = 30) -> str:
        """
        Get a sample of the repository file structure.
        
        Args:
            repo_path: Path to repository root
            max_depth: Maximum directory depth to traverse
            max_files: Maximum number of files to include
            
        Returns:
            Formatted file structure string
        """
        lines = []
        file_count = 0
        
        def traverse(path: Path, depth: int = 0, prefix: str = ""):
            nonlocal file_count
            
            if depth > max_depth or file_count >= max_files:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                
                for item in items:
                    # Skip hidden files and common ignore patterns
                    if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build']:
                        continue
                    
                    if file_count >= max_files:
                        break
                    
                    indent = "  " * depth
                    if item.is_dir():
                        lines.append(f"{indent}{item.name}/")
                        traverse(item, depth + 1, prefix + item.name + "/")
                    else:
                        lines.append(f"{indent}{item.name}")
                        file_count += 1
                        
            except PermissionError:
                pass
        
        traverse(repo_path)
        
        if file_count >= max_files:
            lines.append("... (truncated)")
        
        return "\n".join(lines[:50])  # Limit output lines
