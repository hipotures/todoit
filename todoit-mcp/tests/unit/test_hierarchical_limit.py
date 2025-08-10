"""
Unit tests for hierarchical list items with limit functionality
Tests limit parameter for todo_get_list_items_hierarchical
"""
import pytest
from core.manager import TodoManager


class TestHierarchicalLimit:
    """Test suite for hierarchical limit functionality"""

    def test_hierarchical_with_limit(self, manager):
        """Test hierarchical items retrieval with limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Add parent items
        for i in range(5):
            manager.add_item("test_list", f"parent_{i}", f"Parent {i}")
        
        # Add subtasks to each parent
        for i in range(5):
            for j in range(2):
                manager.add_subtask("test_list", f"parent_{i}", f"sub_{i}_{j}", f"Subtask {i}-{j}")
        
        # Get all items (15 total: 5 parents + 10 subtasks)
        all_items = manager.get_list_items("test_list")
        assert len(all_items) == 15
        
        # Get limited items - limit applies to flat result, not hierarchical grouping
        limited_items = manager.get_list_items("test_list", limit=3)
        assert len(limited_items) == 3  # First 3 items by position
        
        # Check we got first 3 items (1 parent + 2 subtasks by position ordering)
        assert limited_items[0].item_key == "parent_0"
        assert limited_items[1].item_key == "sub_0_0"
        assert limited_items[2].item_key == "parent_1"

    def test_hierarchical_limit_with_status_filter(self, manager):
        """Test hierarchical items with status filter and limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Add parent items
        for i in range(6):
            manager.add_item("test_list", f"parent_{i}", f"Parent {i}")
        
        # Complete some parents
        manager.update_item_status("test_list", "parent_1", "completed")
        manager.update_item_status("test_list", "parent_3", "completed")
        manager.update_item_status("test_list", "parent_5", "completed")
        
        # Add subtasks to all parents
        for i in range(6):
            manager.add_subtask("test_list", f"parent_{i}", f"sub_{i}", f"Subtask {i}")
        
        # Get limited pending items (flat limit across all pending items)
        pending_limited = manager.get_list_items("test_list", status="pending", limit=2)
        
        # Should get first 2 pending items by position (could be parents or subtasks)
        assert len(pending_limited) == 2
        assert pending_limited[0].item_key == "parent_0"  # First pending parent
        assert pending_limited[1].item_key == "sub_0"     # First subtask of parent_0

    def test_hierarchical_limit_zero(self, manager):
        """Test hierarchical items with zero limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Add items with hierarchy
        manager.add_item("test_list", "parent_1", "Parent 1")
        manager.add_subtask("test_list", "parent_1", "sub_1", "Subtask 1")
        
        # Get zero items
        zero_items = manager.get_list_items("test_list", limit=0)
        assert len(zero_items) == 0

    def test_hierarchical_limit_respects_position_ordering(self, manager):
        """Test that limit respects position ordering in hierarchical structure"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Add items with specific positions
        manager.add_item("test_list", "parent_high", "High Priority Parent", position=100)
        manager.add_item("test_list", "parent_low", "Low Priority Parent", position=1)  
        manager.add_item("test_list", "parent_medium", "Medium Priority Parent", position=50)
        
        # Add subtasks
        for parent in ["parent_high", "parent_low", "parent_medium"]:
            manager.add_subtask("test_list", parent, f"sub_{parent}", f"Subtask for {parent}")
        
        # Get limited items (should be ordered by position, flat limit)
        limited_items = manager.get_list_items("test_list", limit=2)
        
        # Should get first 2 items by position (parent_low at position 1, then its subtask)
        assert len(limited_items) == 2
        assert limited_items[0].item_key == "parent_low"
        assert limited_items[1].item_key == "sub_parent_low"

    def test_hierarchical_limit_preserves_subtask_relationships(self, manager):
        """Test that limit returns first N items by position regardless of hierarchy"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Add parents with varying numbers of subtasks
        manager.add_item("test_list", "parent_1", "Parent 1")
        manager.add_subtask("test_list", "parent_1", "sub_1_1", "Subtask 1-1")
        manager.add_subtask("test_list", "parent_1", "sub_1_2", "Subtask 1-2")
        
        manager.add_item("test_list", "parent_2", "Parent 2")
        manager.add_subtask("test_list", "parent_2", "sub_2_1", "Subtask 2-1")
        
        manager.add_item("test_list", "parent_3", "Parent 3")
        # No subtasks for parent_3
        
        # Get limited to first 2 items by position
        limited_items = manager.get_list_items("test_list", limit=2)
        
        # Should get first 2 items: parent_1 and sub_1_1
        assert len(limited_items) == 2
        assert limited_items[0].item_key == "parent_1"
        assert limited_items[1].item_key == "sub_1_1"

    def test_hierarchical_limit_edge_cases(self, manager):
        """Test hierarchical limit edge cases"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")
        
        # Test limit larger than available
        manager.add_item("test_list", "parent_1", "Parent 1")
        manager.add_subtask("test_list", "parent_1", "sub_1", "Subtask 1")
        
        large_limit = manager.get_list_items("test_list", limit=100)
        assert len(large_limit) == 2  # Should return all available
        
        # Test negative limit (should return all)
        negative_limit = manager.get_list_items("test_list", limit=-1)
        assert len(negative_limit) == 2
        
        # Test empty list with limit
        empty_list = manager.create_list("empty", "Empty")
        empty_limited = manager.get_list_items("empty", limit=5)
        assert len(empty_limited) == 0