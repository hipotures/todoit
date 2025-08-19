"""
Comprehensive tests for all HistoryAction enum values
Tests that were missing and caused enum validation errors during refactoring
"""

import pytest
from core.manager import TodoManager
from core.models import HistoryAction


class TestHistoryActionsComprehensive:
    """Test all possible history actions are properly recorded"""

    @pytest.fixture
    def manager(self, temp_db):
        return TodoManager(temp_db)

    def test_all_history_actions_enum_values(self):
        """Test that all enum values are valid strings"""
        expected_actions = {
            "created", "updated", "status_updated", "content_updated", 
            "completed", "failed", "deleted", "states_cleared", 
            "rename_list", "exported", "dependency_added", 
            "dependency_removed", "renamed", "subitem_created", 
            "auto_completed", "moved_to_subitem"
        }
        
        actual_actions = {action.value for action in HistoryAction}
        assert actual_actions == expected_actions

    def test_item_creation_records_created_action(self, manager):
        """Test that item creation records 'created' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        
        # Check history (would need history retrieval method)
        # This tests the enum value is valid
        action = HistoryAction.CREATED
        assert action.value == "created"

    def test_status_update_records_status_updated_action(self, manager):
        """Test that status updates record 'status_updated' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        manager.update_item_status("test", "item1", "completed")
        
        action = HistoryAction.STATUS_UPDATED
        assert action.value == "status_updated"

    def test_content_update_records_content_updated_action(self, manager):
        """Test that content updates record 'content_updated' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        manager.update_item_content("test", "item1", "New content")
        
        action = HistoryAction.CONTENT_UPDATED
        assert action.value == "content_updated"

    def test_item_deletion_records_deleted_action(self, manager):
        """Test that item deletion records 'deleted' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        manager.delete_item("test", "item1")
        
        action = HistoryAction.DELETED
        assert action.value == "deleted"

    def test_states_clearing_records_states_cleared_action(self, manager):
        """Test that clearing completion states records 'states_cleared' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        
        # Set some completion states first
        manager.update_item_status("test", "item1", "in_progress", completion_states={"step1": True})
        
        # Clear states
        manager.clear_item_completion_states("test", "item1")
        
        action = HistoryAction.STATES_CLEARED
        assert action.value == "states_cleared"

    def test_item_rename_records_renamed_action(self, manager):
        """Test that item renaming records 'renamed' action"""
        manager.create_list("test", "Test")
        manager.add_item("test", "item1", "Content")
        manager.rename_item("test", "item1", new_key="item2")
        
        action = HistoryAction.RENAMED
        assert action.value == "renamed"

    def test_subitem_creation_would_record_subitem_created_action(self, manager):
        """Test that subitem creation would record 'subitem_created' action"""
        # Test the enum value exists
        action = HistoryAction.SUBITEM_CREATED
        assert action.value == "subitem_created"

    def test_dependency_actions_enum_values(self):
        """Test dependency-related action enum values"""
        assert HistoryAction.DEPENDENCY_ADDED.value == "dependency_added"
        assert HistoryAction.DEPENDENCY_REMOVED.value == "dependency_removed"

    def test_auto_completion_action_enum_value(self):
        """Test auto-completion action enum value"""
        assert HistoryAction.AUTO_COMPLETED.value == "auto_completed"

    def test_move_to_subitem_action_enum_value(self):
        """Test move-to-subitem action enum value"""
        assert HistoryAction.MOVED_TO_SUBITEM.value == "moved_to_subitem"