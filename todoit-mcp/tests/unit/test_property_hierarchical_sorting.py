"""
Unit tests for hierarchical sorting in property listing
Tests that get_all_items_properties returns items in hierarchical order
"""

import pytest
from core.manager import TodoManager


class TestPropertyHierarchicalSorting:
    """Test suite for property hierarchical sorting functionality"""

    def test_properties_sorted_by_hierarchical_position(self, manager):
        """Test that properties are returned in hierarchical order not alphabetical"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add items in specific order: z, a, m (should stay in this order, not alphabetical)
        task_z = manager.add_item("test_list", "task_z", "Item Z")
        task_a = manager.add_item("test_list", "task_a", "Item A") 
        task_m = manager.add_item("test_list", "task_m", "Item M")

        # Add properties to all tasks
        manager.set_item_property("test_list", "task_z", "priority", "high")
        manager.set_item_property("test_list", "task_a", "priority", "low")
        manager.set_item_property("test_list", "task_m", "priority", "medium")

        # Get all properties
        properties = manager.get_all_items_properties("test_list")

        # Should be in hierarchical order (z, a, m) not alphabetical (a, m, z)
        item_keys_in_order = [prop["item_key"] for prop in properties]
        assert item_keys_in_order == ["task_z", "task_a", "task_m"]

    def test_properties_with_subtasks_hierarchical_order(self, manager):
        """Test hierarchical ordering with main tasks and subtasks"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add main tasks
        task_1 = manager.add_item("test_list", "main_b", "Main B")  # First position
        task_2 = manager.add_item("test_list", "main_a", "Main A")  # Second position

        # Add subtasks
        sub_1 = manager.add_subitem("test_list", "main_b", "sub_b1", "Sub B1")
        sub_2 = manager.add_subitem("test_list", "main_a", "sub_a1", "Sub A1")
        sub_3 = manager.add_subitem("test_list", "main_b", "sub_b2", "Sub B2")

        # Add properties
        manager.set_item_property("test_list", "main_b", "type", "parent")
        manager.set_item_property("test_list", "main_a", "type", "parent")
        manager.set_item_property("test_list", "sub_b1", "type", "child")
        manager.set_item_property("test_list", "sub_a1", "type", "child")
        manager.set_item_property("test_list", "sub_b2", "type", "child")

        # Get all properties
        properties = manager.get_all_items_properties("test_list")

        # Should be in hierarchical order: main tasks first, then subtasks grouped by parent
        item_keys_in_order = [prop["item_key"] for prop in properties]
        expected_order = ["main_b", "main_a", "sub_b1", "sub_b2", "sub_a1"]
        assert item_keys_in_order == expected_order

    def test_properties_multiple_properties_per_item(self, manager):
        """Test ordering with multiple properties per item"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add tasks
        task_1 = manager.add_item("test_list", "task_z", "Item Z")
        task_2 = manager.add_item("test_list", "task_a", "Item A")

        # Add multiple properties to each item
        manager.set_item_property("test_list", "task_z", "priority", "high")
        manager.set_item_property("test_list", "task_z", "category", "urgent")
        manager.set_item_property("test_list", "task_a", "priority", "low")
        manager.set_item_property("test_list", "task_a", "category", "normal")

        # Get all properties
        properties = manager.get_all_items_properties("test_list")

        # Should maintain item order, then sort properties alphabetically within each item
        expected_sequence = [
            ("task_z", "category"),  # category comes before priority alphabetically
            ("task_z", "priority"),
            ("task_a", "category"),
            ("task_a", "priority")
        ]
        
        actual_sequence = [(prop["item_key"], prop["property_key"]) for prop in properties]
        assert actual_sequence == expected_sequence

    def test_properties_with_status_filter_maintains_order(self, manager):
        """Test that status filtering maintains hierarchical order"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add tasks and change some statuses
        task_1 = manager.add_item("test_list", "task_c", "Item C")
        task_2 = manager.add_item("test_list", "task_a", "Item A")
        task_3 = manager.add_item("test_list", "task_b", "Item B")

        # Change some statuses
        manager.update_item_status("test_list", "task_a", "completed")
        manager.update_item_status("test_list", "task_b", "completed")

        # Add properties
        manager.set_item_property("test_list", "task_c", "type", "pending_task")
        manager.set_item_property("test_list", "task_a", "type", "completed_task")
        manager.set_item_property("test_list", "task_b", "type", "completed_task")

        # Get properties for completed items only
        properties = manager.get_all_items_properties("test_list", status="completed")

        # Should maintain hierarchical order among completed items (a, then b in creation order)
        item_keys_in_order = [prop["item_key"] for prop in properties]
        assert item_keys_in_order == ["task_a", "task_b"]

    def test_empty_properties_maintains_structure(self, manager):
        """Test that items without properties don't break ordering"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add tasks
        task_1 = manager.add_item("test_list", "task_z", "Item Z")
        task_2 = manager.add_item("test_list", "task_a", "Item A")
        task_3 = manager.add_item("test_list", "task_m", "Item M")

        # Add properties only to some tasks
        manager.set_item_property("test_list", "task_z", "priority", "high")
        manager.set_item_property("test_list", "task_m", "priority", "medium")
        # task_a has no properties

        # Get all properties
        properties = manager.get_all_items_properties("test_list")

        # Should only return items that have properties, in hierarchical order
        item_keys_in_order = [prop["item_key"] for prop in properties]
        assert item_keys_in_order == ["task_z", "task_m"]  # task_a omitted (no properties)