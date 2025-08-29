"""
Performance tests for todoit list all command and bulk operations.
These tests ensure that bulk operations remain fast and detect performance regressions.
"""

import os
import tempfile
import time

import pytest

from core.manager import TodoManager


class TestListAllPerformance:
    """Test performance of list all command and related bulk operations"""

    @pytest.fixture
    def large_manager(self):
        """Create a manager with many lists and items for performance testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)

            # Create 100 lists with 20 items each (2000 total items)
            # This should be enough to detect N+1 query problems
            for list_idx in range(100):
                list_key = f"perf_list_{list_idx:03d}"
                list_title = f"Performance Test List {list_idx}"

                # Create list
                manager.create_list(list_key, list_title)

                # Add items with various statuses
                for item_idx in range(20):
                    item_key = f"item_{item_idx:02d}"
                    content = f"Test item {item_idx} in list {list_idx}"

                    manager.add_item(list_key, item_key, content)

                    # Set different statuses to test aggregation
                    if item_idx < 5:
                        manager.update_item_status(list_key, item_key, "completed")
                    elif item_idx < 8:
                        manager.update_item_status(list_key, item_key, "in_progress")
                    elif item_idx < 10:
                        manager.update_item_status(list_key, item_key, "failed")
                    # Rest remain pending

                # Add tags to some lists for tag performance testing
                if list_idx % 10 == 0:
                    manager.add_tag_to_list(list_key, "performance")
                if list_idx % 20 == 0:
                    manager.add_tag_to_list(list_key, "bulk_test")

            yield manager

        finally:
            try:
                os.unlink(db_path)
            except:
                pass

    def test_bulk_progress_performance(self, large_manager):
        """Test that bulk progress fetching is fast"""
        # Get all list keys
        lists = large_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Test bulk method
        start_time = time.time()
        progress_bulk = large_manager.get_progress_bulk_minimal(list_keys)
        bulk_time = time.time() - start_time

        # Test individual method for comparison
        start_time = time.time()
        progress_individual = {}
        for list_key in list_keys[:10]:  # Only test first 10 to avoid timeout
            progress_individual[list_key] = large_manager.get_progress(list_key)
        individual_time = time.time() - start_time

        # Bulk should be much faster
        print(f"Bulk progress time for {len(list_keys)} lists: {bulk_time:.3f}s")
        print(f"Individual progress time for 10 lists: {individual_time:.3f}s")
        print(
            f"Estimated individual time for all lists: {individual_time * len(list_keys) / 10:.3f}s"
        )

        # Bulk should complete in under 1 second for 100 lists
        assert (
            bulk_time < 1.0
        ), f"Bulk progress took {bulk_time:.3f}s, should be under 1.0s"

        # Verify results are equivalent (test a few lists)
        for list_key in list_keys[:5]:
            bulk_stats = progress_bulk[list_key]
            individual_stats = large_manager.get_progress(list_key)

            # Compare basic stats (minimal version doesn't have all fields)
            assert bulk_stats.total == individual_stats.total
            assert bulk_stats.completed == individual_stats.completed
            assert bulk_stats.in_progress == individual_stats.in_progress
            assert bulk_stats.pending == individual_stats.pending
            assert bulk_stats.failed == individual_stats.failed
            assert (
                abs(
                    bulk_stats.completion_percentage
                    - individual_stats.completion_percentage
                )
                < 0.1
            )

    def test_bulk_tags_performance(self, large_manager):
        """Test that bulk tag fetching is fast"""
        # Get all list keys
        lists = large_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Test bulk method
        start_time = time.time()
        tags_bulk = large_manager.get_tags_for_lists_bulk(list_keys)
        bulk_time = time.time() - start_time

        # Test individual method for comparison
        start_time = time.time()
        tags_individual = {}
        for list_key in list_keys[:10]:  # Only test first 10 to avoid timeout
            tags_individual[list_key] = large_manager.get_tags_for_list(list_key)
        individual_time = time.time() - start_time

        # Bulk should be much faster
        print(f"Bulk tags time for {len(list_keys)} lists: {bulk_time:.3f}s")
        print(f"Individual tags time for 10 lists: {individual_time:.3f}s")
        print(
            f"Estimated individual time for all lists: {individual_time * len(list_keys) / 10:.3f}s"
        )

        # Bulk should complete in under 0.5 seconds for 100 lists
        assert bulk_time < 0.5, f"Bulk tags took {bulk_time:.3f}s, should be under 0.5s"

        # Verify results are equivalent (test a few lists)
        for list_key in list_keys[:5]:
            bulk_tags = tags_bulk[list_key]
            individual_tags = large_manager.get_tags_for_list(list_key)

            # Should have same number of tags
            assert len(bulk_tags) == len(individual_tags)

            # Should have same tag names and colors
            bulk_names = {tag.name: tag.color for tag in bulk_tags}
            individual_names = {tag.name: tag.color for tag in individual_tags}
            assert bulk_names == individual_names

    def test_database_bulk_operations_performance(self, large_manager):
        """Test that database-level bulk operations are fast"""
        # Get list IDs for testing
        lists = large_manager.list_all()
        list_ids = [lst.id for lst in lists]

        # Test bulk status counts
        start_time = time.time()
        status_counts = large_manager.db.get_status_counts_for_lists(list_ids)
        status_time = time.time() - start_time

        print(
            f"Database status counts time for {len(list_ids)} lists: {status_time:.3f}s"
        )
        assert (
            status_time < 0.1
        ), f"Database status counts took {status_time:.3f}s, should be under 0.1s"

        # Test bulk tags
        start_time = time.time()
        tags_by_list = large_manager.db.get_tags_for_lists(list_ids)
        tags_time = time.time() - start_time

        print(f"Database tags time for {len(list_ids)} lists: {tags_time:.3f}s")
        assert (
            tags_time < 0.1
        ), f"Database tags took {tags_time:.3f}s, should be under 0.1s"

        # Verify we got data for all lists
        assert len(status_counts) == len(list_ids)
        assert len(tags_by_list) == len(list_ids)

        # Verify status counts structure
        for list_id, counts in status_counts.items():
            assert isinstance(counts, dict)
            assert all(
                key in counts
                for key in ["pending", "in_progress", "completed", "failed"]
            )
            assert all(isinstance(count, int) for count in counts.values())

    def test_list_all_overall_performance(self, large_manager):
        """Test overall performance of list_all operation using bulk methods"""
        # This simulates what the CLI does

        start_time = time.time()

        # Get all lists
        lists = large_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Bulk fetch progress and tags (like optimized CLI does)
        progress_by_key = large_manager.get_progress_bulk_minimal(list_keys)
        tags_by_key = large_manager.get_tags_for_lists_bulk(list_keys)

        # Simulate building the display data
        data = []
        for todo_list in lists:
            progress = progress_by_key.get(todo_list.list_key)
            list_tags = tags_by_key.get(todo_list.list_key, [])

            # Simulate the data structure CLI builds
            record = {
                "ID": str(todo_list.id),
                "Key": todo_list.list_key,
                "Title": todo_list.title,
                "Tags": len(list_tags),
                "Pending": progress.pending if progress else 0,
                "InProgress": progress.in_progress if progress else 0,
                "Completed": progress.completed if progress else 0,
                "Failed": progress.failed if progress else 0,
                "Percentage": (
                    f"{progress.completion_percentage:.0f}%" if progress else "0%"
                ),
            }
            data.append(record)

        total_time = time.time() - start_time

        print(
            f"Total list_all simulation time for {len(lists)} lists: {total_time:.3f}s"
        )
        print(f"Average time per list: {total_time / len(lists) * 1000:.1f}ms")

        # Should complete in under 2 seconds for 100 lists
        assert (
            total_time < 2.0
        ), f"List all simulation took {total_time:.3f}s, should be under 2.0s"

        # Should have data for all lists
        assert len(data) == len(lists)

        # Verify data structure
        for record in data[:5]:  # Check first 5
            assert all(
                key in record
                for key in ["ID", "Key", "Title", "Tags", "Pending", "Completed"]
            )

    def test_performance_regression_detection(self, large_manager):
        """Test to detect if performance regresses (e.g., missing indexes)"""
        lists = large_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Test multiple operations to ensure consistent performance
        times = []
        for _ in range(3):
            start_time = time.time()
            progress_by_key = large_manager.get_progress_bulk_minimal(list_keys)
            tags_by_key = large_manager.get_tags_for_lists_bulk(list_keys)
            times.append(time.time() - start_time)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"Performance regression test:")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Times: {[f'{t:.3f}s' for t in times]}")

        # Performance should be consistent and fast
        assert (
            avg_time < 1.0
        ), f"Average time {avg_time:.3f}s indicates performance regression"
        assert (
            max_time < 1.5
        ), f"Max time {max_time:.3f}s indicates performance regression"

        # Times shouldn't vary too much (indicates caching/index issues)
        time_variation = max_time - min(times)
        assert (
            time_variation < 0.5
        ), f"Time variation {time_variation:.3f}s indicates inconsistent performance"


class TestBulkOperationsCorrectness:
    """Test that bulk operations return correct results"""

    @pytest.fixture
    def test_manager(self):
        """Create a small test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)

            # Create 3 test lists
            for i in range(3):
                list_key = f"test_list_{i}"
                manager.create_list(list_key, f"Test List {i}")

                # Add items with known statuses
                manager.add_item(list_key, "item1", "First item")
                manager.add_item(list_key, "item2", "Second item")
                manager.add_item(list_key, "item3", "Third item")

                # Set specific statuses
                manager.update_item_status(list_key, "item1", "completed")
                manager.update_item_status(list_key, "item2", "in_progress")
                # item3 remains pending

                # Add tags
                if i == 0:
                    manager.add_tag_to_list(list_key, "urgent")
                elif i == 1:
                    manager.add_tag_to_list(list_key, "urgent")
                    manager.add_tag_to_list(list_key, "review")
                # list 2 has no tags

            yield manager

        finally:
            try:
                os.unlink(db_path)
            except:
                pass

    def test_bulk_progress_correctness(self, test_manager):
        """Test that bulk progress returns same results as individual calls"""
        lists = test_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Get results both ways
        bulk_results = test_manager.get_progress_bulk_minimal(list_keys)
        individual_results = {}
        for list_key in list_keys:
            individual_results[list_key] = test_manager.get_progress(list_key)

        # Compare results
        for list_key in list_keys:
            bulk = bulk_results[list_key]
            individual = individual_results[list_key]

            assert bulk.total == individual.total == 3
            assert bulk.completed == individual.completed == 1
            assert bulk.in_progress == individual.in_progress == 1
            assert bulk.pending == individual.pending == 1
            assert bulk.failed == individual.failed == 0
            assert (
                abs(bulk.completion_percentage - individual.completion_percentage) < 0.1
            )

    def test_bulk_tags_correctness(self, test_manager):
        """Test that bulk tags return same results as individual calls"""
        lists = test_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Get results both ways
        bulk_results = test_manager.get_tags_for_lists_bulk(list_keys)
        individual_results = {}
        for list_key in list_keys:
            individual_results[list_key] = test_manager.get_tags_for_list(list_key)

        # Compare results
        for list_key in list_keys:
            bulk_tags = bulk_results[list_key]
            individual_tags = individual_results[list_key]

            # Same number of tags
            assert len(bulk_tags) == len(individual_tags)

            # Same tag details
            bulk_data = [(tag.name, tag.color) for tag in bulk_tags]
            individual_data = [(tag.name, tag.color) for tag in individual_tags]
            assert sorted(bulk_data) == sorted(individual_data)
