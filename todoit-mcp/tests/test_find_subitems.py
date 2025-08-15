"""
Tests for find_subitems_by_status functionality
"""

import pytest
from core.manager import TodoManager
from core.models import TodoItem


@pytest.fixture
def manager_with_test_data(tmp_path):
    """Create manager with test data for subitem search tests"""
    db_path = tmp_path / "test_find_subitems.db"
    manager = TodoManager(str(db_path))

    # Create a test list
    test_list = manager.create_list("test_list", "Test List for Subitems")

    # Create parent task
    parent = manager.add_item("test_list", "parent_task", "Parent task for testing")

    # Create subitems with different statuses
    manager.add_subtask("test_list", "parent_task", "generate", "Generate image")
    manager.add_subtask("test_list", "parent_task", "download", "Download image")
    manager.add_subtask("test_list", "parent_task", "process", "Process image")

    # Create second parent with different subitems
    parent2 = manager.add_item("test_list", "parent_task2", "Second parent task")
    manager.add_subtask("test_list", "parent_task2", "design", "Design feature")
    manager.add_subtask("test_list", "parent_task2", "code", "Write code")
    manager.add_subtask("test_list", "parent_task2", "test", "Write tests")

    # Set some initial statuses
    manager.update_item_status("test_list", "generate", status="completed")
    manager.update_item_status("test_list", "download", status="pending")
    manager.update_item_status("test_list", "process", status="pending")

    manager.update_item_status("test_list", "design", status="completed")
    manager.update_item_status("test_list", "code", status="completed")
    manager.update_item_status("test_list", "test", status="pending")

    return manager


class TestFindSubitemsByStatus:
    """Test the find_subitems_by_status functionality"""

    def test_basic_search_single_condition(self, manager_with_test_data):
        """Test basic search with single condition"""
        manager = manager_with_test_data

        # Find subitems where generate is completed
        results = manager.find_subitems_by_status(
            "test_list", {"generate": "completed"}, limit=10
        )

        # Should find the generate subitem
        assert len(results) == 1
        assert results[0].item_key == "generate"
        assert results[0].status.value == "completed"

    def test_search_multiple_conditions(self, manager_with_test_data):
        """Test search with multiple conditions"""
        manager = manager_with_test_data

        # Find subitems where generate is completed AND download is pending
        results = manager.find_subitems_by_status(
            "test_list",
            {"generate": "completed", "download": "pending"},
            limit=10,
        )

        # Should find both generate and download subitems
        assert len(results) == 2
        found_keys = {item.item_key for item in results}
        assert found_keys == {"generate", "download"}

    def test_search_with_failing_conditions(self, manager_with_test_data):
        """Test search where conditions are not met"""
        manager = manager_with_test_data

        # Look for conditions that don't exist
        results = manager.find_subitems_by_status(
            "test_list",
            {"generate": "failed", "download": "completed"},  # Wrong statuses
            limit=10,
        )

        # Should find nothing
        assert len(results) == 0

    def test_search_different_parent_groups(self, manager_with_test_data):
        """Test that search works across different parent groups"""
        manager = manager_with_test_data

        # Find subitems where design and code are both completed
        results = manager.find_subitems_by_status(
            "test_list",
            {"design": "completed", "code": "completed"},
            limit=10,
        )

        # Should find design and code subitems from second parent
        assert len(results) == 2
        found_keys = {item.item_key for item in results}
        assert found_keys == {"design", "code"}

    def test_search_with_limit(self, manager_with_test_data):
        """Test that limit parameter works correctly"""
        manager = manager_with_test_data

        # Find with limit of 1
        results = manager.find_subitems_by_status(
            "test_list", {"generate": "completed"}, limit=1
        )

        assert len(results) == 1

    def test_search_nonexistent_list(self, manager_with_test_data):
        """Test search on non-existent list raises error"""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.find_subitems_by_status(
                "nonexistent", {"generate": "completed"}, limit=10
            )

    def test_search_empty_conditions(self, manager_with_test_data):
        """Test search with empty conditions raises error"""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="Conditions dictionary cannot be empty"):
            manager.find_subitems_by_status("test_list", {}, limit=10)

    def test_search_ordering_by_position(self, manager_with_test_data):
        """Test that results are ordered by position"""
        manager = manager_with_test_data

        # Find multiple subitems
        results = manager.find_subitems_by_status(
            "test_list",
            {"generate": "completed", "download": "pending", "process": "pending"},
            limit=10,
        )

        # Should be ordered by position
        assert len(results) == 3
        positions = [item.position for item in results]
        assert positions == sorted(positions)

    def test_workflow_scenario_image_processing(self, manager_with_test_data):
        """Test realistic workflow scenario for image processing"""
        manager = manager_with_test_data

        # Scenario: Find downloads ready to process (generation completed)
        ready_downloads = manager.find_subitems_by_status(
            "test_list",
            {"generate": "completed", "download": "pending"},
            limit=5,
        )

        # Should find download subitem
        downloads = [item for item in ready_downloads if item.item_key == "download"]
        assert len(downloads) == 1
        assert downloads[0].status.value == "pending"

    def test_workflow_scenario_development(self, manager_with_test_data):
        """Test realistic workflow scenario for development tasks"""
        manager = manager_with_test_data

        # Scenario: Find tests ready to run (design and code completed)
        ready_tests = manager.find_subitems_by_status(
            "test_list",
            {"design": "completed", "code": "completed", "test": "pending"},
            limit=5,
        )

        # Should find test subitem
        tests = [item for item in ready_tests if item.item_key == "test"]
        assert len(tests) == 1
        assert tests[0].status.value == "pending"

    def test_complex_scenario_multiple_parents(self, manager_with_test_data):
        """Test complex scenario with multiple parent groups"""
        manager = manager_with_test_data

        # Add third parent with different subitems (unique keys)
        manager.add_item("test_list", "parent_task3", "Third parent task")
        manager.add_subtask("test_list", "parent_task3", "generate_v3", "Generate v3")
        manager.add_subtask("test_list", "parent_task3", "download_v3", "Download v3")

        # Set statuses for third parent
        manager.update_item_status("test_list", "generate_v3", status="in_progress")
        manager.update_item_status("test_list", "download_v3", status="pending")

        # Search for original conditions should still work
        results = manager.find_subitems_by_status(
            "test_list",
            {"generate": "completed", "download": "pending"},
            limit=10,
        )

        # Should only find from first parent (where generate is completed)
        assert len(results) == 2
        found_keys = {item.item_key for item in results}
        assert found_keys == {"generate", "download"}

        # Verify these are from the same parent group
        parent_ids = {item.parent_item_id for item in results}
        assert len(parent_ids) == 1  # Only one parent group


class TestFindSubitemsByStatusIntegration:
    """Integration tests with real database operations"""

    def test_with_status_synchronization(self, manager_with_test_data):
        """Test that search works correctly with status synchronization"""
        manager = manager_with_test_data

        # Initially: generate=completed, download=pending, process=pending
        # Parent should have status in_progress due to mixed children

        # Complete download - this should trigger parent sync
        manager.update_item_status("test_list", "download", status="completed")

        # Now search for completed downloads with completed generation
        results = manager.find_subitems_by_status(
            "test_list",
            {"generate": "completed", "download": "completed"},
            limit=10,
        )

        # Should find both
        assert len(results) == 2
        found_keys = {item.item_key for item in results}
        assert found_keys == {"generate", "download"}

    def test_large_dataset_performance(self, tmp_path):
        """Test performance with larger dataset"""
        db_path = tmp_path / "test_performance.db"
        manager = TodoManager(str(db_path))

        # Create test list
        manager.create_list("perf_test", "Performance Test List")

        # Create many parent tasks with subitems (unique keys)
        for i in range(20):
            parent_key = f"parent_{i}"
            manager.add_item("perf_test", parent_key, f"Parent task {i}")
            
            # Add subitems with unique keys
            manager.add_subtask("perf_test", parent_key, f"step1_{i}", f"Step 1 for {i}")
            manager.add_subtask("perf_test", parent_key, f"step2_{i}", f"Step 2 for {i}")
            manager.add_subtask("perf_test", parent_key, f"step3_{i}", f"Step 3 for {i}")

            # Set statuses for some groups
            if i % 3 == 0:
                manager.update_item_status("perf_test", f"step1_{i}", status="completed")
                manager.update_item_status("perf_test", f"step2_{i}", status="pending")
                manager.update_item_status("perf_test", f"step3_{i}", status="pending")

        # For this test, we need to search for specific conditions that exist
        # Let's search for one specific group we know exists (parent_0)
        results = manager.find_subitems_by_status(
            "perf_test",
            {"step1_0": "completed", "step2_0": "pending"},
            limit=50,
        )

        # Should find step1_0 and step2_0
        assert len(results) == 2
        found_keys = {item.item_key for item in results}
        assert found_keys == {"step1_0", "step2_0"}

        # Verify all results are correct
        for item in results:
            assert item.item_key in ["step1_0", "step2_0"]