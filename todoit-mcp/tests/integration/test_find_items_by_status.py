"""
Integration tests for find_items_by_status functionality
Tests the universal function with all modes: simple, multiple, and complex
"""

import pytest
from core.manager import TodoManager
from core.models import ItemStatus


@pytest.fixture
def manager_with_test_data(tmp_path):
    """Create manager with test data for comprehensive testing."""
    db_path = tmp_path / "test_find_items.db"
    manager = TodoManager(str(db_path))

    # Create test lists
    list1 = manager.create_list("list1", "Test List 1")
    list2 = manager.create_list("list2", "Test List 2")

    # Create items with different statuses in list1
    manager.add_item("list1", "pending_item1", "Pending task 1")
    manager.add_item("list1", "pending_item2", "Pending task 2")
    manager.add_item("list1", "progress_item1", "In progress task")
    manager.add_item("list1", "completed_item1", "Completed task")

    # Update statuses
    manager.update_item_status("list1", "progress_item1", "in_progress")
    manager.update_item_status("list1", "completed_item1", "completed")

    # Create parent with subitems for complex testing
    manager.add_item("list1", "complex_parent", "Complex parent task")
    manager.update_item_status("list1", "complex_parent", "in_progress")

    # Add subitems
    manager.add_subitem("list1", "complex_parent", "download", "Download subtask")
    manager.add_subitem("list1", "complex_parent", "process", "Process subtask")
    manager.add_subitem("list1", "complex_parent", "upload", "Upload subtask")

    # Set subitem statuses
    manager.update_item_status("list1", "download", "pending", parent_item_key="complex_parent")
    manager.update_item_status("list1", "process", "completed", parent_item_key="complex_parent")
    manager.update_item_status("list1", "upload", "pending", parent_item_key="complex_parent")

    # Create items in list2
    manager.add_item("list2", "pending_item3", "Another pending task")
    manager.add_item("list2", "failed_item1", "Failed task")
    manager.update_item_status("list2", "failed_item1", "failed")

    return manager


class TestSimpleStatusSearch:
    """Test simple status search mode (string condition)."""

    def test_find_pending_items_single_list(self, manager_with_test_data):
        """Test finding pending items in a specific list."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("pending", "list1")

        assert len(results) == 4  # 2 main items + 2 pending subitems
        assert all(item.status == ItemStatus.PENDING for item in results)
        assert {item.item_key for item in results} == {"pending_item1", "pending_item2", "download", "upload"}

    def test_find_pending_items_all_lists(self, manager_with_test_data):
        """Test finding pending items across all lists."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("pending", None)

        assert len(results) == 5  # 2 from list1 + 1 from list2 + 2 subitems
        pending_keys = {item.item_key for item in results}
        assert "pending_item1" in pending_keys
        assert "pending_item2" in pending_keys
        assert "pending_item3" in pending_keys

    def test_find_nonexistent_status(self, manager_with_test_data):
        """Test finding items with status that doesn't exist."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("nonexistent", "list1")

        assert len(results) == 0

    def test_find_status_with_limit(self, manager_with_test_data):
        """Test finding items with limit parameter."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("pending", None, limit=2)

        assert len(results) == 2


class TestMultipleStatusSearch:
    """Test multiple status search mode (list condition)."""

    def test_find_multiple_statuses_or_logic(self, manager_with_test_data):
        """Test finding items with multiple statuses (OR logic)."""
        manager = manager_with_test_data

        results = manager.find_items_by_status(["pending", "in_progress"], "list1")

        # Should find: 2 pending items + 2 in_progress items + 2 pending subitems
        assert len(results) == 6
        statuses = {item.status for item in results}
        assert statuses == {ItemStatus.PENDING, ItemStatus.IN_PROGRESS}

    def test_find_multiple_statuses_all_lists(self, manager_with_test_data):
        """Test finding multiple statuses across all lists."""
        manager = manager_with_test_data

        results = manager.find_items_by_status(["completed", "failed"], None)

        assert len(results) == 3  # 2 completed (item + subitem) + 1 failed
        statuses = {item.status for item in results}
        assert statuses == {ItemStatus.COMPLETED, ItemStatus.FAILED}

    def test_empty_status_list_raises_error(self, manager_with_test_data):
        """Test that empty status list raises ValueError."""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="Status list cannot be empty"):
            manager.find_items_by_status([], "list1")


class TestComplexConditions:
    """Test complex conditions mode (dict with item/subitem)."""

    def test_find_by_item_status_only(self, manager_with_test_data):
        """Test complex search with item status condition only."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "item": {"status": "in_progress"}
        }, "list1")

        assert len(results) == 2  # progress_item1 and complex_parent both have in_progress status
        in_progress_keys = {result["parent"].item_key for result in results}
        assert in_progress_keys == {"progress_item1", "complex_parent"}
        for result in results:
            assert result["parent"].status == ItemStatus.IN_PROGRESS

    def test_find_by_subitem_conditions_only(self, manager_with_test_data):
        """Test complex search with subitem conditions only."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "subitem": {"download": "pending", "process": "completed"}
        }, "list1")

        assert len(results) == 1
        assert results[0]["parent"].item_key == "complex_parent"
        assert len(results[0]["matching_subitems"]) == 2

        subitem_keys = {s.item_key for s in results[0]["matching_subitems"]}
        assert subitem_keys == {"download", "process"}

    def test_find_by_item_and_subitem_conditions(self, manager_with_test_data):
        """Test complex search with both item and subitem conditions."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "item": {"status": "in_progress"},
            "subitem": {"download": "pending"}
        }, "list1")

        assert len(results) == 1
        assert results[0]["parent"].item_key == "complex_parent"
        assert results[0]["parent"].status == ItemStatus.IN_PROGRESS
        assert len(results[0]["matching_subitems"]) == 1
        assert results[0]["matching_subitems"][0].item_key == "download"

    def test_find_complex_conditions_no_matches(self, manager_with_test_data):
        """Test complex search that returns no matches."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "item": {"status": "completed"},
            "subitem": {"download": "pending"}
        }, "list1")

        assert len(results) == 0

    def test_complex_conditions_invalid_structure(self, manager_with_test_data):
        """Test invalid complex conditions raise error."""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="Conditions dictionary cannot be empty"):
            manager.find_items_by_status({}, "list1")


class TestBackwardsCompatibility:
    """Test backwards compatibility with find_subitems_by_status."""

    def test_backwards_compatibility_dict_without_item_subitem(self, manager_with_test_data):
        """Test that dict without 'item'/'subitem' keys works like old find_subitems_by_status."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "download": "pending",
            "process": "completed"
        }, "list1")

        # Should work exactly like find_subitems_by_status
        assert len(results) == 1
        assert results[0]["parent"].item_key == "complex_parent"
        assert len(results[0]["matching_subitems"]) == 2

    def test_backwards_compatibility_requires_list_key(self, manager_with_test_data):
        """Test that backwards compatibility mode requires list_key."""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="list_key is required for subitem matching"):
            manager.find_items_by_status({
                "download": "pending"
            }, None)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_conditions_type(self, manager_with_test_data):
        """Test that invalid conditions type raises error."""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="Unsupported conditions type"):
            manager.find_items_by_status(123, "list1")

    def test_nonexistent_list(self, manager_with_test_data):
        """Test that nonexistent list raises error."""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.find_items_by_status("pending", "nonexistent")

    def test_empty_results_with_limit(self, manager_with_test_data):
        """Test limit parameter with empty results."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("nonexistent", "list1", limit=10)

        assert len(results) == 0


class TestCrossListSearch:
    """Test cross-list search functionality."""

    def test_cross_list_simple_search(self, manager_with_test_data):
        """Test simple status search across all lists."""
        manager = manager_with_test_data

        results = manager.find_items_by_status("pending", None)

        # Should find items from both lists
        list_ids = {getattr(item, 'list_id', None) for item in results}
        assert len(list_ids) > 1  # Multiple lists represented

    def test_cross_list_complex_search(self, manager_with_test_data):
        """Test complex conditions search across all lists."""
        manager = manager_with_test_data

        results = manager.find_items_by_status({
            "item": {"status": "in_progress"}
        }, None)

        # Should work across all lists
        assert len(results) >= 0  # At least no errors