"""
Unit tests for completion states management functionality
Tests clear_item_completion_states method and related operations
"""

import pytest
import tempfile
import os
from core.manager import TodoManager


@pytest.fixture
def manager():
    """Create temporary TodoManager for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    try:
        manager = TodoManager(db_path)
        yield manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def manager_with_states(manager):
    """Create manager with list and item that has completion states"""
    # Create list
    manager.create_list("test_list", "Test List")

    # Add item
    manager.add_item("test_list", "test_item", "Test Item")

    # Set some completion states via status update
    manager.update_item_status(
        "test_list",
        "test_item",
        status="completed",
        completion_states={"quality": True, "tested": False, "reviewed": True},
    )

    return manager


class TestClearCompletionStates:
    """Test clear_item_completion_states functionality"""

    def test_clear_all_states(self, manager_with_states):
        """Test clearing all completion states from an item"""
        # Verify states exist
        item = manager_with_states.get_item("test_list", "test_item")
        assert item.completion_states == {
            "quality": True,
            "tested": False,
            "reviewed": True,
        }

        # Clear all states
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list", "test_item"
        )

        # Verify states are cleared
        assert updated_item.completion_states == {}

        # Verify in database
        db_item = manager_with_states.get_item("test_list", "test_item")
        assert db_item.completion_states == {}

    def test_clear_specific_states(self, manager_with_states):
        """Test clearing specific completion states"""
        # Clear only specific states
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list", "test_item", state_keys=["tested", "quality"]
        )

        # Should keep 'reviewed' but remove 'tested' and 'quality'
        assert updated_item.completion_states == {"reviewed": True}

        # Verify in database
        db_item = manager_with_states.get_item("test_list", "test_item")
        assert db_item.completion_states == {"reviewed": True}

    def test_clear_nonexistent_states(self, manager_with_states):
        """Test clearing states that don't exist"""
        # Try to clear states that don't exist
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list", "test_item", state_keys=["nonexistent", "also_missing"]
        )

        # Original states should remain unchanged
        assert updated_item.completion_states == {
            "quality": True,
            "tested": False,
            "reviewed": True,
        }

    def test_clear_mixed_existing_nonexistent(self, manager_with_states):
        """Test clearing mix of existing and non-existing states"""
        # Clear mix of existing and non-existing states
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list",
            "test_item",
            state_keys=["tested", "nonexistent", "quality"],  # 2 exist, 1 doesn't
        )

        # Should remove existing ones, ignore non-existing
        assert updated_item.completion_states == {"reviewed": True}

    def test_clear_states_empty_item(self, manager):
        """Test clearing states from item with no states"""
        # Create item without states
        manager.create_list("empty_list", "Empty List")
        manager.add_item("empty_list", "empty_item", "Empty Item")

        # Try to clear states (should work without error)
        updated_item = manager.clear_item_completion_states("empty_list", "empty_item")

        # Should remain empty
        assert updated_item.completion_states == {}

    def test_clear_states_invalid_list(self, manager):
        """Test clearing states from non-existent list"""
        with pytest.raises(ValueError, match="List 'nonexistent' does not exist"):
            manager.clear_item_completion_states("nonexistent", "item")

    def test_clear_states_invalid_item(self, manager):
        """Test clearing states from non-existent item"""
        manager.create_list("valid_list", "Valid List")

        with pytest.raises(ValueError, match="Item 'nonexistent' does not exist"):
            manager.clear_item_completion_states("valid_list", "nonexistent")

    def test_clear_states_preserves_other_fields(self, manager_with_states):
        """Test that clearing states doesn't affect other item fields"""
        # Get original item data
        original = manager_with_states.get_item("test_list", "test_item")
        original_content = original.content
        original_status = original.status
        original_position = original.position

        # Clear states
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list", "test_item"
        )

        # Verify other fields unchanged
        assert updated_item.content == original_content
        assert updated_item.status == original_status
        assert updated_item.position == original_position
        assert updated_item.completion_states == {}

    def test_clear_states_history_recorded(self, manager_with_states):
        """Test that state clearing is recorded in history"""
        # Clear states
        manager_with_states.clear_item_completion_states("test_list", "test_item")

        # Get history
        item = manager_with_states.get_item("test_list", "test_item")
        history = manager_with_states.get_item_history("test_list", "test_item")

        # Should have history entry for states_cleared action
        assert len(history) > 0

        # Find the states_cleared entry
        states_cleared_entries = [h for h in history if h.action == "states_cleared"]
        assert len(states_cleared_entries) == 1

        entry = states_cleared_entries[0]
        assert entry.old_value["completion_states"] == {
            "quality": True,
            "tested": False,
            "reviewed": True,
        }
        assert entry.new_value["completion_states"] == {}

    def test_clear_states_empty_list_parameter(self, manager_with_states):
        """Test clearing with empty state_keys list"""
        # Pass empty list (should clear nothing)
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list", "test_item", state_keys=[]
        )

        # All states should remain
        assert updated_item.completion_states == {
            "quality": True,
            "tested": False,
            "reviewed": True,
        }

    def test_clear_states_duplicate_keys(self, manager_with_states):
        """Test clearing with duplicate state keys"""
        # Pass duplicate keys
        updated_item = manager_with_states.clear_item_completion_states(
            "test_list",
            "test_item",
            state_keys=["quality", "quality", "tested"],  # quality appears twice
        )

        # Should work correctly, removing each key only once
        assert updated_item.completion_states == {"reviewed": True}


class TestCompletionStatesIntegration:
    """Integration tests for completion states with other functionality"""

    def test_states_preserved_during_status_update(self, manager_with_states):
        """Test that existing states are preserved when updating status"""
        # Update status without changing states
        updated_item = manager_with_states.update_item_status(
            "test_list", "test_item", status="in_progress"
        )

        # States should be preserved
        assert updated_item.completion_states == {
            "quality": True,
            "tested": False,
            "reviewed": True,
        }

    def test_states_merged_during_status_update(self, manager_with_states):
        """Test that new states are merged with existing ones"""
        # Update status and add new states
        updated_item = manager_with_states.update_item_status(
            "test_list",
            "test_item",
            status="failed",
            completion_states={
                "error_logged": True,
                "tested": True,
            },  # Override tested, add new
        )

        # Should merge states
        expected_states = {
            "quality": True,
            "tested": True,  # Updated from False to True
            "reviewed": True,
            "error_logged": True,  # New state added
        }
        assert updated_item.completion_states == expected_states
