"""
Test JSON output format for stats progress command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for stats progress command
"""

import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestStatsProgressJsonOutput:
    """Test JSON output format for stats progress command"""

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

    def test_stats_progress_json_output_with_mixed_tasks(self):
        """Test stats progress command with JSON output when list has mixed task statuses"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Progress Test List",
                ],
            )
            assert result.exit_code == 0

            # Add tasks with different statuses
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "add",
                    "testlist",
                    "task1",
                    "Completed Task",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "add",
                    "testlist",
                    "task2",
                    "In Progress Task",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task3", "Pending Task"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task4", "Failed Task"],
            )
            assert result.exit_code == 0

            # Set appropriate statuses
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task1",
                    "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task2",
                    "--status",
                    "in_progress",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task4",
                    "--status",
                    "failed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for progress
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            # Check data structure
            progress_data = output_data["data"][0]
            assert "List" in progress_data
            assert "Total" in progress_data
            assert "Completed" in progress_data
            assert "Completion %" in progress_data
            assert "In Progress" in progress_data
            assert "Pending" in progress_data
            assert "Failed" in progress_data

            # Verify actual values
            assert progress_data["List"] == "Progress Test List"
            assert progress_data["Total"] == "4"
            assert progress_data["Completed"] == "1"
            assert progress_data["In Progress"] == "1"
            assert progress_data["Pending"] == "1"
            assert progress_data["Failed"] == "1"

            # Verify completion percentage (25% = 1/4)
            assert "25.0%" in progress_data["Completion %"]

    def test_stats_progress_json_output_empty_list(self):
        """Test stats progress command with JSON output for empty list"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create an empty test list
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "emptylist",
                    "--title",
                    "Empty List",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for progress of empty list
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "emptylist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            # Check empty list progress
            progress_data = output_data["data"][0]
            assert progress_data["List"] == "Empty List"
            assert progress_data["Total"] == "0"
            assert progress_data["Completed"] == "0"
            assert progress_data["In Progress"] == "0"
            assert progress_data["Pending"] == "0"
            assert progress_data["Failed"] == "0"
            assert "0.0%" in progress_data["Completion %"]

    def test_stats_progress_json_output_all_completed(self):
        """Test stats progress command with JSON output when all tasks are completed"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Completed List",
                ],
            )
            assert result.exit_code == 0

            # Add tasks and complete them
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "add", "testlist", "task1", "Task 1"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "add", "testlist", "task2", "Task 2"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task1",
                    "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task2",
                    "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for 100% completed list
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            progress_data = output_data["data"][0]

            assert progress_data["Total"] == "2"
            assert progress_data["Completed"] == "2"
            assert progress_data["In Progress"] == "0"
            assert progress_data["Pending"] == "0"
            assert progress_data["Failed"] == "0"
            assert "100.0%" in progress_data["Completion %"]

    def test_stats_progress_json_output_with_detailed_flag(self):
        """Test stats progress command with JSON output and --detailed flag"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list with tasks
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task1", "Test Task"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "task1",
                    "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output with detailed flag
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist", "--detailed"]
            )
            assert result.exit_code == 0

            # Detailed mode should still start with valid JSON, followed by progress bar
            # Verify that output starts with JSON
            assert result.output.strip().startswith("{")

            # Verify that it contains progress information and visual progress bar
            assert "Test List" in result.output
            assert "100.0%" in result.output
            assert "█" in result.output  # Progress bar visual element

            # Basic validation that JSON structure exists
            assert '"title":' in result.output
            assert '"count":' in result.output
            assert '"data":' in result.output

    def test_stats_progress_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task1", "Test Task"],
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist"]
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "Test List" in result.output
            assert "Progress Report" in result.output

    def test_stats_progress_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task1", "Test Task"],
            )
            assert result.exit_code == 0

            # Test YAML output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist"]
            )
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "Test List" in result.output

    def test_stats_progress_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list",
                    "create",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "testlist", "task1", "Test Task"],
            )
            assert result.exit_code == 0

            # Test XML output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "stats", "progress", "testlist"]
            )
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "Test List" in result.output
