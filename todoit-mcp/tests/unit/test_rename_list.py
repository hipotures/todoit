"""
Unit tests for rename_list functionality in TodoManager.

Tests the business logic of list renaming including validation,
error handling, and history recording.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from core.manager import TodoManager
from core.models import TodoList


class TestRenameListUnit:
    """Unit tests for rename_list method with mocked database"""

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
            return manager

    @pytest.fixture
    def sample_list_db(self):
        """Sample database list object"""
        mock_list = MagicMock()
        mock_list.id = 1
        mock_list.list_key = "old_key"
        mock_list.title = "Old Title"
        mock_list.description = "Test description"
        mock_list.list_type = "sequential"
        mock_list.status = "active"
        mock_list.parent_list_id = None
        mock_list.meta_data = {}
        mock_list.created_at = "2025-01-01T10:00:00"
        mock_list.updated_at = "2025-01-01T10:00:00"
        return mock_list

    def test_rename_key_only(self, manager_with_mock, mock_db, sample_list_db):
        """Test renaming only the list key"""

        # Setup - mock get_list_by_key to return sample_list_db for old_key, None for new_key
        def get_list_side_effect(key):
            if key == "old_key":
                return sample_list_db
            elif key == "new_key":
                return None  # New key doesn't exist
            return None

        mock_db.get_list_by_key.side_effect = get_list_side_effect
        mock_db.update_list.return_value = sample_list_db

        # Execute
        result = manager_with_mock.rename_list("old_key", new_key="new_key")

        # Verify
        assert mock_db.get_list_by_key.call_count >= 1
        mock_db.update_list.assert_called_with(1, {"list_key": "new_key"})
        manager_with_mock._record_history.assert_called_once()
        assert isinstance(result, TodoList)

    def test_rename_title_only(self, manager_with_mock, mock_db, sample_list_db):
        """Test renaming only the list title"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.update_list.return_value = sample_list_db

        # Execute
        result = manager_with_mock.rename_list("old_key", new_title="New Title")

        # Verify
        mock_db.update_list.assert_called_with(1, {"title": "New Title"})
        manager_with_mock._record_history.assert_called_once()

    def test_rename_both_key_and_title(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test renaming both key and title"""

        # Setup
        def get_list_side_effect(key):
            if key == "old_key":
                return sample_list_db
            elif key == "new_key":
                return None  # New key doesn't exist
            return None

        mock_db.get_list_by_key.side_effect = get_list_side_effect
        mock_db.update_list.return_value = sample_list_db

        # Execute
        result = manager_with_mock.rename_list(
            "old_key", new_key="new_key", new_title="New Title"
        )

        # Verify
        mock_db.update_list.assert_called_with(
            1, {"list_key": "new_key", "title": "New Title"}
        )
        manager_with_mock._record_history.assert_called_once()

    def test_rename_no_parameters_error(self, manager_with_mock, mock_db):
        """Test error when no new_key or new_title provided"""
        with pytest.raises(
            ValueError, match="At least one of new_key or new_title must be provided"
        ):
            manager_with_mock.rename_list("test_key")

    def test_rename_nonexistent_list_error(self, manager_with_mock, mock_db):
        """Test error when list doesn't exist"""
        mock_db.get_list_by_key.return_value = None

        with pytest.raises(ValueError, match="List 'nonexistent' does not exist"):
            manager_with_mock.rename_list("nonexistent", new_key="new_key")

    def test_rename_invalid_key_error(self, manager_with_mock, mock_db, sample_list_db):
        """Test error when new key doesn't contain letters"""
        mock_db.get_list_by_key.return_value = sample_list_db

        with pytest.raises(ValueError, match="must contain at least one letter"):
            manager_with_mock.rename_list("old_key", new_key="123")

    def test_rename_duplicate_key_error(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test error when new key already exists"""
        # Setup
        existing_list = MagicMock()
        existing_list.id = 2  # Different ID from sample_list_db

        mock_db.get_list_by_key.side_effect = lambda key: {
            "old_key": sample_list_db,
            "existing_key": existing_list,
        }.get(key, None)

        # Execute & Verify
        with pytest.raises(ValueError, match="List key 'existing_key' already exists"):
            manager_with_mock.rename_list("old_key", new_key="existing_key")

    def test_rename_same_key_allowed(self, manager_with_mock, mock_db, sample_list_db):
        """Test that renaming to the same key is allowed (should work for title-only changes)"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.update_list.return_value = sample_list_db

        # Execute - rename to same key but different title should work
        result = manager_with_mock.rename_list(
            "old_key", new_key="old_key", new_title="New Title"
        )

        # Verify
        mock_db.update_list.assert_called_with(
            1, {"list_key": "old_key", "title": "New Title"}
        )

    def test_rename_update_failure_error(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test error when database update fails"""
        mock_db.get_list_by_key.return_value = sample_list_db
        mock_db.update_list.return_value = None  # Simulate failure
        mock_db.get_list_by_key.side_effect = lambda key: (
            sample_list_db if key == "old_key" else None
        )

        with pytest.raises(ValueError, match="Failed to update list 'old_key'"):
            manager_with_mock.rename_list("old_key", new_key="new_key")

    def test_rename_history_recording(self, manager_with_mock, mock_db, sample_list_db):
        """Test that history is recorded correctly"""

        # Setup
        def get_list_side_effect(key):
            if key == "old_key":
                return sample_list_db
            elif key == "new_key":
                return None  # New key doesn't exist
            return None

        mock_db.get_list_by_key.side_effect = get_list_side_effect
        mock_db.update_list.return_value = sample_list_db

        # Execute
        manager_with_mock.rename_list(
            "old_key", new_key="new_key", new_title="New Title"
        )

        # Verify history call
        call_args = manager_with_mock._record_history.call_args
        assert call_args[1]["list_id"] == 1
        assert call_args[1]["action"] == "rename_list"
        assert call_args[1]["old_value"] == {
            "list_key": "old_key",
            "title": "Old Title",
        }
        assert call_args[1]["new_value"]["list_key"] == "new_key"
        assert call_args[1]["new_value"]["title"] == "New Title"
        assert "key: old_key → new_key" in call_args[1]["new_value"]["changes"]
        assert "title: Old Title → New Title" in call_args[1]["new_value"]["changes"]

    def test_rename_key_validation_logic(
        self, manager_with_mock, mock_db, sample_list_db
    ):
        """Test the key validation regex logic"""
        # Setup
        mock_db.get_list_by_key.return_value = sample_list_db

        # Execute & Verify - test with actual regex logic (no letters)
        with pytest.raises(ValueError, match="must contain at least one letter"):
            manager_with_mock.rename_list("old_key", new_key="123")

        # Test with valid key (has letters) - should not raise
        mock_db.get_list_by_key.side_effect = lambda key: (
            sample_list_db if key == "old_key" else None
        )
        mock_db.update_list.return_value = sample_list_db

        # This should work
        result = manager_with_mock.rename_list("old_key", new_key="abc123")
        assert isinstance(result, TodoList)
