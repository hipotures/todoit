"""
Unit tests for hierarchical numbering in display functionality
Tests the fix for subitem numbering to ensure proper parent-relative indexing
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from interfaces.cli_modules.display import _render_table_view, _organize_items_by_hierarchy


class TestHierarchicalNumbering:
    """Test hierarchical numbering functionality"""

    @pytest.fixture
    def mock_items_with_hierarchy(self):
        """Create mock items with hierarchical structure"""
        # Mock main tasks
        task1 = Mock()
        task1.id = 1
        task1.item_key = "task1"
        task1.content = "Main Item 1"
        task1.position = 1
        task1.parent_item_id = None
        task1.status = Mock()
        task1.status.value = "pending"
        task1.completion_states = {}
        task1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        task2 = Mock()
        task2.id = 3
        task2.item_key = "task2"
        task2.content = "Main Item 2"
        task2.position = 3
        task2.parent_item_id = None
        task2.status = Mock()
        task2.status.value = "pending"
        task2.completion_states = {}
        task2.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        # Mock subtasks for task1 (positions 2, 4, 5)
        task1_sub1 = Mock()
        task1_sub1.id = 2
        task1_sub1.item_key = "task1_sub1"
        task1_sub1.content = "Subitem 1 for Item 1"
        task1_sub1.position = 2  # Global position
        task1_sub1.parent_item_id = 1
        task1_sub1.status = Mock()
        task1_sub1.status.value = "pending"
        task1_sub1.completion_states = {}
        task1_sub1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        task1_sub2 = Mock()
        task1_sub2.id = 4
        task1_sub2.item_key = "task1_sub2"
        task1_sub2.content = "Subitem 2 for Item 1"
        task1_sub2.position = 4  # Global position
        task1_sub2.parent_item_id = 1
        task1_sub2.status = Mock()
        task1_sub2.status.value = "pending"
        task1_sub2.completion_states = {}
        task1_sub2.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        task1_sub3 = Mock()
        task1_sub3.id = 5
        task1_sub3.item_key = "task1_sub3"
        task1_sub3.content = "Subitem 3 for Item 1"
        task1_sub3.position = 5  # Global position
        task1_sub3.parent_item_id = 1
        task1_sub3.status = Mock()
        task1_sub3.status.value = "pending"
        task1_sub3.completion_states = {}
        task1_sub3.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        # Mock subtasks for task2 (positions 6, 7)
        task2_sub1 = Mock()
        task2_sub1.id = 6
        task2_sub1.item_key = "task2_sub1"
        task2_sub1.content = "Subitem 1 for Item 2"
        task2_sub1.position = 6  # Global position
        task2_sub1.parent_item_id = 3
        task2_sub1.status = Mock()
        task2_sub1.status.value = "pending"
        task2_sub1.completion_states = {}
        task2_sub1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        task2_sub2 = Mock()
        task2_sub2.id = 7
        task2_sub2.item_key = "task2_sub2"
        task2_sub2.content = "Subitem 2 for Item 2"
        task2_sub2.position = 7  # Global position
        task2_sub2.parent_item_id = 3
        task2_sub2.status = Mock()
        task2_sub2.status.value = "pending"
        task2_sub2.completion_states = {}
        task2_sub2.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

        return [task1, task1_sub1, task2, task1_sub2, task2_sub1, task1_sub3, task2_sub2]

    @pytest.fixture
    def mock_todo_list(self):
        """Create mock todo list"""
        todo_list = Mock()
        todo_list.id = 1
        todo_list.list_key = "test_list"
        todo_list.title = "Test List"
        todo_list.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        todo_list.metadata = {}
        return todo_list

    def test_organize_items_by_hierarchy(self, mock_items_with_hierarchy):
        """Test that items are properly organized by hierarchy"""
        hierarchy = _organize_items_by_hierarchy(mock_items_with_hierarchy)
        
        # Should have 2 root items
        assert len(hierarchy["roots"]) == 2
        assert hierarchy["roots"][0].item_key == "task1"
        assert hierarchy["roots"][1].item_key == "task2"
        
        # Check children mapping
        assert 1 in hierarchy["children"]  # task1 has children
        assert 3 in hierarchy["children"]  # task2 has children
        assert len(hierarchy["children"][1]) == 3  # task1 has 3 subtasks
        assert len(hierarchy["children"][3]) == 2  # task2 has 2 subtasks
        
        # Check children are sorted by position within parent
        task1_children = hierarchy["children"][1]
        assert task1_children[0].position == 2  # task1_sub1
        assert task1_children[1].position == 4  # task1_sub2  
        assert task1_children[2].position == 5  # task1_sub3

    def test_hierarchical_numbering_in_table_view(self, mock_items_with_hierarchy, mock_todo_list):
        """Test that hierarchical numbering is correct in table view"""
        # Capture the rendered data
        data_captured = []
        
        def mock_display_records(data, title, columns):
            data_captured.extend(data)
        
        # Mock the output format to avoid JSON processing
        with pytest.MonkeyPatch().context() as m:
            m.setenv("TODOIT_OUTPUT_FORMAT", "table")
            # Mock _display_records to capture data instead of printing
            from interfaces.cli_modules import display
            original_display_records = display._display_records
            display._display_records = mock_display_records
            
            try:
                _render_table_view(mock_todo_list, mock_items_with_hierarchy, {})
                
                # Verify hierarchical numbering
                numbering = [item["#"] for item in data_captured]
                
                # Expected numbering:
                # Item 1: "1"
                # Item 1 Subitem 1: "1.1" 
                # Item 1 Subitem 2: "1.2"
                # Item 1 Subitem 3: "1.3"
                # Item 2: "3"
                # Item 2 Subitem 1: "3.1"
                # Item 2 Subitem 2: "3.2"
                expected_numbering = ["1", "1.1", "1.2", "1.3", "3", "3.1", "3.2"]
                
                assert numbering == expected_numbering, f"Expected {expected_numbering}, got {numbering}"
                
                # Verify that item keys match expected order
                keys = [item["Key"] for item in data_captured]
                expected_keys = ["task1", "task1_sub1", "task1_sub2", "task1_sub3", "task2", "task2_sub1", "task2_sub2"]
                assert keys == expected_keys, f"Expected {expected_keys}, got {keys}"
                
            finally:
                # Restore original function
                display._display_records = original_display_records

    def test_subtask_numbering_resets_per_parent(self, mock_items_with_hierarchy):
        """Test that subitem numbering resets to 1 for each parent"""
        hierarchy = _organize_items_by_hierarchy(mock_items_with_hierarchy)
        
        # Test internal numbering logic by checking the data structure
        task1_children = hierarchy["children"][1]  # task1 children
        task2_children = hierarchy["children"][3]  # task2 children
        
        # Although global positions are different, the relative indexing should work correctly
        # Task1 subtasks have global positions 2, 4, 5 but should get relative indices 1, 2, 3
        # Task2 subtasks have global positions 6, 7 but should get relative indices 1, 2
        
        assert len(task1_children) == 3
        assert len(task2_children) == 2
        
        # Verify that children are ordered by position within each parent
        assert task1_children[0].position < task1_children[1].position < task1_children[2].position
        assert task2_children[0].position < task2_children[1].position

    def test_main_task_numbering_uses_position(self, mock_items_with_hierarchy):
        """Test that main tasks use their actual position for numbering"""
        hierarchy = _organize_items_by_hierarchy(mock_items_with_hierarchy)
        
        # Root items should maintain their original positions
        roots = hierarchy["roots"]
        assert roots[0].position == 1  # task1
        assert roots[1].position == 3  # task2 (position 3, not 2)
        
        # This tests that main task numbering respects actual positions,
        # not just sequential counting