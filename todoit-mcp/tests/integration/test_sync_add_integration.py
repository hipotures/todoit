"""
Integration tests for add_item synchronization functionality
Tests end-to-end synchronization with real database and TodoManager
"""

import pytest
import tempfile
import os
from core.manager import TodoManager
from core.models import ItemStatus


class TestSyncAddIntegration:
    """Test add_item synchronization with real database operations"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def manager(self, temp_db_path):
        """Create TodoManager with temporary database"""
        return TodoManager(temp_db_path)

    def test_basic_sync_add(self, manager):
        """Test basic synchronization of add_item from parent to child"""
        # Setup: Create parent list with initial tasks
        manager.create_list("parent", "Parent List")
        manager.add_item("parent", "task1", "Initial item 1")
        manager.add_item("parent", "task2", "Initial item 2")

        # Link to create child list
        result = manager.link_list_1to1("parent", "child", "Child List")
        assert result["success"] is True
        assert result["items_copied"] == 2

        # Verify initial sync
        parent_items = manager.get_list_items("parent")
        child_items = manager.get_list_items("child")
        assert len(parent_items) == len(child_items) == 2

        # Add NEW item to parent - should sync to child
        manager.add_item("parent", "task3", "NEW synced item")

        # Verify sync occurred
        parent_items_after = manager.get_list_items("parent")
        child_items_after = manager.get_list_items("child")

        assert len(parent_items_after) == 3
        assert len(child_items_after) == 3

        # Verify the new item exists in both with correct properties
        parent_task3 = next(
            (item for item in parent_items_after if item.item_key == "task3"), None
        )
        child_task3 = next(
            (item for item in child_items_after if item.item_key == "task3"), None
        )

        assert parent_task3 is not None
        assert child_task3 is not None
        assert parent_task3.content == child_task3.content == "NEW synced item"
        assert child_task3.status == ItemStatus.PENDING  # Always reset to pending

    def test_sync_add_with_properties(self, manager):
        """Test synchronization with item properties"""
        # Setup parent and child
        manager.create_list("dev", "Development")
        manager.add_item("dev", "setup", "Setup item")
        manager.link_list_1to1("dev", "test", "Testing")

        # Add item with properties to parent
        manager.add_item(
            "dev",
            "complex_task",
            "Complex item with properties",
            metadata={"priority": "high", "category": "feature"},
        )

        # Add properties after creation
        manager.set_item_property("dev", "complex_task", "assignee", "john_doe")
        manager.set_item_property("dev", "complex_task", "estimated_hours", "8")

        # Add another item to trigger sync
        manager.add_item("dev", "sync_test", "Test sync functionality")

        # Verify sync
        dev_items = manager.get_list_items("dev")
        test_items = manager.get_list_items("test")

        assert len(dev_items) == len(test_items) == 3

        # Find the synced item
        test_sync = next(
            (item for item in test_items if item.item_key == "sync_test"), None
        )
        assert test_sync is not None
        assert test_sync.content == "Test sync functionality"
        assert test_sync.status == ItemStatus.PENDING

    def test_sync_add_multiple_children(self, manager):
        """Test synchronization to multiple 1:1 children"""
        # Setup parent
        manager.create_list("main", "Main List")
        manager.add_item("main", "base", "Base item")

        # Create multiple children
        manager.link_list_1to1("main", "child1", "Child 1")
        manager.link_list_1to1("main", "child2", "Child 2")

        # Verify initial state
        main_items = manager.get_list_items("main")
        child1_items = manager.get_list_items("child1")
        child2_items = manager.get_list_items("child2")

        assert len(main_items) == len(child1_items) == len(child2_items) == 1

        # Add item to parent
        manager.add_item("main", "multi_sync", "Should sync to all children")

        # Verify sync to all children
        main_items_after = manager.get_list_items("main")
        child1_items_after = manager.get_list_items("child1")
        child2_items_after = manager.get_list_items("child2")

        assert (
            len(main_items_after)
            == len(child1_items_after)
            == len(child2_items_after)
            == 2
        )

        # Verify the item exists in all lists
        main_multi = next(
            (item for item in main_items_after if item.item_key == "multi_sync"), None
        )
        child1_multi = next(
            (item for item in child1_items_after if item.item_key == "multi_sync"), None
        )
        child2_multi = next(
            (item for item in child2_items_after if item.item_key == "multi_sync"), None
        )

        assert all([main_multi, child1_multi, child2_multi])
        assert main_multi.content == child1_multi.content == child2_multi.content

    def test_no_sync_to_non_1to1_lists(self, manager):
        """Test that sync only works for 1:1 relationships"""
        # Create lists with regular (non-1:1) relation
        manager.create_list("source", "Source List")
        manager.create_list("related", "Related List")
        manager.add_item("source", "initial", "Initial item")

        # Create regular relation (not 1:1)
        source_list = manager.get_list("source")
        related_list = manager.get_list("related")
        manager.create_list_relation(
            source_list.id,
            related_list.id,
            "project",
            "test_project",
            metadata={"relationship": "related"},  # NOT 1:1
        )

        # Add item to source
        manager.add_item("source", "no_sync", "Should NOT sync")

        # Verify no sync occurred
        source_items = manager.get_list_items("source")
        related_items = manager.get_list_items("related")

        assert len(source_items) == 2  # initial + no_sync
        assert len(related_items) == 0  # No sync occurred

        # Verify the item doesn't exist in related
        no_sync_in_related = any(item.item_key == "no_sync" for item in related_items)
        assert not no_sync_in_related

    def test_sync_skip_existing_items(self, manager):
        """Test that sync skips items that already exist in child"""
        # Setup
        manager.create_list("parent", "Parent")
        manager.add_item("parent", "task1", "Item 1")
        manager.link_list_1to1("parent", "child", "Child")

        # Manually add item to child with same key
        manager.add_item("child", "duplicate", "Child version")

        # Add item with same key to parent - should not overwrite child
        manager.add_item("parent", "duplicate", "Parent version")

        # Verify child version unchanged
        child_items = manager.get_list_items("child")
        duplicate_in_child = next(
            (item for item in child_items if item.item_key == "duplicate"), None
        )

        assert duplicate_in_child is not None
        assert duplicate_in_child.content == "Child version"  # Not overwritten

    def test_sync_with_positions(self, manager):
        """Test that sync respects position ordering"""
        # Setup
        manager.create_list("ordered", "Ordered List")
        manager.add_item("ordered", "first", "First item", position=1)
        manager.add_item("ordered", "second", "Second item", position=2)
        manager.link_list_1to1("ordered", "copy", "Copy List")

        # Add item with specific position
        manager.add_item("ordered", "middle", "Middle item", position=2)

        # Verify sync maintained structure
        ordered_items = manager.get_list_items("ordered")
        copy_items = manager.get_list_items("copy")

        assert len(ordered_items) == len(copy_items) == 3

        # Find middle item in copy
        middle_in_copy = next(
            (item for item in copy_items if item.item_key == "middle"), None
        )
        assert middle_in_copy is not None
        assert middle_in_copy.content == "Middle item"

    def test_sync_performance_with_many_items(self, manager):
        """Test sync performance with larger lists"""
        # Create parent with some items
        manager.create_list("big_parent", "Big Parent")
        for i in range(10):
            manager.add_item("big_parent", f"init_{i:02d}", f"Initial item {i}")

        # Link child
        manager.link_list_1to1("big_parent", "big_child", "Big Child")

        # Verify initial sync
        parent_items = manager.get_list_items("big_parent")
        child_items = manager.get_list_items("big_child")
        assert len(parent_items) == len(child_items) == 10

        # Time the sync operation
        import time

        start_time = time.time()

        # Add multiple new tasks
        for i in range(5):
            manager.add_item("big_parent", f"new_{i:02d}", f"New item {i}")

        end_time = time.time()
        sync_time = end_time - start_time

        # Verify all synced
        parent_items_final = manager.get_list_items("big_parent")
        child_items_final = manager.get_list_items("big_child")

        assert len(parent_items_final) == len(child_items_final) == 15
        assert sync_time < 2.0  # Should complete quickly

        # Verify all new tasks synced
        for i in range(5):
            new_key = f"new_{i:02d}"
            parent_has = any(item.item_key == new_key for item in parent_items_final)
            child_has = any(item.item_key == new_key for item in child_items_final)
            assert parent_has and child_has
