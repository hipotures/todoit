"""
Test JSON output format for item next --list command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for item next --list command
"""

import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestItemNextJsonOutput:
    """Test JSON output format for item next --list and next-smart commands"""

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

    def test_item_next_json_output_with_pending_task(self):
        """Test item next --list command with JSON output when pending item exists"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add a pending item
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Pending Item"],
            )
            assert result.exit_code == 0

            # Test JSON output for next item
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
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
            task_data = output_data["data"][0]
            assert "Item" in task_data
            assert "Key" in task_data
            assert "Position" in task_data
            assert "Status" in task_data
            assert task_data["Item"] == "Pending Item"
            assert task_data["Key"] == "task1"
            assert task_data["Position"] == "1"

    def test_item_next_json_output_with_multiple_pending_tasks(self):
        """Test item next --list command with JSON output when multiple pending tasks exist (should return first)"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add multiple pending tasks
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "First Item"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task2", "--title", "Second Item"],
            )
            assert result.exit_code == 0

            # Test JSON output for next item (should return first)
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            # Should return the first item (position 1)
            task_data = output_data["data"][0]
            assert task_data["Item"] == "First Item"
            assert task_data["Key"] == "task1"
            assert task_data["Position"] == "1"

    def test_item_next_json_output_no_pending_tasks(self):
        """Test item next --list command with JSON output when no pending tasks exist"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add a completed item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "add", "--list", "testlist", "--item", "task1", "--title", "Completed Item",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "status", "--list", "testlist", "--item", "task1", "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output when no pending tasks
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []

    def test_item_next_json_output_skip_in_progress_tasks(self):
        """Test item next --list command with JSON output skips in_progress tasks"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add tasks with different statuses
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "add", "--list", "testlist", "--item", "task1", "--title", "In Progress Item",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task2", "--title", "Pending Item"],
            )
            assert result.exit_code == 0

            # Set first item to in_progress
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "status", "--list", "testlist", "--item", "task1", "--status",
                    "in_progress",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output - should return the pending item, not in_progress
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            # Should return the pending item (task2)
            task_data = output_data["data"][0]
            assert task_data["Item"] == "Pending Item"
            assert task_data["Key"] == "task2"
            assert task_data["Position"] == "2"

    def test_item_next_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a test list and item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "Test Item" in result.output
            assert "task1" in result.output

    def test_item_next_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Create a test list and item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test YAML output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "Test Item" in result.output
            assert "task1" in result.output

    def test_item_next_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Create a test list and item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test XML output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "Test Item" in result.output
            assert "task1" in result.output

    # Tests for item next-smart command

    def test_item_next_smart_json_output_with_pending_task(self):
        """Test item next-smart command with JSON output when pending item exists"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add a pending item
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Pending Item"],
            )
            assert result.exit_code == 0

            # Test JSON output for next-smart item
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next-smart", "--list", "testlist"]
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
            task_data = output_data["data"][0]
            assert "Type" in task_data
            assert "Item" in task_data
            assert "Key" in task_data
            assert "Position" in task_data
            assert "Status" in task_data
            assert task_data["Type"] == "Item"  # Should be Task, not Subitem
            assert task_data["Item"] == "Pending Item"
            assert task_data["Key"] == "task1"
            assert task_data["Position"] == "1"

    def test_item_next_smart_json_output_with_subtask(self):
        """Test item next-smart command with JSON output when next item is a subitem"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add a parent item
            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "parent", "--title", "Parent Item"],
            )
            assert result.exit_code == 0

            # Add a subitem
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "add", "--list", "testlist", "--item", "parent", "--subitem", "subtask1", "--title", "Subitem 1",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for next-smart item (should prioritize subitem)
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next-smart", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            # Check that it returns the subitem
            task_data = output_data["data"][0]
            assert task_data["Type"] == "Subitem"  # Should be Subtask
            assert task_data["Item"] == "Subitem 1"
            assert task_data["Key"] == "subtask1"

    def test_item_next_smart_json_output_no_pending_tasks(self):
        """Test item next-smart command with JSON output when no pending tasks exist"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list with completed item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "add", "--list", "testlist", "--item", "task1", "--title", "Completed Item",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "item", "status", "--list", "testlist", "--item", "task1", "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output when no pending tasks
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next-smart", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []

    def test_item_next_smart_table_format_still_works(self):
        """Test that table format still works correctly for next-smart (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a test list and item
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "item", "next-smart", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "Test Item" in result.output
            assert "task1" in result.output
            assert "Item" in result.output  # Should show Type column
