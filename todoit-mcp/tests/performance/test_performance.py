"""
Performance tests for TODOIT MCP - testing system performance under various loads.

These tests identify performance bottlenecks, N+1 query problems, and
measure response times for core operations with large datasets.
"""

import os
import tempfile
import time
from typing import Any, Dict, List

import pytest

from core.manager import TodoManager
from core.models import ItemStatus


class TestPerformance:
    """Performance tests for core operations"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for performance tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_bulk_list_creation_performance(self, temp_manager):
        """Test performance of creating many lists"""
        num_lists = 100

        start_time = time.time()
        for i in range(num_lists):
            temp_manager.create_list(f"list{i}", f"Test List {i}")
        creation_time = time.time() - start_time

        # Should create 100 lists in reasonable time
        assert creation_time < 30.0  # 30 seconds max
        avg_time_per_list = creation_time / num_lists
        assert avg_time_per_list < 0.5  # 0.5 seconds per list max

        # Verify all lists were created
        lists = temp_manager.list_all()
        assert len(lists) == num_lists

    def test_bulk_item_creation_performance(self, temp_manager):
        """Test performance of creating many items in one list"""
        temp_manager.create_list("test", "Test List")
        num_items = 1000

        start_time = time.time()
        for i in range(num_items):
            temp_manager.add_item("test", f"task{i}", f"Task content {i}")
        creation_time = time.time() - start_time

        # Should create 1000 items in reasonable time
        assert creation_time < 60.0  # 1 minute max
        avg_time_per_item = creation_time / num_items
        assert avg_time_per_item < 0.1  # 0.1 seconds per item max

        # Verify all items were created
        items = temp_manager.get_list_items("test")
        assert len(items) == num_items

    def test_item_retrieval_performance(self, temp_manager):
        """Test performance of retrieving items from large list"""
        temp_manager.create_list("test", "Test List")
        num_items = 500

        # Create items
        for i in range(num_items):
            temp_manager.add_item("test", f"task{i}", f"Task {i}")

        # Test individual item retrieval
        start_time = time.time()
        for i in range(0, num_items, 10):  # Test every 10th item
            temp_manager.get_item("test", f"task{i}")
        retrieval_time = time.time() - start_time

        # Should retrieve 50 items quickly
        assert retrieval_time < 5.0  # 5 seconds max

        # Test bulk list retrieval
        start_time = time.time()
        all_items = temp_manager.get_list_items("test")
        bulk_retrieval_time = time.time() - start_time

        assert len(all_items) == num_items
        assert bulk_retrieval_time < 2.0  # 2 seconds max

    def test_next_pending_algorithm_performance(self, temp_manager):
        """Test performance of get_next_pending with large datasets"""
        temp_manager.create_list("test", "Test List")

        # Create complex hierarchy: 50 parents with 10 subtasks each
        num_parents = 50
        subtasks_per_parent = 10

        start_time = time.time()
        for i in range(num_parents):
            parent_key = f"parent{i}"
            temp_manager.add_item("test", parent_key, f"Parent Task {i}")

            for j in range(subtasks_per_parent):
                temp_manager.add_subitem(
                    "test", parent_key, f"child{i}_{j}", f"Child {i}-{j}"
                )
        setup_time = time.time() - start_time

        # Setup should be reasonable
        assert setup_time < 60.0  # 1 minute max

        # Test next pending algorithm performance
        start_time = time.time()
        processed_tasks = 0
        for _ in range(20):  # Test 20 consecutive next pending calls
            next_task = temp_manager.get_next_pending_with_subtasks("test")
            if next_task:
                try:
                    # Mark as in progress to test algorithm progression
                    temp_manager.update_item_status(
                        "test", next_task.item_key, ItemStatus.IN_PROGRESS
                    )
                    processed_tasks += 1
                except ValueError:
                    # Task might not be found due to hierarchy rules, skip
                    pass
        algorithm_time = time.time() - start_time

        # Algorithm should be fast even with 500+ items
        assert algorithm_time < 10.0  # 10 seconds max
        if processed_tasks > 0:
            avg_time_per_call = algorithm_time / 20
            assert avg_time_per_call < 0.5  # 0.5 seconds per call max

    def test_dependency_resolution_performance(self, temp_manager):
        """Test performance of dependency resolution with many dependencies"""
        # Create multiple lists
        num_lists = 10
        items_per_list = 20

        for i in range(num_lists):
            list_key = f"list{i}"
            temp_manager.create_list(list_key, f"List {i}")

            for j in range(items_per_list):
                temp_manager.add_item(list_key, f"task{j}", f"Task {j}")

        # Create complex dependency chain
        start_time = time.time()
        for i in range(num_lists - 1):
            for j in range(items_per_list):
                # Each item depends on corresponding item in previous list
                temp_manager.add_item_dependency(
                    f"list{i+1}",  # dependent_list
                    f"task{j}",  # dependent_item
                    f"list{i}",  # required_list
                    f"task{j}",  # required_item
                )
        dependency_creation_time = time.time() - start_time

        # Dependency creation should be reasonable
        assert dependency_creation_time < 30.0  # 30 seconds max

        # Test dependency checking performance
        start_time = time.time()
        for i in range(num_lists):
            for j in range(min(5, items_per_list)):  # Check first 5 items in each list
                next_task = temp_manager.get_next_pending(f"list{i}")
                # Don't need to do anything with result, just testing performance
        dependency_check_time = time.time() - start_time

        # Dependency checking should be fast
        assert dependency_check_time < 15.0  # 15 seconds max

    def test_property_operations_performance(self, temp_manager):
        """Test performance of property operations with many properties"""
        temp_manager.create_list("test", "Test List")
        num_items = 100
        properties_per_item = 10

        # Create items
        for i in range(num_items):
            temp_manager.add_item("test", f"task{i}", f"Task {i}")

        # Add many properties
        start_time = time.time()
        for i in range(num_items):
            for j in range(properties_per_item):
                temp_manager.set_item_property(
                    "test", f"task{i}", f"prop{j}", f"value{j}"
                )
        property_creation_time = time.time() - start_time

        # Property creation should be reasonable (1000 properties)
        assert property_creation_time < 60.0  # 1 minute max

        # Test property retrieval performance
        start_time = time.time()
        for i in range(0, num_items, 5):  # Test every 5th item
            for j in range(properties_per_item):
                temp_manager.get_item_property("test", f"task{i}", f"prop{j}")
        property_retrieval_time = time.time() - start_time

        # Property retrieval should be fast (200 retrievals)
        assert property_retrieval_time < 10.0  # 10 seconds max

        # Test property search performance
        start_time = time.time()
        results = temp_manager.find_items_by_property("test", "prop0", "value0")
        search_time = time.time() - start_time

        assert len(results) == num_items  # All items have prop0=value0
        assert search_time < 5.0  # 5 seconds max

    def test_tag_operations_performance(self, temp_manager):
        """Test performance of tag operations with many tags"""
        num_lists = 50
        num_tags = 20

        # Create lists
        for i in range(num_lists):
            temp_manager.create_list(f"list{i}", f"List {i}")

        # Create and assign tags
        start_time = time.time()
        for i in range(num_lists):
            for j in range(num_tags):
                tag_name = f"tag{j % 10}"  # Reuse tags across lists
                temp_manager.add_tag_to_list(f"list{i}", tag_name)
        tag_operations_time = time.time() - start_time

        # Tag operations should be reasonable (1000 assignments)
        assert tag_operations_time < 30.0  # 30 seconds max

        # Test tag filtering performance
        start_time = time.time()
        for i in range(10):  # Test filtering by first 10 tags
            lists = temp_manager.list_all(filter_tags=[f"tag{i}"])
            assert len(lists) > 0  # Should find lists with this tag
        filter_time = time.time() - start_time

        # Tag filtering should be fast
        assert filter_time < 5.0  # 5 seconds max

    def test_concurrent_operation_performance(self, temp_manager):
        """Test performance of operations that might cause concurrency issues"""
        temp_manager.create_list("test", "Test List")

        # Simulate rapid successive operations
        start_time = time.time()

        for i in range(50):
            # Rapid item creation and status changes
            temp_manager.add_item("test", f"task{i}", f"Task {i}")
            temp_manager.update_item_status("test", f"task{i}", ItemStatus.IN_PROGRESS)
            try:
                temp_manager.add_subitem("test", f"task{i}", f"sub{i}", f"Subtask {i}")
                temp_manager.update_item_status("test", f"sub{i}", ItemStatus.COMPLETED)
            except ValueError:
                # Subtask operations might fail, continue test
                pass

            # Parent should auto-complete
            parent = temp_manager.get_item("test", f"task{i}")
            # Don't assert status - just testing performance, not logic

        concurrent_time = time.time() - start_time

        # Rapid operations should complete in reasonable time
        assert concurrent_time < 60.0  # 1 minute max

        # Verify data integrity after rapid operations
        items = temp_manager.get_list_items("test")
        assert len(items) >= 50  # At least 50 parents, children may vary


class TestPerformanceBottlenecks:
    """Tests specifically targeting known performance bottlenecks"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for performance tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_n_plus_one_query_problem(self, temp_manager):
        """Test for N+1 query problems identified in code review"""
        temp_manager.create_list("test", "Test List")

        # Create hierarchy that could trigger N+1 queries
        num_parents = 20
        for i in range(num_parents):
            parent_key = f"parent{i}"
            temp_manager.add_item("test", parent_key, f"Parent {i}")
            # Add 5 children to each parent
            for j in range(5):
                temp_manager.add_subitem(
                    "test", parent_key, f"child{i}_{j}", f"Child {i}-{j}"
                )

        # This operation might trigger N+1 queries per the code review
        start_time = time.time()
        next_task = temp_manager.get_next_pending_with_subtasks("test")
        query_time = time.time() - start_time

        # Should not take excessive time even with complex hierarchy
        assert query_time < 5.0  # 5 seconds max
        assert next_task is not None

        # Test multiple consecutive calls (this is where N+1 shows up)
        start_time = time.time()
        for _ in range(10):
            temp_manager.get_next_pending_with_subtasks("test")
        batch_time = time.time() - start_time

        # Batch calls should not scale linearly (indicating N+1 problem)
        avg_time = batch_time / 10
        assert avg_time < 1.0  # Each call should be under 1 second

    def test_missing_index_performance(self, temp_manager):
        """Test operations that might suffer from missing database indexes"""
        temp_manager.create_list("test", "Test List")

        # Create many items with various statuses
        for i in range(200):
            temp_manager.add_item("test", f"task{i}", f"Task {i}")
            if i % 3 == 0:
                temp_manager.update_item_status(
                    "test", f"task{i}", ItemStatus.COMPLETED
                )
            elif i % 3 == 1:
                temp_manager.update_item_status(
                    "test", f"task{i}", ItemStatus.IN_PROGRESS
                )

        # Test status-based queries (might need composite indexes)
        start_time = time.time()
        pending_items = [
            item
            for item in temp_manager.get_list_items("test")
            if item.status == ItemStatus.PENDING
        ]
        status_query_time = time.time() - start_time

        assert len(pending_items) > 0
        assert status_query_time < 2.0  # Should be fast with proper indexing

        # Test position-based operations (might need indexes on parent_item_id + position)
        start_time = time.time()
        for i in range(10):
            # Operations that might scan by position
            temp_manager.get_next_pending("test")
        position_query_time = time.time() - start_time

        assert position_query_time < 5.0  # Should be fast with proper indexing

    def test_session_creation_overhead(self, temp_manager):
        """Test for excessive session creation overhead mentioned in code review"""
        temp_manager.create_list("test", "Test List")

        # Perform many small operations that might create separate sessions
        start_time = time.time()

        for i in range(100):
            # Each of these might create a new session
            temp_manager.add_item("test", f"task{i}", f"Task {i}")
            temp_manager.get_item("test", f"task{i}")
            temp_manager.set_item_property("test", f"task{i}", "priority", "normal")
            temp_manager.get_item_property("test", f"task{i}", "priority")

        session_overhead_time = time.time() - start_time

        # 400 operations should complete quickly if session overhead is minimal
        assert session_overhead_time < 30.0  # 30 seconds max
        avg_time_per_operation = session_overhead_time / 400
        assert avg_time_per_operation < 0.1  # 0.1 seconds per operation max


class TestMemoryPerformance:
    """Tests for memory usage and performance"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for memory tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_large_content_memory_usage(self, temp_manager):
        """Test memory performance with large item content"""
        temp_manager.create_list("test", "Test List")

        # Create items with large content within model limits
        large_content = "A" * 950  # 950 chars - within 1000 char limit

        start_time = time.time()
        for i in range(50):  # 50 * 950 chars
            temp_manager.add_item("test", f"task{i}", large_content)
        creation_time = time.time() - start_time

        # Should handle large content efficiently
        assert creation_time < 30.0  # 30 seconds max

        # Test retrieval of large content
        start_time = time.time()
        all_items = temp_manager.get_list_items("test")
        retrieval_time = time.time() - start_time

        assert len(all_items) == 50
        assert all(len(item.content) == 950 for item in all_items)
        assert retrieval_time < 5.0  # Should retrieve quickly

    def test_deep_hierarchy_memory(self, temp_manager):
        """Test memory performance with deep task hierarchies"""
        temp_manager.create_list("test", "Test List")

        # Create deep hierarchy (parent -> child -> grandchild)
        current_parent = "root"
        temp_manager.add_item("test", current_parent, "Root Task")

        start_time = time.time()
        for i in range(20):  # 20 levels deep
            child_key = f"level{i}"
            temp_manager.add_subitem(
                "test", current_parent, child_key, f"Task at level {i}"
            )
            current_parent = child_key
        hierarchy_creation_time = time.time() - start_time

        # Deep hierarchy should be created efficiently
        assert hierarchy_creation_time < 15.0  # 15 seconds max

        # Test traversal of deep hierarchy
        start_time = time.time()
        next_task = temp_manager.get_next_pending_with_subtasks("test")
        traversal_time = time.time() - start_time

        assert next_task is not None
        assert traversal_time < 2.0  # Should traverse efficiently


class TestListAllPerformanceRegression:
    """Specific tests for list_all command performance regression detection"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for list_all performance tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_list_all_bulk_optimization(self, temp_manager):
        """Test that list_all uses bulk operations and is fast"""
        # Create 50 lists with items and tags (realistic but testable size)
        for i in range(50):
            list_key = f"list_{i:03d}"
            temp_manager.create_list(list_key, f"Test List {i}")

            # Add items with various statuses
            for j in range(10):
                item_key = f"item_{j:02d}"
                temp_manager.add_item(list_key, item_key, f"Task {j} in list {i}")

                # Set different statuses
                if j < 3:
                    temp_manager.update_item_status(
                        list_key, item_key, ItemStatus.COMPLETED
                    )
                elif j < 5:
                    temp_manager.update_item_status(
                        list_key, item_key, ItemStatus.IN_PROGRESS
                    )
                elif j < 6:
                    temp_manager.update_item_status(
                        list_key, item_key, ItemStatus.FAILED
                    )
                # Rest remain pending

            # Add tags to create N+1 scenario
            if i % 10 == 0:
                temp_manager.add_tag_to_list(list_key, "important")
            if i % 20 == 0:
                temp_manager.add_tag_to_list(list_key, "urgent")

        # Test bulk operations directly
        lists = temp_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Test bulk progress (should use get_progress_bulk_minimal)
        start_time = time.time()
        progress_bulk = temp_manager.get_progress_bulk_minimal(list_keys)
        bulk_progress_time = time.time() - start_time

        # Test bulk tags (should use get_tags_for_lists_bulk)
        start_time = time.time()
        tags_bulk = temp_manager.get_tags_for_lists_bulk(list_keys)
        bulk_tags_time = time.time() - start_time

        # Both operations should be very fast
        assert (
            bulk_progress_time < 0.5
        ), f"Bulk progress took {bulk_progress_time:.3f}s, should be under 0.5s"
        assert (
            bulk_tags_time < 0.3
        ), f"Bulk tags took {bulk_tags_time:.3f}s, should be under 0.3s"

        # Verify we got data for all lists
        assert len(progress_bulk) == len(lists)
        assert len(tags_bulk) == len(lists)

        print(f"Bulk progress time for {len(lists)} lists: {bulk_progress_time:.3f}s")
        print(f"Bulk tags time for {len(lists)} lists: {bulk_tags_time:.3f}s")

    def test_list_all_no_n_plus_one(self, temp_manager):
        """Test that list_all doesn't have N+1 query problems"""
        # Create test data
        for i in range(30):
            list_key = f"test_list_{i}"
            temp_manager.create_list(list_key, f"Test List {i}")

            # Add items and tags to trigger potential N+1
            for j in range(5):
                temp_manager.add_item(list_key, f"item_{j}", f"Item {j}")

            temp_manager.add_tag_to_list(list_key, f"tag_{i % 5}")  # Shared tags

        # Simulate what CLI does (this is where N+1 would show up)
        start_time = time.time()

        # Get lists
        lists = temp_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Get progress and tags in bulk (optimized way)
        progress_by_key = temp_manager.get_progress_bulk_minimal(list_keys)
        tags_by_key = temp_manager.get_tags_for_lists_bulk(list_keys)

        # Simulate building display data
        display_data = []
        for todo_list in lists:
            progress = progress_by_key.get(todo_list.list_key)
            list_tags = tags_by_key.get(todo_list.list_key, [])

            record = {
                "key": todo_list.list_key,
                "title": todo_list.title,
                "pending": progress.pending if progress else 0,
                "completed": progress.completed if progress else 0,
                "tags": len(list_tags),
            }
            display_data.append(record)

        total_time = time.time() - start_time

        # Total operation should be very fast
        assert (
            total_time < 1.0
        ), f"list_all simulation took {total_time:.3f}s, should be under 1.0s"
        assert len(display_data) == len(lists)

        print(f"list_all simulation for {len(lists)} lists: {total_time:.3f}s")

    def test_individual_vs_bulk_performance(self, temp_manager):
        """Compare individual vs bulk operations to detect regressions"""
        # Create test data
        for i in range(20):
            list_key = f"perf_list_{i}"
            temp_manager.create_list(list_key, f"Performance List {i}")

            for j in range(8):
                temp_manager.add_item(list_key, f"item_{j}", f"Item {j}")
                if j < 2:
                    temp_manager.update_item_status(
                        list_key, f"item_{j}", ItemStatus.COMPLETED
                    )

            if i % 5 == 0:
                temp_manager.add_tag_to_list(list_key, "performance")

        lists = temp_manager.list_all()
        list_keys = [lst.list_key for lst in lists]

        # Test individual approach (old way that was slow)
        start_time = time.time()
        individual_progress = {}
        individual_tags = {}
        for list_key in list_keys[:10]:  # Only test subset to avoid timeout
            individual_progress[list_key] = temp_manager.get_progress(list_key)
            individual_tags[list_key] = temp_manager.get_tags_for_list(list_key)
        individual_time = time.time() - start_time

        # Test bulk approach (new optimized way)
        start_time = time.time()
        bulk_progress = temp_manager.get_progress_bulk_minimal(list_keys)
        bulk_tags = temp_manager.get_tags_for_lists_bulk(list_keys)
        bulk_time = time.time() - start_time

        # Bulk should be much faster
        estimated_individual_time = individual_time * len(list_keys) / 10
        improvement_ratio = (
            estimated_individual_time / bulk_time if bulk_time > 0 else float("inf")
        )

        print(f"Individual time for 10 lists: {individual_time:.3f}s")
        print(
            f"Estimated individual time for {len(list_keys)} lists: {estimated_individual_time:.3f}s"
        )
        print(f"Bulk time for {len(list_keys)} lists: {bulk_time:.3f}s")
        print(f"Performance improvement: {improvement_ratio:.1f}x faster")

        # Bulk should be at least 5x faster (realistic threshold)
        assert (
            improvement_ratio >= 5
        ), f"Bulk operations only {improvement_ratio:.1f}x faster, should be 5x+"

        # Verify results are equivalent for the subset we tested
        for list_key in list_keys[:10]:
            # Compare basic progress fields
            individual_prog = individual_progress[list_key]
            bulk_prog = bulk_progress[list_key]

            assert individual_prog.total == bulk_prog.total
            assert individual_prog.completed == bulk_prog.completed
            assert individual_prog.pending == bulk_prog.pending

            # Compare tags
            individual_tag_names = {tag.name for tag in individual_tags[list_key]}
            bulk_tag_names = {tag.name for tag in bulk_tags[list_key]}
            assert individual_tag_names == bulk_tag_names
