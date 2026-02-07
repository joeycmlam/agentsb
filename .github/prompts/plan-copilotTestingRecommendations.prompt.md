# Plan: Copilot-Powered Testing Recommendations (Markdown)

This feature adds intelligent, per-repository testing recommendations using Copilot, exported as markdown files. A new `--recommendations` CLI flag triggers generation alongside the standard Excel report. The recommendations will include gap analysis, coverage improvements, testing maturity scoring, and tool/framework suggestions based on detected repo characteristics.

**Key Design Decisions:**
- **Per-repo markdown files**: Each analyzed repository gets its own `<repo-name>_recommendations.md` in the reports directory
- **Optional activation**: `--recommendations` flag prevents performance overhead when not needed
- **Copilot-powered intelligence**: Leverages existing `CopilotService` with context from all analyzers + [docs/testing/training.md](docs/testing/training.md) as authoritative guidance
- **Extensible scoring**: Testing maturity score (0-100) calculated from metrics to provide quantitative baseline

**Steps**

1. **Extend data model** in [src/repo-app/models.py](src/repo-app/models.py)
   - Add `recommendations: Optional[dict] = None` field to `TestMetrics` dataclass
   - Add `testing_maturity_score: Optional[float] = None` field
   - Structure `recommendations` dict with keys: `gaps`, `coverage_improvements`, `maturity_roadmap`, `tool_recommendations`

2. **Create `RecommendationAnalyzer`** at [src/repo-app/analyzers/recommendation_analyzer.py](src/repo-app/analyzers/recommendation_analyzer.py)
   - Implement `generate_recommendations(repo_path, metrics)` async method
   - Check if `copilot_service` is available at start - if not, log warning and return None (skip recommendation generation)
   - Add `_calculate_maturity_score(metrics)` helper using weighted scoring:
     - Test coverage % (30%), CI/CD presence (20%), test diversity (20%), commit activity (15%), BDD adoption (15%)
   - Add `_analyze_gaps(metrics)` to identify missing test types (compare against pyramid: unit > integration > e2e)
   - Add `_generate_with_copilot(repo_path, metrics, training_guide)` to send comprehensive prompt:
     - Include detected languages, frameworks, current metrics, file structure sample
     - Attach excerpts from [docs/testing/training.md](docs/testing/training.md) as best practice context
     - Request structured recommendations in JSON format for parsing
   - Follow existing analyzer pattern: accept `copilot_service` in constructor
   - If Copilot API call fails, log error and return None (do not generate recommendations)

3. **Register new analyzer** in [src/repo-app/analyzers/__init__.py](src/repo-app/analyzers/__init__.py)
   - Import `RecommendationAnalyzer`
   - Add to `__all__` list

4. **Create `MarkdownReportGenerator`** at [src/repo-app/markdown_report_generator.py](src/repo-app/markdown_report_generator.py)
   - Implement `generate_report(metrics: TestMetrics, output_path: Path)` method
   - Build markdown structure with sections:
     - **Executive Summary**: Repo name, analysis date, maturity score with visual indicator (🟢🟡🔴)
     - **Current State**: Table of test counts, coverage %, CI/CD status
     - **Gap Analysis**: Bulleted list of missing/weak areas from `recommendations['gaps']`
     - **Coverage Improvements**: Prioritized suggestions from `recommendations['coverage_improvements']`
     - **Testing Maturity Roadmap**: Phased improvements from `recommendations['maturity_roadmap']`
     - **Recommended Tools**: Framework/tool suggestions from `recommendations['tool_recommendations']`
     - **References**: Links to training.md sections, official docs for recommended tools
   - Use consistent markdown formatting: `##` for sections, tables for metrics, code blocks for commands
   - Add metadata YAML frontmatter with repo URL, timestamp, analyzer version

5. **Integrate in main analyzer** at [src/repo-app/analyzer.py](src/repo-app/analyzer.py)
   - Import `RecommendationAnalyzer` and `MarkdownReportGenerator`
   - In `RepositoryAnalyzer.__init__()`, instantiate `self.recommendation_analyzer = RecommendationAnalyzer(copilot_service=self.copilot_service)`
   - In `analyze_repository()` method, after all existing analyzers complete:
     - Check if recommendations enabled (passed as parameter from CLI)
     - If enabled: `await self.recommendation_analyzer.generate_recommendations(repo_path, metrics)`
     - Store result in `metrics.recommendations` and `metrics.testing_maturity_score`
   - Add `generate_recommendations` parameter to `analyze_repository()` signature

6. **Update CLI arguments** in [src/repo-app/repo_analyzer.py](src/repo-app/repo_analyzer.py)
   - Add `--recommendations` flag to argument parser:
     ```python
     parser.add_argument('--recommendations', action='store_true', 
                        help='Generate markdown testing recommendations for each repository')
     ```
   - Pass `args.recommendations` to `RepositoryAnalyzer.analyze_repository()` calls

7. **Update report generation flow** in [src/repo-app/repo_analyzer.py](src/repo-app/repo_analyzer.py)
   - After Excel report generation, check if recommendations were generated
   - If `metrics.recommendations` exists for any repo:
     - Instantiate `MarkdownReportGenerator()`
     - For each repository with recommendations:
       - Generate filename: `f"{repo_name}_recommendations.md"`
       - Call `markdown_generator.generate_report(metrics, output_path)`
       - Log success with path to generated markdown file

8. **Load training guide as context** in [src/repo-app/analyzers/recommendation_analyzer.py](src/repo-app/analyzers/recommendation_analyzer.py)
   - Add `_load_training_guide()` method to read [docs/testing/training.md](docs/testing/training.md)
   - Extract relevant sections (testing pyramid, maturity phases, anti-patterns, tool recommendations)
   - Include in Copilot context to ensure recommendations align with documented best practices
   - Cache content to avoid re-reading for each repository

**Verification**

Test the feature end-to-end:
```bash
# Analyze repos with recommendations enabled
python3 src/repo-app/repo_analyzer.py --repos src/repo_list_test.json --recommendations

# Verify outputs in reports/
ls -la reports/*.md
ls -la reports/*.xlsx

# Check markdown structure
cat reports/<repo-name>_recommendations.md
# Should contain: maturity score, gap analysis, coverage suggestions, roadmap, tool recommendations

# Test without flag (no markdown generated)
python3 src/repo-app/repo_analyzer.py --repos src/repo_list_test.json
ls reports/*.md  # Should be empty or unchanged
```

Manual checks:
- Maturity score is 0-100 and sensible (higher for well-tested repos)
- Gap analysis correctly identifies missing test types
- Tool recommendations match detected languages/frameworks
- Markdown formatting is clean and readable
- Warning logged when Copilot service unavailable (no recommendations generated)
- No markdown files created when Copilot unavailable

**Decisions**

- **Chose optional flag over automatic**: Copilot API calls add latency; users can opt-in when needed
- **Chose per-repo markdown over consolidated**: Easier to share individual repo recommendations with teams
- **Chose training.md as authoritative source**: Ensures consistency with documented organizational standards
- **Chose weighted maturity scoring**: Provides objective, comparable metric across repos
- **Chose JSON parsing from Copilot**: Structured responses easier to parse than free-form text

---

This plan provides a complete, executable roadmap. The feature integrates cleanly with existing architecture using established patterns.
