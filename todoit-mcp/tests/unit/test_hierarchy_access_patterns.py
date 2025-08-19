"""
Unit tests for different hierarchy access patterns
Tests that were missing and caused confusion during refactoring
"""

import pytest
from core.manager import TodoManager


class TestHierarchyAccessPatterns:
    """Test various ways to access hierarchical items"""

    @pytest.fixture
    def manager_with_hierarchy(self, temp_db):
        manager = TodoManager(temp_db)
        manager.create_list("test", "Test")
        
        # 3-level hierarchy
        manager.add_item("test", "root", "Root")
        manager.add_subitem("test", "root", "level1", "Level 1")
        manager.add_subitem("test", "level1", "level2", "Level 2")
        
        return manager

    def test_direct_item_access(self, manager_with_hierarchy):
        """Test accessing top-level items directly"""
        root = manager_with_hierarchy.get_item("test", "root")
        assert root is not None
        assert root.item_key == "root"
        assert root.parent_item_id is None

    def test_subitem_access_with_parent_key(self, manager_with_hierarchy):
        """Test accessing subitems with parent_item_key"""
        level1 = manager_with_hierarchy.get_item("test", "level1", parent_item_key="root")
        assert level1 is not None
        assert level1.item_key == "level1"
        assert level1.parent_item_id is not None

    def test_deep_subitem_access(self, manager_with_hierarchy):
        """Test accessing deeply nested subitems"""
        level2 = manager_with_hierarchy.get_item("test", "level2", parent_item_key="level1")
        assert level2 is not None
        assert level2.item_key == "level2"

    def test_subitem_access_without_parent_key_fails(self, manager_with_hierarchy):
        """Test that subitems cannot be accessed without parent_item_key"""
        # This should return None because "level1" is a subitem
        result = manager_with_hierarchy.get_item("test", "level1")
        assert result is None

    def test_wrong_parent_key_fails(self, manager_with_hierarchy):
        """Test accessing subitem with wrong parent fails"""
        # "level2" is child of "level1", not "root"
        result = manager_with_hierarchy.get_item("test", "level2", parent_item_key="root")
        assert result is None

    def test_update_operations_require_correct_parent_key(self, manager_with_hierarchy):
        """Test that update operations need correct parent_item_key"""
        # Update leaf item (level2 has no children) - should work
        manager_with_hierarchy.update_item_status("test", "level2", "completed", parent_item_key="level1")
        item = manager_with_hierarchy.get_item("test", "level2", parent_item_key="level1")
        assert item.status == "completed"
        
        # This should fail - wrong parent key
        with pytest.raises(ValueError, match="not found under parent"):
            manager_with_hierarchy.update_item_status("test", "level2", "completed", parent_item_key="root")

    def test_items_with_children_cannot_have_manual_status_change(self, manager_with_hierarchy):
        """Test that items with subtasks cannot have manual status changes"""
        # level1 has level2 as child, so manual status change should fail
        with pytest.raises(ValueError, match="has subtasks"):
            manager_with_hierarchy.update_item_status("test", "level1", "completed", parent_item_key="root")

    def test_delete_operations_require_correct_parent_key(self, manager_with_hierarchy):
        """Test that delete operations need correct parent_item_key"""
        # Create extra subitem for testing
        manager_with_hierarchy.add_subitem("test", "root", "extra", "Extra")
        
        # This should work
        success = manager_with_hierarchy.delete_item("test", "extra", parent_item_key="root")
        assert success is True
        
        # Verify it's gone
        result = manager_with_hierarchy.get_item("test", "extra", parent_item_key="root")
        assert result is None