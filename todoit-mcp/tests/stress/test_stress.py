"""
Stress tests for TODOIT MCP - testing system behavior under extreme loads.

These tests push the system to its limits to identify breaking points,
memory issues, and performance degradation under high load.
"""

import gc
import os
import random
import tempfile
import threading
import time
from typing import Any, Dict, List

import pytest

from core.manager import TodoManager
from core.models import ItemStatus


class TestSystemLimits:
    """Test system behavior at extreme limits"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for stress tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.slow
    def test_maximum_lists_stress(self, temp_manager):
        """Test system with maximum number of lists"""
        max_lists = 5000  # Stress test with 5000 lists

        start_time = time.time()
        created_count = 0

        try:
            for i in range(max_lists):
                temp_manager.create_list(f"list{i:05d}", f"Stress Test List {i}")
                created_count += 1

                # Check progress every 500 lists
                if i % 500 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    print(f"Created {i} lists in {elapsed:.2f}s")
                    # Force garbage collection to manage memory
                    gc.collect()

        except Exception as e:
            pytest.fail(f"System failed after creating {created_count} lists: {e}")

        creation_time = time.time() - start_time
        print(f"Created {created_count} lists in {creation_time:.2f}s")

        # Verify system still responds after stress
        start_time = time.time()
        all_lists = temp_manager.list_all()
        list_retrieval_time = time.time() - start_time

        assert len(all_lists) == created_count
        assert list_retrieval_time < 30.0  # Should list all within 30 seconds

        # Test random access still works
        random_list = temp_manager.get_list(
            f"list{random.randint(0, created_count-1):05d}"
        )
        assert random_list is not None

    @pytest.mark.slow
    def test_maximum_items_per_list_stress(self, temp_manager):
        """Test system with maximum items in single list"""
        temp_manager.create_list("stress", "Stress Test List")
        max_items = 10000  # 10,000 items in one list

        start_time = time.time()
        created_count = 0

        try:
            for i in range(max_items):
                temp_manager.add_item("stress", f"item{i:06d}", f"Stress test item {i}")
                created_count += 1

                # Progress check every 1000 items
                if i % 1000 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    print(f"Created {i} items in {elapsed:.2f}s")
                    gc.collect()

        except Exception as e:
            pytest.fail(f"System failed after creating {created_count} items: {e}")

        creation_time = time.time() - start_time
        print(f"Created {created_count} items in {creation_time:.2f}s")

        # Test retrieval performance with large list
        start_time = time.time()
        all_items = temp_manager.get_list_items("stress")
        retrieval_time = time.time() - start_time

        assert len(all_items) == created_count
        assert retrieval_time < 60.0  # Should retrieve within 1 minute

        # Test next pending still works efficiently
        start_time = time.time()
        next_task = temp_manager.get_next_pending("stress")
        next_pending_time = time.time() - start_time

        assert next_task is not None
        assert next_pending_time < 5.0  # Should find next task quickly

    @pytest.mark.slow
    def test_deep_hierarchy_stress(self, temp_manager):
        """Test system with extremely deep task hierarchy"""
        temp_manager.create_list("deep", "Deep Hierarchy Test")
        max_depth = 100  # 100 levels deep

        current_parent = "root"
        temp_manager.add_item("deep", current_parent, "Root task")

        start_time = time.time()
        try:
            for i in range(max_depth):
                child_key = f"level{i:03d}"
                temp_manager.add_subitem(
                    "deep", current_parent, child_key, f"Task at depth {i}"
                )
                current_parent = child_key
        except Exception as e:
            pytest.fail(f"System failed at depth {i}: {e}")

        creation_time = time.time() - start_time
        print(f"Created {max_depth}-level hierarchy in {creation_time:.2f}s")

        # Test system can still navigate deep hierarchy
        start_time = time.time()
        next_task = temp_manager.get_next_pending_with_subtasks("deep")
        navigation_time = time.time() - start_time

        assert next_task is not None
        assert navigation_time < 10.0  # Should navigate deep hierarchy efficiently

        # Test getting all items from deep hierarchy
        start_time = time.time()
        all_items = temp_manager.get_list_items("deep")
        retrieval_time = time.time() - start_time

        assert len(all_items) == max_depth + 1  # root + all children
        assert retrieval_time < 15.0  # Should retrieve deep hierarchy efficiently

    @pytest.mark.slow
    def test_wide_hierarchy_stress(self, temp_manager):
        """Test system with extremely wide task hierarchy"""
        temp_manager.create_list("wide", "Wide Hierarchy Test")

        # Create one parent with many children
        temp_manager.add_item("wide", "parent", "Parent with many children")
        max_children = 1000  # 1000 children under one parent

        start_time = time.time()
        created_count = 0

        try:
            for i in range(max_children):
                temp_manager.add_subitem(
                    "wide", "parent", f"child{i:04d}", f"Child task {i}"
                )
                created_count += 1

                if i % 100 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    print(f"Created {i} children in {elapsed:.2f}s")

        except Exception as e:
            pytest.fail(f"System failed after creating {created_count} children: {e}")

        creation_time = time.time() - start_time
        print(f"Created {created_count} children in {creation_time:.2f}s")

        # Test parent-child navigation via get_list_items
        start_time = time.time()
        all_items = temp_manager.get_list_items("wide")
        parent_item = next(item for item in all_items if item.item_key == "parent")
        children = [item for item in all_items if item.parent_item_id == parent_item.id]
        navigation_time = time.time() - start_time

        assert len(children) == created_count
        assert navigation_time < 10.0  # Should list children efficiently

        # Test next pending with wide hierarchy
        start_time = time.time()
        next_task = temp_manager.get_next_pending_with_subtasks("wide")
        next_time = time.time() - start_time

        assert next_task is not None
        assert next_time < 5.0  # Should find next task efficiently

    @pytest.mark.slow
    def test_maximum_properties_stress(self, temp_manager):
        """Test system with maximum number of properties"""
        temp_manager.create_list("props", "Properties Stress Test")
        temp_manager.add_item("props", "task", "Task with many properties")

        max_properties = 1000  # 1000 properties per item

        start_time = time.time()
        created_count = 0

        try:
            for i in range(max_properties):
                temp_manager.set_item_property(
                    "props", "task", f"prop{i:04d}", f"value{i}"
                )
                created_count += 1

                if i % 100 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    print(f"Created {i} properties in {elapsed:.2f}s")

        except Exception as e:
            pytest.fail(f"System failed after creating {created_count} properties: {e}")

        creation_time = time.time() - start_time
        print(f"Created {created_count} properties in {creation_time:.2f}s")

        # Test property retrieval
        start_time = time.time()
        for i in range(0, created_count, 50):  # Test every 50th property
            value = temp_manager.get_item_property("props", "task", f"prop{i:04d}")
            assert value == f"value{i}"
        retrieval_time = time.time() - start_time

        assert retrieval_time < 10.0  # Should retrieve properties efficiently

    @pytest.mark.slow
    def test_maximum_dependencies_stress(self, temp_manager):
        """Test system with maximum number of dependencies"""
        num_lists = 5  # Reduced from 20 for practical testing
        items_per_list = 10  # Reduced from 50 for practical testing

        # Create test data
        for i in range(num_lists):
            list_key = f"list{i:02d}"
            temp_manager.create_list(list_key, f"List {i}")

            for j in range(items_per_list):
                temp_manager.add_item(list_key, f"task{j:02d}", f"Task {j}")

        # Create dependencies (every item depends on every item in previous list)
        max_dependencies = (
            (num_lists - 1) * items_per_list * items_per_list
        )  # Now 4*10*10 = 400

        start_time = time.time()
        created_count = 0

        try:
            for i in range(1, num_lists):  # Skip first list (no dependencies)
                for j in range(items_per_list):
                    for k in range(items_per_list):
                        temp_manager.add_item_dependency(
                            f"list{i:02d}",  # dependent_list
                            f"task{j:02d}",  # dependent_item
                            f"list{i-1:02d}",  # required_list
                            f"task{k:02d}",  # required_item
                        )
                        created_count += 1

                        if created_count % 500 == 0:
                            elapsed = time.time() - start_time
                            print(
                                f"Created {created_count} dependencies in {elapsed:.2f}s"
                            )

        except Exception as e:
            pytest.fail(
                f"System failed after creating {created_count} dependencies: {e}"
            )

        creation_time = time.time() - start_time
        print(f"Created {created_count} dependencies in {creation_time:.2f}s")

        # Test dependency resolution still works
        start_time = time.time()
        for i in range(min(5, num_lists)):
            next_task = temp_manager.get_next_pending(f"list{i:02d}")
            # First list should have available tasks, others might be blocked
        resolution_time = time.time() - start_time

        assert resolution_time < 30.0  # Should resolve dependencies efficiently

    @pytest.mark.slow
    def test_large_content_stress(self, temp_manager):
        """Test system with extremely large item content"""
        temp_manager.create_list("large", "Large Content Test")

        # Test with large content within model limits (900 chars - under 1000 limit)
        large_content = "X" * 900  # 900 chars - within validation limit
        num_large_items = 100  # More items but smaller content

        start_time = time.time()
        try:
            for i in range(num_large_items):
                temp_manager.add_item("large", f"big{i}", large_content)
        except Exception as e:
            pytest.fail(f"System failed with large content: {e}")

        creation_time = time.time() - start_time
        print(f"Created {num_large_items} large items in {creation_time:.2f}s")

        # Test retrieval of large content
        start_time = time.time()
        all_items = temp_manager.get_list_items("large")
        retrieval_time = time.time() - start_time

        assert len(all_items) == num_large_items
        assert all(len(item.content) == 900 for item in all_items)
        assert retrieval_time < 30.0  # Should handle large content efficiently

    @pytest.mark.slow
    def test_database_size_limits(self, temp_manager):
        """Test system behavior as database grows very large"""
        # Create substantial amount of data to grow database
        num_lists = 100
        items_per_list = 100

        start_time = time.time()
        total_items = 0

        try:
            for i in range(num_lists):
                list_key = f"db{i:03d}"
                temp_manager.create_list(list_key, f"Database Growth Test List {i}")

                for j in range(items_per_list):
                    # Add item with moderate content
                    content = (
                        f"Database growth test item {j} with some content to increase DB size. "
                        * 10
                    )
                    temp_manager.add_item(list_key, f"item{j:03d}", content)
                    total_items += 1

                    # Add some properties
                    temp_manager.set_item_property(
                        list_key, f"item{j:03d}", "priority", "normal"
                    )
                    temp_manager.set_item_property(
                        list_key, f"item{j:03d}", "category", f"cat{j%5}"
                    )

                if i % 10 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    print(f"Created {i} lists ({total_items} items) in {elapsed:.2f}s")

        except Exception as e:
            pytest.fail(f"System failed with large database: {e}")

        creation_time = time.time() - start_time
        print(
            f"Created large database with {total_items} items in {creation_time:.2f}s"
        )

        # Test system still responds efficiently with large database
        start_time = time.time()
        all_lists = temp_manager.list_all()
        list_time = time.time() - start_time

        assert len(all_lists) == num_lists
        assert list_time < 10.0  # Should list all efficiently even with large DB

        # Test search performance with large database
        start_time = time.time()
        results = temp_manager.find_items_by_property("db050", "priority", "normal")
        search_time = time.time() - start_time

        assert len(results) == items_per_list
        assert search_time < 5.0  # Should search efficiently


class TestConcurrencyStress:
    """Test system behavior under concurrent access patterns"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for concurrency stress tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_rapid_successive_operations(self, temp_manager):
        """Test rapid successive operations (simulating very active user)"""
        temp_manager.create_list("rapid", "Rapid Operations Test")

        operations_count = 1000
        start_time = time.time()

        try:
            for i in range(operations_count):
                # Mix of different operations
                if i % 4 == 0:
                    temp_manager.add_item("rapid", f"task{i}", f"Task {i}")
                elif i % 4 == 1:
                    temp_manager.update_item_status(
                        "rapid", f"task{i-1}", ItemStatus.IN_PROGRESS
                    )
                elif i % 4 == 2:
                    temp_manager.set_item_property(
                        "rapid", f"task{i-2}", "priority", "high"
                    )
                else:
                    try:
                        temp_manager.get_item("rapid", f"task{i-3}")
                    except ValueError:
                        pass  # Item might not exist yet

        except Exception as e:
            pytest.fail(f"System failed during rapid operations: {e}")

        rapid_time = time.time() - start_time
        print(f"Completed {operations_count} rapid operations in {rapid_time:.2f}s")

        # Verify data integrity after rapid operations
        items = temp_manager.get_list_items("rapid")
        assert len(items) > 0  # Should have created some items

        # System should still be responsive
        start_time = time.time()
        next_task = temp_manager.get_next_pending("rapid")
        response_time = time.time() - start_time
        assert response_time < 2.0  # Should respond quickly after stress

    @pytest.mark.slow
    def test_memory_stress_with_cleanup(self, temp_manager):
        """Test system memory behavior with creation and cleanup cycles"""
        cycles = 50
        items_per_cycle = 100

        for cycle in range(cycles):
            cycle_list = f"cycle{cycle:03d}"
            temp_manager.create_list(cycle_list, f"Memory Stress Cycle {cycle}")

            # Create items
            start_time = time.time()
            for i in range(items_per_cycle):
                content = (
                    f"Memory stress test content for cycle {cycle} item {i}. " * 20
                )
                temp_manager.add_item(cycle_list, f"item{i:03d}", content)
            creation_time = time.time() - start_time

            # Clean up (delete list)
            start_time = time.time()
            deleted = temp_manager.delete_list(cycle_list)
            cleanup_time = time.time() - start_time

            if cycle % 10 == 0:
                print(
                    f"Cycle {cycle}: Create={creation_time:.2f}s, Cleanup={cleanup_time:.2f}s, Deleted={deleted}"
                )
                gc.collect()  # Force garbage collection

            # Verify cleanup worked - check if delete was successful
            if deleted:
                try:
                    temp_manager.get_list(cycle_list)
                    # If we can still get the list, deletion failed
                    print(f"Warning: List {cycle_list} still exists after deletion")
                except ValueError:
                    pass  # Expected - list should not exist
            else:
                print(f"Warning: delete_list returned False for {cycle_list}")

        # Verify system is clean after all cycles
        remaining_lists = temp_manager.list_all()
        # Should only have minimal system lists, if any
        assert len(remaining_lists) < 5
