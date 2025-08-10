"""
Integration tests for MCP todo_get_list_items with limit functionality
Tests MCP interface with limit parameter and response format
"""
import pytest
import asyncio
from unittest.mock import patch
from interfaces.mcp_server import todo_get_list_items, todo_create_list, todo_add_item, todo_update_item_status, init_manager


class TestMCPListItemsLimit:
    """Test suite for MCP todo_get_list_items limit functionality"""

    @pytest.mark.asyncio
    async def test_mcp_get_list_items_no_limit(self, temp_db):
        """Test MCP interface without limit"""
        # Initialize manager with temp database
        with patch('interfaces.mcp_server.manager', init_manager(temp_db)):
            # Create list
            list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add multiple items
        for i in range(6):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Get all items (no limit)
        result = await todo_get_list_items("test_list")
        
        assert result["success"]
        assert result["count"] == 6
        assert len(result["items"]) == 6
        assert result["total_count"] == 6
        assert not result["more_available"]  # No limit means no more available
        
        # Verify items are in correct order
        for i, item in enumerate(result["items"]):
            assert item["item_key"] == f"item_{i}"

    @pytest.mark.asyncio
    async def test_mcp_get_list_items_with_limit(self, temp_db):
        """Test MCP interface with limit parameter"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add multiple items
        for i in range(10):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Get limited items
        result = await todo_get_list_items("test_list", limit=4)
        
        assert result["success"]
        assert result["count"] == 4
        assert len(result["items"]) == 4
        assert result["total_count"] == 10
        assert result["more_available"]  # More items available
        
        # Verify we get first 4 items
        for i, item in enumerate(result["items"]):
            assert item["item_key"] == f"item_{i}"

    @pytest.mark.asyncio
    async def test_mcp_get_list_items_with_status_and_limit(self, temp_db):
        """Test MCP interface with both status filter and limit"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add multiple items
        for i in range(8):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Complete some items
        for i in [1, 3, 5, 7]:
            status_result = await todo_update_item_status("test_list", f"item_{i}", "completed")
            assert status_result["success"]
        
        # Get limited pending items
        result = await todo_get_list_items("test_list", status="pending", limit=2)
        
        assert result["success"]
        assert result["count"] == 2
        assert len(result["items"]) == 2
        assert result["total_count"] == 4  # Total pending items
        assert result["more_available"]  # More pending items available
        
        # Should get item_0 and item_2 (first two pending)
        assert result["items"][0]["item_key"] == "item_0"
        assert result["items"][1]["item_key"] == "item_2"

    @pytest.mark.asyncio
    async def test_mcp_limit_larger_than_available(self, temp_db):
        """Test MCP interface when limit is larger than available items"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add only 3 items
        for i in range(3):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Request 10 items (more than available)
        result = await todo_get_list_items("test_list", limit=10)
        
        assert result["success"]
        assert result["count"] == 3  # Only 3 items available
        assert len(result["items"]) == 3
        assert result["total_count"] == 3
        assert not result["more_available"]  # No more items available

    @pytest.mark.asyncio
    async def test_mcp_zero_limit(self, temp_db):
        """Test MCP interface with zero limit"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add items
        for i in range(5):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Request 0 items
        result = await todo_get_list_items("test_list", limit=0)
        
        assert result["success"]
        assert result["count"] == 0
        assert len(result["items"]) == 0
        assert result["total_count"] == 5
        assert result["more_available"]  # More items available (since we got 0)

    @pytest.mark.asyncio 
    async def test_mcp_response_format_with_limit(self, temp_db):
        """Test MCP response format includes all expected fields with limit"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add items
        for i in range(7):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Get limited items
        result = await todo_get_list_items("test_list", limit=3)
        
        # Verify response structure
        assert result["success"]
        assert "items" in result
        assert "count" in result
        assert "total_count" in result
        assert "more_available" in result
        
        # Verify values
        assert result["count"] == 3
        assert result["total_count"] == 7
        assert result["more_available"] is True
        assert len(result["items"]) == 3
        
        # Verify item structure is maintained
        for item in result["items"]:
            assert "item_key" in item
            assert "content" in item
            assert "status" in item
            assert "list_key" in item

    @pytest.mark.asyncio
    async def test_mcp_limit_with_nonexistent_list(self, temp_db):
        """Test MCP interface with limit on nonexistent list"""
        result = await todo_get_list_items("nonexistent", limit=5)
        
        assert not result["success"]
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mcp_limit_edge_case_exact_match(self, temp_db):
        """Test MCP interface when limit exactly matches available items"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List") 
        assert list_result["success"]
        
        # Add exactly 5 items
        for i in range(5):
            item_result = await todo_add_item("test_list", f"item_{i}", f"Item {i}")
            assert item_result["success"]
        
        # Request exactly 5 items
        result = await todo_get_list_items("test_list", limit=5)
        
        assert result["success"]
        assert result["count"] == 5
        assert result["total_count"] == 5
        assert not result["more_available"]  # No more items available

    @pytest.mark.asyncio
    async def test_mcp_limit_performance_consistency(self, temp_db):
        """Test MCP interface limit performance and consistency"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add many items
        for i in range(50):
            item_result = await todo_add_item("test_list", f"item_{i:02d}", f"Item {i}")
            assert item_result["success"]
        
        # Test different limit sizes
        limits = [1, 5, 10, 25, 50, 100]
        
        for limit in limits:
            result = await todo_get_list_items("test_list", limit=limit)
            
            assert result["success"]
            expected_count = min(limit, 50)
            assert result["count"] == expected_count
            assert result["total_count"] == 50
            assert len(result["items"]) == expected_count
            
            # Verify more_available logic
            if limit < 50:
                assert result["more_available"] is True
            else:
                assert result["more_available"] is False

    @pytest.mark.asyncio
    async def test_mcp_limit_with_completed_status_filter(self, temp_db):
        """Test MCP interface limit with completed status filter"""
        # Create list
        list_result = await todo_create_list("test_list", "Test List")
        assert list_result["success"]
        
        # Add items
        for i in range(12):
            item_result = await todo_add_item("test_list", f"item_{i:02d}", f"Item {i}")
            assert item_result["success"]
        
        # Complete every third item (4 total completed)
        for i in [2, 5, 8, 11]:
            status_result = await todo_update_item_status("test_list", f"item_{i:02d}", "completed")
            assert status_result["success"]
        
        # Get limited completed items
        result = await todo_get_list_items("test_list", status="completed", limit=2)
        
        assert result["success"]
        assert result["count"] == 2
        assert result["total_count"] == 4  # Total completed items
        assert result["more_available"] is True
        
        # Verify we get the first 2 completed items by position
        assert result["items"][0]["item_key"] == "item_02"
        assert result["items"][1]["item_key"] == "item_05"
        
        # Test getting all completed items
        all_completed = await todo_get_list_items("test_list", status="completed", limit=10)
        assert all_completed["success"]
        assert all_completed["count"] == 4
        assert all_completed["more_available"] is False