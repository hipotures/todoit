"""
Unit tests for todo_get_list_items limit functionality
Tests limit parameter functionality at all layers
"""

import pytest
from core.manager import TodoManager


class TestListItemsLimit:
    """Test suite for list items limit functionality"""

    def test_get_list_items_no_limit(self, manager):
        """Test getting all items when no limit specified"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add multiple items
        for i in range(5):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Get all items (no limit)
        items = manager.get_list_items("test_list")
        assert len(items) == 5

        # Verify order by position
        for i, item in enumerate(items):
            assert item.item_key == f"item_{i}"

    def test_get_list_items_with_limit(self, manager):
        """Test getting limited number of items"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add multiple items
        for i in range(10):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Get limited items
        items = manager.get_list_items("test_list", limit=3)
        assert len(items) == 3

        # Verify we get first 3 items by position
        for i, item in enumerate(items):
            assert item.item_key == f"item_{i}"

    def test_get_list_items_with_status_and_limit(self, manager):
        """Test combining status filter with limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add multiple items
        for i in range(10):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Complete some items
        for i in [1, 3, 5, 7, 9]:
            manager.update_item_status("test_list", f"item_{i}", status="completed")

        # Get limited pending items
        pending_items = manager.get_list_items("test_list", status="pending", limit=2)
        assert len(pending_items) == 2

        # Should get item_0 and item_2 (first two pending)
        assert pending_items[0].item_key == "item_0"
        assert pending_items[1].item_key == "item_2"

        # Get limited completed items
        completed_items = manager.get_list_items(
            "test_list", status="completed", limit=3
        )
        assert len(completed_items) == 3

        # Should get item_1, item_3, item_5 (first three completed)
        expected_completed = ["item_1", "item_3", "item_5"]
        for i, item in enumerate(completed_items):
            assert item.item_key == expected_completed[i]

    def test_get_list_items_limit_larger_than_available(self, manager):
        """Test limit larger than available items"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add only 3 items
        for i in range(3):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Request 10 items (more than available)
        items = manager.get_list_items("test_list", limit=10)
        assert len(items) == 3  # Should return all available items

        # Verify all items returned
        for i, item in enumerate(items):
            assert item.item_key == f"item_{i}"

    def test_get_list_items_zero_limit(self, manager):
        """Test behavior with zero limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items
        for i in range(5):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Request 0 items
        items = manager.get_list_items("test_list", limit=0)
        assert len(items) == 0

    def test_get_list_items_negative_limit(self, manager):
        """Test behavior with negative limit"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items
        for i in range(5):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Request negative limit (should be treated as no limit since < 0)
        items = manager.get_list_items("test_list", limit=-1)
        assert len(items) == 5  # Should return all items

    def test_get_list_items_empty_list_with_limit(self, manager):
        """Test limit on empty list"""
        # Create empty list
        todo_list = manager.create_list("test_list", "Test List")

        # Request items with limit
        items = manager.get_list_items("test_list", limit=5)
        assert len(items) == 0

    def test_database_layer_limit(self, manager):
        """Test limit functionality at database layer"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items
        for i in range(8):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Test database layer directly
        db_list = manager.db.get_list_by_key("test_list")

        # Get limited items from database
        db_items = manager.db.get_list_items(db_list.id, limit=4)
        assert len(db_items) == 4

        # Verify order (should be by position)
        for i, db_item in enumerate(db_items):
            assert db_item.item_key == f"item_{i}"

    def test_limit_with_different_item_keys(self, manager):
        """Test limit respects natural sorting by item_key"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items with different item_keys (position is no longer primary sort criterion)
        manager.add_item("test_list", "item_high", "High Priority", position=100)
        manager.add_item("test_list", "item_low", "Low Priority", position=1)
        manager.add_item("test_list", "item_medium", "Medium Priority", position=50)

        # Get limited items (should respect natural sort order by item_key)
        items = manager.get_list_items("test_list", limit=2)
        assert len(items) == 2

        # Should get items ordered naturally by item_key: item_high, item_low (alphabetically)
        assert items[0].item_key == "item_high"
        assert items[1].item_key == "item_low"

    def test_limit_preserves_data_integrity(self, manager):
        """Test that limit doesn't affect item data quality"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items with various properties
        for i in range(5):
            manager.add_item("test_list", f"item_{i}", f"Detailed content for item {i}")
            manager.set_item_property("test_list", f"item_{i}", "priority", str(i))

        # Get limited items
        items = manager.get_list_items("test_list", limit=3)
        assert len(items) == 3

        # Verify all item data is intact
        for i, item in enumerate(items):
            assert item.item_key == f"item_{i}"
            assert item.content == f"Detailed content for item {i}"
            assert item.list_id == todo_list.id
            assert item.status.value == "pending"  # Default status

    def test_limit_consistency_across_calls(self, manager):
        """Test that limit returns consistent results across multiple calls"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items
        for i in range(10):
            manager.add_item("test_list", f"item_{i}", f"Item {i}")

        # Call multiple times with same limit
        items_1 = manager.get_list_items("test_list", limit=4)
        items_2 = manager.get_list_items("test_list", limit=4)

        # Results should be identical
        assert len(items_1) == len(items_2) == 4
        for i in range(4):
            assert items_1[i].item_key == items_2[i].item_key
            assert items_1[i].id == items_2[i].id
