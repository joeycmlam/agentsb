# JSON Validation Tool

A command-line tool to compare two JSON files and detect differences in structure and values. Designed for validating API responses between different system versions.

## Installation

```bash
pip install -r script/requirements.txt
```

## Usage

```bash
python3 src/json_validator.py <baseline_file.json> <comparison_file.json>
```

### Exit Codes
- 0: Files are identical (PASS)
- 1: Differences found (FAIL) or error occurred

### Example Output

**No differences:**
```
Validation Result: PASS
No differences found.
```

**With differences:**
```
Validation Result: FAIL
Differences found:
  - Added: root['email']
  - Changed: root['status'] from 'active' to 'inactive'
```

## Features

- Detects added/removed fields
- Identifies value changes
- Handles nested JSON structures
- Reports type changes
- Command-line interface with clear output