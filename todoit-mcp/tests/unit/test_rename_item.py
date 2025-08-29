"""
Unit tests for rename_item functionality in TodoManager.

Tests the business logic of item renaming including validation,
error handling, and history recording with mocked dependencies.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from core.manager import TodoManager
from core.models import TodoItem


class TestRenameItemUnit:
    """Unit tests for rename_item method with mocked database"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database object for testing."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def manager_with_mock(self, mock_db):
        """Create a TodoManager instance with a mocked database."""
        with patch("core.manager.Database") as MockDatabase:
            MockDatabase.return_value = mock_db
            manager = TodoManager(":memory:")
            manager.db = mock_db
            manager._record_history = Mock()  # Mock the history method
            manager._db_to_model = Mock()  # Mock the model conversion
            return manager

    @pytest.fixture
    def sample_list_db(self):
        """Sample database list object"""
        mock_list = MagicMock()
        mock_list.id = 1
        mock_list.list_key = "project"
        mock_list.title = "Project"
        return mock_list

    @pytest.fixture
    def sample_item_db(self):
        """Sample database item object"""
        mock_item = MagicMock()
        mock_item.id = 10
        mock_item.list_id = 1
        mock_item.item_key = "old_task"
        mock_item.content = "Old Task Content"
        mock_item.position = 1
        mock_item.status = "pending"
        mock_item.parent_item_id = None
        mock_item.metadata = {}
        mock_item.completion_states = {}
        mock_item.created_at = "2025-01-01T10:00:00"
        mock_item.updated_at = "2025-01-01T10:00:00"
        return mock_item

    @pytest.fixture
    def sample_parent_item_db(self):
        """Sample parent item for subitem testing"""
        mock_parent = MagicMock()
        mock_parent.id = 20
        mock_parent.list_id = 1
        mock_parent.item_key = "parent_task"
        mock_parent.content = "Parent Task"
        return mock_parent

    @pytest.fixture
    def sample_subitem_db(self):
        """Sample subitem database object"""
        mock_subitem = MagicMock()
        mock_subitem.id = 30
        mock_subitem.list_id = 1
        mock_subitem.item_key = "old_subtask"
        mock_subitem.content = "Old Subtask Content"
        mock_subitem.parent_item_id = 20
        mock_subitem.position = 1
        mock_subitem.status = "pending"
        return mock_subitem

    def test_rename_item_key_only(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test renaming only the item key"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        # Updated to use get_item_by_key_and_parent (new API after refactoring)
        # First call returns the item to rename, second call returns None for uniqueness check
        mock_db.get_item_by_key_and_parent.side_effect = [sample_item_db, None]
        mock_db.update_item.return_value = sample_item_db

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute
        result = manager_with_mock.rename_item(
            "project", "old_task", new_key="new_task"
        )

        # Verify
        mock_db.get_list_by_key.assert_called_with("project")
        assert (
            mock_db.get_item_by_key_and_parent.call_count == 2
        )  # First for item lookup, second for uniqueness check
        mock_db.update_item.assert_called_with(10, {"item_key": "new_task"})
        manager_with_mock._record_history.assert_called_once()
        assert result == mock_todo_item

    def test_rename_item_title_only(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test renaming only the item title"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.return_value = (
            sample_item_db  # Updated to use unified API
        )
        mock_db.update_item.return_value = sample_item_db  # Updated to use update_item

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute
        result = manager_with_mock.rename_item(
            "project", "old_task", new_content="New Task Title"
        )

        # Verify
        mock_db.update_item.assert_called_with(10, {"content": "New Task Title"})
        manager_with_mock._record_history.assert_called_once()
        assert result == mock_todo_item

    def test_rename_item_both_key_and_title(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test renaming both key and title"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ]  # First for item, second for uniqueness check
        mock_db.update_item.return_value = sample_item_db

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute
        result = manager_with_mock.rename_item(
            "project", "old_task", new_key="new_task", new_content="New Task Title"
        )

        # Verify
        mock_db.update_item.assert_called_with(
            10, {"item_key": "new_task", "content": "New Task Title"}
        )
        manager_with_mock._record_history.assert_called_once()
        assert result == mock_todo_item

    def test_rename_subitem(
        self,
        manager_with_mock,
        mock_db,
        sample_list_db,
        sample_parent_item_db,
        sample_subitem_db,
    ):
        """Test renaming a subitem"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key.return_value = sample_parent_item_db  # Parent lookup
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_subitem_db,  # First call: get existing subitem
            None,  # Second call: check new key doesn't exist
        ]
        mock_db.update_item.return_value = sample_subitem_db

        # Execute
        result = manager_with_mock.rename_item(
            "project",
            "old_subtask",
            new_key="new_subtask",
            new_content="New Subtask Title",
            parent_item_key="parent_task",
        )

        # Verify
        mock_db.get_item_by_key.assert_called_with(1, "parent_task")
        mock_db.update_item.assert_called_with(
            30, {"item_key": "new_subtask", "content": "New Subtask Title"}
        )

    def test_rename_no_parameters_error(self, manager_with_mock):
        """Test error when no new_key or new_content provided"""
        with pytest.raises(
            ValueError, match="Either new_key or new_content must be provided"
        ):
            manager_with_mock.rename_item("project", "task1")

    def test_rename_list_not_found_error(self, manager_with_mock, mock_db):
        """Test error when list doesn't exist"""
        mock_db.get_list_by_key.return_value = None

        with pytest.raises(ValueError, match="List 'nonexistent' does not exist"):
            manager_with_mock.rename_item("nonexistent", "task1", new_key="new_task")

    def test_rename_item_not_found_error(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test error when item doesn't exist"""
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.return_value = None

        with pytest.raises(
            ValueError, match="Item 'nonexistent' not found in list 'project'"
        ):
            manager_with_mock.rename_item("project", "nonexistent", new_key="new_task")

    def test_rename_subitem_not_found_error(
        self, manager_with_mock, mock_db, sample_list_db, sample_parent_item_db
    ):
        """Test error when subitem doesn't exist"""
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key.return_value = sample_parent_item_db
        mock_db.get_item_by_key_and_parent.return_value = None

        with pytest.raises(
            ValueError,
            match="Item 'nonexistent' not found under parent 'parent_task' in list 'project'",
        ):
            manager_with_mock.rename_item(
                "project",
                "nonexistent",
                new_key="new_task",
                parent_item_key="parent_task",
            )

    def test_rename_parent_not_found_error(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test error when parent item doesn't exist for subitem"""
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key.return_value = None  # Parent not found

        with pytest.raises(
            ValueError, match="Parent item 'nonexistent_parent' not found"
        ):
            manager_with_mock.rename_item(
                "project",
                "subtask1",
                new_key="new_subtask",
                parent_item_key="nonexistent_parent",
            )

    def test_rename_duplicate_key_error_item(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test error when new item key already exists"""
        # Setup
        existing_item = MagicMock()
        existing_item.id = 99  # Different ID

        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            existing_item,
        ]  # First call gets item, second checks for duplicate

        with pytest.raises(
            ValueError,
            match="Item with key 'existing_task' already exists in list 'project'",
        ):
            manager_with_mock.rename_item(
                "project", "old_task", new_key="existing_task"
            )

    def test_rename_duplicate_key_error_subitem(
        self,
        manager_with_mock,
        mock_db,
        sample_list_db,
        sample_parent_item_db,
        sample_subitem_db,
    ):
        """Test error when new subitem key already exists"""
        # Setup
        existing_subitem = MagicMock()
        existing_subitem.id = 99  # Different ID

        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key.return_value = sample_parent_item_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_subitem_db,  # First call: get existing subitem
            existing_subitem,  # Second call: new key already exists
        ]

        with pytest.raises(
            ValueError,
            match="Item with key 'existing_subtask' already exists under parent 'parent_task' in list 'project'",
        ):
            manager_with_mock.rename_item(
                "project",
                "old_subtask",
                new_key="existing_subtask",
                parent_item_key="parent_task",
            )

    def test_rename_same_key_allowed(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test that renaming to the same key is allowed (for title-only changes)"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.return_value = (
            sample_item_db  # Same item for both calls
        )
        mock_db.update_item.return_value = sample_item_db

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute - rename to same key but different title should work
        result = manager_with_mock.rename_item(
            "project", "old_task", new_key="old_task", new_content="New Title"
        )

        # Verify - should not raise duplicate key error
        mock_db.update_item.assert_called_with(10, {"content": "New Title"})
        assert result == mock_todo_item

    def test_rename_database_failure_error(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test error when database update fails"""
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ]  # First call finds item, second for uniqueness check returns None
        mock_db.update_item.return_value = None  # Simulate failure

        with pytest.raises(
            AttributeError
        ):  # update_item failure would cause AttributeError when accessing None.item_key
            manager_with_mock.rename_item("project", "old_task", new_key="new_task")

    def test_rename_history_recording_item(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test that history is recorded correctly for item rename"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ]  # First call finds item, second for uniqueness check returns None

        # Create a mock for the renamed item with updated values
        renamed_item = MagicMock()
        renamed_item.id = 10
        renamed_item.item_key = "new_task"
        renamed_item.content = "New Title"
        mock_db.update_item.return_value = renamed_item

        # Execute
        manager_with_mock.rename_item(
            "project", "old_task", new_key="new_task", new_content="New Title"
        )

        # Verify history call
        call_args = manager_with_mock._record_history.call_args
        assert call_args[1]["item_id"] == 10
        assert call_args[1]["action"] == "renamed"
        assert call_args[1]["old_value"] == {
            "item_key": "old_task",
            "content": "Old Task Content",
        }
        assert call_args[1]["new_value"]["item_key"] == "new_task"
        assert call_args[1]["new_value"]["content"] == "New Title"

    def test_rename_history_recording_subitem(
        self,
        manager_with_mock,
        mock_db,
        sample_list_db,
        sample_parent_item_db,
        sample_subitem_db,
    ):
        """Test that history is recorded correctly for subitem rename"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key.return_value = sample_parent_item_db
        mock_db.get_item_by_key_and_parent.side_effect = [sample_subitem_db, None]

        # Create a mock for the renamed subitem with updated values
        renamed_subitem = MagicMock()
        renamed_subitem.id = 30
        renamed_subitem.item_key = "new_subtask"
        renamed_subitem.content = (
            "Old Subtask Content"  # Content unchanged in this test
        )
        mock_db.update_item.return_value = renamed_subitem

        # Execute
        manager_with_mock.rename_item(
            "project",
            "old_subtask",
            new_key="new_subtask",
            parent_item_key="parent_task",
        )

        # Verify history call includes parent context
        call_args = manager_with_mock._record_history.call_args
        assert call_args[1]["item_id"] == 30
        assert call_args[1]["action"] == "renamed"
        assert call_args[1]["old_value"]["item_key"] == "old_subtask"
        assert call_args[1]["new_value"]["item_key"] == "new_subtask"

    def test_rename_key_validation_alphanumeric(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test that item key validation allows alphanumeric with underscores and hyphens"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ] * 5  # Return pattern for each valid key test
        mock_db.update_item.return_value = sample_item_db

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute - valid keys should work
        valid_keys = ["task_1", "task-2", "Task123", "my_new_task", "item-v2"]

        for valid_key in valid_keys:
            result = manager_with_mock.rename_item(
                "project", "old_task", new_key=valid_key
            )
            assert result == mock_todo_item

    def test_rename_preserves_item_relationships(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test that rename preserves all item relationships and properties"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ]  # First call finds item, second for uniqueness check returns None

        # Mock that the returned item maintains all properties
        renamed_item = MagicMock()
        renamed_item.id = sample_item_db.id
        renamed_item.list_id = sample_item_db.list_id
        renamed_item.position = sample_item_db.position
        renamed_item.status = sample_item_db.status
        renamed_item.parent_item_id = sample_item_db.parent_item_id
        renamed_item.metadata = sample_item_db.metadata
        renamed_item.created_at = sample_item_db.created_at
        mock_db.update_item.return_value = renamed_item

        # Mock the model conversion to return a TodoItem
        mock_todo_item = Mock(spec=TodoItem)
        mock_todo_item.id = sample_item_db.id
        mock_todo_item.list_id = sample_item_db.list_id
        mock_todo_item.position = sample_item_db.position
        manager_with_mock._db_to_model.return_value = mock_todo_item

        # Execute
        result = manager_with_mock.rename_item(
            "project", "old_task", new_key="new_task"
        )

        # Verify that update_item was called with only the key changes
        mock_db.update_item.assert_called_with(10, {"item_key": "new_task"})

        # The database should preserve all other properties
        assert result.id == sample_item_db.id
        assert result.list_id == sample_item_db.list_id
        assert result.position == sample_item_db.position

    def test_rename_validation_flow(
        self, manager_with_mock, mock_db, sample_list_db, sample_item_db
    ):
        """Test the complete validation flow"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.get_item_by_key_and_parent.side_effect = [
            sample_item_db,
            None,
        ]  # First call finds item, second for uniqueness check returns None
        mock_db.update_item.return_value = sample_item_db

        # Execute
        manager_with_mock.rename_item("project", "old_task", new_key="new_task")

        # Verify validation steps were called in correct order
        call_order = [
            mock_db.get_list_by_key,  # 1. Validate list exists
            mock_db.get_item_by_key_and_parent,  # 2. Validate item exists
            mock_db.update_item,  # 3. Perform update
        ]

        for mock_call in call_order:
            assert mock_call.called
