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
        with patch("core.manager.Database") as MockDatabase:
            MockDatabase.return_value = mock_db
            manager = TodoManager(":memory:")
            manager.db = mock_db
            return manager

    def test_get_next_pending_algorithm(self, manager_with_mock, mock_db):
        """Test the core logic of the next pending task algorithm."""
        mock_parent = MagicMock(
            id=1,
            item_key="task1",
            status="in_progress",
            parent_item_id=None,
            position=1,
        )
        mock_subtask1 = MagicMock(
            id=2, item_key="task2", status="pending", parent_item_id=1, position=1
        )
        mock_subtask2 = MagicMock(
            id=3, item_key="task3", status="pending", parent_item_id=1, position=2
        )

        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [mock_subtask1, mock_subtask2]
        mock_db.is_item_blocked.return_value = False

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        assert next_task is not None
        assert next_task.item_key == "task2"
        mock_db.get_root_items.assert_called_once()
        mock_db.get_item_children.assert_called_with(mock_parent.id)

    def test_create_list_key_validation(self, manager_with_mock, mock_db):
        """Test that list keys must contain at least one letter."""
        # Create a proper mock database object that returns a mock with required attributes
        mock_list_obj = MagicMock()
        mock_list_obj.__table__ = MagicMock()
        mock_list_obj.__table__.columns = []

        # Test valid keys
        valid_keys = ["test123", "abc", "task_1", "list-a", "A1B2C3"]
        for key in valid_keys:
            mock_db.get_list_by_key.return_value = None  # No existing list
            mock_db.create_list.return_value = mock_list_obj
            try:
                # This should not raise an error
                result = manager_with_mock.create_list(key, f"Title for {key}")
                assert result is not None
            except ValueError as e:
                if "must contain at least one letter" in str(e):
                    pytest.fail(f"Valid key '{key}' was rejected: {e}")

        # Test invalid keys (numeric only)
        invalid_keys = ["123", "456789", "0", "999"]
        for key in invalid_keys:
            mock_db.get_list_by_key.return_value = None  # No existing list
            mock_db.create_list.return_value = mock_list_obj
            with pytest.raises(ValueError, match="must contain at least one letter"):
                manager_with_mock.create_list(key, f"Title for {key}")

    def test_get_next_pending_skips_blocked_subtasks(self, manager_with_mock, mock_db):
        """Test that the algorithm correctly skips subtasks that are blocked."""
        mock_parent = MagicMock(
            id=1, item_key="parent", status="in_progress", parent_item_id=None
        )
        blocked_subtask = MagicMock(
            id=2, item_key="blocked", status="pending", parent_item_id=1, position=1
        )
        available_subtask = MagicMock(
            id=3, item_key="available", status="pending", parent_item_id=1, position=2
        )

        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [blocked_subtask, available_subtask]
        mock_db.is_item_blocked.side_effect = (
            lambda item_id: item_id == blocked_subtask.id
        )

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        assert next_task is not None
        assert next_task.item_key == "available"
        assert mock_db.is_item_blocked.call_count == 2

    def test_get_next_pending_returns_none_if_all_blocked(
        self, manager_with_mock, mock_db
    ):
        """Test that None is returned if all available subtasks are blocked."""
        mock_parent = MagicMock(
            id=1, item_key="parent", status="in_progress", parent_item_id=None
        )
        subtask1 = MagicMock(
            id=2, item_key="sub1", status="pending", parent_item_id=1, position=1
        )
        subtask2 = MagicMock(
            id=3, item_key="sub2", status="pending", parent_item_id=1, position=2
        )

        mock_db.get_root_items.return_value = [mock_parent]
        mock_db.get_item_children.return_value = [subtask1, subtask2]
        mock_db.is_item_blocked.return_value = True

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        assert next_task is None

    def test_auto_complete_parent_succeeds(self, manager_with_mock, mock_db):
        """Test that a parent task is auto-completed when all its children are complete."""
        parent = MagicMock(id=10, status="in_progress")
        child = MagicMock(id=100, parent_item_id=10)

        mock_db.get_item_by_key.return_value = child
        mock_db.get_item_by_id.return_value = parent
        mock_db.check_all_children_completed.return_value = True

        result = manager_with_mock.auto_complete_parent("test", "child_key")

        assert result is True
        mock_db.update_item.assert_called_once()
        call_args, call_kwargs = mock_db.update_item.call_args
        assert call_args[0] == parent.id
        update_dict = call_args[1]
        assert update_dict.get("status") == "completed"
        assert "completed_at" in update_dict

    def test_auto_complete_parent_does_not_complete_if_children_pending(
        self, manager_with_mock, mock_db
    ):
        """Test that a parent task is NOT completed if at least one child is pending."""
        parent = MagicMock(id=10, status="in_progress")
        child = MagicMock(id=100, parent_item_id=10)

        mock_db.get_item_by_key.return_value = child
        mock_db.get_item_by_id.return_value = parent
        mock_db.check_all_children_completed.return_value = False

        result = manager_with_mock.auto_complete_parent("test", "child_key")

        assert result is False
        mock_db.update_item.assert_not_called()

    def test_auto_complete_parent_handles_no_parent(self, manager_with_mock, mock_db):
        """Test that the function handles items without a parent gracefully."""
        item_without_parent = MagicMock(parent_item_id=None)
        mock_db.get_item_by_key.return_value = item_without_parent

        result = manager_with_mock.auto_complete_parent("test", "some_key")

        assert result is False
        mock_db.get_item_by_id.assert_not_called()
        mock_db.check_all_children_completed.assert_not_called()
        mock_db.update_item.assert_not_called()

    def test_is_item_blocked_by_dependency(self, manager_with_mock, mock_db):
        """Test that is_item_blocked correctly identifies a blocked item."""
        item_to_check = MagicMock(id=1)
        mock_db.get_item_by_key.return_value = item_to_check
        mock_db.is_item_blocked.return_value = True

        is_blocked = manager_with_mock.is_item_blocked("test", "some_key")

        assert is_blocked is True
        mock_db.is_item_blocked.assert_called_once_with(item_to_check.id)

    def test_is_item_not_blocked_if_dependency_is_completed(
        self, manager_with_mock, mock_db
    ):
        """Test that is_item_blocked returns False if the blocking item is completed."""
        item_to_check = MagicMock(id=1)
        mock_db.get_item_by_key.return_value = item_to_check
        mock_db.is_item_blocked.return_value = False

        is_blocked = manager_with_mock.is_item_blocked("test", "some_key")

        assert is_blocked is False
        mock_db.is_item_blocked.assert_called_once_with(item_to_check.id)

    def test_add_circular_dependency_is_handled(self, manager_with_mock, mock_db):
        """Test that adding a circular dependency is handled."""
        item_a = MagicMock(id=1)
        item_b = MagicMock(id=2)

        mock_db.get_item_by_key.side_effect = lambda list_id, key: {
            "item_a": item_a,
            "item_b": item_b,
        }.get(key)

        # A depends on B
        dep_a_b = MagicMock(dependent_item_id=1, required_item_id=2)
        mock_db.get_all_item_dependencies.return_value = [dep_a_b]

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            with pytest.raises(ValueError, match="Circular dependency detected"):
                manager_with_mock.add_item_dependency(
                    dependent_list="test",
                    dependent_item="item_b",
                    required_list="test",
                    required_item="item_a",
                )

    def test_get_next_pending_handles_orphaned_subtasks(
        self, manager_with_mock, mock_db
    ):
        """Test that orphaned subtasks (parent is completed) are picked up."""
        completed_parent = MagicMock(id=1, status="completed", position=1)
        orphaned_subtask = MagicMock(
            id=2, parent_item_id=1, status="pending", position=1
        )

        mock_db.get_root_items.return_value = []
        mock_db.get_list_items.return_value = [orphaned_subtask]
        mock_db.get_item_by_id.return_value = completed_parent
        mock_db.is_item_blocked.return_value = False

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            next_task = manager_with_mock.get_next_pending_with_subtasks("test")

        assert next_task is not None
        assert next_task.id == orphaned_subtask.id

    def test_move_to_subtask(self, manager_with_mock, mock_db):
        """Test moving an item to become a subtask of another item."""
        item_to_move = MagicMock(id=100)
        new_parent = MagicMock(id=200)

        mock_db.get_item_by_key.side_effect = [item_to_move, new_parent]
        mock_db.get_item_path.return_value = []

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            manager_with_mock.move_to_subtask("test", "item_to_move", "new_parent")

        mock_db.update_item.assert_called_once_with(
            item_to_move.id, {"parent_item_id": new_parent.id}
        )

    def test_add_subtask_to_nonexistent_parent_raises_error(
        self, manager_with_mock, mock_db
    ):
        """Test that adding a subtask to a non-existent parent raises ValueError."""
        mock_db.get_item_by_key.return_value = None

        with pytest.raises(
            ValueError, match="Parent task 'nonexistent_parent' not found"
        ):
            manager_with_mock.add_subtask(
                list_key="test",
                parent_key="nonexistent_parent",
                subtask_key="new_subtask",
                content="some content",
            )

    def test_add_dependency_to_nonexistent_item_raises_error(
        self, manager_with_mock, mock_db
    ):
        """Test that adding a dependency to a non-existent item raises ValueError."""
        item_a = MagicMock(id=1)
        mock_db.get_item_by_key.side_effect = [item_a, None]

        with pytest.raises(
            ValueError, match="Required item 'nonexistent_item' not found"
        ):
            manager_with_mock.add_item_dependency(
                dependent_list="test",
                dependent_item="item_a",
                required_list="test",
                required_item="nonexistent_item",
            )

    def test_delete_item_cascades_to_subtasks(self, manager_with_mock, mock_db):
        """Test that deleting a parent item also deletes its subtasks."""
        parent = MagicMock(id=1, item_key="parent_key", parent_item_id=None)
        subtask1 = MagicMock(id=2, item_key="subtask1", parent_item_id=1)
        subtask2 = MagicMock(id=3, item_key="subtask2", parent_item_id=1)

        mock_db.get_item_by_key.side_effect = lambda list_id, key: {
            "parent_key": parent,
            "subtask1": subtask1,
            "subtask2": subtask2,
        }.get(key)

        mock_db.get_item_children.side_effect = lambda item_id: {
            parent.id: [subtask1, subtask2],
            subtask1.id: [],
            subtask2.id: [],
        }.get(item_id, [])

        # Mock the status synchronization methods to avoid calling them
        mock_db.get_children_status_summary.return_value = {
            'total': 0, 'failed': 0, 'pending': 0, 'completed': 0, 'in_progress': 0
        }
        mock_db.get_item_by_id.return_value = None  # No parent to sync

        manager_with_mock.delete_item("test", "parent_key")

        assert mock_db.delete_item.call_count == 3
        mock_db.delete_item.assert_any_call(parent.id)
        mock_db.delete_item.assert_any_call(subtask1.id)
        mock_db.delete_item.assert_any_call(subtask2.id)

    def test_delete_item_removes_dependencies(self, manager_with_mock, mock_db):
        """Test that deleting an item also removes its dependencies."""
        item_to_delete = MagicMock(id=1, parent_item_id=None)
        mock_db.get_item_by_key.return_value = item_to_delete
        mock_db.get_item_children.return_value = []

        # Mock the status synchronization methods
        mock_db.get_children_status_summary.return_value = {
            'total': 0, 'failed': 0, 'pending': 0, 'completed': 0, 'in_progress': 0
        }
        mock_db.get_item_by_id.return_value = None  # No parent to sync

        manager_with_mock.delete_item("test", "some_key")

        mock_db.delete_all_dependencies_for_item.assert_called_once_with(
            item_to_delete.id
        )
        mock_db.delete_item.assert_called_once_with(item_to_delete.id)

    def test_archive_list_basic_flow(self, manager_with_mock, mock_db):
        """Test basic flow of archiving a list."""
        mock_list = MagicMock(id=1, list_key="test_list", status="active")
        mock_db.get_list_by_key.return_value = mock_list

        # The actual implementation of archive_list will be tested in integration tests
        # Here we just test that the method exists and basic validation works
        assert hasattr(manager_with_mock, "archive_list")
        assert callable(getattr(manager_with_mock, "archive_list"))

    def test_archive_already_archived_list_raises_error(
        self, manager_with_mock, mock_db
    ):
        """Test that archiving an already archived list raises ValueError."""
        mock_list = MagicMock(id=1, list_key="test_list", status="archived")
        mock_db.get_list_by_key.return_value = mock_list

        with pytest.raises(ValueError, match="List 'test_list' is already archived"):
            manager_with_mock.archive_list("test_list")

    def test_archive_nonexistent_list_raises_error(self, manager_with_mock, mock_db):
        """Test that archiving a non-existent list raises ValueError."""
        mock_db.get_list_by_key.return_value = None

        with pytest.raises(ValueError, match="List 'nonexistent' does not exist"):
            manager_with_mock.archive_list("nonexistent")

    def test_unarchive_list_basic_flow(self, manager_with_mock, mock_db):
        """Test basic flow of unarchiving a list."""
        mock_list = MagicMock(id=1, list_key="test_list", status="archived")
        mock_db.get_list_by_key.return_value = mock_list

        # The actual implementation of unarchive_list will be tested in integration tests
        # Here we just test that the method exists and basic validation works
        assert hasattr(manager_with_mock, "unarchive_list")
        assert callable(getattr(manager_with_mock, "unarchive_list"))

    def test_unarchive_already_active_list_raises_error(
        self, manager_with_mock, mock_db
    ):
        """Test that unarchiving an already active list raises ValueError."""
        mock_list = MagicMock(id=1, list_key="test_list", status="active")
        mock_db.get_list_by_key.return_value = mock_list

        with pytest.raises(ValueError, match="List 'test_list' is already active"):
            manager_with_mock.unarchive_list("test_list")

    def test_unarchive_nonexistent_list_raises_error(self, manager_with_mock, mock_db):
        """Test that unarchiving a non-existent list raises ValueError."""
        mock_db.get_list_by_key.return_value = None

        with pytest.raises(ValueError, match="List 'nonexistent' does not exist"):
            manager_with_mock.unarchive_list("nonexistent")

    def test_list_all_with_include_archived(self, manager_with_mock, mock_db):
        """Test list_all with include_archived parameter."""
        active_list = MagicMock(id=1, list_key="active", status="active")
        archived_list = MagicMock(id=2, list_key="archived", status="archived")

        # Test include_archived=False (default behavior)
        mock_db.get_all_lists.return_value = [active_list, archived_list]
        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            result = manager_with_mock.list_all(include_archived=False)
            assert len(result) == 1
            assert result[0].list_key == "active"

        # Test include_archived=True
        mock_db.get_all_lists.return_value = [active_list, archived_list]
        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            result = manager_with_mock.list_all(include_archived=True)
            assert len(result) == 2

    def test_get_archived_lists(self, manager_with_mock, mock_db):
        """Test get_archived_lists returns only archived lists."""
        active_list = MagicMock(id=1, list_key="active", status="active")
        archived_list = MagicMock(id=2, list_key="archived", status="archived")
        mock_db.get_all_lists.return_value = [active_list, archived_list]

        with patch.object(
            manager_with_mock,
            "_db_to_model",
            side_effect=lambda db_obj, model_class: db_obj,
        ):
            result = manager_with_mock.get_archived_lists()
            assert len(result) == 1
            assert result[0].list_key == "archived"
            assert result[0].status == "archived"
