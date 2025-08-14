"""
Integration tests for live monitoring functionality.
Tests the logic behind live monitoring without actual UI interaction.
"""

import pytest
import hashlib
import json
from core.manager import TodoManager


class TestLiveMonitoring:
    """Test live monitoring logic and utilities"""

    @pytest.fixture
    def temp_manager(self, temp_db):
        """Create manager with test database"""
        return TodoManager(temp_db)

    @pytest.fixture
    def sample_list_with_items(self, temp_manager):
        """Create a sample list with items for testing"""
        # Create list
        temp_manager.create_list("live_test", "Live Test List")

        # Add items with different statuses
        temp_manager.add_item("live_test", "task1", "First task")
        temp_manager.add_item("live_test", "task2", "Second task")
        temp_manager.update_item_status("live_test", "task2", status="in_progress")

        return temp_manager.get_list("live_test")

    def test_get_list_hash_for_change_detection(
        self, temp_manager, sample_list_with_items
    ):
        """Test hash generation for change detection"""

        def get_list_hash(items_data):
            """Same function as in CLI"""
            state_str = json.dumps(items_data, sort_keys=True, default=str)
            return hashlib.md5(state_str.encode()).hexdigest()

        # Get initial items
        items = temp_manager.get_list_items("live_test")

        # Create items data
        items_data1 = []
        for item in items:
            items_data1.append(
                {
                    "id": item.item_key,
                    "content": item.content,
                    "status": item.status,
                    "position": item.position,
                    "updated_at": str(item.updated_at),
                }
            )

        hash1 = get_list_hash(items_data1)

        # Make same data again - should produce same hash
        items_data2 = []
        for item in items:
            items_data2.append(
                {
                    "id": item.item_key,
                    "content": item.content,
                    "status": item.status,
                    "position": item.position,
                    "updated_at": str(item.updated_at),
                }
            )

        hash2 = get_list_hash(items_data2)
        assert hash1 == hash2

        # Change something - should produce different hash
        temp_manager.update_item_status("live_test", "task1", status="completed")
        updated_items = temp_manager.get_list_items("live_test")

        items_data3 = []
        for item in updated_items:
            items_data3.append(
                {
                    "id": item.item_key,
                    "content": item.content,
                    "status": item.status,
                    "position": item.position,
                    "updated_at": str(item.updated_at),
                }
            )

        hash3 = get_list_hash(items_data3)
        assert hash3 != hash1  # Should be different after status change

    def test_change_detection_on_item_status_update(
        self, temp_manager, sample_list_with_items
    ):
        """Test that status changes are detected"""

        def get_items_snapshot():
            items = temp_manager.get_list_items("live_test")
            return [
                (item.item_key, item.status, str(item.updated_at)) for item in items
            ]

        # Get initial snapshot
        snapshot1 = get_items_snapshot()

        # Update item status
        temp_manager.update_item_status("live_test", "task1", status="completed")

        # Get new snapshot
        snapshot2 = get_items_snapshot()

        # Should be different
        assert snapshot1 != snapshot2

    def test_change_detection_on_item_content_edit(
        self, temp_manager, sample_list_with_items
    ):
        """Test that content changes are detected"""

        def get_items_snapshot():
            items = temp_manager.get_list_items("live_test")
            return [
                (item.item_key, item.content, str(item.updated_at)) for item in items
            ]

        # Get initial snapshot
        snapshot1 = get_items_snapshot()

        # Edit item content
        temp_manager.update_item_content("live_test", "task1", "Updated first task")

        # Get new snapshot
        snapshot2 = get_items_snapshot()

        # Should be different
        assert snapshot1 != snapshot2

    def test_change_detection_on_item_deletion(
        self, temp_manager, sample_list_with_items
    ):
        """Test that item deletion is detected"""

        def get_items_count():
            items = temp_manager.get_list_items("live_test")
            return len(items)

        # Get initial count
        count1 = get_items_count()
        assert count1 == 2

        # Delete an item
        temp_manager.delete_item("live_test", "task1")

        # Get new count
        count2 = get_items_count()
        assert count2 == 1

        # Should be different
        assert count1 != count2

    def test_change_detection_on_new_item_addition(
        self, temp_manager, sample_list_with_items
    ):
        """Test that new items are detected"""

        def get_items_count():
            items = temp_manager.get_list_items("live_test")
            return len(items)

        # Get initial count
        count1 = get_items_count()
        assert count1 == 2

        # Add new item
        temp_manager.add_item("live_test", "task3", "Third task")

        # Get new count
        count2 = get_items_count()
        assert count2 == 3

        # Should be different
        assert count1 != count2

    def test_progress_tracking_for_live_display(
        self, temp_manager, sample_list_with_items
    ):
        """Test progress calculation for live display"""
        # Get initial progress
        progress1 = temp_manager.get_progress("live_test")
        assert progress1.total == 2
        assert progress1.pending == 1  # task1 is pending
        assert progress1.in_progress == 1  # task2 is in_progress
        assert progress1.completed == 0

        # Complete a task
        temp_manager.update_item_status("live_test", "task1", status="completed")

        # Check updated progress
        progress2 = temp_manager.get_progress("live_test")
        assert progress2.total == 2
        assert progress2.pending == 0
        assert progress2.in_progress == 1  # task2 still in_progress
        assert progress2.completed == 1  # task1 now completed

    def test_filtered_status_view(self, temp_manager, sample_list_with_items):
        """Test filtering items by status (for --filter-status option)"""
        # Add more items with different statuses
        temp_manager.add_item("live_test", "task3", "Third task")
        temp_manager.update_item_status("live_test", "task3", status="completed")
        temp_manager.add_item("live_test", "task4", "Fourth task")  # pending by default

        # Filter by pending
        pending_items = temp_manager.get_list_items("live_test", status="pending")
        pending_keys = [item.item_key for item in pending_items]
        assert "task1" in pending_keys
        assert "task4" in pending_keys
        assert len(pending_items) == 2

        # Filter by in_progress
        in_progress_items = temp_manager.get_list_items(
            "live_test", status="in_progress"
        )
        in_progress_keys = [item.item_key for item in in_progress_items]
        assert "task2" in in_progress_keys
        assert len(in_progress_items) == 1

        # Filter by completed
        completed_items = temp_manager.get_list_items("live_test", status="completed")
        completed_keys = [item.item_key for item in completed_items]
        assert "task3" in completed_keys
        assert len(completed_items) == 1

    def test_live_monitoring_with_subtasks(self, temp_manager):
        """Test live monitoring with hierarchical structures"""
        # Create list with subtasks
        temp_manager.create_list("hierarchy_test", "Hierarchy Test")
        temp_manager.add_item("hierarchy_test", "parent", "Parent task")
        temp_manager.add_subtask("hierarchy_test", "parent", "sub1", "Subtask 1")
        temp_manager.add_subtask("hierarchy_test", "parent", "sub2", "Subtask 2")

        # Get all items (including subtasks)
        all_items = temp_manager.get_list_items("hierarchy_test")
        assert len(all_items) == 3  # parent + 2 subtasks

        # Change subtask status
        temp_manager.update_item_status("hierarchy_test", "sub1", status="completed")

        # Get progress (should include subtasks)
        # Note: parent status is now auto-synchronized to "in_progress" when subtasks are mixed
        progress = temp_manager.get_progress("hierarchy_test")
        assert progress.total == 3
        assert progress.completed == 1
        assert progress.in_progress == 1  # Parent auto-synchronized to in_progress
        assert progress.pending == 1  # Only sub2 remains pending

    def test_error_handling_for_nonexistent_list(self, temp_manager):
        """Test error handling when list doesn't exist"""
        # Try to get non-existent list
        result = temp_manager.get_list("nonexistent_list")
        assert result is None

        # Try to get items from non-existent list - returns empty list
        items = temp_manager.get_list_items("nonexistent_list")
        assert items == []

        # Try to get progress from non-existent list - should raise error
        with pytest.raises(ValueError, match="List 'nonexistent_list' does not exist"):
            temp_manager.get_progress("nonexistent_list")
