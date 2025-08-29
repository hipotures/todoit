"""
Integration tests for get_all_items_properties functionality.

Tests the new function that retrieves all properties for all items
in a list with optional status filtering.
"""

import pytest

from core.manager import TodoManager


class TestGetAllItemsPropertiesIntegration:
    """Integration tests for get_all_items_properties with real database"""

    @pytest.fixture
    def manager(self, temp_db):
        """Create TodoManager with temporary database."""
        return TodoManager(temp_db)

    @pytest.fixture
    def setup_test_data(self, manager):
        """Setup test data with items and properties."""
        # Create test list
        manager.create_list("testlist", "Test List")

        # Add test items with different statuses
        manager.add_item("testlist", "task1", "First item")
        manager.add_item("testlist", "task2", "Second item")
        manager.add_item("testlist", "task3", "Third item")

        # Update statuses
        manager.update_item_status("testlist", "task2", status="in_progress")
        manager.update_item_status("testlist", "task3", status="completed")

        # Add properties to items
        manager.set_item_property("testlist", "task1", "image_downloaded", "pending")
        manager.set_item_property("testlist", "task1", "image_generated", "completed")
        manager.set_item_property("testlist", "task1", "priority", "high")

        manager.set_item_property("testlist", "task2", "priority", "medium")
        manager.set_item_property("testlist", "task2", "image_downloaded", "completed")

        manager.set_item_property("testlist", "task3", "priority", "low")
        manager.set_item_property("testlist", "task3", "process_status", "done")

        return {"list_key": "testlist"}

    def test_get_all_items_properties_no_filter(self, manager, setup_test_data):
        """Test getting all properties for all items without status filter."""
        result = manager.get_all_items_properties("testlist")

        # Filter only actual properties (exclude placeholder entries with "—")
        actual_properties = [p for p in result if p["property_key"] != "—"]

        # Should have 7 total properties (3+2+2)
        assert len(actual_properties) == 7

        # Check structure
        for prop in result:
            assert "item_key" in prop
            assert "property_key" in prop
            assert "property_value" in prop
            assert "status" in prop

        # Check specific properties
        item_keys = set(prop["item_key"] for prop in result)
        assert item_keys == {"task1", "task2", "task3"}

        # Check that status is included
        statuses = set(prop["status"] for prop in result)
        assert statuses == {"pending", "in_progress", "completed"}

    def test_get_all_items_properties_pending_filter(self, manager, setup_test_data):
        """Test getting properties only for pending items."""
        result = manager.get_all_items_properties("testlist", "pending")

        # Filter only actual properties and check count
        actual_properties = [p for p in result if p["property_key"] != "—"]
        assert len(actual_properties) == 3

        # All should be from task1 and have pending status
        for prop in result:
            assert prop["item_key"] == "task1"
            assert prop["status"] == "pending"

        # Check property keys
        property_keys = set(prop["property_key"] for prop in result)
        assert property_keys == {"image_downloaded", "image_generated", "priority"}

    def test_get_all_items_properties_in_progress_filter(
        self, manager, setup_test_data
    ):
        """Test getting properties only for in_progress items."""
        result = manager.get_all_items_properties("testlist", "in_progress")

        # Filter only actual properties and check count
        actual_properties = [p for p in result if p["property_key"] != "—"]
        assert len(actual_properties) == 2

        # All should be from task2 and have in_progress status
        for prop in result:
            assert prop["item_key"] == "task2"
            assert prop["status"] == "in_progress"

        # Check property keys (excluding placeholders)
        actual_properties = [p for p in result if p["property_key"] != "—"]
        property_keys = set(prop["property_key"] for prop in actual_properties)
        assert property_keys == {"priority", "image_downloaded"}

    def test_get_all_items_properties_completed_filter(self, manager, setup_test_data):
        """Test getting properties only for completed items."""
        result = manager.get_all_items_properties("testlist", "completed")

        # Filter only actual properties and check count
        actual_properties = [p for p in result if p["property_key"] != "—"]
        assert len(actual_properties) == 2

        # All should be from task3 and have completed status
        for prop in result:
            assert prop["item_key"] == "task3"
            assert prop["status"] == "completed"

        # Check property keys (excluding placeholders)
        actual_properties = [p for p in result if p["property_key"] != "—"]
        property_keys = set(prop["property_key"] for prop in actual_properties)
        assert property_keys == {"priority", "process_status"}

    def test_get_all_items_properties_failed_filter(self, manager, setup_test_data):
        """Test getting properties for failed items (none exist)."""
        result = manager.get_all_items_properties("testlist", "failed")

        # Should be empty since no failed items
        assert len(result) == 0

    def test_get_all_items_properties_invalid_status(self, manager, setup_test_data):
        """Test error handling for invalid status."""
        with pytest.raises(ValueError, match="Invalid status 'invalid'"):
            manager.get_all_items_properties("testlist", "invalid")

    def test_get_all_items_properties_list_not_found(self, manager):
        """Test error handling for non-existent list."""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.get_all_items_properties("nonexistent")

    def test_get_all_items_properties_empty_list(self, manager):
        """Test with list that has no items."""
        manager.create_list("empty", "Empty List")
        result = manager.get_all_items_properties("empty")

        assert len(result) == 0

    def test_get_all_items_properties_items_without_properties(self, manager):
        """Test with items that have no properties."""
        manager.create_list("noprops", "No Properties List")
        manager.add_item("noprops", "task1", "Item without properties")
        manager.add_item("noprops", "task2", "Another item without properties")

        result = manager.get_all_items_properties("noprops")
        # Should have placeholder entries for items without properties
        assert len(result) == 2
        # All entries should be placeholders
        for prop in result:
            assert prop["property_key"] == "—"
            assert prop["property_value"] == "—"

    def test_get_all_items_properties_sorting(self, manager, setup_test_data):
        """Test that results are sorted by item_key and then property_key."""
        result = manager.get_all_items_properties("testlist")

        # Extract sorting keys
        sort_keys = [(prop["item_key"], prop["property_key"]) for prop in result]

        # Should be sorted
        assert sort_keys == sorted(sort_keys)

        # First actual property should be task1 with image_downloaded (alphabetically first)
        actual_properties = [p for p in result if p["property_key"] != "—"]
        assert actual_properties[0]["item_key"] == "task1"
        assert actual_properties[0]["property_key"] == "image_downloaded"

    def test_get_all_items_properties_with_limit(self, manager, setup_test_data):
        """Test getting properties with item limit."""
        # Get all items first to understand the order
        all_items = manager.get_list_items("testlist")
        items_with_props = [
            item for item in all_items if item.item_key in ["task1", "task2", "task3"]
        ]

        # Test with limit that will include some items with properties
        result = manager.get_all_items_properties("testlist", limit=len(all_items))

        # Should include all properties from items that have them
        actual_properties = [p for p in result if p["property_key"] != "—"]
        expected_props = 7  # 3 + 2 + 2 from setup_test_data
        assert len(actual_properties) == expected_props

        # Test with smaller limit - get just first 2 items with properties
        first_two_items = sorted(items_with_props, key=lambda x: x.position)[:2]
        first_two_keys = [item.item_key for item in first_two_items]

        # Now test with a limit that should return these specific items
        # Since we know the positions, we can calculate the right limit
        position_limit = max(item.position for item in first_two_items)
        result_limited = manager.get_all_items_properties(
            "testlist", limit=position_limit
        )

        # Should have properties from first 2 items with properties
        item_keys = set(prop["item_key"] for prop in result_limited)
        assert len(item_keys) <= 2

        # All properties should be from the first two items with properties
        for prop in result_limited:
            assert prop["item_key"] in first_two_keys

    def test_get_all_items_properties_with_limit_and_status(
        self, manager, setup_test_data
    ):
        """Test getting properties with both limit and status filter."""
        # Get pending items to understand which ones have properties
        pending_items = [
            item
            for item in manager.get_list_items("testlist")
            if item.status == "pending" and item.item_key in ["task1", "task2", "task3"]
        ]

        if not pending_items:
            # Skip test if no pending items with properties
            return

        # Test with limit that includes at least one pending item with properties
        max_position = max(item.position for item in pending_items)
        result = manager.get_all_items_properties(
            "testlist", status="pending", limit=max_position
        )

        # Should have properties from pending items only
        assert len(result) > 0

        # All should have pending status
        for prop in result:
            assert prop["status"] == "pending"

    def test_get_all_items_properties_limit_zero(self, manager, setup_test_data):
        """Test with limit=0."""
        result = manager.get_all_items_properties("testlist", limit=0)

        # Should return empty list
        assert len(result) == 0

    def test_get_all_items_properties_limit_larger_than_items(
        self, manager, setup_test_data
    ):
        """Test with limit larger than number of items."""
        # Get total number of items in the list
        all_items = manager.get_list_items("testlist")
        large_limit = len(all_items) + 10

        result = manager.get_all_items_properties("testlist", limit=large_limit)

        # Should return all properties (same as no limit)
        result_no_limit = manager.get_all_items_properties("testlist")
        assert len(result) == len(result_no_limit)
        assert result == result_no_limit
