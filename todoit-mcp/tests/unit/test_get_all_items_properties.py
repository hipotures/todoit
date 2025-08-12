"""
Unit tests for get_all_items_properties functionality
"""
import pytest
from core.manager import TodoManager


@pytest.fixture
def manager_with_properties(temp_db):
    """Create manager with test data including properties"""
    manager = TodoManager(temp_db)
    
    # Create list and items
    manager.create_list("test_list", "Test List")
    manager.add_item("test_list", "item1", "First item")
    manager.add_item("test_list", "item2", "Second item")
    manager.add_item("test_list", "item3", "Third item")
    
    # Set properties
    manager.set_item_property("test_list", "item1", "priority", "high")
    manager.set_item_property("test_list", "item1", "assignee", "john")
    manager.set_item_property("test_list", "item2", "priority", "low")
    manager.set_item_property("test_list", "item2", "status", "active")
    manager.set_item_property("test_list", "item3", "size", "large")
    
    return manager


class TestGetAllItemsProperties:
    """Test get_all_items_properties functionality"""
    
    def test_get_all_items_properties_success(self, manager_with_properties):
        """Test successful retrieval of all item properties"""
        result = manager_with_properties.get_all_items_properties("test_list")
        
        assert len(result) == 5  # 2 + 2 + 1 properties
        
        # Check structure of returned data
        for prop in result:
            assert "item_key" in prop
            assert "property_key" in prop
            assert "property_value" in prop
        
        # Check specific properties
        expected_props = [
            {"item_key": "item1", "property_key": "assignee", "property_value": "john"},
            {"item_key": "item1", "property_key": "priority", "property_value": "high"},
            {"item_key": "item2", "property_key": "priority", "property_value": "low"},
            {"item_key": "item2", "property_key": "status", "property_value": "active"},
            {"item_key": "item3", "property_key": "size", "property_value": "large"},
        ]
        
        assert result == expected_props
    
    def test_get_all_items_properties_empty_list(self, temp_db):
        """Test with list that has no items with properties"""
        manager = TodoManager(temp_db)
        manager.create_list("empty_list", "Empty List")
        
        result = manager.get_all_items_properties("empty_list")
        assert result == []
    
    def test_get_all_items_properties_items_without_properties(self, temp_db):
        """Test with list that has items but no properties"""
        manager = TodoManager(temp_db)
        manager.create_list("no_props", "No Properties")
        manager.add_item("no_props", "item1", "Item without properties")
        
        result = manager.get_all_items_properties("no_props")
        assert result == []
    
    def test_get_all_items_properties_nonexistent_list(self, temp_db):
        """Test with nonexistent list"""
        manager = TodoManager(temp_db)
        
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.get_all_items_properties("nonexistent")
    
    def test_get_all_items_properties_sorting(self, manager_with_properties):
        """Test that results are sorted by item_key, then property_key"""
        result = manager_with_properties.get_all_items_properties("test_list")
        
        # Verify sorting
        for i in range(len(result) - 1):
            current = (result[i]['item_key'], result[i]['property_key'])
            next_item = (result[i + 1]['item_key'], result[i + 1]['property_key'])
            assert current <= next_item, f"Sorting failed: {current} > {next_item}"