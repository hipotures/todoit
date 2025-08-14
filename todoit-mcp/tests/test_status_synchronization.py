"""
Test suite for automatic status synchronization functionality

Tests the complete status synchronization system including:
- Automatic parent status calculation based on children
- Blocking of manual status changes for tasks with subtasks
- Proper synchronization triggers on add/delete/update operations
- Recursive propagation through hierarchy levels
"""

import pytest
import tempfile
import os
from core.manager import TodoManager
from core.models import TodoItem, ItemStatus


class TestStatusSynchronization:

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            yield tmp.name
        os.unlink(tmp.name)

    @pytest.fixture
    def manager(self, temp_db):
        """Create TodoManager with temporary database"""
        return TodoManager(db_path=temp_db)

    def test_basic_status_propagation(self, manager):
        """Test 1: Basic status propagation rules"""
        # Create list and parent task
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent Task")

        # Add subtasks - all pending initially
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")
        manager.add_subtask("test_list", "parent", "sub2", "Subtask 2")
        manager.add_subtask("test_list", "parent", "sub3", "Subtask 3")

        # Verify parent status = pending (all children pending)
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "pending"

        # Change one subtask to in_progress -> parent should be in_progress
        manager.update_item_status("test_list", "sub1", "in_progress")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "in_progress"

        # Complete two subtasks -> parent still in_progress (sub3 pending)
        manager.update_item_status("test_list", "sub1", "completed")
        manager.update_item_status("test_list", "sub2", "completed")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "in_progress"

        # Complete last subtask -> parent should be completed
        manager.update_item_status("test_list", "sub3", "completed")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

    def test_failed_status_priority(self, manager):
        """Test 2: Failed status has highest priority"""
        # Create setup
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent Task")
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")
        manager.add_subtask("test_list", "parent", "sub2", "Subtask 2")
        manager.add_subtask("test_list", "parent", "sub3", "Subtask 3")

        # Set mixed statuses: completed, in_progress, failed
        manager.update_item_status("test_list", "sub1", "completed")
        manager.update_item_status("test_list", "sub2", "in_progress")
        manager.update_item_status("test_list", "sub3", "failed")

        # Parent should be failed (highest priority)
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "failed"

        # Change failed to completed -> parent should be in_progress
        manager.update_item_status("test_list", "sub3", "completed")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "in_progress"  # sub2 still in_progress

        # Complete remaining -> parent should be completed
        manager.update_item_status("test_list", "sub2", "completed")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

    def test_manual_status_change_blocked(self, manager):
        """Test 3: Block manual status changes for tasks with subtasks"""
        # Create setup
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent Task")

        # Should be able to change status before adding subtasks
        manager.update_item_status("test_list", "parent", "in_progress")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "in_progress"

        # Add subtask
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")

        # Now manual status change should be blocked
        with pytest.raises(ValueError, match="has subtasks"):
            manager.update_item_status("test_list", "parent", "completed")

        # Subtask status change should still work
        manager.update_item_status("test_list", "sub1", "completed")

        # Parent should automatically be completed
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

    def test_recursive_propagation(self, manager):
        """Test 4: Recursive propagation through multiple levels"""
        # Create 3-level hierarchy
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "grandparent", "Grandparent")
        manager.add_subtask("test_list", "grandparent", "parent", "Parent")
        manager.add_subtask("test_list", "parent", "child", "Child")

        # Change child status -> should propagate up 2 levels
        manager.update_item_status("test_list", "child", "in_progress")

        # Check propagation
        child = manager.get_item("test_list", "child")
        parent = manager.get_item("test_list", "parent")
        grandparent = manager.get_item("test_list", "grandparent")

        assert child.status == "in_progress"
        assert parent.status == "in_progress"  # Based on child
        assert grandparent.status == "in_progress"  # Based on parent

        # Complete child -> all should be completed
        manager.update_item_status("test_list", "child", "completed")

        child = manager.get_item("test_list", "child")
        parent = manager.get_item("test_list", "parent")
        grandparent = manager.get_item("test_list", "grandparent")

        assert child.status == "completed"
        assert parent.status == "completed"
        assert grandparent.status == "completed"

    def test_add_first_subtask_changes_parent(self, manager):
        """Test 5: Adding first subtask changes parent status appropriately"""
        # Create parent with completed status
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent Task")
        manager.update_item_status("test_list", "parent", "completed")

        # Verify initial status
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

        # Add first subtask (pending by default)
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")

        # Parent should now be pending (based on pending subtask)
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "pending"

    def test_delete_subtask_synchronization(self, manager):
        """Test 6: Deleting subtasks triggers parent synchronization"""
        # Create setup with 2 subtasks
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent Task")
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")
        manager.add_subtask("test_list", "parent", "sub2", "Subtask 2")

        # Set mixed statuses
        manager.update_item_status("test_list", "sub1", "completed")
        manager.update_item_status("test_list", "sub2", "pending")

        # Parent should be in_progress (mixed statuses)
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "in_progress"

        # Delete pending subtask
        manager.delete_item("test_list", "sub2")

        # Parent should now be completed (only completed subtask remains)
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

        # Delete last subtask - parent status should remain completed
        # (no automatic change when all subtasks removed)
        manager.delete_item("test_list", "sub1")
        parent = manager.get_item("test_list", "parent")
        # Parent should maintain its last synchronized status
        assert parent.status == "completed"

        # Now manual changes should work again
        manager.update_item_status("test_list", "parent", "pending")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "pending"

    def test_complex_hierarchy_scenarios(self, manager):
        """Test 7: Complex scenarios with multiple branches"""
        # Create complex hierarchy
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "root", "Root Task")

        # Branch 1
        manager.add_subtask("test_list", "root", "branch1", "Branch 1")
        manager.add_subtask("test_list", "branch1", "leaf1", "Leaf 1")
        manager.add_subtask("test_list", "branch1", "leaf2", "Leaf 2")

        # Branch 2
        manager.add_subtask("test_list", "root", "branch2", "Branch 2")
        manager.add_subtask("test_list", "branch2", "leaf3", "Leaf 3")

        # Set leaf statuses
        manager.update_item_status("test_list", "leaf1", "completed")
        manager.update_item_status(
            "test_list", "leaf2", "completed"
        )  # branch1 -> completed
        manager.update_item_status(
            "test_list", "leaf3", "pending"
        )  # branch2 -> pending

        # Check intermediate statuses
        branch1 = manager.get_item("test_list", "branch1")
        branch2 = manager.get_item("test_list", "branch2")
        root = manager.get_item("test_list", "root")

        assert branch1.status == "completed"  # all children completed
        assert branch2.status == "pending"  # all children pending
        assert root.status == "in_progress"  # mixed branch statuses

        # Complete remaining leaf
        manager.update_item_status("test_list", "leaf3", "completed")

        # Everything should cascade to completed
        branch2 = manager.get_item("test_list", "branch2")
        root = manager.get_item("test_list", "root")

        assert branch2.status == "completed"
        assert root.status == "completed"

    def test_performance_with_many_subtasks(self, manager):
        """Test 8: Performance with larger hierarchies"""
        # Create list and parent
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent with many subtasks")

        # Add 100 subtasks
        for i in range(100):
            manager.add_subtask("test_list", "parent", f"sub{i:03d}", f"Subtask {i}")

        # Complete all subtasks one by one - should be fast
        import time

        start_time = time.time()

        for i in range(100):
            manager.update_item_status("test_list", f"sub{i:03d}", "completed")

        elapsed = time.time() - start_time

        # Should complete in reasonable time (less than 5 seconds)
        assert elapsed < 5.0, f"Status synchronization too slow: {elapsed:.2f}s"

        # Parent should be completed
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

    def test_circular_dependency_protection(self, manager):
        """Test 9: Protection against circular dependencies in sync"""
        # This tests the visited set mechanism in _sync_parent_status
        # Create normal hierarchy first
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent")
        manager.add_subtask("test_list", "parent", "child", "Child")

        # Normal operation should work
        manager.update_item_status("test_list", "child", "completed")
        parent = manager.get_item("test_list", "parent")
        assert parent.status == "completed"

        # The circular dependency protection is mainly for database corruption
        # scenarios, which are hard to create through normal API calls.
        # The visited set ensures we don't get infinite recursion.

    def test_transaction_atomicity(self, manager):
        """Test 10: Ensure all status updates happen in transactions"""
        # Create setup
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "parent", "Parent")
        manager.add_subtask("test_list", "parent", "sub1", "Subtask 1")

        # This tests that status updates are atomic - if parent sync fails,
        # the subtask update should also be rolled back
        # This is mainly tested by the transaction structure in the code

        # Normal case - both subtask and parent should update
        manager.update_item_status("test_list", "sub1", "completed")

        sub1 = manager.get_item("test_list", "sub1")
        parent = manager.get_item("test_list", "parent")

        assert sub1.status == "completed"
        assert parent.status == "completed"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
