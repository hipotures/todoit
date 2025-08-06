"""
Unit tests for the TodoManager class with a mocked database.

This file focuses on testing the business logic of the TodoManager in isolation
from the database, ensuring that algorithms for task selection, status updates,
and hierarchy management work as expected.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from core.manager import TodoManager
from core.models import TodoList, TodoItem, ItemStatus

class TestTodoManagerUnit:
    """Unit tests for TodoManager with mocked database"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database object for testing."""
        mock = MagicMock()
        mock.get_list_by_key.return_value = MagicMock(id=1, list_key="test")
        return mock
    
    @pytest.fixture
    def manager_with_mock(self, mock_db):
        """Create a TodoManager instance with a mocked database."""
        # By patching 'core.manager.Database', we prevent the real database
        # from being instantiated.
        with patch('core.manager.Database') as MockDatabase:
            MockDatabase.return_value = mock_db
            # The DSN can be anything as it won't be used.
            manager = TodoManager(":memory:")
            manager.db = mock_db
            return manager
    
    def test_get_next_pending_algorithm(self, manager_with_mock, mock_db):
        """
        Test the core logic of the next pending task algorithm.
        
        Scenario:
        - A parent task is 'in_progress'.
        - It has several 'pending' subtasks.
        - The algorithm should prioritize the first subtask of the 'in_progress' parent.
        """
        # Arrange: Setup mock data returned by the mocked database
        mock_parent = MagicMock(
            id=1, item_key="task1", status="in_progress", 
            parent_item_id=None, position=1
        )
        mock_subtask1 = MagicMock(
            id=2, item_key="task2", status="pending", 
            parent_item_id=1, position=1
        )
        mock_subtask2 = MagicMock(
            id=3, item_key="task3", status="pending", 
            parent_item_id=1, position=2
        )
        
        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [mock_subtask1, mock_subtask2]
        mock_db.is_item_blocked.return_value = False

        # Also, mock the internal model conversion to avoid the __table__ error.
        # The side_effect lambda function simply returns the first argument it receives.
        with patch.object(manager_with_mock, '_db_to_model', side_effect=lambda db_obj, model_class: db_obj):
            # Act: Call the method being tested
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")
        
        # Assert: Verify the outcome
        assert next_task is not None
        assert next_task.item_key == "task2"
        
        # Verify that the correct database methods were called
        mock_db.get_root_items.assert_called_once()
        mock_db.get_item_children.assert_called_with(mock_parent.id)

    def test_get_next_pending_skips_blocked_subtasks(self, manager_with_mock, mock_db):
        """
        Test that the algorithm correctly skips subtasks that are blocked.

        Scenario:
        - A parent task is 'in_progress'.
        - It has two pending subtasks.
        - The first subtask is blocked by a dependency.
        - The algorithm should skip the first and return the second subtask.
        """
        # Arrange
        mock_parent = MagicMock(id=1, item_key="parent", status="in_progress", parent_item_id=None)
        blocked_subtask = MagicMock(id=2, item_key="blocked", status="pending", parent_item_id=1, position=1)
        available_subtask = MagicMock(id=3, item_key="available", status="pending", parent_item_id=1, position=2)

        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [blocked_subtask, available_subtask]

        # Mock the is_item_blocked to return True for the first subtask
        mock_db.is_item_blocked.side_effect = lambda item_id: item_id == blocked_subtask.id

        with patch.object(manager_with_mock, '_db_to_model', side_effect=lambda db_obj, model_class: db_obj):
            # Act
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        # Assert
        assert next_task is not None
        assert next_task.item_key == "available"

        # Verify that is_item_blocked was called for both subtasks
        assert mock_db.is_item_blocked.call_count == 2

    def test_get_next_pending_returns_none_if_all_blocked(self, manager_with_mock, mock_db):
        """
        Test that None is returned if all available subtasks are blocked.

        Scenario:
        - A parent task is 'in_progress'.
        - All of its subtasks are blocked by dependencies.
        - The algorithm should return None, as there is no actionable task.
        """
        # Arrange
        mock_parent = MagicMock(id=1, item_key="parent", status="in_progress", parent_item_id=None)
        subtask1 = MagicMock(id=2, item_key="sub1", status="pending", parent_item_id=1, position=1)
        subtask2 = MagicMock(id=3, item_key="sub2", status="pending", parent_item_id=1, position=2)

        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [subtask1, subtask2]

        # Mock all items to be blocked
        mock_db.is_item_blocked.return_value = True

        with patch.object(manager_with_mock, '_db_to_model', side_effect=lambda db_obj, model_class: db_obj):
            # Act
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        # Assert
        assert next_task is None

    def test_auto_complete_parent_succeeds(self, manager_with_mock, mock_db):
        """
        Test that a parent task is auto-completed when all its children are complete.
        """
        # Arrange
        parent = MagicMock(id=10, status="in_progress")
        child = MagicMock(id=100, parent_item_id=10)

        mock_db.get_item_by_key.return_value = child
        mock_db.get_item_by_id.return_value = parent
        # All children are completed
        mock_db.check_all_children_completed.return_value = True

        # Act
        result = manager_with_mock.auto_complete_parent("test", "child_key")

        # Assert
        assert result is True
        # Verify that update_item was called exactly once.
        mock_db.update_item.assert_called_once()

        # More robust check: verify the content of the call without being brittle.
        # We get the arguments the mock was called with.
        call_args, call_kwargs = mock_db.update_item.call_args

        # Check the parent ID was correct.
        assert call_args[0] == parent.id

        # Check that the update dictionary contains the correct status.
        update_dict = call_args[1]
        assert update_dict.get('status') == 'completed'

        # Check that the 'completed_at' timestamp was also set.
        assert 'completed_at' in update_dict

    def test_auto_complete_parent_does_not_complete_if_children_pending(self, manager_with_mock, mock_db):
        """
        Test that a parent task is NOT completed if at least one child is pending.
        """
        # Arrange
        parent = MagicMock(id=10, status="in_progress")
        child = MagicMock(id=100, parent_item_id=10)

        mock_db.get_item_by_key.return_value = child
        mock_db.get_item_by_id.return_value = parent
        # Not all children are completed
        mock_db.check_all_children_completed.return_value = False

        # Act
        result = manager_with_mock.auto_complete_parent("test", "child_key")

        # Assert
        assert result is False
        # Verify that update_item was not called
        mock_db.update_item.assert_not_called()

    def test_auto_complete_parent_handles_no_parent(self, manager_with_mock, mock_db):
        """
        Test that the function handles items without a parent gracefully.
        """
        # Arrange
        # This item has no parent_item_id
        item_without_parent = MagicMock(parent_item_id=None)
        mock_db.get_item_by_key.return_value = item_without_parent

        # Act
        result = manager_with_mock.auto_complete_parent("test", "some_key")

        # Assert
        assert result is False
        # Verify that no other database methods were called
        mock_db.get_item_by_id.assert_not_called()
        mock_db.check_all_children_completed.assert_not_called()
        mock_db.update_item.assert_not_called()
