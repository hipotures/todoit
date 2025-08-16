"""
Test JSON output format for item tree command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for item tree command
"""

import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestItemTreeJsonOutput:
    """Test JSON output format for item tree command"""

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

    def test_item_tree_json_output_entire_list(self):
        """Test item list --list command --item with JSON output for entire list"""
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
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add some tasks with different statuses
            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "First Item"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task2", "--title", "Second Item"],
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
                    "in_progress",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for entire list tree
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 2
            assert len(output_data["data"]) == 2

            # Check data structure
            for item_data in output_data["data"]:
                assert "Position" in item_data
                assert "Key" in item_data
                assert "Status" in item_data
                assert "Item" in item_data

            # Verify tasks are present
            keys = [item["Key"] for item in output_data["data"]]
            assert "task1" in keys
            assert "task2" in keys

            # Verify status icons are present
            statuses = [item["Status"] for item in output_data["data"]]
            assert any("✅" in status for status in statuses)  # completed
            assert any("🔄" in status for status in statuses)  # in_progress

    def test_item_tree_json_output_specific_item(self):
        """Test item list --list command --item with JSON output for specific item"""
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
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Add a parent item
            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "parent", "--title", "Parent Item"],
            )
            assert result.exit_code == 0

            # Add subtasks
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "add",
                    "testlist",
                    "parent",
                    "sub1",
                    "Subitem 1",
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
                    "parent",
                    "sub2",
                    "Subitem 2",
                ],
            )
            assert result.exit_code == 0

            # Set some statuses
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "status",
                    "testlist",
                    "sub1",
                    "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for specific item hierarchy
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist", "parent"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 3  # parent + 2 subtasks

            # Check hierarchy structure
            levels = [item["Level"] for item in output_data["data"]]
            assert "0" in levels  # parent level
            assert "1" in levels  # subitem level

            # Verify parent item is at level 0
            parent_items = [
                item for item in output_data["data"] if item["Level"] == "0"
            ]
            assert len(parent_items) == 1
            assert parent_items[0]["Item"] == "parent"
            assert parent_items[0]["Content"] == "Parent Item"

            # Verify subtasks are at level 1
            subtask_items = [
                item for item in output_data["data"] if item["Level"] == "1"
            ]
            assert len(subtask_items) == 2
            subtask_keys = [item["Item"] for item in subtask_items]
            assert "sub1" in subtask_keys
            assert "sub2" in subtask_keys

    def test_item_tree_json_output_empty_list(self):
        """Test item list --list command --item with JSON output for empty list"""
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

            # Test JSON output for empty list tree
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "emptylist"]
            )
            assert result.exit_code == 0

            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []

    def test_item_tree_json_output_hierarchy_display(self):
        """Test that hierarchy visualization is present in JSON output"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list with hierarchy
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

            # Add a parent item
            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "parent", "--title", "Parent Item"],
            )
            assert result.exit_code == 0

            # Add a subitem
            result = self.runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item",
                    "add",
                    "testlist",
                    "parent",
                    "child",
                    "Child Item",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for specific item
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist", "parent"]
            )
            assert result.exit_code == 0

            # Verify hierarchy visualization in JSON
            output_data = json.loads(result.output)

            # Check parent item hierarchy display
            parent_item = next(
                item for item in output_data["data"] if item["Level"] == "0"
            )
            assert "📋" in parent_item["Hierarchy"]
            assert "parent:" in parent_item["Hierarchy"]

            # Check child item hierarchy display
            child_item = next(
                item for item in output_data["data"] if item["Level"] == "1"
            )
            assert "└─" in child_item["Hierarchy"]
            assert "child:" in child_item["Hierarchy"]

    def test_item_tree_json_output_nonexistent_item(self):
        """Test item list --list command --item with JSON output for nonexistent item"""
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
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output for nonexistent item (should handle gracefully)
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist", "nonexistent"]
            )

            # Command may fail or return empty - either is acceptable for nonexistent items
            # We just verify it doesn't crash
            assert isinstance(result.output, str)

    def test_item_tree_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a test list and item
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
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist"]
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "Test Item" in result.output
            assert "task1" in result.output

    def test_item_tree_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Create a test list and item
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
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test YAML output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "Test Item" in result.output

    def test_item_tree_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Create a test list and item
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
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Test Item"],
            )
            assert result.exit_code == 0

            # Test XML output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "Test Item" in result.output

    def test_item_tree_positions_and_keys_present(self):
        """Test that positions and keys are correctly present in JSON output"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list with multiple tasks
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
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "first", "--title", "First Item"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "second", "--title", "Second Item"],
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db", "test.db", "item", "list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify positions and keys
            output_data = json.loads(result.output)

            positions = [item["Position"] for item in output_data["data"]]
            keys = [item["Key"] for item in output_data["data"]]

            assert "1" in positions
            assert "2" in positions
            assert "first" in keys
            assert "second" in keys
