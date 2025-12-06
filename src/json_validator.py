#!/usr/bin/env python3
"""
JSON Validation Tool

A tool to compare two JSON files and detect differences in structure and values.
Used for validating API responses between different system versions.

Usage:
    python3 json_validator.py <baseline_file> <comparison_file>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from deepdiff import DeepDiff


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class JsonValidator:
    """JSON file validation and comparison tool."""

    def __init__(self):
        self.differences = []

    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data

        Raises:
            ValidationError: If file not found or invalid JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ValidationError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {file_path}: {e}")

    def compare_json(self, baseline: Dict[str, Any], comparison: Dict[str, Any]) -> List[str]:
        """
        Compare two JSON objects and return list of differences.

        Args:
            baseline: Baseline JSON data
            comparison: Comparison JSON data

        Returns:
            List of difference descriptions
        """
        diff = DeepDiff(baseline, comparison, ignore_order=True)
        differences = []

        # Added items
        if 'dictionary_item_added' in diff:
            for path in diff['dictionary_item_added']:
                differences.append(f"Added: {path}")

        # Removed items
        if 'dictionary_item_removed' in diff:
            for path in diff['dictionary_item_removed']:
                differences.append(f"Removed: {path}")

        # Changed values
        if 'values_changed' in diff:
            for path, change in diff['values_changed'].items():
                old_val = change['old_value']
                new_val = change['new_value']
                differences.append(f"Changed: {path} from '{old_val}' to '{new_val}'")

        # Type changes
        if 'type_changes' in diff:
            for path, change in diff['type_changes'].items():
                old_type = type(change['old_value']).__name__
                new_type = type(change['new_value']).__name__
                differences.append(f"Type changed: {path} from {old_type} to {new_type}")

        return differences

    def validate_files(self, baseline_file: str, comparison_file: str) -> Dict[str, Any]:
        """
        Validate two JSON files by comparing them.

        Args:
            baseline_file: Path to baseline JSON file
            comparison_file: Path to comparison JSON file

        Returns:
            Validation result with status and differences
        """
        baseline_data = self.load_json_file(baseline_file)
        comparison_data = self.load_json_file(comparison_file)

        differences = self.compare_json(baseline_data, comparison_data)

        status = "PASS" if not differences else "FAIL"

        return {
            "status": status,
            "differences": differences,
            "baseline_file": baseline_file,
            "comparison_file": comparison_file
        }


def main():
    """Command line interface."""
    if len(sys.argv) != 3:
        print("Usage: python3 json_validator.py <baseline_file> <comparison_file>")
        sys.exit(1)

    baseline_file = sys.argv[1]
    comparison_file = sys.argv[2]

    validator = JsonValidator()

    try:
        result = validator.validate_files(baseline_file, comparison_file)

        print(f"Validation Result: {result['status']}")
        if result['differences']:
            print("Differences found:")
            for diff in result['differences']:
                print(f"  - {diff}")
        else:
            print("No differences found.")

        sys.exit(0 if result['status'] == 'PASS' else 1)

    except ValidationError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()