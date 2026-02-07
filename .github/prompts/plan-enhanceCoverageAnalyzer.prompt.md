# Plan: Enable Automated Coverage Generation via Copilot

Enhance [coverage_analyzer.py](src/repo-app/analyzers/coverage_analyzer.py) to intelligently run tests and generate fresh coverage reports using Copilot SDK. Currently, it only reads existing reports - this adds capability to execute test frameworks with coverage collection when reports are missing or stale, auto-install dependencies, and use Copilot to determine optimal test commands for each repository's specific setup.

## Approach

**Read-First Strategy**: 
1. Attempt to read existing coverage reports (current behavior)
2. Check if report exists and is fresh (modified within configurable threshold)
3. If missing or stale, generate new report by running tests with coverage
4. Fall back to existing stale report if generation fails

## Steps

1. **Add imports and constants** to [coverage_analyzer.py](src/repo-app/analyzers/coverage_analyzer.py#L1-L12)
   - Import `asyncio`, `subprocess`, `shutil` for command execution
   - Import `copilot_service` types: `CopilotService`
   - Import `datetime`, `time` for staleness checking
   - Add constants: 
     - `TEST_TIMEOUT = 300`
     - `COVERAGE_TIMEOUT = 60`
     - `STALE_THRESHOLD_HOURS = 24` (report older than this triggers regeneration)

2. **Add constructor** to `CoverageAnalyzer` class
   - Accept optional `copilot_service: CopilotService` parameter
   - Store for use in command generation
   - Matches pattern from `TestFileAnalyzer.__init__()`

3. **Create `_is_coverage_stale()` helper method**
   - Takes `coverage_file: Path` parameter
   - Checks file modification time using `coverage_file.stat().st_mtime`
   - Compares against `STALE_THRESHOLD_HOURS` 
   - Returns `bool` (True if file doesn't exist OR older than threshold)
   - Logs staleness reason: "Coverage report not found" vs "Coverage report is X hours old"

4. **Create `generate_coverage_if_needed()` async method**
   - Main orchestration method called by `analyzer.py`
   - Takes `repo_path: Path`, `metrics: TestMetrics`
   - **Step 1**: Check for existing coverage files in common locations:
     - `coverage.xml`, `coverage/coverage-final.json`, `htmlcov/index.html`
   - **Step 2**: If found, call `_is_coverage_stale()` to check freshness
   - **Step 3**: If missing OR stale:
     - Check if test frameworks detected (from `metrics.test_frameworks`)
     - Call `_determine_coverage_command()` using Copilot
     - Call `_install_dependencies()` if needed
     - Execute command via `_execute_coverage_command()`
   - **Step 4**: Set metric flag `metrics.coverage_generated = True/False`
   - Returns `bool` indicating if new coverage was generated

5. **Create `_determine_coverage_command()` async method**
   - Uses `copilot_service.send_prompt()` with repo context:
     - Detected frameworks from `metrics.test_frameworks`
     - Languages from `metrics.languages`
     - Repo structure (presence of `package.json`, `requirements.txt`, etc.)
   - Prompt asks Copilot: "What command generates coverage for [frameworks] in this repo?"
   - Parses response to extract command string
   - Falls back to predefined commands if Copilot unavailable:
     - Python + pytest → `coverage run -m pytest && coverage xml`
     - JavaScript + jest → `npm test -- --coverage`
     - Matches pattern map from research findings

6. **Create `_install_dependencies()` async method**
   - Detects package manager: `requirements.txt` → pip, `package.json` → npm
   - For Python: Run `pip install coverage pytest` (if pytest in frameworks)
   - For JavaScript: Run `npm install` (dependencies already in package.json)
   - Uses same async subprocess pattern from `git_analyzer._run_git_command()` 
   - Timeout: 120 seconds for install operations
   - Logs installation status via `get_logger()`

7. **Create `_execute_coverage_command()` async method**
   - Accepts `command: str` and `repo_path: Path`
   - Splits command into parts for `asyncio.create_subprocess_exec()`
   - Configure: `cwd=repo_path`, capture stdout/stderr
   - Wait with 300 second timeout (constant `TEST_TIMEOUT`)
   - Returns `(success: bool, output: str, error: str)`
   - Uses pattern from [git_analyzer.py](src/repo-app/analyzers/git_analyzer.py#L72-L85)

8. **Create `_validate_tools_installed()` helper method**
   - Checks if required tools exist: `pytest`, `coverage`, `npm`, `jest`
   - Uses `shutil.which(tool_name)` to verify PATH availability
   - Called before `_install_dependencies()` to determine what's needed
   - Returns `List[str]` of missing tools

9. **Update `extract_coverage()` method**
   - Keep existing parsing logic unchanged
   - Add logging when coverage files found vs not found
   - Add parameter to record coverage source in metrics
   - Log: "Using existing coverage report" vs "Using generated coverage report"

10. **Update [analyzer.py](src/repo-app/analyzer.py#L93)** to call new flow
    - Pass `copilot_service` to `CoverageAnalyzer.__init__()`
    - Call sequence:
      ```python
      coverage_analyzer = CoverageAnalyzer(copilot_service)
      # Try to generate if needed (checks staleness internally)
      await coverage_analyzer.generate_coverage_if_needed(repo_path, metrics)
      # Then extract (will use newly generated or existing report)
      await coverage_analyzer.extract_coverage(repo_path, metrics)
      ```
    - Wrap in try/except to handle execution failures gracefully
    - Matches async patterns in `analyze_repository()` method

11. **Add error handling and logging**
    - Use `get_logger()` consistently for all operations
    - `log_metric()` for: 
      - Coverage staleness status ("Fresh", "Stale", "Missing")
      - Tool installation status
      - Test execution time
      - Coverage generation success/failure
      - Coverage source ("Existing", "Generated", "Fallback")
    - Store error details in `metrics` if new error field added, or log warnings
    - Non-fatal failures → fall back to existing report reading (if stale report exists)
    - Log decision points: "Coverage report is fresh, skipping generation" vs "Generating new coverage report"

## Verification

1. **Unit test**: Mock Copilot service, verify command generation logic and staleness checking
   - Test `_is_coverage_stale()` with various file timestamps
   - Test `generate_coverage_if_needed()` decision tree
2. **Integration test**: Run against test repository with pytest setup
   - **Scenario 1**: No coverage file exists → should generate new
   - **Scenario 2**: Fresh coverage file exists (< 24h) → should skip generation
   - **Scenario 3**: Stale coverage file exists (> 24h) → should regenerate
   - Verify coverage.xml generated/reused correctly
   - Verify metrics populated with correct source
3. **Manual test**: Execute `repo_analyzer.py --config repo_list_test.json`
   - Observer logs for: 
     - Staleness check decisions
     - Copilot command suggestion (when triggered)
     - Dependency installation (when triggered)
     - Test execution (when triggered)
     - Coverage parsing (always)
   - Check generated reports in analyzed repos
   - Verify timestamp-based logic by manually aging coverage files

## Decisions

- **Read-first approach**: Preserves current behavior as default path, only generates when necessary
- **24-hour staleness threshold**: Balances freshness with avoiding unnecessary test runs (configurable via constant)
- **Copilot-first command generation**: Leverages existing SDK integration for intelligent commands, more adaptive than pattern matching
- **300s test timeout**: Matches `CLONE_TIMEOUT` for consistency, handles comprehensive test suites
- **Auto-install dependencies**: Ensures tests can run even in fresh repo clones
- **Graceful fallback chain**: 
  1. Try existing fresh report (preferred)
  2. Try generating new report if stale/missing
  3. Fall back to stale report if generation fails
  4. Report no coverage if all fail (current behavior)
- **Non-blocking**: Coverage generation failures don't fail entire analysis
