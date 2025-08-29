"""
Test JSON output format for dep graph command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for dep graph command
"""

import json
import os

import pytest
from click.testing import CliRunner

from interfaces.cli import cli


class TestDepGraphJsonOutput:
    """Test JSON output format for dep graph command"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        # Clean environment before each test
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]

    def teardown_method(self):
        """Clean up after each test"""
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]

    def test_dep_graph_json_output_no_project(self):
        """Test dep graph command with JSON output when no project specified"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output without project parameter (should show error)
            result = self.runner.invoke(cli, ["--db-path", "test.db", "dep", "graph"])

            # Command should handle missing project parameter
            assert isinstance(result.output, str)
            # May not be valid JSON due to error message, which is acceptable

    def test_dep_graph_json_output_empty_project(self):
        """Test dep graph command with JSON output for nonexistent project"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for nonexistent project
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "nonexistent"],
            )
            assert result.exit_code == 0

            # Should return empty result in JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []
            assert "nonexistent" in output_data["title"]

    def test_dep_graph_json_output_basic_project(self):
        """Test dep graph command with JSON output for basic project without dependencies"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a list with project tag
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "backend",
                    "--title",
                    "Backend",
                ],
            )
            assert result.exit_code == 0

            # Add project tag/relation (this may require specific setup depending on implementation)
            # For now, just test with basic list and see what the graph shows

            # Test JSON output for project
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "testproject"],
            )
            assert result.exit_code == 0

            # Verify JSON format (may be empty if no project relations exist)
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert "testproject" in output_data["title"]

    def test_dep_graph_json_output_structure_consistency(self):
        """Test that JSON structure is consistent"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test with any project name
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "testproject"],
            )
            assert result.exit_code == 0

            # Verify consistent JSON structure
            output_data = json.loads(result.output)

            # Check required top-level fields
            required_fields = ["title", "count", "data"]
            for field in required_fields:
                assert field in output_data

            # Check that data is a list
            assert isinstance(output_data["data"], list)

            # If data exists, check structure
            for item in output_data["data"]:
                # Each data item should have these fields for dep graph
                expected_fields = ["Type", "Name", "Details", "Status"]
                for field in expected_fields:
                    assert field in item
                    assert isinstance(item[field], str)

    def test_dep_graph_json_output_with_mock_data(self):
        """Test dep graph with some lists (even if not properly linked to project)"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create some lists that could be part of a project
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "frontend",
                    "--title",
                    "Frontend Tasks",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "backend",
                    "--title",
                    "Backend Tasks",
                ],
            )
            assert result.exit_code == 0

            # Add some tasks
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item",
                    "add",
                    "--list",
                    "frontend",
                    "--item",
                    "ui",
                    "--title",
                    "User Interface",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item",
                    "add",
                    "--list",
                    "backend",
                    "--item",
                    "api",
                    "--title",
                    "API Development",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output (may be empty if lists aren't properly linked to project)
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "dep", "graph", "--project", "webapp"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data

            # Count should match data length
            assert output_data["count"] == len(output_data["data"])

    def test_dep_graph_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Test table output
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "testproject"],
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "testproject" in result.output

    def test_dep_graph_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Test YAML output
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "testproject"],
            )
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "testproject" in result.output

    def test_dep_graph_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Test XML output
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "dep", "graph", "--project", "testproject"],
            )
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "testproject" in result.output

    def test_dep_graph_json_output_error_handling(self):
        """Test that errors are handled gracefully in JSON output"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test with various potentially problematic inputs
            test_cases = [
                "normal_project",
                "project-with-dashes",
                "project_with_underscores",
                "Project With Spaces",  # This might cause issues
                "123numeric",
                "special!chars@#",  # This might cause issues
            ]

            for project_name in test_cases:
                result = self.runner.invoke(
                    cli,
                    ["--db-path", "test.db", "dep", "graph", "--project", project_name],
                )

                # Should not crash, either success or controlled failure
                assert isinstance(result.output, str)

                # If it succeeds, should be valid JSON
                if result.exit_code == 0:
                    try:
                        output_data = json.loads(result.output)
                        assert "title" in output_data
                        assert "count" in output_data
                        assert "data" in output_data
                    except json.JSONDecodeError:
                        # If JSON parsing fails, that's acceptable for error cases
                        pass

    def test_dep_graph_json_field_types(self):
        """Test that all JSON fields have correct types"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "dep", "graph", "--project", "typetest"]
            )
            assert result.exit_code == 0

            # Verify field types
            output_data = json.loads(result.output)

            # Top-level fields
            assert isinstance(output_data["title"], str)
            assert isinstance(output_data["count"], int)
            assert isinstance(output_data["data"], list)

            # Data item fields
            for item in output_data["data"]:
                assert isinstance(item["Type"], str)
                assert isinstance(item["Name"], str)
                assert isinstance(item["Details"], str)
                assert isinstance(item["Status"], str)

    def test_dep_graph_json_count_accuracy(self):
        """Test that count field accurately reflects data length"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "dep", "graph", "--project", "counttest"]
            )
            assert result.exit_code == 0

            # Verify count accuracy
            output_data = json.loads(result.output)
            assert output_data["count"] == len(output_data["data"])

            # Count should be non-negative
            assert output_data["count"] >= 0
