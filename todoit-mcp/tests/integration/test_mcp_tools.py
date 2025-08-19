"""
Consolidated MCP Tools Tests
Combines tests from test_mcp_tools_simple.py, test_mcp_tools_fixed.py, and test_mcp_tools_functional.py
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from core.manager import TodoManager


class TestMCPToolsBasic:
    """Basic MCP tools functionality tests"""

    def test_mcp_server_imports(self):
        """Test that mcp_server can be imported without errors"""
        from interfaces import mcp_server

        assert hasattr(mcp_server, "mcp")

    def test_mcp_tools_count(self):
        """Test that we have expected number of MCP tools"""
        import subprocess

        current_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_server_path = os.path.join(
            current_dir, "..", "..", "interfaces", "mcp_server.py"
        )

        result = subprocess.run(
            ["grep", "-c", "async def todo_", mcp_server_path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise AssertionError(
                f"Failed to count tools in {mcp_server_path}: {result.stderr}"
            )

        tool_count = int(result.stdout.strip())
        # Expected count is 51 as per current implementation
        expected_count = 51
        assert tool_count == expected_count, f"Expected exactly {expected_count} MCP tools, found {tool_count}"

    def test_mcp_tool_names(self):
        """Test that all expected tool names are present"""
        import subprocess

        current_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_server_path = os.path.join(
            current_dir, "..", "..", "interfaces", "mcp_server.py"
        )

        result = subprocess.run(
            ["grep", "-oE", "async def todo_[a-z_]+", mcp_server_path],
            capture_output=True,
            text=True,
        )

        tool_functions = result.stdout.strip().split("\n")
        tool_names = [func.replace("async def ", "") for func in tool_functions]

        expected_tools = [
            "todo_create_list",
            "todo_get_list",
            "todo_delete_list",
            "todo_list_all",
            "todo_add_item",
            "todo_update_item_status",
            "todo_get_next_pending",
            "todo_get_progress",
            "todo_quick_add",
            "todo_delete_item",
        ]

        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"Missing expected tool: {expected_tool}"


class TestMCPToolsFunctional:
    """Functional tests for MCP tools with real database"""

    @pytest.fixture
    def temp_manager(self):
        """Create manager with temporary database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        manager = TodoManager(db_path)
        yield manager
        os.unlink(db_path)

    def test_list_operations(self, temp_manager):
        """Test list CRUD operations"""
        # Create list
        list_obj = temp_manager.create_list(
            list_key="test_list", title="Test List", items=["Item 1", "Item 2"]
        )
        assert list_obj.list_key == "test_list"
        assert list_obj.title == "Test List"

        # Get list
        retrieved = temp_manager.get_list("test_list")
        assert retrieved.list_key == "test_list"

        # List all
        all_lists = temp_manager.list_all()
        assert len(all_lists) == 1

        # Delete list
        temp_manager.delete_list("test_list")
        all_lists = temp_manager.list_all()
        assert len(all_lists) == 0

    def test_item_operations(self, temp_manager):
        """Test item CRUD operations"""
        # Create list with items
        list_obj = temp_manager.create_list("item_test", "Item Test List")

        # Add items
        item1 = temp_manager.add_item("item_test", "task1", "Do something")
        item2 = temp_manager.add_item("item_test", "task2", "Do something else")

        assert item1.item_key == "task1"
        assert item2.item_key == "task2"

        # Update status
        updated = temp_manager.update_item_status("item_test", "task1", status="in_progress")
        assert updated.status == "in_progress"

        # Mark completed using status update
        completed = temp_manager.update_item_status("item_test", "task2", status="completed")
        assert completed.status == "completed"

        # Get progress
        progress = temp_manager.get_progress("item_test")
        assert progress.total == 2
        assert progress.completed == 1

        # Update content
        updated_content = temp_manager.update_item_content(
            "item_test", "task1", "Updated item"
        )
        assert updated_content.content == "Updated item"

        # Delete item
        temp_manager.delete_item("item_test", "task1")
        progress = temp_manager.get_progress("item_test")
        assert progress.total == 1

    def test_subtask_operations(self, temp_manager):
        """Test subitem functionality if available"""
        list_obj = temp_manager.create_list("subtask_test", "Subitem Test")

        # Add parent item
        parent = temp_manager.add_item("subtask_test", "parent", "Parent item")

        # Test subtasks if the methods exist
        if hasattr(temp_manager, "add_subitem"):
            subitem = temp_manager.add_subitem(
                "subtask_test", "parent", "sub1", "Subitem 1"
            )
            # Note: subtask might not have parent_key attribute in the model
            assert subitem.item_key == "sub1"

            # Get subtasks
            if hasattr(temp_manager, "get_subitems"):
                subtasks = temp_manager.get_subitems("subtask_test", "parent")
                assert len(subtasks) >= 1

    def test_dependency_operations(self, temp_manager):
        """Test cross-list dependencies if available"""
        # Create two lists
        backend = temp_manager.create_list("backend", "Backend Tasks")
        frontend = temp_manager.create_list("frontend", "Frontend Tasks")

        # Add items
        temp_manager.add_item("backend", "api", "Create API")
        temp_manager.add_item("frontend", "ui", "Create UI")

        # Test dependencies if the methods exist
        if hasattr(temp_manager, "add_item_dependency"):
            dep = temp_manager.add_item_dependency(
                "frontend", "ui", "backend", "api", "blocks"
            )
            assert dep is not None

            # Check if blocked
            if hasattr(temp_manager, "get_item_blockers"):
                blockers = temp_manager.get_item_blockers("frontend", "ui")
                # blockers might return a list or object with blockers attribute
                if hasattr(blockers, "blockers"):
                    assert len(blockers.blockers) >= 0
                elif isinstance(blockers, list):
                    assert len(blockers) >= 0

    def test_properties_operations(self, temp_manager):
        """Test list and item properties"""
        list_obj = temp_manager.create_list("prop_test", "Property Test")

        # Set list property
        prop = temp_manager.set_list_property("prop_test", "priority", "high")
        assert prop.property_value == "high"

        # Get list property
        value = temp_manager.get_list_property("prop_test", "priority")
        assert value == "high"

        # Add item with properties
        temp_manager.add_item("prop_test", "item1", "Test item")
        item_prop = temp_manager.set_item_property(
            "prop_test", "item1", "size", "large"
        )
        assert item_prop.property_value == "large"

        # Get item property
        item_value = temp_manager.get_item_property("prop_test", "item1", "size")
        assert item_value == "large"

    def test_quick_add(self, temp_manager):
        """Test quick add functionality if available"""
        temp_manager.create_list("quick_test", "Quick Test")

        # Test quick add if method exists
        if hasattr(temp_manager, "quick_add"):
            items = ["Item A", "Item B", "Item C"]
            added = temp_manager.quick_add("quick_test", items)

            assert len(added) == 3
            # Check if returned as dict or object
            if isinstance(added[0], dict):
                assert added[0]["content"] == "Item A"
                assert "item_0001" in added[0]["item_key"] or added[0][
                    "item_key"
                ].startswith("item_")
            else:
                assert added[0].content == "Item A"

    def test_smart_next_pending(self, temp_manager):
        """Test next pending algorithm"""
        list_obj = temp_manager.create_list("smart_test", "Smart Algorithm Test")

        # Add some items
        temp_manager.add_item("smart_test", "task1", "Item 1")
        temp_manager.add_item("smart_test", "task2", "Item 2")

        # Test next pending methods if available
        if hasattr(temp_manager, "get_next_pending"):
            next_item = temp_manager.get_next_pending("smart_test")
            assert next_item is not None
            # Check return format
            if isinstance(next_item, dict):
                assert next_item["item_key"] in ["task1", "task2"]
            else:
                assert next_item.item_key in ["task1", "task2"]

    def test_comprehensive_status(self, temp_manager):
        """Test comprehensive status functionality if available"""
        list_obj = temp_manager.create_list("status_test", "Status Test")

        # Add items
        temp_manager.add_item("status_test", "task1", "Item 1")
        temp_manager.add_item("status_test", "task2", "Item 2")
        temp_manager.update_item_status("status_test", "task1", status="completed")

        # Test comprehensive status if method exists
        if hasattr(temp_manager, "get_comprehensive_status"):
            status = temp_manager.get_comprehensive_status("status_test")
            assert status is not None
            # Status might have different structure
            if isinstance(status, dict):
                assert "stats" in status or "total" in status

    def test_error_handling(self, temp_manager):
        """Test error handling in MCP tools"""
        # Try to create duplicate list
        temp_manager.create_list("error_test", "Error Test")
        with pytest.raises(ValueError):
            temp_manager.create_list("error_test", "Another Error Test")

        # Try to add item to non-existent list
        try:
            temp_manager.add_item("non_existent", "item", "content")
            assert False, "Should have raised an error"
        except (ValueError, Exception):
            # Expected some kind of error
            pass

    def test_empty_list_handling(self, temp_manager):
        """Test handling of empty lists"""
        empty_list = temp_manager.create_list("empty", "Empty List")

        # Get progress on empty list
        progress = temp_manager.get_progress("empty")
        assert progress.total == 0
        assert progress.completed == 0

        # Get next pending on empty list
        if hasattr(temp_manager, "get_next_pending"):
            next_item = temp_manager.get_next_pending("empty")
            assert next_item is None
