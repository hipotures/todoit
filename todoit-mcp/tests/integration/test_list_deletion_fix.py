"""
Integration test for list deletion with item properties fix.
Tests the foreign key constraint issue resolution.
"""

import pytest
from core.manager import TodoManager


class TestListDeletionFix:
    """Test list deletion with proper cascade handling"""

    @pytest.fixture
    def temp_manager(self, temp_db):
        """Create manager with test database"""
        return TodoManager(temp_db)

    def test_delete_list_with_item_properties(self, temp_manager):
        """Test deleting list with items that have properties (main bug)"""
        # Create list
        test_list = temp_manager.create_list("test_list", "Test List")

        # Create item
        test_item = temp_manager.add_item("test_list", "test_item", "Test content")

        # Add item properties (this was causing foreign key constraint error)
        temp_manager.set_item_property("test_list", "test_item", "priority", "high")
        temp_manager.set_item_property("test_list", "test_item", "assignee", "john_doe")

        # Verify properties exist
        properties = temp_manager.get_item_properties("test_list", "test_item")
        assert len(properties) == 2
        assert "priority" in properties
        assert "assignee" in properties
        assert properties["priority"] == "high"
        assert properties["assignee"] == "john_doe"

        # Delete list - this should NOT raise foreign key constraint error
        success = temp_manager.delete_list("test_list")
        assert success is True

        # Verify list is gone
        deleted_list = temp_manager.get_list("test_list")
        assert deleted_list is None

    def test_delete_list_with_complex_structure(self, temp_manager):
        """Test deleting list with items, properties, subtasks, and history"""
        # Create list
        temp_manager.create_list("complex_list", "Complex List")

        # Create parent item
        temp_manager.add_item("complex_list", "parent_item", "Parent item")
        temp_manager.set_item_property(
            "complex_list", "parent_item", "priority", "high"
        )

        # Create subitem
        temp_manager.add_subitem("complex_list", "parent_item", "subtask1", "Subitem 1")
        temp_manager.set_item_property("complex_list", "subtask1", "assignee", "alice", parent_item_key="parent_item")

        # Update subitem status (creates history and auto-syncs parent)
        temp_manager.update_item_status(
            "complex_list", "subtask1", status="in_progress", parent_item_key="parent_item"
        )
        temp_manager.update_item_content(
            "complex_list", "subtask1", "Updated subitem content", parent_item_key="parent_item"
        )

        # Add list properties
        temp_manager.set_list_property("complex_list", "team", "backend")
        temp_manager.set_list_property("complex_list", "project", "main")

        # Verify everything exists
        parent = temp_manager.get_item("complex_list", "parent_item")
        assert parent is not None

        subtasks = temp_manager.get_subitems("complex_list", "parent_item")
        assert len(subtasks) == 1

        # Delete list - should handle all cascade deletions properly
        success = temp_manager.delete_list("complex_list")
        assert success is True

        # Verify everything is gone
        deleted_list = temp_manager.get_list("complex_list")
        assert deleted_list is None

    def test_delete_list_with_cross_list_dependencies(self, temp_manager):
        """Test deleting list with cross-list item dependencies"""
        # Create two lists
        temp_manager.create_list("list_a", "List A")
        temp_manager.create_list("list_b", "List B")

        # Create items in both lists
        temp_manager.add_item("list_a", "task_a", "Item A")
        temp_manager.add_item("list_b", "task_b", "Item B")

        # Add properties to both items
        temp_manager.set_item_property("list_a", "task_a", "priority", "high")
        temp_manager.set_item_property("list_b", "task_b", "priority", "low")

        # Create cross-list dependency
        temp_manager.add_item_dependency("list_b", "task_b", "list_a", "task_a")

        # Verify dependency exists
        blockers = temp_manager.get_item_blockers("list_b", "task_b")
        assert len(blockers) == 1

        # Delete list_a - should clean up cross-list dependencies properly
        success = temp_manager.delete_list("list_a")
        assert success is True

        # Verify list_a is gone
        deleted_list_a = temp_manager.get_list("list_a")
        assert deleted_list_a is None

        # Verify list_b still exists but dependency is gone
        list_b = temp_manager.get_list("list_b")
        assert list_b is not None

        # Check that cross-list dependency was cleaned up
        blockers_after = temp_manager.get_item_blockers("list_b", "task_b")
        assert len(blockers_after) == 0

    def test_bulk_list_deletion_no_foreign_key_errors(self, temp_manager):
        """Test bulk deletion of multiple lists (like the CLI command that failed)"""
        # Create multiple lists with complex structures
        for i in range(3):
            list_key = f"bulk_list_{i}"
            temp_manager.create_list(list_key, f"Bulk List {i}")

            # Add items with properties
            for j in range(2):
                item_key = f"item_{j}"
                temp_manager.add_item(list_key, item_key, f"Item {j} in list {i}")
                temp_manager.set_item_property(
                    list_key, item_key, "priority", f"level_{j}"
                )
                temp_manager.set_item_property(
                    list_key, item_key, "category", f"cat_{i}"
                )

        # Delete all lists - should work without foreign key errors
        for i in range(3):
            list_key = f"bulk_list_{i}"
            success = temp_manager.delete_list(list_key)
            assert success is True

            # Verify each list is gone
            deleted_list = temp_manager.get_list(list_key)
            assert deleted_list is None
