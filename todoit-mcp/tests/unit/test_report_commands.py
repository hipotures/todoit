"""
Unit tests for report commands functionality
Tests both CLI and MCP implementations for failed item reporting
"""

import asyncio
import re
from io import StringIO
from unittest.mock import patch

import pytest

from core.manager import TodoManager
from interfaces.cli_modules.display import _display_records
from interfaces.mcp_server import todo_report_errors


class TestReportCommands:
    """Test report commands functionality"""

    @pytest.fixture
    def manager_with_failed_tasks(self, manager):
        """Create manager with mixed status tasks including failed ones"""
        # Create test lists with different naming patterns
        list1 = manager.create_list(
            "0001_project_alpha", "Project Alpha", ["Item 1", "Item 2", "Item 3"]
        )
        list2 = manager.create_list(
            "0023_beta_sprint", "Beta Sprint", ["Feature A", "Bug fix"]
        )
        list3 = manager.create_list(
            "simple_project", "Simple Project", ["Regular item"]
        )

        # Get actual item keys
        items1 = manager.get_list_items("0001_project_alpha")
        items2 = manager.get_list_items("0023_beta_sprint")
        items3 = manager.get_list_items("simple_project")

        # Set various statuses including failed
        if items1:
            manager.update_item_status(
                "0001_project_alpha", items1[0].item_key, status="failed"
            )
            manager.update_item_status(
                "0001_project_alpha", items1[1].item_key, status="completed"
            )
            # Add properties to failed item
            manager.set_item_property(
                "0001_project_alpha", items1[0].item_key, "error_type", "timeout"
            )
            manager.set_item_property(
                "0001_project_alpha", items1[0].item_key, "retry_count", "3"
            )

        if items2:
            manager.update_item_status(
                "0023_beta_sprint", items2[0].item_key, status="failed"
            )
            manager.update_item_status(
                "0023_beta_sprint", items2[1].item_key, status="in_progress"
            )
            # Add properties to failed item
            manager.set_item_property(
                "0023_beta_sprint", items2[0].item_key, "severity", "high"
            )

        if items3:
            manager.update_item_status(
                "simple_project", items3[0].item_key, status="pending"
            )

        return manager

    def test_get_all_failed_items_basic(self, manager_with_failed_tasks):
        """Test basic functionality of get_all_failed_items"""
        failed_items = manager_with_failed_tasks.get_all_failed_items()

        assert len(failed_items) == 2  # Two failed items across lists

        # Verify data structure
        for item in failed_items:
            assert "list_key" in item
            assert "list_title" in item
            assert "item_key" in item
            assert "content" in item
            assert "properties" in item
            assert "updated_at" in item

        # Verify failed items are from expected lists
        list_keys = [item["list_key"] for item in failed_items]
        assert "0001_project_alpha" in list_keys
        assert "0023_beta_sprint" in list_keys
        assert "simple_project" not in list_keys  # No failed items

    def test_get_all_failed_items_with_regex_filter(self, manager_with_failed_tasks):
        """Test regex filtering functionality"""
        # Filter for NNNN_ pattern (4 digits + underscore)
        filtered_items = manager_with_failed_tasks.get_all_failed_items(
            list_filter=r"^\d{4}_.*"
        )

        assert len(filtered_items) == 2  # Both failed items match pattern

        for item in filtered_items:
            assert re.match(r"^\d{4}_.*", item["list_key"])

        # Test more specific filter
        specific_filter = manager_with_failed_tasks.get_all_failed_items(
            list_filter=r"^0001_.*"
        )
        assert len(specific_filter) == 1
        assert specific_filter[0]["list_key"] == "0001_project_alpha"

    def test_get_all_failed_items_no_matches(self, manager_with_failed_tasks):
        """Test behavior when no failed items match criteria"""
        # Filter that won't match any lists
        no_matches = manager_with_failed_tasks.get_all_failed_items(
            list_filter=r"^nonexistent_.*"
        )
        assert len(no_matches) == 0

    def test_get_all_failed_items_invalid_regex(self, manager_with_failed_tasks):
        """Test handling of invalid regex patterns"""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            manager_with_failed_tasks.get_all_failed_items(list_filter=r"[invalid")

    def test_get_all_failed_items_includes_properties(self, manager_with_failed_tasks):
        """Test that properties are included in failed items"""
        failed_items = manager_with_failed_tasks.get_all_failed_items()

        # Find item from project alpha
        alpha_item = next(
            item for item in failed_items if item["list_key"] == "0001_project_alpha"
        )

        assert "properties" in alpha_item
        assert alpha_item["properties"]["error_type"] == "timeout"
        assert alpha_item["properties"]["retry_count"] == "3"

        # Find item from beta sprint
        beta_item = next(
            item for item in failed_items if item["list_key"] == "0023_beta_sprint"
        )
        assert beta_item["properties"]["severity"] == "high"

    def test_get_all_failed_items_sorting(self, manager_with_failed_tasks):
        """Test that results are sorted by list_key then position"""
        failed_items = manager_with_failed_tasks.get_all_failed_items()

        # Should be sorted by list_key first
        list_keys = [item["list_key"] for item in failed_items]
        assert list_keys == sorted(list_keys)

    def test_get_all_failed_items_empty_result(self, manager):
        """Test behavior when no failed tasks exist"""
        # Create list with no failed items
        manager.create_list("test_list", "Test List", ["Item 1", "Item 2"])

        failed_items = manager.get_all_failed_items()
        assert len(failed_items) == 0

    def test_get_all_failed_items_ignores_archived_lists(
        self, manager_with_failed_tasks
    ):
        """Test that archived lists are excluded from results"""
        # Archive one of the lists with failed items
        manager_with_failed_tasks.archive_list("0001_project_alpha", force=True)

        failed_items = manager_with_failed_tasks.get_all_failed_items()

        # Should only have failed item from active list
        assert len(failed_items) == 1
        assert failed_items[0]["list_key"] == "0023_beta_sprint"

    @pytest.mark.asyncio
    async def test_mcp_todo_report_errors_basic(self, manager_with_failed_tasks):
        """Test MCP tool basic functionality"""
        with patch(
            "interfaces.mcp_server.init_manager", return_value=manager_with_failed_tasks
        ):
            result = await todo_report_errors()

        assert result["success"] is True
        assert "failed_tasks" in result
        assert "count" in result
        assert "metadata" in result

        assert result["count"] == 2
        assert len(result["failed_tasks"]) == 2

        # Check metadata
        metadata = result["metadata"]
        assert "lists_scanned" in metadata
        assert "lists_matched" in metadata
        assert "unique_lists_with_failures" in metadata

        assert metadata["unique_lists_with_failures"] == 2

    @pytest.mark.asyncio
    async def test_mcp_todo_report_errors_with_filter(self, manager_with_failed_tasks):
        """Test MCP tool with regex filtering"""
        with patch(
            "interfaces.mcp_server.init_manager", return_value=manager_with_failed_tasks
        ):
            result = await todo_report_errors(list_filter=r"^\d{4}_.*")

        assert result["success"] is True
        assert result["count"] == 2
        assert result["metadata"]["list_filter_applied"] == r"^\d{4}_.*"
        assert result["metadata"]["lists_matched"] == 2  # Both NNNN_ lists

    @pytest.mark.asyncio
    async def test_mcp_todo_report_errors_no_failures(self, manager):
        """Test MCP tool when no failed tasks exist"""
        manager.create_list("test_list", "Test List", ["Item 1"])

        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_report_errors()

        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["failed_tasks"]) == 0
        assert result["metadata"]["unique_lists_with_failures"] == 0

    @pytest.mark.asyncio
    async def test_mcp_todo_report_errors_datetime_serialization(
        self, manager_with_failed_tasks
    ):
        """Test that datetime objects are properly serialized to ISO format"""
        with patch(
            "interfaces.mcp_server.init_manager", return_value=manager_with_failed_tasks
        ):
            result = await todo_report_errors()

        assert result["success"] is True

        for item in result["failed_tasks"]:
            # Check that datetime fields are strings in ISO format
            if "updated_at" in item:
                assert isinstance(item["updated_at"], str)
                # Should be parseable as ISO datetime
                from datetime import datetime

                datetime.fromisoformat(item["updated_at"])

            if "created_at" in item:
                assert isinstance(item["created_at"], str)
                datetime.fromisoformat(item["created_at"])

    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_display_format_table(self, mock_stdout, manager_with_failed_tasks):
        """Test CLI display format in table mode"""
        failed_items = manager_with_failed_tasks.get_all_failed_items()

        # Simulate CLI data preparation
        data = []
        for item_info in failed_items:
            props_str = ", ".join(
                [f"{k}={v}" for k, v in item_info.get("properties", {}).items()]
            )
            record = {
                "List": item_info["list_key"],
                "Item": item_info["item_key"],
                "Content": item_info["content"][:35],
                "Properties": (
                    props_str[:30] + "..." if len(props_str) > 30 else props_str
                ),
            }
            data.append(record)

        # Test that _display_records can handle the data structure
        _display_records(data, "Test Failed Tasks Report")

        # Should have produced some output
        output = mock_stdout.getvalue()
        assert len(output) > 0
        assert "Test Failed Tasks Report" in output

    def test_regex_patterns_common_cases(self, manager_with_failed_tasks):
        """Test common regex patterns that users might use"""
        # Test various patterns
        patterns = [
            (r"^\d{4}_.*", 2, "NNNN_ pattern"),
            (r"^0001.*", 1, "Starting with 0001"),
            (r".*project.*", 1, "Containing 'project'"),
            (r"^(0001|0023)_.*", 2, "Multiple specific prefixes"),
            (r".*alpha.*", 1, "Containing 'alpha'"),
            (r"^simple.*", 0, "Simple project (no failed items)"),
        ]

        for pattern, expected_count, description in patterns:
            filtered_items = manager_with_failed_tasks.get_all_failed_items(
                list_filter=pattern
            )
            assert (
                len(filtered_items) == expected_count
            ), f"Pattern {pattern} ({description}) should return {expected_count} items"

    def test_properties_handling_edge_cases(self, manager):
        """Test handling of items with no properties or empty properties"""
        # Create list with failed item but no properties
        manager.create_list("no_props_list", "No Props List", ["Failed item"])
        items = manager.get_list_items("no_props_list")

        if items:
            manager.update_item_status(
                "no_props_list", items[0].item_key, status="failed"
            )

        failed_items = manager.get_all_failed_items()
        assert len(failed_items) == 1

        # Should have empty properties dict
        assert failed_items[0]["properties"] == {}

    def teardown_method(self):
        """Clean up any environment changes"""
        # No cleanup needed for this test class
        pass
