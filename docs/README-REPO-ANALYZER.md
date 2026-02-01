# Repository Test Analyzer

**Automated repository analysis tool using GitHub Copilot SDK**

Generates comprehensive test metrics across multiple GitHub repositories in a standardized Excel format.

## Features

✅ **Intelligent Test Classification** - Uses GitHub Copilot SDK to intelligently categorize tests
✅ **Multi-Repository Analysis** - Batch analyze all your GitHub repos
✅ **Comprehensive Metrics** - Unit, Feature/BDD, Performance, E2E, and Smoke test coverage
✅ **Automatic Coverage Extraction** - Parses existing coverage reports (Python, JavaScript)
✅ **Excel Report Generation** - Professional, formatted reports with color-coding
✅ **Configurable Repository List** - Edit which repos to analyze

## Metrics Collected

| Category | Metrics |
|----------|---------|
| **Unit Tests** | Test count, Line coverage %, Lines covered, Total lines |
| **Feature Tests** | BDD scenario count, Feature file count |
| **Performance Tests** | Test count, File count |
| **E2E Tests** | Test count, File count |
| **Smoke Tests** | Test count, File count |
| **Overall** | Total test files, Frameworks detected, Languages detected |

## Installation

### 1. Install Dependencies

```bash
cd /Users/joeylam/repo/mypps
pip install -r script/repo_analysis_requirements.txt
```

### 2. Install GitHub Copilot SDK

As of February 2026, the GitHub Copilot SDK is available. Install it:

```bash
# If available on PyPI
pip install github-copilot-sdk

# Or from GitHub
pip install git+https://github.com/github/copilot-sdk-python.git
```

**Note:** If Copilot SDK is not installed, the tool falls back to pattern-based analysis.

### 3. Set Up GitHub Token

Create a GitHub Personal Access Token with `repo` scope:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Copy token

```bash
export GITHUB_TOKEN="ghp_your_token_here"

# Or add to ~/.zshrc or ~/.bashrc for persistence
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.zshrc
```

## Usage

### Step 1: Initialize Repository List

Fetch your repositories from GitHub and create a configuration file:

```bash
# Fetch all your personal repositories
python3 script/repo_analyzer.py --init

# Or fetch from a specific organization
python3 script/repo_analyzer.py --init --org your-org-name

# Or fetch from a specific user
python3 script/repo_analyzer.py --init --user github-username
```

This creates `repo_list.json` with all repositories.

### Step 2: Edit Repository List (Optional)

Edit `repo_list.json` to enable/disable specific repositories:

```json
{
  "repositories": [
    {
      "name": "owner/repo-name",
      "url": "https://github.com/owner/repo-name.git",
      "enabled": true,
      "description": "Repository description"
    },
    {
      "name": "owner/another-repo",
      "url": "https://github.com/owner/another-repo.git",
      "enabled": false,
      "description": "Skip this one"
    }
  ]
}
```

Set `"enabled": false` to skip repositories you don't want to analyze.

### Step 3: Run Analysis

```bash
python3 script/repo_analyzer.py
```

This will:
1. Clone each enabled repository (shallow clone)
2. Detect languages and test frameworks
3. Analyze test files using Copilot SDK (or pattern matching)
4. Extract coverage from existing reports
5. Generate Excel report: `test_analysis_report.xlsx`

### Custom Options

```bash
# Use custom config file
python3 script/repo_analyzer.py --config my_repos.json

# Custom output file
python3 script/repo_analyzer.py --output reports/february_2026.xlsx

# Provide token inline (not recommended for security)
python3 script/repo_analyzer.py --token ghp_your_token
```

## Output Format

The Excel report includes:

### Columns

1. **Repository** - Repository name (owner/repo)
2. **Status** - Analysis status (success/failed)
3. **Last Analyzed** - Timestamp
4. **Unit Tests** - Count of unit tests
5. **Coverage %** - Line coverage percentage
6. **Lines Covered** - Number of lines covered
7. **Total Lines** - Total lines of code
8. **Feature Scenarios** - BDD scenario count
9. **Feature Files** - Number of .feature files
10. **Perf Tests** - Performance test count
11. **Perf Files** - Performance test files
12. **E2E Tests** - End-to-end test count
13. **E2E Files** - E2E test files
14. **Smoke Tests** - Smoke test count
15. **Smoke Files** - Smoke test files
16. **Total Test Files** - All test files found
17. **Frameworks** - Detected test frameworks (pytest, Jest, etc.)
18. **Languages** - Programming languages (Python, TypeScript, etc.)
19. **Repository URL** - Clone URL
20. **Error Message** - Error details if analysis failed

### Color Coding

- 🟢 **Green** - Successfully analyzed
- 🔴 **Red** - Analysis failed
- **Header** - Blue background with white text

## How It Works

### Test Detection Strategy

#### 1. **With GitHub Copilot SDK** (Recommended)

Uses AI to intelligently classify tests by analyzing code content:

```python
# Copilot analyzes the test code and determines:
# - Test type (unit/integration/e2e/performance/smoke)
# - Number of test cases
# - Testing patterns used
```

Benefits:
- ✅ Accurate classification even with non-standard naming
- ✅ Understands context (mocking = unit, browser automation = e2e)
- ✅ Adapts to different coding styles

#### 2. **Pattern-Based Fallback**

If Copilot SDK unavailable, uses file patterns and content analysis:

- **File name patterns**: `test_*.py`, `*.test.ts`, `*_e2e.py`
- **Content keywords**: "benchmark", "playwright", "smoke"
- **Directory structure**: `/e2e/`, `/performance/`, `/integration/`

### Coverage Extraction

#### Python Projects

Looks for:
1. `coverage.xml` (generated by `pytest --cov`)
2. `.coverage` database file

Parses XML to extract:
- Line coverage percentage
- Lines covered vs total lines

#### JavaScript/TypeScript Projects

Looks for:
1. `coverage/coverage-summary.json` (Jest/Vitest)
2. `coverage/lcov.info`

Parses JSON to extract coverage metrics.

#### Auto-Generation (Future Enhancement)

Currently **reads existing reports only**. Future versions could:
- Run `pytest --cov` for Python repos
- Run `npm test -- --coverage` for JS repos
- Execute tests in isolated containers

### Supported Test Frameworks

| Language | Frameworks Detected |
|----------|-------------------|
| **Python** | pytest, unittest, pytest-bdd, behave |
| **JavaScript/TypeScript** | Jest, Vitest, Mocha, Playwright, Cypress |
| **Java** | JUnit, TestNG |
| **Go** | testing package |

## Configuration File Schema

```json
{
  "repositories": [
    {
      "name": "string (required)",
      "url": "string (required)",
      "enabled": "boolean (default: true)",
      "description": "string (optional)"
    }
  ]
}
```

## Examples

### Example 1: Analyze Your Organization

```bash
# Step 1: Fetch org repos
python3 script/repo_analyzer.py --init --org mycompany

# Step 2: Review repo_list.json, disable unwanted repos

# Step 3: Run analysis
python3 script/repo_analyzer.py
```

### Example 2: Custom Workflow

```bash
# Different config for different teams
python3 script/repo_analyzer.py --init --org mycompany --config backend_repos.json
python3 script/repo_analyzer.py --init --org mycompany --config frontend_repos.json

# Analyze each separately
python3 script/repo_analyzer.py --config backend_repos.json --output backend_report.xlsx
python3 script/repo_analyzer.py --config frontend_repos.json --output frontend_report.xlsx
```

### Example 3: CI/CD Integration

```bash
#!/bin/bash
# weekly_analysis.sh

export GITHUB_TOKEN="${GITHUB_TOKEN}"

cd /path/to/mypps
python3 script/repo_analyzer.py \
  --config repo_list.json \
  --output "reports/weekly_$(date +%Y%m%d).xlsx"

# Upload to SharePoint, S3, etc.
```

## Troubleshooting

### "GitHub token required" Error

```bash
# Check if token is set
echo $GITHUB_TOKEN

# Set token
export GITHUB_TOKEN="ghp_..."
```

### "Copilot SDK not available" Warning

The tool will work without Copilot SDK but with reduced accuracy. Install:

```bash
pip install github-copilot-sdk
```

### Clone Failures

- Check network connectivity
- Verify token has `repo` access
- Check if repository is private (token needs appropriate scope)

### No Coverage Data

- Ensure tests have been run with coverage enabled
- Check for `coverage.xml` (Python) or `coverage/` directory (JS)
- Consider running tests before analysis

### Large Repository Timeouts

- The tool uses `--depth 1` shallow clones to minimize time
- For very large repos, consider analyzing locally instead

## Performance

Typical performance:
- **Small repo** (< 1000 files): ~30 seconds
- **Medium repo** (1000-5000 files): ~60 seconds
- **Large repo** (> 5000 files): ~120 seconds

With Copilot SDK, add ~5-10 seconds per repository for AI analysis.

## Limitations

1. **Coverage Reports**: Only reads existing reports, doesn't generate new ones
2. **Private Repos**: Requires GitHub token with appropriate scopes
3. **Test Execution**: Doesn't run tests, only analyzes structure
4. **Language Support**: Best support for Python and JavaScript/TypeScript

## Future Enhancements

- [ ] Auto-run tests to generate fresh coverage
- [ ] Support for GitLab, Bitbucket
- [ ] Trend analysis (compare reports over time)
- [ ] CI/CD integration examples (GitHub Actions, Jenkins)
- [ ] PDF report generation
- [ ] Dashboard UI (web-based)

## License

MIT License - see project root for details

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create new issue with `[repo-analyzer]` prefix
3. Include sample `repo_list.json` and error output

---

**Last Updated:** February 2026
**Version:** 1.0.0
