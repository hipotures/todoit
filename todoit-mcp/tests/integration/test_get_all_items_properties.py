"""
Integration tests for get_all_items_properties functionality.

Tests the new function that retrieves all properties for all items
in a list with optional status filtering.
"""
import pytest
from core.manager import TodoManager


class TestGetAllItemsPropertiesIntegration:
    """Integration tests for get_all_items_properties with real database"""
    
    @pytest.fixture
    def manager(self, temp_db):
        """Create TodoManager with temporary database."""
        return TodoManager(temp_db)
    
    @pytest.fixture
    def setup_test_data(self, manager):
        """Setup test data with items and properties."""
        # Create test list
        manager.create_list("testlist", "Test List", "Test description")
        
        # Add test items with different statuses
        manager.add_item("testlist", "task1", "First task")
        manager.add_item("testlist", "task2", "Second task")
        manager.add_item("testlist", "task3", "Third task")
        
        # Update statuses
        manager.update_item_status("testlist", "task2", "in_progress")
        manager.update_item_status("testlist", "task3", "completed")
        
        # Add properties to items
        manager.set_item_property("testlist", "task1", "image_downloaded", "pending")
        manager.set_item_property("testlist", "task1", "image_generated", "completed")
        manager.set_item_property("testlist", "task1", "priority", "high")
        
        manager.set_item_property("testlist", "task2", "priority", "medium")
        manager.set_item_property("testlist", "task2", "image_downloaded", "completed")
        
        manager.set_item_property("testlist", "task3", "priority", "low")
        manager.set_item_property("testlist", "task3", "process_status", "done")
        
        return {"list_key": "testlist"}
    
    def test_get_all_items_properties_no_filter(self, manager, setup_test_data):
        """Test getting all properties for all items without status filter."""
        result = manager.get_all_items_properties("testlist")
        
        # Should have 7 total properties (3+2+2)
        assert len(result) == 7
        
        # Check structure
        for prop in result:
            assert "item_key" in prop
            assert "property_key" in prop
            assert "property_value" in prop
            assert "status" in prop
        
        # Check specific properties
        item_keys = set(prop["item_key"] for prop in result)
        assert item_keys == {"task1", "task2", "task3"}
        
        # Check that status is included
        statuses = set(prop["status"] for prop in result)
        assert statuses == {"pending", "in_progress", "completed"}
    
    def test_get_all_items_properties_pending_filter(self, manager, setup_test_data):
        """Test getting properties only for pending items."""
        result = manager.get_all_items_properties("testlist", "pending")
        
        # Should have 3 properties from task1 only
        assert len(result) == 3
        
        # All should be from task1 and have pending status
        for prop in result:
            assert prop["item_key"] == "task1"
            assert prop["status"] == "pending"
        
        # Check property keys
        property_keys = set(prop["property_key"] for prop in result)
        assert property_keys == {"image_downloaded", "image_generated", "priority"}
    
    def test_get_all_items_properties_in_progress_filter(self, manager, setup_test_data):
        """Test getting properties only for in_progress items."""
        result = manager.get_all_items_properties("testlist", "in_progress")
        
        # Should have 2 properties from task2 only
        assert len(result) == 2
        
        # All should be from task2 and have in_progress status
        for prop in result:
            assert prop["item_key"] == "task2"
            assert prop["status"] == "in_progress"
        
        # Check property keys
        property_keys = set(prop["property_key"] for prop in result)
        assert property_keys == {"priority", "image_downloaded"}
    
    def test_get_all_items_properties_completed_filter(self, manager, setup_test_data):
        """Test getting properties only for completed items."""
        result = manager.get_all_items_properties("testlist", "completed")
        
        # Should have 2 properties from task3 only
        assert len(result) == 2
        
        # All should be from task3 and have completed status
        for prop in result:
            assert prop["item_key"] == "task3"
            assert prop["status"] == "completed"
        
        # Check property keys
        property_keys = set(prop["property_key"] for prop in result)
        assert property_keys == {"priority", "process_status"}
    
    def test_get_all_items_properties_failed_filter(self, manager, setup_test_data):
        """Test getting properties for failed items (none exist)."""
        result = manager.get_all_items_properties("testlist", "failed")
        
        # Should be empty since no failed items
        assert len(result) == 0
    
    def test_get_all_items_properties_invalid_status(self, manager, setup_test_data):
        """Test error handling for invalid status."""
        with pytest.raises(ValueError, match="Invalid status 'invalid'"):
            manager.get_all_items_properties("testlist", "invalid")
    
    def test_get_all_items_properties_list_not_found(self, manager):
        """Test error handling for non-existent list."""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.get_all_items_properties("nonexistent")
    
    def test_get_all_items_properties_empty_list(self, manager):
        """Test with list that has no items."""
        manager.create_list("empty", "Empty List")
        result = manager.get_all_items_properties("empty")
        
        assert len(result) == 0
    
    def test_get_all_items_properties_items_without_properties(self, manager):
        """Test with items that have no properties."""
        manager.create_list("noprops", "No Properties List")
        manager.add_item("noprops", "task1", "Task without properties")
        manager.add_item("noprops", "task2", "Another task without properties")
        
        result = manager.get_all_items_properties("noprops")
        assert len(result) == 0
    
    def test_get_all_items_properties_sorting(self, manager, setup_test_data):
        """Test that results are sorted by item_key and then property_key."""
        result = manager.get_all_items_properties("testlist")
        
        # Extract sorting keys
        sort_keys = [(prop["item_key"], prop["property_key"]) for prop in result]
        
        # Should be sorted
        assert sort_keys == sorted(sort_keys)
        
        # First item should be task1 with image_downloaded (alphabetically first)
        assert result[0]["item_key"] == "task1"
        assert result[0]["property_key"] == "image_downloaded"