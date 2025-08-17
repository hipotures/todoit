"""
Integration tests for item management functionality (delete and edit content).
Tests both manager and MCP layers for the new CRUD operations.
"""

import pytest
from unittest.mock import patch
from core.manager import TodoManager
from core.models import ItemStatus
from interfaces import mcp_server


class TestItemManagement:
    """Test item deletion and content editing"""

    @pytest.fixture
    def temp_manager(self, temp_db):
        """Create manager with test database"""
        return TodoManager(temp_db)

    @pytest.fixture
    def sample_list_and_item(self, temp_manager):
        """Create a sample list and item for testing"""
        # Create list
        test_list = temp_manager.create_list("test_list", "Test List")

        # Create item
        test_item = temp_manager.add_item(
            "test_list", "test_item", "Original test content"
        )

        return test_list, test_item

    # ===== MANAGER TESTS =====

    def test_delete_item_success(self, temp_manager, sample_list_and_item):
        """Test successful item deletion through manager"""
        test_list, test_item = sample_list_and_item

        # Verify item exists
        item = temp_manager.get_item("test_list", "test_item")
        assert item is not None
        assert item.content == "Original test content"

        # Delete item
        success = temp_manager.delete_item("test_list", "test_item")
        assert success is True

        # Verify item is gone
        deleted_item = temp_manager.get_item("test_list", "test_item")
        assert deleted_item is None

    def test_delete_item_nonexistent_list(self, temp_manager):
        """Test deleting item from non-existent list"""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            temp_manager.delete_item("nonexistent", "item")

    def test_delete_item_nonexistent_item(self, temp_manager, sample_list_and_item):
        """Test deleting non-existent item"""
        # Should return False for non-existent item
        success = temp_manager.delete_item("test_list", "nonexistent_item")
        assert success is False

    def test_delete_item_with_subtasks(self, temp_manager, sample_list_and_item):
        """Test deleting item with subtasks deletes all recursively"""
        test_list, test_item = sample_list_and_item

        # Add subtasks
        subtask1 = temp_manager.add_subitem(
            "test_list", "test_item", "sub1", "Subitem 1"
        )
        subtask2 = temp_manager.add_subitem(
            "test_list", "test_item", "sub2", "Subitem 2"
        )

        # Add sub-subitem
        temp_manager.add_subitem("test_list", "sub1", "subsub1", "Sub-subitem 1")

        # Verify all items exist
        assert temp_manager.get_item("test_list", "test_item") is not None
        assert temp_manager.get_item("test_list", "sub1") is not None
        assert temp_manager.get_item("test_list", "sub2") is not None
        assert temp_manager.get_item("test_list", "subsub1") is not None

        # Delete parent item
        success = temp_manager.delete_item("test_list", "test_item")
        assert success is True

        # Verify all items are gone
        assert temp_manager.get_item("test_list", "test_item") is None
        assert temp_manager.get_item("test_list", "sub1") is None
        assert temp_manager.get_item("test_list", "sub2") is None
        assert temp_manager.get_item("test_list", "subsub1") is None

    def test_update_item_content_success(self, temp_manager, sample_list_and_item):
        """Test successful content update through manager"""
        test_list, test_item = sample_list_and_item

        # Update content
        new_content = "Updated test content"
        updated_item = temp_manager.update_item_content(
            "test_list", "test_item", new_content
        )

        # Verify update
        assert updated_item.content == new_content
        assert updated_item.item_key == "test_item"

        # Verify persistence
        retrieved_item = temp_manager.get_item("test_list", "test_item")
        assert retrieved_item.content == new_content

    def test_update_item_content_nonexistent_list(self, temp_manager):
        """Test updating content in non-existent list"""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            temp_manager.update_item_content("nonexistent", "item", "new content")

    def test_update_item_content_nonexistent_item(
        self, temp_manager, sample_list_and_item
    ):
        """Test updating content of non-existent item"""
        with pytest.raises(ValueError, match="Item 'nonexistent' not found"):
            temp_manager.update_item_content("test_list", "nonexistent", "new content")

    def test_update_item_content_empty_content(
        self, temp_manager, sample_list_and_item
    ):
        """Test updating with empty content"""
        # Should be allowed - empty content is valid
        updated_item = temp_manager.update_item_content("test_list", "test_item", "")
        assert updated_item.content == ""

    def test_update_item_content_history_tracking(
        self, temp_manager, sample_list_and_item
    ):
        """Test that content updates are tracked in history"""
        test_list, test_item = sample_list_and_item

        # Update content
        temp_manager.update_item_content(
            "test_list", "test_item", "New content for history test"
        )

        # Check history was recorded
        history = temp_manager.get_item_history("test_list", "test_item")

        # Should have creation history and update history
        assert len(history) >= 2

        # Find the update history entry
        update_entries = [h for h in history if h.action == "updated"]
        assert len(update_entries) >= 1

        # Check the history contains content update info
        update_entry = update_entries[-1]  # Most recent update
        assert update_entry.new_value is not None
        assert update_entry.new_value.get("content") == "New content for history test"
        assert update_entry.old_value is not None
        assert update_entry.old_value.get("content") == "Original test content"

    # ===== MCP TESTS =====

    def test_mcp_delete_item_success(self, temp_manager, sample_list_and_item):
        """Test successful item deletion through MCP"""
        test_list, test_item = sample_list_and_item

        # Mock the manager initialization
        with patch("interfaces.mcp_server.init_manager", return_value=temp_manager):
            # Call MCP function
            import asyncio

            result = asyncio.run(mcp_server.todo_delete_item("test_list", "test_item"))

        # Verify MCP response
        assert result["success"] is True
        assert "deleted" in result["message"].lower()
        assert "test_item" in result["message"]
        assert "test_list" in result["message"]

        # Verify item is actually deleted
        deleted_item = temp_manager.get_item("test_list", "test_item")
        assert deleted_item is None

    def test_mcp_delete_item_not_found(self, temp_manager, sample_list_and_item):
        """Test MCP delete item when item doesn't exist"""
        test_list, test_item = sample_list_and_item

        with patch("interfaces.mcp_server.init_manager", return_value=temp_manager):
            import asyncio

            result = asyncio.run(
                mcp_server.todo_delete_item("test_list", "nonexistent")
            )

        # Should return success=False
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_mcp_update_content_success(self, temp_manager, sample_list_and_item):
        """Test successful content update through MCP"""
        test_list, test_item = sample_list_and_item

        new_content = "MCP updated content"

        with patch("interfaces.mcp_server.init_manager", return_value=temp_manager):
            import asyncio

            result = asyncio.run(
                mcp_server.todo_rename_item(
                    "test_list", "test_item", new_title=new_content
                )
            )

        # Verify MCP response
        assert result["success"] is True
        assert "renamed" in result["message"].lower()
        assert "test_item" in result["message"]

        # Verify response contains updated item
        assert "item" in result
        assert result["item"]["title"] == new_content

        # Verify persistence
        updated_item = temp_manager.get_item("test_list", "test_item")
        assert updated_item.content == new_content

    def test_mcp_update_content_error_handling(self, temp_manager):
        """Test MCP content update error handling"""
        with patch("interfaces.mcp_server.init_manager", return_value=temp_manager):
            import asyncio

            result = asyncio.run(
                mcp_server.todo_rename_item("nonexistent", "item", new_title="content")
            )

        # Should return error
        assert result["success"] is False
        assert "error" in result

    # ===== INTEGRATION TESTS =====

    def test_delete_and_recreate_item(self, temp_manager, sample_list_and_item):
        """Test deleting an item and recreating it with same key"""
        test_list, test_item = sample_list_and_item

        # Delete item
        temp_manager.delete_item("test_list", "test_item")

        # Recreate with same key but different content
        new_item = temp_manager.add_item(
            "test_list", "test_item", "Recreated item content"
        )

        # Verify it's a new item
        assert new_item.content == "Recreated item content"
        assert new_item.item_key == "test_item"

    def test_content_update_preserves_other_fields(
        self, temp_manager, sample_list_and_item
    ):
        """Test that content update doesn't affect other item fields"""
        test_list, test_item = sample_list_and_item

        # Update status first
        temp_manager.update_item_status("test_list", "test_item", status="in_progress")

        # Get current state
        item_before = temp_manager.get_item("test_list", "test_item")

        # Update content
        temp_manager.update_item_content("test_list", "test_item", "Content updated")

        # Get updated state
        item_after = temp_manager.get_item("test_list", "test_item")

        # Verify content changed but other fields preserved
        assert item_after.content == "Content updated"
        assert item_after.status == item_before.status  # Should still be in_progress
        assert item_after.item_key == item_before.item_key
        assert item_after.position == item_before.position

    def test_bulk_operations_compatibility(self, temp_manager):
        """Test that new operations work with bulk scenarios"""
        # Create multiple items
        temp_manager.create_list("bulk_test", "Bulk Test List")

        items = []
        for i in range(5):
            item = temp_manager.add_item("bulk_test", f"item_{i}", f"Content {i}")
            items.append(item)

        # Update content of multiple items
        for i in range(3):
            temp_manager.update_item_content(
                "bulk_test", f"item_{i}", f"Updated content {i}"
            )

        # Delete some items
        for i in range(2):
            temp_manager.delete_item("bulk_test", f"item_{i}")

        # Verify final state
        remaining_items = temp_manager.get_list_items("bulk_test")
        assert len(remaining_items) == 3

        # Check updated items
        item_2 = temp_manager.get_item("bulk_test", "item_2")
        assert item_2.content == "Updated content 2"

        # Check unchanged items
        item_3 = temp_manager.get_item("bulk_test", "item_3")
        assert item_3.content == "Content 3"
