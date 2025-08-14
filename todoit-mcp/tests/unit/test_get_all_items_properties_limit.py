"""
Unit tests for get_all_items_properties limit parameter.

Tests the limit functionality in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from core.manager import TodoManager


class TestGetAllItemsPropertiesLimit:
    """Unit tests for get_all_items_properties limit parameter"""

    @pytest.fixture
    def mock_manager(self):
        """Create TodoManager with mocked database."""
        manager = TodoManager()
        manager.db = Mock()
        return manager

    def test_get_all_items_properties_no_limit(self, mock_manager):
        """Test that without limit, all items are processed."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock 3 items
        mock_items = [
            Mock(id=1, item_key="task1", status="pending"),
            Mock(id=2, item_key="task2", status="in_progress"),
            Mock(id=3, item_key="task3", status="completed"),
        ]
        mock_manager.db.get_list_items.return_value = mock_items

        # Mock properties for each item
        mock_manager.db.get_item_properties.side_effect = [
            {"prop1": "val1", "prop2": "val2"},  # task1
            {"prop3": "val3"},  # task2
            {"prop4": "val4", "prop5": "val5"},  # task3
        ]

        result = mock_manager.get_all_items_properties("testlist")

        # Should process all 3 items
        assert len(result) == 5  # 2 + 1 + 2 properties
        assert mock_manager.db.get_item_properties.call_count == 3

    def test_get_all_items_properties_with_limit(self, mock_manager):
        """Test that limit restricts number of items processed."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock 3 items
        mock_items = [
            Mock(id=1, item_key="task1", status="pending"),
            Mock(id=2, item_key="task2", status="in_progress"),
            Mock(id=3, item_key="task3", status="completed"),
        ]
        mock_manager.db.get_list_items.return_value = mock_items

        # Mock properties for each item
        mock_manager.db.get_item_properties.side_effect = [
            {"prop1": "val1", "prop2": "val2"},  # task1
            {"prop3": "val3"},  # task2 (task3 should not be processed)
        ]

        result = mock_manager.get_all_items_properties("testlist", limit=2)

        # Should process only first 2 items
        assert len(result) == 3  # 2 + 1 properties
        assert mock_manager.db.get_item_properties.call_count == 2

        # Verify correct items were processed
        item_keys = {prop["item_key"] for prop in result}
        assert item_keys == {"task1", "task2"}

    def test_get_all_items_properties_limit_zero(self, mock_manager):
        """Test that limit=0 returns empty list."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock items (should not be processed)
        mock_items = [Mock(id=1, item_key="task1", status="pending")]
        mock_manager.db.get_list_items.return_value = mock_items

        result = mock_manager.get_all_items_properties("testlist", limit=0)

        # Should return empty list and not process any items
        assert len(result) == 0
        assert mock_manager.db.get_item_properties.call_count == 0

    def test_get_all_items_properties_limit_with_status_filter(self, mock_manager):
        """Test limit works correctly with status filter."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock 2 pending items (after status filter)
        mock_items = [
            Mock(id=1, item_key="task1", status="pending"),
            Mock(id=3, item_key="task3", status="pending"),
        ]
        mock_manager.db.get_items_by_status.return_value = mock_items

        # Mock properties
        mock_manager.db.get_item_properties.side_effect = [
            {"prop1": "val1"}  # Only task1 should be processed due to limit=1
        ]

        result = mock_manager.get_all_items_properties(
            "testlist", status="pending", limit=1
        )

        # Should process only 1 item despite 2 matching status filter
        assert len(result) == 1
        assert mock_manager.db.get_item_properties.call_count == 1
        assert result[0]["item_key"] == "task1"
        assert result[0]["status"] == "pending"

    def test_get_all_items_properties_limit_larger_than_available(self, mock_manager):
        """Test limit larger than available items."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock only 1 item
        mock_items = [Mock(id=1, item_key="task1", status="pending")]
        mock_manager.db.get_list_items.return_value = mock_items

        # Mock properties
        mock_manager.db.get_item_properties.return_value = {"prop1": "val1"}

        result = mock_manager.get_all_items_properties("testlist", limit=10)

        # Should process the 1 available item
        assert len(result) == 1
        assert mock_manager.db.get_item_properties.call_count == 1
        assert result[0]["item_key"] == "task1"

    def test_get_all_items_properties_limit_none_means_no_limit(self, mock_manager):
        """Test that limit=None means no limit applied."""
        # Mock database responses
        mock_list = Mock()
        mock_list.id = 1
        mock_manager.db.get_list_by_key.return_value = mock_list

        # Mock 3 items
        mock_items = [
            Mock(id=1, item_key="task1", status="pending"),
            Mock(id=2, item_key="task2", status="pending"),
            Mock(id=3, item_key="task3", status="pending"),
        ]
        mock_manager.db.get_list_items.return_value = mock_items

        # Mock properties for each item
        mock_manager.db.get_item_properties.side_effect = [
            {"prop1": "val1"},
            {"prop2": "val2"},
            {"prop3": "val3"},
        ]

        result = mock_manager.get_all_items_properties("testlist", limit=None)

        # Should process all items (same as no limit parameter)
        assert len(result) == 3
        assert mock_manager.db.get_item_properties.call_count == 3
