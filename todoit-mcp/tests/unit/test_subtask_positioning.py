"""
Unit tests for subitem positioning logic
Tests the fix for position conflicts in add_subitem method
"""

import pytest
from unittest.mock import Mock, patch
from core.manager import TodoManager
from core.models import TodoItem


class TestSubtaskPositioning:
    """Test subitem positioning functionality"""

    @pytest.fixture
    def mock_manager(self):
        """Create a TodoManager with mocked database"""
        manager = TodoManager()
        manager.db = Mock()
        return manager

    @pytest.fixture
    def mock_list(self):
        """Mock list object"""
        mock_list = Mock()
        mock_list.id = 1
        mock_list.list_key = "test_list"
        return mock_list

    @pytest.fixture
    def mock_parent_item(self):
        """Mock parent item object"""
        mock_parent = Mock()
        mock_parent.id = 1
        mock_parent.position = 1
        return mock_parent

    @pytest.fixture
    def mock_db_item(self):
        """Mock database item with required attributes for _db_to_model"""
        from datetime import datetime
        
        mock_item = Mock()
        # Mock the __table__ attribute needed by _db_to_model
        mock_table = Mock()
        
        # Create all required columns
        columns = []
        column_names = ["id", "item_key", "content", "position", "status", "parent_item_id", "list_id", "created_at", "updated_at"]
        for name in column_names:
            col = Mock()
            col.name = name
            columns.append(col)
        
        mock_table.columns = columns
        mock_item.__table__ = mock_table
        
        # Set attribute values for all required fields
        mock_item.id = 1
        mock_item.item_key = "sub_key"
        mock_item.content = "Sub content"
        mock_item.position = 5
        mock_item.status = "pending"
        mock_item.parent_item_id = 1
        mock_item.list_id = 1
        mock_item.created_at = datetime.now()
        mock_item.updated_at = datetime.now()
        
        return mock_item

    def test_add_subitem_uses_next_position(self, mock_manager, mock_list, mock_parent_item, mock_db_item):
        """Test that add_subitem always uses get_next_position() to avoid conflicts"""
        
        # Setup mocks
        mock_manager.db.get_list_by_key.return_value = mock_list
        mock_manager.db.get_item_by_key.return_value = mock_parent_item  # parent exists
        mock_manager.db.get_item_by_key_and_parent.return_value = None  # subitem doesn't exist for this parent
        mock_manager.db.get_next_position.return_value = 5  # Next available position
        mock_manager.db.create_item.return_value = mock_db_item
        mock_manager.db.get_session.return_value.__enter__ = Mock(return_value=Mock())
        mock_manager.db.get_session.return_value.__exit__ = Mock(return_value=None)
        mock_manager.db.get_children_status_summary.return_value = None  # No children yet

        # Call add_subitem
        result = mock_manager.add_subitem("test_list", "parent_key", "sub_key", "Sub content")

        # Verify get_next_position was called with parent_item_id (new hierarchical logic)
        mock_manager.db.get_next_position.assert_called_once_with(1, parent_item_id=1)
        
        # Verify create_item was called with the next position
        args, kwargs = mock_manager.db.create_item.call_args
        item_data = args[0]
        assert item_data["position"] == 5
        assert item_data["parent_item_id"] == 1
        assert item_data["item_key"] == "sub_key"
        
        # Verify result is a TodoItem
        assert isinstance(result, TodoItem)

    def test_add_subitem_no_position_shifting(self, mock_manager, mock_list, mock_parent_item, mock_db_item):
        """Test that add_subitem no longer shifts positions (old buggy behavior)"""
        
        # Setup mocks
        mock_manager.db.get_list_by_key.return_value = mock_list
        mock_manager.db.get_item_by_key.return_value = mock_parent_item
        mock_manager.db.get_item_by_key_and_parent.return_value = None
        mock_manager.db.get_next_position.return_value = 4
        mock_manager.db.create_item.return_value = mock_db_item
        mock_manager.db.get_session.return_value.__enter__ = Mock(return_value=Mock())
        mock_manager.db.get_session.return_value.__exit__ = Mock(return_value=None)
        mock_manager.db.get_children_status_summary.return_value = None  # No children yet

        # Call add_subitem
        mock_manager.add_subitem("test_list", "parent_key", "sub_key", "Sub content")

        # Verify shift_positions was NOT called (old behavior would call this)
        mock_manager.db.shift_positions.assert_not_called()

    def test_add_subitem_ignores_existing_subtasks_positions(self, mock_manager, mock_list, mock_parent_item, mock_db_item):
        """Test that add_subitem ignores existing subtasks' positions (old logic would check these)"""
        
        # Setup mocks - including existing subtasks with various positions
        existing_subtasks = [
            Mock(position=3),
            Mock(position=7),
            Mock(position=9)
        ]
        
        mock_manager.db.get_list_by_key.return_value = mock_list
        mock_manager.db.get_item_by_key.return_value = mock_parent_item
        mock_manager.db.get_item_by_key_and_parent.return_value = None
        mock_manager.db.get_item_children.return_value = existing_subtasks  # This should be ignored now
        mock_manager.db.get_next_position.return_value = 10  # Next available position
        mock_manager.db.create_item.return_value = mock_db_item
        mock_manager.db.get_session.return_value.__enter__ = Mock(return_value=Mock())
        mock_manager.db.get_session.return_value.__exit__ = Mock(return_value=None)
        mock_manager.db.get_children_status_summary.return_value = None  # No children yet

        # Call add_subitem
        mock_manager.add_subitem("test_list", "parent_key", "sub_key", "Sub content")

        # Verify get_item_children was NOT called (old logic would call this)
        mock_manager.db.get_item_children.assert_not_called()
        
        # Verify position is from get_next_position, not max(existing) + 1
        args, kwargs = mock_manager.db.create_item.call_args
        item_data = args[0]
        assert item_data["position"] == 10  # Not 9 + 1 = 10 from existing subtasks

    def test_add_subitem_sequential_calls_increment_position(self, mock_manager, mock_list, mock_parent_item, mock_db_item):
        """Test that sequential add_subitem calls get incrementing positions"""
        
        # Setup mocks
        mock_manager.db.get_list_by_key.return_value = mock_list
        mock_manager.db.get_item_by_key.return_value = mock_parent_item
        mock_manager.db.get_item_by_key_and_parent.return_value = None
        mock_manager.db.get_next_position.side_effect = [4, 5]  # Incrementing positions
        mock_manager.db.create_item.return_value = mock_db_item
        mock_manager.db.get_session.return_value.__enter__ = Mock(return_value=Mock())
        mock_manager.db.get_session.return_value.__exit__ = Mock(return_value=None)
        mock_manager.db.get_children_status_summary.return_value = None  # No children yet

        # Call add_subitem twice
        mock_manager.add_subitem("test_list", "parent_key", "sub1", "Sub 1")
        mock_manager.add_subitem("test_list", "parent_key", "sub2", "Sub 2")

        # Verify both calls used get_next_position
        assert mock_manager.db.get_next_position.call_count == 2
        
        # Verify positions increment
        first_call = mock_manager.db.create_item.call_args_list[0]
        second_call = mock_manager.db.create_item.call_args_list[1]
        
        first_position = first_call[0][0]["position"]
        second_position = second_call[0][0]["position"]
        
        assert first_position == 4
        assert second_position == 5

    def test_add_subitem_validates_inputs_before_positioning(self, mock_manager):
        """Test that input validation occurs before position calculation"""
        
        # Setup mocks for validation failures
        mock_manager.db.get_list_by_key.return_value = None  # List doesn't exist
        
        # Should raise ValueError before any position logic
        with pytest.raises(ValueError, match="List 'bad_list' does not exist"):
            mock_manager.add_subitem("bad_list", "parent_key", "sub_key", "Sub content")
        
        # Verify get_next_position was not called due to early validation failure
        mock_manager.db.get_next_position.assert_not_called()

    def test_add_subitem_metadata_preserved(self, mock_manager, mock_list, mock_parent_item, mock_db_item):
        """Test that metadata is correctly preserved with new positioning logic"""
        
        # Setup mocks
        mock_manager.db.get_list_by_key.return_value = mock_list
        mock_manager.db.get_item_by_key.return_value = mock_parent_item
        mock_manager.db.get_item_by_key_and_parent.return_value = None
        mock_manager.db.get_next_position.return_value = 3
        mock_manager.db.create_item.return_value = mock_db_item
        mock_manager.db.get_session.return_value.__enter__ = Mock(return_value=Mock())
        mock_manager.db.get_session.return_value.__exit__ = Mock(return_value=None)
        mock_manager.db.get_children_status_summary.return_value = None  # No children yet

        # Call add_subitem with metadata
        test_metadata = {"priority": "high", "tags": ["urgent"]}
        mock_manager.add_subitem("test_list", "parent_key", "sub_key", "Sub content", test_metadata)

        # Verify metadata is preserved in item_data
        args, kwargs = mock_manager.db.create_item.call_args
        item_data = args[0]
        assert item_data["meta_data"] == test_metadata