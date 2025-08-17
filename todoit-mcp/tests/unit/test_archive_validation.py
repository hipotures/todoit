"""
Unit tests for archive validation functionality
Tests the core archive validation logic in TodoManager
"""

import pytest
import tempfile
import os
from core.manager import TodoManager


class TestArchiveValidation:
    """Unit tests for archive validation in TodoManager"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def manager(self, temp_db_path):
        """Create TodoManager instance with temporary database"""
        return TodoManager(temp_db_path)

    def test_archive_empty_list_without_force(self, manager):
        """Test archiving empty list succeeds without force"""
        # Create empty list
        empty_list = manager.create_list("empty-test", "Empty Test List")

        # Should succeed without force
        archived_list = manager.archive_list("empty-test", force=False)
        assert archived_list.status == "archived"

    def test_archive_completed_list_without_force(self, manager):
        """Test archiving list with all completed tasks succeeds without force"""
        # Create list with tasks
        test_list = manager.create_list(
            "completed-test", "Completed Test", items=["Item 1", "Item 2"]
        )

        # Complete all tasks
        manager.update_item_status("completed-test", "item_1", status="completed")
        manager.update_item_status("completed-test", "item_2", status="completed")

        # Should succeed without force
        archived_list = manager.archive_list("completed-test", force=False)
        assert archived_list.status == "archived"

    def test_archive_incomplete_list_without_force_fails(self, manager):
        """Test archiving list with incomplete tasks fails without force"""
        # Create list with tasks
        test_list = manager.create_list(
            "incomplete-test", "Incomplete Test", items=["Item 1", "Item 2", "Item 3"]
        )

        # Complete only one item
        manager.update_item_status("incomplete-test", "item_1", status="completed")

        # Should fail without force
        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("incomplete-test", force=False)

        error_message = str(exc_info.value)
        assert "Cannot archive list with incomplete tasks" in error_message
        assert "Incomplete: 2/3 tasks" in error_message
        assert "Use force=True to archive anyway" in error_message

    def test_archive_incomplete_list_with_force_succeeds(self, manager):
        """Test archiving list with incomplete tasks succeeds with force=True"""
        # Create list with tasks
        test_list = manager.create_list(
            "force-test", "Force Test", items=["Item 1", "Item 2"]
        )

        # Don't complete any tasks

        # Should succeed with force=True
        archived_list = manager.archive_list("force-test", force=True)
        assert archived_list.status == "archived"

    def test_archive_mixed_status_list_without_force_fails(self, manager):
        """Test archiving list with mixed item statuses fails without force"""
        # Create list with tasks
        test_list = manager.create_list(
            "mixed-test",
            "Mixed Status Test",
            items=["Item 1", "Item 2", "Item 3", "Item 4"],
        )

        # Set various statuses
        manager.update_item_status("mixed-test", "item_1", status="completed")
        manager.update_item_status("mixed-test", "item_2", status="in_progress")
        manager.update_item_status("mixed-test", "item_3", status="failed")
        # item_4 remains pending

        # Should fail without force (3 out of 4 are not completed)
        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("mixed-test", force=False)

        error_message = str(exc_info.value)
        assert "Cannot archive list with incomplete tasks" in error_message
        assert "Incomplete: 3/4 tasks" in error_message

    def test_archive_mixed_status_list_with_force_succeeds(self, manager):
        """Test archiving list with mixed item statuses succeeds with force=True"""
        # Create list with tasks
        test_list = manager.create_list(
            "mixed-force-test", "Mixed Force Test", items=["Item 1", "Item 2"]
        )

        # Set mixed statuses
        manager.update_item_status("mixed-force-test", "item_1", status="completed")
        manager.update_item_status("mixed-force-test", "item_2", status="failed")

        # Should succeed with force=True
        archived_list = manager.archive_list("mixed-force-test", force=True)
        assert archived_list.status == "archived"

    def test_archive_nonexistent_list_fails(self, manager):
        """Test archiving non-existent list fails regardless of force"""
        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("nonexistent", force=False)
        assert "does not exist" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("nonexistent", force=True)
        assert "does not exist" in str(exc_info.value)

    def test_archive_already_archived_list_fails(self, manager):
        """Test archiving already archived list fails regardless of force"""
        # Create and archive a list
        test_list = manager.create_list("already-archived", "Already Archived")
        manager.archive_list("already-archived", force=True)

        # Try to archive again
        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("already-archived", force=False)
        assert "is already archived" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("already-archived", force=True)
        assert "is already archived" in str(exc_info.value)

    def test_force_parameter_defaults_to_false(self, manager):
        """Test that force parameter defaults to False when not specified"""
        # Create list with incomplete tasks
        test_list = manager.create_list(
            "default-force-test", "Default Force Test", items=["Item 1"]
        )

        # Should fail when calling without force parameter (defaults to False)
        with pytest.raises(ValueError) as exc_info:
            manager.archive_list("default-force-test")  # No force parameter
        assert "Cannot archive list with incomplete tasks" in str(exc_info.value)
