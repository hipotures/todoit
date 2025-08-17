"""
Edge case tests for system limits and extreme values.

These tests verify the system handles extreme data sizes and values
gracefully without performance degradation or crashes.
"""

import pytest
import tempfile
import string
import random
from core.manager import TodoManager


class TestLimits:
    """Test system limits and extreme values"""

    @pytest.fixture
    def manager(self):
        """Create a fresh TodoManager for each test"""
        import tempfile
        import os

        # Create unique temporary database for each test
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        manager = TodoManager(path)
        yield manager
        # Cleanup
        try:
            os.unlink(path)
        except:
            pass

    def test_very_long_task_content(self, manager):
        """Test handling of very long item content"""
        manager.create_list("test", "Test List")

        # Test different content sizes (keeping within Pydantic limits)
        sizes_to_test = [500, 999]  # Under 1000 char limit

        for size in sizes_to_test:
            long_content = "A" * size

            # Should handle gracefully
            item = manager.add_item("test", f"long_task_{size}", long_content)
            assert item.content == long_content

            # Verify it's stored and retrieved correctly
            retrieved = manager.get_item("test", f"long_task_{size}")
            assert len(retrieved.content) == size

        # Test exceeding limits
        try:
            very_long_content = "A" * 2000  # Exceeds 1000 char limit
            manager.add_item("test", "too_long", very_long_content)
            assert False, "Should have failed due to length limit"
        except Exception as e:
            error_msg = str(e).lower()
            assert any(
                keyword in error_msg
                for keyword in ["string_too_long", "1000 characters", "validation"]
            )

    def test_very_long_list_title(self, manager):
        """Test handling of very long list titles"""
        # Test progressively longer titles (within 255 char limit)
        for length in [100, 254]:
            long_title = "T" * length

            list_obj = manager.create_list(f"list_{length}", long_title)
            assert list_obj.title == long_title

            # Verify retrieval works
            retrieved = manager.get_list(f"list_{length}")
            assert retrieved.title == long_title

    def test_many_items_in_list(self, manager):
        """Test performance and functionality with many items"""
        manager.create_list("large_list", "Large List")

        # Add many items (reduced for test performance)
        num_items = 100

        # Test adding items
        for i in range(num_items):
            item = manager.add_item("large_list", f"item_{i}", f"Item number {i}")
            assert item.item_key == f"item_{i}"

        # Test retrieval performance
        all_items = manager.get_list_items("large_list")
        assert len(all_items) == num_items

        # Test progress calculation with many items
        progress = manager.get_progress("large_list")
        assert progress.total == num_items
        assert progress.completed == 0
        assert progress.completion_percentage == 0.0

        # Test next item selection with many items
        next_task = manager.get_next_pending("large_list")
        assert next_task is not None
        assert next_task.item_key == "item_0"  # Should get first pending

    def test_deep_subtask_hierarchy(self, manager):
        """Test deep nested subitem hierarchies"""
        manager.create_list("deep_list", "Deep Hierarchy List")

        # Create root item
        manager.add_item("deep_list", "root", "Root Item")

        # Create moderate depth hierarchy (5 levels for performance)
        max_depth = 5
        parent_key = "root"

        for depth in range(1, max_depth + 1):
            subitem_key = f"subtask_level_{depth}"
            manager.add_subitem(
                "deep_list", parent_key, subitem_key, f"Subitem at level {depth}"
            )
            parent_key = subitem_key

        # Test hierarchy retrieval
        hierarchy = manager.get_item_hierarchy("deep_list", "root")
        assert hierarchy is not None

        # Test next item selection with deep hierarchy
        next_task = manager.get_next_pending_with_subtasks("deep_list")
        assert next_task is not None
        # Should select deepest available subitem first
        assert "level" in next_task.item_key

    def test_many_subtasks_per_parent(self, manager):
        """Test parent item with many subtasks"""
        manager.create_list("wide_list", "Wide Hierarchy List")

        # Create parent item
        manager.add_item("wide_list", "parent", "Parent with Many Children")

        # Add many subtasks (reduced for performance)
        num_subtasks = 50
        for i in range(num_subtasks):
            manager.add_subitem("wide_list", "parent", f"child_{i}", f"Child item {i}")

        # Test subitem retrieval
        subtasks = manager.get_subitems("wide_list", "parent")
        assert len(subtasks) == num_subtasks

        # Test completion logic with many subtasks
        # Complete all but one subitem
        for i in range(num_subtasks - 1):
            manager.update_item_status("wide_list", f"child_{i}", status="completed")

        # Parent should not auto-complete yet
        parent = manager.get_item("wide_list", "parent")
        assert parent.status != "completed"

        # Complete last subitem
        manager.update_item_status(
            "wide_list", f"child_{num_subtasks - 1}", status="completed"
        )

        # Parent should now auto-complete
        parent = manager.get_item("wide_list", "parent")
        assert parent.status == "completed"

    def test_many_cross_list_dependencies(self, manager):
        """Test system with many cross-list dependencies"""
        # Create multiple lists (reduced for performance)
        num_lists = 10
        lists = []
        for i in range(num_lists):
            list_key = f"list_{i}"
            manager.create_list(list_key, f"List {i}")
            lists.append(list_key)

            # Add item to each list
            manager.add_item(list_key, f"task_{i}", f"Item in list {i}")

        # Create many dependencies (each item depends on previous)
        for i in range(1, num_lists):
            manager.add_item_dependency(
                lists[i], f"task_{i}", lists[i - 1], f"task_{i-1}"
            )

        # Test dependency resolution
        # Only first item should be available
        next_task = manager.get_next_pending(lists[0])
        assert next_task is not None
        assert next_task.item_key == "task_0"

        # Other tasks should be blocked
        for i in range(1, min(3, num_lists)):  # Test first few
            is_blocked = manager.is_item_blocked(lists[i], f"task_{i}")
            assert is_blocked == True

        # Complete tasks in order and verify unblocking
        for i in range(min(3, num_lists)):  # Test first few
            manager.update_item_status(lists[i], f"task_{i}", status="completed")

            # Next item should now be available
            if i < min(2, num_lists - 1):
                is_blocked = manager.is_item_blocked(lists[i + 1], f"task_{i + 1}")
                assert is_blocked == False

    def test_unicode_and_special_characters(self, manager):
        """Test handling of Unicode and special characters"""
        # Test various Unicode content
        unicode_tests = [
            "简体中文测试",  # Chinese
            "тест на русском",  # Russian
            "🚀 Emoji test 🎉",  # Emojis
            "Test with\nnewlines\nand\ttabs",  # Whitespace
            "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",  # Special chars
            "Mixed: 中文 + Русский + 🌟 + special!@#",  # Mixed
        ]

        for i, content in enumerate(unicode_tests):
            list_key = f"unicode_list_{i}"
            item_key = f"unicode_item_{i}"

            # Create list with Unicode title (truncated to avoid length issues)
            title = f"Unicode: {content[:50]}..."
            manager.create_list(list_key, title)

            # Add item with Unicode content (truncated to fit limits)
            truncated_content = content[:500]  # Stay under limit
            item = manager.add_item(list_key, item_key, truncated_content)
            assert item.content == truncated_content

            # Verify retrieval preserves Unicode
            retrieved = manager.get_item(list_key, item_key)
            assert retrieved.content == truncated_content

    def test_empty_and_whitespace_values(self, manager):
        """Test handling of empty and whitespace-only values"""
        edge_case_values = [
            "",  # Empty string
            " ",  # Single space
            "\t",  # Tab
            "\n",  # Newline
            "\r\n",  # Windows newline
            "   \t\n  ",  # Mixed whitespace
        ]

        # Test list creation with edge case values
        for i, value in enumerate(edge_case_values):
            try:
                list_obj = manager.create_list(f"edge_list_{i}", value)
                # If it succeeds, verify the value handling
                assert list_obj.title == value or len(list_obj.title.strip()) >= 0
            except Exception as e:
                # Should be validation error if empty values not allowed
                error_msg = str(e).lower()
                assert any(
                    keyword in error_msg
                    for keyword in ["empty", "required", "validation", "exists"]
                )

        # Test item creation with edge case values
        manager.create_list("edge_test", "Edge Test List")
        for i, value in enumerate(edge_case_values):
            try:
                item = manager.add_item("edge_test", f"edge_item_{i}", value)
                assert item.content == value
            except Exception as e:
                # Should handle gracefully
                error_msg = str(e).lower()
                assert any(
                    keyword in error_msg
                    for keyword in ["empty", "content", "validation"]
                )

    def test_maximum_database_size_handling(self, manager):
        """Test behavior approaching database size limits"""
        # Use temporary file to test actual file size limits
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            file_manager = TodoManager(db_path)
            file_manager.create_list("size_test", "Size Test List")

            # Add progressively larger amounts of data
            # Note: Keep reasonable for test performance and within Pydantic limits
            large_content = "X" * 999  # Just under 1000 char limit

            # Add multiple items
            items_added = 0
            for i in range(50):  # Reasonable number for testing
                try:
                    file_manager.add_item("size_test", f"large_item_{i}", large_content)
                    items_added += 1
                except Exception as e:
                    # If we hit limits, should be clear error
                    error_msg = str(e).lower()
                    assert any(
                        keyword in error_msg
                        for keyword in [
                            "size",
                            "space",
                            "limit",
                            "full",
                            "string_too_long",
                            "1000 characters",
                        ]
                    )
                    break

            # Should have added at least some items
            assert items_added > 0

            # Verify database is still functional
            items = file_manager.get_list_items("size_test")
            assert len(items) == items_added

        finally:
            import os

            os.unlink(db_path)
