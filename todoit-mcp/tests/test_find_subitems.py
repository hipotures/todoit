"""
Tests for find_items_by_status functionality (legacy subitem format)
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

    # Create parent item
    parent = manager.add_item("test_list", "parent_task", "Parent item for testing")

    # Create subitems with different statuses
    manager.add_subitem("test_list", "parent_task", "generate", "Generate image")
    manager.add_subitem("test_list", "parent_task", "download", "Download image")
    manager.add_subitem("test_list", "parent_task", "process", "Process image")

    # Create second parent with different subitems
    parent2 = manager.add_item("test_list", "parent_task2", "Second parent item")
    manager.add_subitem("test_list", "parent_task2", "design", "Design feature")
    manager.add_subitem("test_list", "parent_task2", "code", "Write code")
    manager.add_subitem("test_list", "parent_task2", "test", "Write tests")

    # Set some initial statuses
    manager.update_item_status(
        "test_list", "generate", status="completed", parent_item_key="parent_task"
    )
    manager.update_item_status(
        "test_list", "download", status="pending", parent_item_key="parent_task"
    )
    manager.update_item_status(
        "test_list", "process", status="pending", parent_item_key="parent_task"
    )

    manager.update_item_status(
        "test_list", "design", status="completed", parent_item_key="parent_task2"
    )
    manager.update_item_status(
        "test_list", "code", status="completed", parent_item_key="parent_task2"
    )
    manager.update_item_status(
        "test_list", "test", status="pending", parent_item_key="parent_task2"
    )

    return manager


class TestFindSubitemsByStatus:
    """Test the find_items_by_status functionality (legacy format)"""

    def test_basic_search_single_condition(self, manager_with_test_data):
        """Test basic search with single condition"""
        manager = manager_with_test_data

        # Find subitems where generate is completed
        matches = manager.find_items_by_status(
            {"generate": "completed"}, "test_list", limit=10
        )

        # Should find one parent group with generate subitem
        assert len(matches) == 1
        assert matches[0]["parent"].item_key == "parent_task"
        assert len(matches[0]["matching_subitems"]) == 1
        assert matches[0]["matching_subitems"][0].item_key == "generate"
        assert matches[0]["matching_subitems"][0].status.value == "completed"

    def test_search_multiple_conditions(self, manager_with_test_data):
        """Test search with multiple conditions"""
        manager = manager_with_test_data

        # Find subitems where generate is completed AND download is pending
        matches = manager.find_items_by_status({"generate": "completed", "download": "pending"}, "test_list", limit=10)

        # Should find one parent group with both generate and download subitems
        assert len(matches) == 1
        assert matches[0]["parent"].item_key == "parent_task"
        assert len(matches[0]["matching_subitems"]) == 2
        found_keys = {item.item_key for item in matches[0]["matching_subitems"]}
        assert found_keys == {"generate", "download"}

    def test_search_with_failing_conditions(self, manager_with_test_data):
        """Test search where conditions are not met"""
        manager = manager_with_test_data

        # Look for conditions that don't exist
        matches = manager.find_items_by_status(
            {"generate": "failed", "download": "completed"}, "test_list", limit=10
        )

        # Should find nothing
        assert len(matches) == 0

    def test_search_different_parent_groups(self, manager_with_test_data):
        """Test that search works across different parent groups"""
        manager = manager_with_test_data

        # Find subitems where design and code are both completed
        matches = manager.find_items_by_status({"design": "completed", "code": "completed"}, "test_list", limit=10)

        # Should find one parent group with design and code subitems from second parent
        assert len(matches) == 1
        assert matches[0]["parent"].item_key == "parent_task2"
        assert len(matches[0]["matching_subitems"]) == 2
        found_keys = {item.item_key for item in matches[0]["matching_subitems"]}
        assert found_keys == {"design", "code"}

    def test_search_with_limit(self, manager_with_test_data):
        """Test that limit parameter works correctly"""
        manager = manager_with_test_data

        # Find with limit of 1
        matches = manager.find_items_by_status({"generate": "completed"}, "test_list", limit=1)

        assert len(matches) == 1

    def test_search_nonexistent_list(self, manager_with_test_data):
        """Test search on non-existent list raises error"""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.find_items_by_status({"generate": "completed"}, "nonexistent", limit=10)

    def test_search_empty_conditions(self, manager_with_test_data):
        """Test search with empty conditions raises error"""
        manager = manager_with_test_data

        with pytest.raises(ValueError, match="Conditions dictionary cannot be empty"):
            manager.find_items_by_status({}, "test_list", limit=10)

    def test_search_ordering_by_item_key(self, manager_with_test_data):
        """Test that results are ordered naturally by item_key"""
        manager = manager_with_test_data

        # Find multiple subitems
        matches = manager.find_items_by_status({"generate": "completed", "download": "pending", "process": "pending"}, "test_list", limit=10)

        # Should find one parent group with 3 matching subitems ordered naturally by item_key
        assert len(matches) == 1
        assert len(matches[0]["matching_subitems"]) == 3
        item_keys = [item.item_key for item in matches[0]["matching_subitems"]]
        # Natural sort order should be maintained (e.g., "download", "generate", "process" alphabetically)
        expected_keys = sorted(item_keys, key=lambda x: manager.db.natural_sort_key(x))
        assert item_keys == expected_keys

    def test_workflow_scenario_image_processing(self, manager_with_test_data):
        """Test realistic workflow scenario for image processing"""
        manager = manager_with_test_data

        # Scenario: Find downloads ready to process (generation completed)
        ready_matches = manager.find_items_by_status({"generate": "completed", "download": "pending"}, "test_list", limit=5)

        # Should find one parent group with download subitem
        assert len(ready_matches) == 1
        matching_subitems = ready_matches[0]["matching_subitems"]
        downloads = [item for item in matching_subitems if item.item_key == "download"]
        assert len(downloads) == 1
        assert downloads[0].status.value == "pending"

    def test_workflow_scenario_development(self, manager_with_test_data):
        """Test realistic workflow scenario for development tasks"""
        manager = manager_with_test_data

        # Scenario: Find tests ready to run (design and code completed)
        ready_matches = manager.find_items_by_status({"design": "completed", "code": "completed", "test": "pending"}, "test_list", limit=5)

        # Should find one parent group with test subitem
        assert len(ready_matches) == 1
        matching_subitems = ready_matches[0]["matching_subitems"]
        tests = [item for item in matching_subitems if item.item_key == "test"]
        assert len(tests) == 1
        assert tests[0].status.value == "pending"

    def test_complex_scenario_multiple_parents(self, manager_with_test_data):
        """Test complex scenario with multiple parent groups"""
        manager = manager_with_test_data

        # Add third parent with different subitems (unique keys)
        manager.add_item("test_list", "parent_task3", "Third parent item")
        manager.add_subitem("test_list", "parent_task3", "generate_v3", "Generate v3")
        manager.add_subitem("test_list", "parent_task3", "download_v3", "Download v3")

        # Set statuses for third parent
        manager.update_item_status(
            "test_list",
            "generate_v3",
            status="in_progress",
            parent_item_key="parent_task3",
        )
        manager.update_item_status(
            "test_list", "download_v3", status="pending", parent_item_key="parent_task3"
        )

        # Search for original conditions should still work
        matches = manager.find_items_by_status({"generate": "completed", "download": "pending"}, "test_list", limit=10)

        # Should only find one parent group (where generate is completed)
        assert len(matches) == 1
        assert matches[0]["parent"].item_key == "parent_task"
        assert len(matches[0]["matching_subitems"]) == 2
        found_keys = {item.item_key for item in matches[0]["matching_subitems"]}
        assert found_keys == {"generate", "download"}

        # Verify these are from the same parent group (inherently true with new structure)
        parent_ids = {item.parent_item_id for item in matches[0]["matching_subitems"]}
        assert len(parent_ids) == 1  # Only one parent group


class TestFindSubitemsByStatusIntegration:
    """Integration tests with real database operations"""

    def test_with_status_synchronization(self, manager_with_test_data):
        """Test that search works correctly with status synchronization"""
        manager = manager_with_test_data

        # Initially: generate=completed, download=pending, process=pending
        # Parent should have status in_progress due to mixed children

        # Complete download - this should trigger parent sync
        manager.update_item_status(
            "test_list", "download", status="completed", parent_item_key="parent_task"
        )

        # Now search for completed downloads with completed generation
        matches = manager.find_items_by_status({"generate": "completed", "download": "completed"}, "test_list", limit=10)

        # Should find one parent group with both subitems
        assert len(matches) == 1
        assert len(matches[0]["matching_subitems"]) == 2
        found_keys = {item.item_key for item in matches[0]["matching_subitems"]}
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
            manager.add_item("perf_test", parent_key, f"Parent item {i}")

            # Add subitems with unique keys
            manager.add_subitem(
                "perf_test", parent_key, f"step1_{i}", f"Step 1 for {i}"
            )
            manager.add_subitem(
                "perf_test", parent_key, f"step2_{i}", f"Step 2 for {i}"
            )
            manager.add_subitem(
                "perf_test", parent_key, f"step3_{i}", f"Step 3 for {i}"
            )

            # Set statuses for some groups
            if i % 3 == 0:
                manager.update_item_status(
                    "perf_test",
                    f"step1_{i}",
                    status="completed",
                    parent_item_key=parent_key,
                )
                manager.update_item_status(
                    "perf_test",
                    f"step2_{i}",
                    status="pending",
                    parent_item_key=parent_key,
                )
                manager.update_item_status(
                    "perf_test",
                    f"step3_{i}",
                    status="pending",
                    parent_item_key=parent_key,
                )

        # For this test, we need to search for specific conditions that exist
        # Let's search for one specific group we know exists (parent_0)
        matches = manager.find_items_by_status({"step1_0": "completed", "step2_0": "pending"}, "perf_test", limit=50)

        # Should find one parent group with step1_0 and step2_0
        assert len(matches) == 1
        assert matches[0]["parent"].item_key == "parent_0"
        assert len(matches[0]["matching_subitems"]) == 2
        found_keys = {item.item_key for item in matches[0]["matching_subitems"]}
        assert found_keys == {"step1_0", "step2_0"}

        # Verify all results are correct
        for item in matches[0]["matching_subitems"]:
            assert item.item_key in ["step1_0", "step2_0"]
