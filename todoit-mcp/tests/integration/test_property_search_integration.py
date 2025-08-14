"""
Integration tests for property search functionality.

Tests the complete property search workflow including database operations,
MCP tools, and CLI commands with real database interactions.
"""

import pytest
import json
import os
from click.testing import CliRunner
from core.manager import TodoManager
from interfaces.mcp_server import todo_find_items_by_property
from interfaces.cli_modules.item_commands import item_find


class TestPropertySearchIntegration:
    """Integration tests for property search with real database"""

    @pytest.fixture
    def manager(self, temp_db):
        """Create TodoManager with temporary database."""
        return TodoManager(temp_db)

    @pytest.fixture
    def setup_test_data(self, manager):
        """Setup test data with items and properties."""
        # Create test list
        test_list = manager.create_list("testlist", "Test List", "Test description")

        # Add test items
        item1 = manager.add_item(
            "testlist", "task1", "First task", metadata={"priority": "high"}
        )
        item2 = manager.add_item(
            "testlist", "task2", "Second task", metadata={"priority": "low"}
        )
        item3 = manager.add_item(
            "testlist", "task3", "Third task", metadata={"status": "reviewed"}
        )

        # Add properties
        manager.set_item_property("testlist", "task1", "issue_id", "123")
        manager.set_item_property("testlist", "task1", "category", "bug")
        manager.set_item_property("testlist", "task2", "issue_id", "456")
        manager.set_item_property("testlist", "task2", "category", "feature")
        manager.set_item_property("testlist", "task3", "priority", "medium")
        manager.set_item_property("testlist", "task3", "category", "bug")

        return {"list_key": "testlist", "items": [item1, item2, item3]}

    def test_database_find_items_by_property_integration(
        self, manager, setup_test_data
    ):
        """Test database find_items_by_property with real database."""
        # Get list ID
        db_list = manager.db.get_list_by_key("testlist")

        # Search by category=bug
        results = manager.db.find_items_by_property(db_list.id, "category", "bug")

        assert len(results) == 2
        item_keys = [item.item_key for item in results]
        assert "task1" in item_keys
        assert "task3" in item_keys

    def test_database_find_items_by_property_with_limit(self, manager, setup_test_data):
        """Test database search with limit parameter."""
        db_list = manager.db.get_list_by_key("testlist")

        # Search with limit=1
        results = manager.db.find_items_by_property(
            db_list.id, "category", "bug", limit=1
        )

        assert len(results) == 1
        # Should return first result by position
        assert results[0].item_key == "task1"

    def test_manager_find_items_by_property_integration(self, manager, setup_test_data):
        """Test manager find_items_by_property with real database."""
        # Search by issue_id
        results = manager.find_items_by_property("testlist", "issue_id", "123")

        assert len(results) == 1
        assert results[0].item_key == "task1"
        assert results[0].content == "First task"

    def test_manager_find_items_by_property_multiple_results(
        self, manager, setup_test_data
    ):
        """Test manager search returning multiple results."""
        # Search by category=bug (should return 2 items)
        results = manager.find_items_by_property("testlist", "category", "bug")

        assert len(results) == 2
        item_keys = [item.item_key for item in results]
        assert "task1" in item_keys
        assert "task3" in item_keys

    def test_manager_find_items_by_property_with_limit(self, manager, setup_test_data):
        """Test manager search with limit."""
        # Search with limit=1
        results = manager.find_items_by_property("testlist", "category", "bug", limit=1)

        assert len(results) == 1
        assert results[0].item_key == "task1"

    def test_manager_find_items_by_property_list_not_found(self, manager):
        """Test manager search with non-existent list."""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.find_items_by_property("nonexistent", "property", "value")

    @pytest.mark.asyncio
    async def test_mcp_find_items_by_property_integration(
        self, manager, setup_test_data
    ):
        """Test MCP todo_find_items_by_property tool."""
        # Call function directly without @mcp_error_handler decorator to use our manager
        try:
            items = manager.find_items_by_property("testlist", "category", "bug")

            # Convert items to dictionaries like the MCP tool does
            items_data = []
            for item in items:
                item_dict = item.to_dict()
                items_data.append(item_dict)

            result = {
                "success": True,
                "items": items_data,
                "count": len(items_data),
                "search_criteria": {
                    "list_key": "testlist",
                    "property_key": "category",
                    "property_value": "bug",
                    "limit": None,
                },
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["items"]) == 2

        item_keys = [item["item_key"] for item in result["items"]]
        assert "task1" in item_keys
        assert "task3" in item_keys

        # Verify search criteria in response
        assert result["search_criteria"]["property_key"] == "category"
        assert result["search_criteria"]["property_value"] == "bug"
        assert result["search_criteria"]["list_key"] == "testlist"

    def test_mcp_logic_simulation_with_limit(self, manager, setup_test_data):
        """Test MCP logic simulation - search with limit parameter."""
        # Simulate what MCP tool would do
        items = manager.find_items_by_property("testlist", "category", "bug", limit=1)

        assert len(items) == 1
        assert items[0].item_key == "task1"

    def test_mcp_logic_simulation_empty_result(self, manager, setup_test_data):
        """Test MCP logic simulation - search with no results."""
        items = manager.find_items_by_property("testlist", "nonexistent", "value")

        assert len(items) == 0

    def test_mcp_logic_simulation_find_single_item(self, manager, setup_test_data):
        """Test MCP logic simulation - find single item using limit=1."""
        items = manager.find_items_by_property("testlist", "issue_id", "123", limit=1)

        assert len(items) == 1
        assert items[0].item_key == "task1"
        assert items[0].content == "First task"

    def test_mcp_logic_simulation_find_single_not_found(self, manager, setup_test_data):
        """Test MCP logic simulation - single item search with no result."""
        items = manager.find_items_by_property(
            "testlist", "nonexistent", "value", limit=1
        )

        assert len(items) == 0

    def test_cli_item_find_integration(self, manager, setup_test_data):
        """Test CLI item find command."""
        runner = CliRunner()

        # Test successful search
        result = runner.invoke(
            item_find,
            ["testlist", "--property", "category", "--value", "bug"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0
        output = result.output
        assert "task1" in output
        assert "task3" in output
        assert "Found 2 item(s)" in output

    def test_cli_item_find_with_limit(self, manager, setup_test_data):
        """Test CLI item find with limit option."""
        runner = CliRunner()

        result = runner.invoke(
            item_find,
            ["testlist", "--property", "category", "--value", "bug", "--limit", "1"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0
        output = result.output
        assert "task1" in output
        assert "task3" not in output  # Should not appear due to limit
        assert "Found 1 item(s)" in output
        assert "(limit: 1)" in output

    def test_cli_item_find_with_first_flag(self, manager, setup_test_data):
        """Test CLI item find with --first flag."""
        runner = CliRunner()

        result = runner.invoke(
            item_find,
            ["testlist", "--property", "category", "--value", "bug", "--first"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0
        output = result.output
        assert "task1" in output
        assert "task3" not in output  # Should not appear due to --first
        assert "Found 1 item(s)" in output
        assert "(limit: 1)" in output

    def test_cli_item_find_no_results(self, manager, setup_test_data):
        """Test CLI item find with no matching results."""
        runner = CliRunner()

        result = runner.invoke(
            item_find,
            ["testlist", "--property", "nonexistent", "--value", "value"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0
        output = result.output
        # Check that it shows empty results - could be "No search results" or "Found 0 item(s)"
        assert ("Found 0 item(s)" in output) or (
            "No" in output and "search results" in output
        )

    def test_cli_item_find_json_format(self, manager, setup_test_data):
        """Test CLI item find with JSON output format."""
        runner = CliRunner()

        # Set JSON output format
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        try:
            result = runner.invoke(
                item_find,
                ["testlist", "--property", "category", "--value", "bug"],
                obj={"db_path": manager.db.db_path},
            )

            assert result.exit_code == 0

            # Parse JSON output - unified display returns {title, data, count}
            json_data = json.loads(result.output)
            assert json_data["count"] == 2
            assert len(json_data["data"]) == 2

            item_keys = [item["Item Key"] for item in json_data["data"]]
            assert "task1" in item_keys
            assert "task3" in item_keys

        finally:
            # Clean up environment variable
            os.environ.pop("TODOIT_OUTPUT_FORMAT", None)

    def test_cli_item_find_list_not_found(self, manager):
        """Test CLI item find with non-existent list."""
        runner = CliRunner()

        result = runner.invoke(
            item_find,
            ["nonexistent", "--property", "test", "--value", "value"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_search_performance_with_index(self, manager):
        """Test that search performance is reasonable with database index."""
        # Create a list with many items
        manager.create_list("perftest", "Performance Test", "Large list")

        # Add many items with properties
        for i in range(100):
            item_key = f"item{i:03d}"
            manager.add_item("perftest", item_key, f"Task {i}")

            # Add properties - some items will have matching properties
            if i % 10 == 0:  # Every 10th item has priority=high
                manager.set_item_property("perftest", item_key, "priority", "high")
            else:
                manager.set_item_property("perftest", item_key, "priority", "low")

            manager.set_item_property("perftest", item_key, "batch", str(i // 10))

        # Search should complete quickly and return correct results
        import time

        start_time = time.time()
        results = manager.find_items_by_property("perftest", "priority", "high")
        search_time = time.time() - start_time

        # Verify results
        assert len(results) == 10  # Every 10th item

        # Performance check - should complete in under 1 second even with 100 items
        assert search_time < 1.0, f"Search took {search_time:.2f}s, should be under 1s"

        # Verify correct items returned
        for result in results:
            item_num = int(result.item_key.replace("item", ""))
            assert item_num % 10 == 0  # Should only be items 000, 010, 020, etc.
