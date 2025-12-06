import pytest
import json
import tempfile
import os
from pathlib import Path
from src.json_validator import JsonValidator, ValidationError


class TestJsonValidator:
    """Test cases for JSON validation tool."""

    @pytest.fixture
    def validator(self):
        """Fixture for JsonValidator instance."""
        return JsonValidator()

    @pytest.fixture
    def temp_files(self):
        """Fixture to create temporary JSON files."""
        files = {}
        temp_dir = Path(tempfile.mkdtemp())

        def create_file(name, content):
            file_path = temp_dir / name
            with open(file_path, 'w') as f:
                json.dump(content, f)
            files[name] = str(file_path)
            return str(file_path)

        yield create_file

        # Cleanup
        for f in temp_dir.glob('*'):
            f.unlink()
        temp_dir.rmdir()

    def test_identical_files_pass(self, validator, temp_files):
        """Test that identical JSON files pass validation."""
        data = {"id": 1, "name": "test", "email": "test@example.com"}
        file1 = temp_files("baseline.json", data)
        file2 = temp_files("comparison.json", data)

        result = validator.validate_files(file1, file2)

        assert result["status"] == "PASS"
        assert result["differences"] == []

    def test_added_field_detected(self, validator, temp_files):
        """Test detection of added fields."""
        baseline = {"id": 1, "name": "test"}
        comparison = {"id": 1, "name": "test", "email": "test@example.com"}

        file1 = temp_files("baseline.json", baseline)
        file2 = temp_files("comparison.json", comparison)

        result = validator.validate_files(file1, file2)

        assert result["status"] == "FAIL"
        assert len(result["differences"]) > 0
        assert any("email" in str(diff) for diff in result["differences"])

    def test_value_difference_detected(self, validator, temp_files):
        """Test detection of value differences."""
        baseline = {"status": "active"}
        comparison = {"status": "inactive"}

        file1 = temp_files("baseline.json", baseline)
        file2 = temp_files("comparison.json", comparison)

        result = validator.validate_files(file1, file2)

        assert result["status"] == "FAIL"
        assert len(result["differences"]) > 0
        assert any("status" in str(diff) and "active" in str(diff) and "inactive" in str(diff) for diff in result["differences"])

    def test_nested_objects_handled(self, validator, temp_files):
        """Test comparison of nested JSON objects."""
        baseline = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        comparison = {
            "user": {
                "profile": {
                    "name": "Jane",
                    "age": 30
                }
            }
        }

        file1 = temp_files("baseline.json", baseline)
        file2 = temp_files("comparison.json", comparison)

        result = validator.validate_files(file1, file2)

        assert result["status"] == "FAIL"
        assert len(result["differences"]) > 0

    def test_invalid_json_error(self, validator, temp_files):
        """Test error handling for invalid JSON."""
        # Create valid baseline
        baseline = {"test": "data"}
        file1 = temp_files("baseline.json", baseline)

        # Create invalid comparison
        file2 = temp_files("comparison.json", {})  # Will overwrite with invalid
        with open(file2, 'w') as f:
            f.write('{"invalid": json}')

        with pytest.raises(ValidationError):
            validator.validate_files(file1, file2)

    def test_missing_file_error(self, validator):
        """Test error handling for missing files."""
        with pytest.raises(ValidationError):
            validator.validate_files("nonexistent1.json", "nonexistent2.json")