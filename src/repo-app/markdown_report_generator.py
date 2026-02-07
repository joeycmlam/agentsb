"""
Markdown report generator for testing recommendations.

Author: Automated Software Engineering Team
Date: February 2026
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List

from models import TestMetrics
from logger import get_logger


class MarkdownReportGenerator:
    """Generates markdown reports with testing recommendations"""
    
    def __init__(self):
        """Initialize markdown report generator"""
        self.logger = get_logger()
    
    def generate_report(self, metrics: TestMetrics, output_path: Path) -> bool:
        """
        Generate markdown report with testing recommendations.
        
        Args:
            metrics: TestMetrics with recommendations
            output_path: Path to save markdown file
            
        Returns:
            True if report generated successfully, False otherwise
        """
        if not metrics.recommendations:
            self.logger.warning(f"No recommendations available for {metrics.repo_name}")
            return False
        
        try:
            # Build markdown content
            markdown = self._build_markdown(metrics)
            
            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding='utf-8')
            
            self.logger.info(f"   📝 Generated recommendation report: {output_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate markdown report: {e}")
            return False
    
    def _build_markdown(self, metrics: TestMetrics) -> str:
        """
        Build complete markdown document.
        
        Args:
            metrics: TestMetrics with recommendations
            
        Returns:
            Complete markdown document as string
        """
        sections = []
        
        # YAML frontmatter
        sections.append(self._build_frontmatter(metrics))
        
        # Executive Summary
        sections.append(self._build_executive_summary(metrics))
        
        # Current State
        sections.append(self._build_current_state(metrics))
        
        # Gap Analysis
        sections.append(self._build_gap_analysis(metrics))
        
        # Coverage Improvements
        sections.append(self._build_coverage_improvements(metrics))
        
        # Testing Maturity Roadmap
        sections.append(self._build_maturity_roadmap(metrics))
        
        # Recommended Tools
        sections.append(self._build_tool_recommendations(metrics))
        
        # References
        sections.append(self._build_references(metrics))
        
        return "\n\n".join(sections)
    
    def _build_frontmatter(self, metrics: TestMetrics) -> str:
        """Build YAML frontmatter with metadata"""
        return f"""---
repository: {metrics.repo_name}
repository_url: {metrics.repo_url}
analysis_date: {metrics.last_analyzed}
maturity_score: {metrics.testing_maturity_score:.1f}
analyzer_version: "1.0.0"
---"""
    
    def _build_executive_summary(self, metrics: TestMetrics) -> str:
        """Build executive summary section"""
        # Determine maturity indicator
        score = metrics.testing_maturity_score or 0
        if score >= 80:
            indicator = "🟢 Excellent"
            summary = "This repository demonstrates strong testing practices with comprehensive coverage and mature automation."
        elif score >= 60:
            indicator = "🟡 Good"
            summary = "This repository has solid testing fundamentals with opportunities for improvement."
        elif score >= 40:
            indicator = "🟠 Developing"
            summary = "This repository has basic testing in place but requires significant enhancements."
        else:
            indicator = "🔴 Needs Attention"
            summary = "This repository requires immediate attention to establish proper testing practices."
        
        return f"""# Testing Recommendations: {metrics.repo_name}

## Executive Summary

**Testing Maturity Score:** {score:.1f}/100 {indicator}

{summary}

**Generated:** {datetime.fromisoformat(metrics.last_analyzed).strftime('%B %d, %Y at %I:%M %p')}"""
    
    def _build_current_state(self, metrics: TestMetrics) -> str:
        """Build current state metrics table"""
        languages = ', '.join(metrics.languages or ['N/A'])
        frameworks = ', '.join(metrics.test_frameworks or ['None detected'])
        cicd = metrics.cicd_platform if metrics.has_cicd_pipeline else 'Not configured'
        
        return f"""## Current State

| Metric | Value |
|--------|-------|
| **Languages** | {languages} |
| **Test Frameworks** | {frameworks} |
| **Unit Tests** | {metrics.unit_test_count} tests |
| **Unit Test Coverage** | {metrics.unit_test_coverage_pct:.1f}% |
| **BDD Scenarios** | {metrics.feature_test_scenarios} |
| **E2E Tests** | {metrics.e2e_test_count} |
| **Performance Tests** | {metrics.performance_test_count} |
| **Total Test Files** | {metrics.total_test_files} |
| **CI/CD Platform** | {cicd} |
| **Automated Testing** | {'✅ Yes' if metrics.has_automated_testing else '❌ No'} |
| **Security Scanning** | {'✅ Yes' if metrics.has_security_scanning else '❌ No'} |
| **Deployment Automation** | {'✅ Yes' if metrics.has_deployment_automation else '❌ No'} |"""
    
    def _build_gap_analysis(self, metrics: TestMetrics) -> str:
        """Build gap analysis section"""
        gaps = metrics.recommendations.get('gaps', [])
        
        if not gaps:
            return """## Gap Analysis

✅ No critical gaps identified. Continue maintaining current testing standards."""
        
        # Handle both list and dict formats
        gap_items = []
        if isinstance(gaps, list):
            for gap in gaps:
                if isinstance(gap, dict):
                    # Handle dict format with 'gap' or 'description' keys
                    text = gap.get('description') or gap.get('gap') or str(gap)
                    gap_items.append(f"- {text}")
                else:
                    gap_items.append(f"- {gap}")
        elif isinstance(gaps, dict):
            for category, description in gaps.items():
                gap_items.append(f"- **{category}**: {description}")
        
        gap_text = "\n".join(gap_items) if gap_items else "- See recommendations data for gap details"
        
        return f"""## Gap Analysis

The following critical gaps have been identified in the testing strategy:

{gap_text}"""
    
    def _build_coverage_improvements(self, metrics: TestMetrics) -> str:
        """Build coverage improvements section"""
        improvements = metrics.recommendations.get('coverage_improvements', [])
        
        if not improvements:
            return """## Coverage Improvements

Current coverage is satisfactory. Focus on maintaining quality as codebase evolves."""
        
        # Number the improvements by priority
        improvement_items = []
        for i, improvement in enumerate(improvements):
            # Handle both string and dict formats
            if isinstance(improvement, dict):
                # Extract key information from dict
                action = improvement.get('action', str(improvement))
                target = improvement.get('target_metric', '')
                if target:
                    improvement_items.append(f"{i+1}. {action}\n   - **Target:** {target}")
                else:
                    improvement_items.append(f"{i+1}. {action}")
            else:
                improvement_items.append(f"{i+1}. {improvement}")
        
        improvement_text = "\n".join(improvement_items)
        
        return f"""## Coverage Improvements

Prioritized recommendations to improve test coverage:

{improvement_text}"""
    
    def _build_maturity_roadmap(self, metrics: TestMetrics) -> str:
        """Build testing maturity roadmap section"""
        roadmap = metrics.recommendations.get('maturity_roadmap', {})
        
        sections = []
        
        # Quick Wins (0-1 month)
        quick_wins = roadmap.get('Quick Wins (0-1 month)', [])
        if quick_wins:
            items = "\n".join([f"- {item}" for item in quick_wins])
            sections.append(f"""### Phase 1: Quick Wins (0-1 month)

{items}""")
        
        # Medium Term (1-3 months)
        medium_term = roadmap.get('Medium Term (1-3 months)', [])
        if medium_term:
            items = "\n".join([f"- {item}" for item in medium_term])
            sections.append(f"""### Phase 2: Medium Term (1-3 months)

{items}""")
        
        # Long Term (3-6 months)
        long_term = roadmap.get('Long Term (3-6 months)', [])
        if long_term:
            items = "\n".join([f"- {item}" for item in long_term])
            sections.append(f"""### Phase 3: Long Term (3-6 months)

{items}""")
        
        roadmap_content = "\n\n".join(sections) if sections else "No specific roadmap phases defined."
        
        return f"""## Testing Maturity Roadmap

{roadmap_content}"""
    
    def _build_tool_recommendations(self, metrics: TestMetrics) -> str:
        """Build tool recommendations section"""
        tools = metrics.recommendations.get('tool_recommendations', {})
        
        if not tools:
            return """## Recommended Tools

Current tooling is appropriate for this repository."""
        
        # Build tool sections
        tool_sections = []
        
        for category, tool_list in tools.items():
            if isinstance(tool_list, list):
                items = []
                for tool in tool_list:
                    if isinstance(tool, dict):
                        # Handle dict format with 'name', 'description', etc.
                        name = tool.get('name', '')
                        desc = tool.get('description', '')
                        if name and desc:
                            items.append(f"- **{name}**: {desc}")
                        elif name:
                            items.append(f"- **{name}**")
                        else:
                            items.append(f"- {str(tool)}")
                    else:
                        items.append(f"- {tool}")
                
                items_text = "\n".join(items)
                tool_sections.append(f"""### {category}

{items_text}""")
            elif isinstance(tool_list, str):
                tool_sections.append(f"""### {category}

{tool_list}""")
        
        tools_content = "\n\n".join(tool_sections) if tool_sections else "See tool recommendations in the data structure."
        
        return f"""## Recommended Tools

{tools_content}"""
    
    def _build_references(self, metrics: TestMetrics) -> str:
        """Build references section"""
        return """## References

### Internal Documentation
- [Testing Best Practices Guide](../../docs/testing/training.md)

### External Resources
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [BDD with Cucumber](https://cucumber.io/docs/bdd/)
- [GitHub Actions CI/CD](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Testing Framework](https://jestjs.io/)
- [Playwright E2E Testing](https://playwright.dev/)

---

*This report was automatically generated by the Repository Testing Analyzer.*
*For questions or feedback, consult your testing team or refer to the internal documentation.*"""
