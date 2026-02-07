# Repository Analyzer - Refactored Architecture

## Overview

Successfully refactored from **800+ line monolithic file** into **5 focused modules** (~1100 total lines with better separation of concerns).

## New Module Structure

```
src/
├── repo_analyzer.py       # Main CLI entry point (~150 lines)
├── models.py              # Data models (~80 lines)  
├── github_client.py       # GitHub API operations (~100 lines)
├── analyzer.py            # Core analysis logic (~650 lines)
└── report_generator.py    # Excel generation (~120 lines)
```

## Benefits of Refactoring

### ✅ Single Responsibility Principle
Each module has one clear purpose:
- **models.py**: Data structures (TestMetrics dataclass)
- **github_client.py**: GitHub API calls & repository cloning
- **analyzer.py**: Test detection, coverage extraction, CI/CD detection
- **report_generator.py**: Excel report formatting
- **repo_analyzer.py**: CLI orchestration

### ✅ Improved Maintainability
- Easier to locate bugs (know which module to check)
- Simpler to add features (e.g., add new CI/CD platform in analyzer.py)
- Clear module boundaries prevent spaghetti code

### ✅ Better Testability
Each module can be unit tested independently:
```python
# Test GitHub client with mocked API responses
# Test analyzer with mocked file system
# Test report generator with sample metrics
```

### ✅ Reduced Cognitive Load
- `analyzer.py` is still largest (~650 lines) but focused on one domain
- Each developer can work on one module without understanding entire system

## Quick Start

### 1. Initialize repository list
```bash
python src/repo_analyzer.py --init --user myusername
```

### 2. Analyze repositories
```bash
python src/repo_analyzer.py
```

Generates `test_analysis_report.xlsx` with comprehensive metrics.

## Module Details

### models.py - Data Models
- **TestMetrics** dataclass: 30+ fields covering all metrics
- No dependencies on other modules (pure data)
- Easy to extend with new metric fields

### github_client.py - GitHub API Client
- `list_user_repos()`: Paginated user repo fetching
- `list_org_repos()`: Organization repo fetching
- `clone_repo()`: Shallow git clone to temp directory
- Authentication via `GITHUB_TOKEN` env variable

### analyzer.py - Core Analysis Engine
**Key Features:**
- Language detection (Python, JS/TS, Java, Go)
- Test framework detection (pytest, Jest, Playwright, etc.)
- **AI-powered test classification** via GitHub Copilot SDK (optional)
- Pattern-based fallback if Copilot unavailable
- Coverage parsing (Python coverage.xml, JS coverage-summary.json)
- Commit activity analysis (30d/90d/1y metrics)
- **Multi-platform CI/CD detection** (GitHub Actions, GitLab, Jenkins, CircleCI, Travis, Azure)

**Graceful Degradation:**
- Falls back to pattern matching if Copilot SDK not installed
- Continues analysis even if individual components fail

### report_generator.py - Excel Report
**Features:**
- 32 columns of metrics per repository
- Professional formatting (color-coded headers, status indicators)
- Auto-adjusted column widths
- Frozen header row
- Success/failure color coding

### repo_analyzer.py - CLI Entry Point
**Commands:**
- `--init`: Fetch repository list from GitHub
- `--config`: Specify custom config file
- `--output`: Custom output filename
- `--token`: Provide GitHub token directly

**Workflow:**
1. Parse CLI arguments
2. Load/create repository config
3. Clone repos to temp directory
4. Analyze each repository asynchronously
5. Generate Excel report
6. Print summary statistics

## Configuration

`repo_list.json`:
```json
{
  "repositories": [
    {
      "name": "owner/repo",
      "url": "https://github.com/owner/repo.git",
      "enabled": true,
      "description": "..."
    }
  ]
}
```

Set `"enabled": false` to skip repositories.

## Dependencies

**Required:**
- `requests` - GitHub API client
- `pandas` - Data manipulation
- `openpyxl` - Excel generation

**Optional:**
- GitHub Copilot SDK - AI-powered test classification

## Architecture Principles Applied

### KISS (Keep It Simple)
- Each module does one thing well
- No premature optimization
- Clear, descriptive names

### YAGNI (You Aren't Gonna Need It)
- No generic frameworks built
- Features implemented for current needs
- Easy to extend when requirements arise

### Dependency Inversion
- High-level (repo_analyzer.py) depends on abstractions (models.py)
- Low-level modules (github_client, analyzer) are independent

## Migration Guide

If you have existing code using the old monolithic file:

**Before (v1):**
```python
from repo_analyzer import RepositoryAnalyzer, GitHubClient, ExcelReportGenerator
```

**After (v2):**
```python
from analyzer import RepositoryAnalyzer
from github_client import GitHubClient
from report_generator import ExcelReportGenerator
from models import TestMetrics
```

The APIs remain the same - only imports changed.

## Future Enhancements

### Easy to Add (due to modularity):
1. **New CI/CD platforms**: Add method to `analyzer.py`
2. **More languages**: Extend `_detect_languages()` in `analyzer.py`
3. **Custom report formats**: New module `pdf_generator.py`
4. **Caching**: Add `cache.py` module
5. **Web dashboard**: Add `web_server.py` module

### Example: Adding Support for a New Language

```python
# In analyzer.py, add to _detect_languages():
def _detect_languages(self, repo_path: Path) -> List[str]:
    languages = []
    
    # Existing detection...
    if list(repo_path.rglob("*.py")):
        languages.append("Python")
    
    # NEW: Add Rust support
    if list(repo_path.rglob("*.rs")):
        languages.append("Rust")
    
    return languages
```

No other files need modification!

## Performance Notes

- **Async operations**: Repository analysis is non-blocking
- **Shallow clones**: Uses `git clone --depth 1` for speed
- **Temp cleanup**: Auto-removes cloned repos after analysis
- **Batch processing**: Copilot API calls batched (10 files/request)

## Error Handling

Each repository gets status:
- `success`: Full analysis complete
- `failed`: Error occurred (see `error_message` field)

Report includes both successful and failed analyses.

## Version History

**v2.0 (Feb 2026)** - Modular refactoring
- Split into 5 focused modules
- Added GitHub Copilot SDK integration
- Enhanced CI/CD detection (6 platforms)
- Professional Excel reporting

**v1.0** - Initial monolithic implementation

---

For detailed module documentation, see inline docstrings in each file.
