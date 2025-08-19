"""
Integration tests for database transaction integrity
Tests that were missing and caused issues during refactoring
"""

import pytest
from core.manager import TodoManager


class TestTransactionIntegrity:
    """Test database transaction consistency"""

    @pytest.fixture
    def temp_manager(self, temp_db):
        return TodoManager(temp_db)

    def test_parent_sync_commits_changes(self, temp_manager):
        """Test that parent status sync actually commits to database"""
        # Create hierarchy
        temp_manager.create_list("test", "Test")
        temp_manager.add_item("test", "parent", "Parent")
        temp_manager.add_subitem("test", "parent", "child", "Child")
        
        # Change child status
        temp_manager.update_item_status("test", "child", "completed", parent_item_key="parent")
        
        # Create NEW manager instance to ensure we're reading from DB
        new_manager = TodoManager(temp_manager.db.db_path)
        parent = new_manager.get_item("test", "parent")
        
        # Parent should be completed (not cached in memory)
        assert parent.status == "completed"

    def test_delete_item_syncs_parent_in_same_transaction(self, temp_manager):
        """Test that delete + parent sync happens atomically"""
        temp_manager.create_list("test", "Test")
        temp_manager.add_item("test", "parent", "Parent")
        temp_manager.add_subitem("test", "parent", "child1", "Child 1")
        temp_manager.add_subitem("test", "parent", "child2", "Child 2")
        
        # Set statuses
        temp_manager.update_item_status("test", "child1", "completed", parent_item_key="parent")
        temp_manager.update_item_status("test", "child2", "pending", parent_item_key="parent")
        
        # Parent should be in_progress
        assert temp_manager.get_item("test", "parent").status == "in_progress"
        
        # Delete pending child
        temp_manager.delete_item("test", "child2", parent_item_key="parent")
        
        # Parent should immediately be completed
        assert temp_manager.get_item("test", "parent").status == "completed"

    def test_timestamp_persistence(self, temp_manager):
        """Test that timestamps are actually saved to database"""
        temp_manager.create_list("test", "Test")
        temp_manager.add_item("test", "task", "Task")
        
        # Set to in_progress
        temp_manager.update_item_status("test", "task", "in_progress")
        item = temp_manager.get_item("test", "task")
        started_time = item.started_at
        assert started_time is not None
        
        # Set to completed
        temp_manager.update_item_status("test", "task", "completed")
        item = temp_manager.get_item("test", "task")
        completed_time = item.completed_at
        assert completed_time is not None
        
        # Verify with fresh manager instance
        new_manager = TodoManager(temp_manager.db.db_path)
        fresh_item = new_manager.get_item("test", "task")
        assert fresh_item.started_at == started_time
        assert fresh_item.completed_at == completed_time