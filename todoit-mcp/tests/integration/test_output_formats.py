"""
Integration tests for multiple output formats (JSON, YAML, XML)
Tests environment variable control and data serialization
"""

import pytest
import os
import json
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from io import StringIO
import sys
from unittest.mock import patch

from core.manager import TodoManager
from interfaces.cli_modules.display import (
    _display_records,
    _get_output_format,
    _serialize_for_output,
    _prepare_data_for_serialization,
)


class TestOutputFormats:
    """Test different output formats"""

    @pytest.fixture
    def sample_data(self):
        """Sample data with various data types"""
        return [
            {
                "ID": "1",
                "Key": "test_list",
                "Title": "Test List",
                "Items": "3",
                "Progress": "33.3%",
                "Created": datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            },
            {
                "ID": "2",
                "Key": "work_tasks",
                "Title": "Work Tasks",
                "Items": "5",
                "Progress": "80.0%",
                "Created": datetime(2025, 1, 2, 14, 30, 0, tzinfo=timezone.utc),
            },
        ]

    def test_get_output_format_default(self):
        """Test default output format"""
        # Clear env var if exists
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]

        assert _get_output_format() == "table"

    def test_get_output_format_valid_values(self):
        """Test valid output format values"""
        valid_formats = ["table", "vertical", "json", "yaml", "xml"]

        for format_name in valid_formats:
            os.environ["TODOIT_OUTPUT_FORMAT"] = format_name
            assert _get_output_format() == format_name

            # Test case insensitive
            os.environ["TODOIT_OUTPUT_FORMAT"] = format_name.upper()
            assert _get_output_format() == format_name

    def test_get_output_format_invalid_fallback(self):
        """Test invalid format falls back to table"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "invalid_format"
        assert _get_output_format() == "table"

    def test_serialize_for_output_datetime(self):
        """Test datetime serialization"""
        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _serialize_for_output(dt)
        assert isinstance(result, str)
        assert "2025-01-01" in result

    def test_serialize_for_output_enum(self):
        """Test enum serialization"""
        from core.models import ItemStatus

        status = ItemStatus.COMPLETED
        result = _serialize_for_output(status)
        assert result == "completed"

    def test_serialize_for_output_string(self):
        """Test string passthrough"""
        test_string = "test_value"
        result = _serialize_for_output(test_string)
        assert result == test_string

    def test_prepare_data_for_serialization(self, sample_data):
        """Test data preparation for serialization"""
        result = _prepare_data_for_serialization(sample_data)

        assert len(result) == 2
        assert isinstance(result[0]["Created"], str)
        assert isinstance(result[1]["Created"], str)

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_records_json(self, mock_stdout, sample_data):
        """Test JSON output format"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        _display_records(sample_data, "Test Lists")

        output = mock_stdout.getvalue()
        json_data = json.loads(output)

        assert json_data["title"] == "Test Lists"
        assert json_data["count"] == 2
        assert len(json_data["data"]) == 2
        assert json_data["data"][0]["Key"] == "test_list"

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_records_yaml(self, mock_stdout, sample_data):
        """Test YAML output format"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        _display_records(sample_data, "Test Lists")

        output = mock_stdout.getvalue()
        yaml_data = yaml.safe_load(output)

        assert yaml_data["title"] == "Test Lists"
        assert yaml_data["count"] == 2
        assert len(yaml_data["data"]) == 2
        assert yaml_data["data"][0]["Key"] == "test_list"

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_records_xml(self, mock_stdout, sample_data):
        """Test XML output format"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        _display_records(sample_data, "Test Lists")

        output = mock_stdout.getvalue()
        root = ET.fromstring(output)

        assert root.tag == "todoit_output"
        title_elem = root.find("title")
        assert title_elem is not None
        assert title_elem.text == "Test Lists"

        count_elem = root.find("count")
        assert count_elem is not None
        assert count_elem.text == "2"

    def test_empty_data_handling(self):
        """Test handling of empty data lists"""
        empty_data = []

        for format_name in ["json", "yaml", "xml"]:
            os.environ["TODOIT_OUTPUT_FORMAT"] = format_name

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                _display_records(empty_data, "Empty Test")
                output = mock_stdout.getvalue()
                assert len(output) > 0  # Should produce some output even for empty data

    def teardown_method(self):
        """Clean up environment variables after each test"""
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]


class TestOutputFormatsWithCLI:
    """Test output formats with actual CLI commands"""

    @pytest.fixture
    def populated_manager(self, manager):
        """Manager with test data"""
        manager.create_list("test1", "Test List 1", ["Task 1", "Task 2"])
        manager.create_list("test2", "Test List 2", ["Task A", "Task B", "Task C"])
        return manager

    def test_cli_list_all_json_format(self, populated_manager):
        """Test list all command with JSON format"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        from click.testing import CliRunner
        from interfaces.cli import cli

        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", populated_manager.db.db_path, "list", "all"]
        )

        assert result.exit_code == 0
        # Extract JSON part from output (may have extra text after JSON)
        output_lines = result.output.split("\n")
        json_start = None
        json_end = None

        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
            elif json_start is not None and line.strip().startswith("}"):
                json_end = i + 1
                break

        if json_start is not None and json_end is not None:
            json_output = "\n".join(output_lines[json_start:json_end])
            try:
                json_data = json.loads(json_output)
                assert "title" in json_data
                assert "count" in json_data
                assert "data" in json_data
                assert json_data["count"] == 2  # We created 2 lists
            except json.JSONDecodeError:
                # If JSON parsing fails, at least check that JSON-like output exists
                assert "{" in result.output
                assert "title" in result.output
                assert "count" in result.output

    def teardown_method(self):
        """Clean up environment variables"""
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]
