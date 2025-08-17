"""
Unit tests for enhanced list all functionality
Tests both CLI and MCP enhancements for failed status display
"""

import pytest
import os
from unittest.mock import patch
from io import StringIO
import json

from core.manager import TodoManager
from interfaces.mcp_server import todo_list_all
from interfaces.cli_modules.display import _display_records


class TestListAllEnhancements:
    """Test enhanced list all functionality with failed status"""

    @pytest.fixture
    def manager_with_failed_tasks(self, manager):
        """Create manager with lists having different statuses including failed"""
        # Create test lists
        list1 = manager.create_list(
            "test_list_1", "Test List 1", ["Item 1", "Item 2", "Item 3"]
        )
        list2 = manager.create_list("test_list_2", "Test List 2", ["Item A", "Item B"])

        # Get actual item keys that were generated
        items_list1 = manager.get_list_items("test_list_1")
        items_list2 = manager.get_list_items("test_list_2")

        # Set different statuses for tasks using actual keys
        if len(items_list1) >= 3:
            manager.update_item_status(
                "test_list_1", items_list1[0].item_key, status="completed"
            )
            manager.update_item_status(
                "test_list_1", items_list1[1].item_key, status="failed"
            )  # Set one item to failed
            manager.update_item_status(
                "test_list_1", items_list1[2].item_key, status="in_progress"
            )

        if len(items_list2) >= 1:
            manager.update_item_status(
                "test_list_2", items_list2[0].item_key, status="failed"
            )  # Another failed item
            # items_list2[1] stays as pending

        return manager

    def test_cli_list_all_includes_failed_column(self, manager_with_failed_tasks):
        """Test that CLI list all now includes separate failed column"""
        # Get lists and their progress stats
        lists = manager_with_failed_tasks.list_all()

        # Simulate the enhanced record structure from CLI
        data = []
        for todo_list in lists:
            progress = manager_with_failed_tasks.get_progress(todo_list.list_key)
            record = {
                "ID": str(todo_list.id),
                "Key": todo_list.list_key,
                "Title": todo_list.title,
                "🔀": "S",  # Sequential type
                "📋": str(progress.pending),
                "🔄": str(progress.in_progress),
                "❌": str(progress.failed),
                "✅": str(progress.completed),
                "⏳": f"{progress.completion_percentage:.0f}%",
            }
            data.append(record)

        # Verify the structure contains all expected columns
        assert len(data) == 2

        # Test list 1: 1 completed, 1 failed, 1 in_progress, 0 pending
        list1_record = next(r for r in data if r["Key"] == "test_list_1")
        assert list1_record["📋"] == "0"  # pending
        assert list1_record["🔄"] == "1"  # in_progress
        assert list1_record["❌"] == "1"  # failed
        assert list1_record["✅"] == "1"  # completed

        # Test list 2: 1 failed, 1 pending, 0 others
        list2_record = next(r for r in data if r["Key"] == "test_list_2")
        assert list2_record["📋"] == "1"  # pending
        assert list2_record["🔄"] == "0"  # in_progress
        assert list2_record["❌"] == "1"  # failed
        assert list2_record["✅"] == "0"  # completed

    def test_cli_failed_column_always_present(self, manager):
        """Test that failed column (❌) is present even when no tasks are failed"""
        # Create list with no failed tasks
        manager.create_list("clean_list", "Clean List", ["Item 1", "Item 2"])

        lists = manager.list_all()
        todo_list = lists[0]
        progress = manager.get_progress(todo_list.list_key)

        record = {
            "ID": str(todo_list.id),
            "Key": todo_list.list_key,
            "Title": todo_list.title,
            "🔀": "S",
            "📋": str(progress.pending),
            "🔄": str(progress.in_progress),
            "❌": str(progress.failed),  # Should be present even if 0
            "✅": str(progress.completed),
            "⏳": f"{progress.completion_percentage:.0f}%",
        }

        # Verify failed column exists and shows 0
        assert "❌" in record
        assert record["❌"] == "0"
        assert progress.failed == 0

    @pytest.mark.asyncio
    async def test_mcp_list_all_includes_progress_stats(
        self, manager_with_failed_tasks
    ):
        """Test that MCP todo_list_all now includes progress statistics"""
        # Mock the manager initialization to use our test manager
        with patch(
            "interfaces.mcp_server.init_manager", return_value=manager_with_failed_tasks
        ):
            result = await todo_list_all(limit=5)

        assert result["success"] is True
        assert result["count"] == 2
        assert "lists" in result

        lists = result["lists"]
        assert len(lists) == 2

        # Check that each list now has progress data
        for list_data in lists:
            assert "progress" in list_data
            progress = list_data["progress"]

            # Verify all expected progress fields exist
            expected_fields = [
                "total",
                "completed",
                "in_progress",
                "pending",
                "failed",
                "completion_percentage",
                "blocked",
                "available",
            ]
            for field in expected_fields:
                assert field in progress, f"Missing field: {field}"

        # Find specific lists and verify their failed counts
        test_list_1 = next(l for l in lists if l["list_key"] == "test_list_1")
        test_list_2 = next(l for l in lists if l["list_key"] == "test_list_2")

        assert test_list_1["progress"]["failed"] == 1
        assert test_list_2["progress"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_mcp_list_all_failed_zero_when_no_failed_tasks(self, manager):
        """Test MCP tool shows failed: 0 when no tasks are failed"""
        manager.create_list("no_failed_list", "No Failed List", ["Item 1"])

        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_list_all(limit=5)

        assert result["success"] is True
        lists = result["lists"]
        list_data = lists[0]

        assert "progress" in list_data
        progress = list_data["progress"]
        assert progress["failed"] == 0
        assert progress["pending"] == 1  # The one item should be pending

    def test_column_styling_definitions(self):
        """Test that column styling includes proper configuration for failed status"""
        expected_columns = {
            "ID": {"style": "dim", "width": 4},
            "Key": {"style": "cyan"},
            "Title": {"style": "white"},
            "🔀": {"style": "yellow", "justify": "center", "width": 3},
            "📋": {"style": "blue", "justify": "right", "width": 3},  # pending
            "🔄": {"style": "yellow", "justify": "right", "width": 3},  # in_progress
            "❌": {"style": "red", "justify": "right", "width": 3},  # failed
            "✅": {"style": "green", "justify": "right", "width": 3},  # completed
            "⏳": {"style": "magenta", "justify": "right"},
        }

        # Verify failed column has correct styling
        assert expected_columns["❌"]["style"] == "red"
        assert expected_columns["❌"]["justify"] == "right"
        assert expected_columns["❌"]["width"] == 3

    @patch("sys.stdout", new_callable=StringIO)
    def test_json_output_includes_failed_stats(
        self, mock_stdout, manager_with_failed_tasks
    ):
        """Test that JSON output format includes failed statistics"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        try:
            # Simulate the data structure that would be passed to _display_records
            lists = manager_with_failed_tasks.list_all()
            data = []

            for todo_list in lists:
                progress = manager_with_failed_tasks.get_progress(todo_list.list_key)
                record = {
                    "Key": todo_list.list_key,
                    "Title": todo_list.title,
                    "📋": str(progress.pending),
                    "🔄": str(progress.in_progress),
                    "❌": str(progress.failed),
                    "✅": str(progress.completed),
                }
                data.append(record)

            _display_records(data, "Test Lists")

            output = mock_stdout.getvalue()
            json_data = json.loads(output)

            assert "data" in json_data
            assert len(json_data["data"]) == 2

            # Check that failed column exists in JSON output (mapped from ❌ to failed_count)
            for record in json_data["data"]:
                assert "failed_count" in record

        finally:
            if "TODOIT_OUTPUT_FORMAT" in os.environ:
                del os.environ["TODOIT_OUTPUT_FORMAT"]

    def teardown_method(self):
        """Clean up environment variables"""
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]
