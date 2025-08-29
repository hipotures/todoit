"""
Test Item Properties functionality - Manager and MCP layers

This file tests the complete Item Properties system:
- Manager layer operations (business logic)
- MCP layer operations (API interface)
- Error handling and edge cases
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from core.manager import TodoManager


class TestItemPropertiesManager:
    """Test item properties through manager layer"""

    @pytest.fixture
    def setup_test_data(self):
        """Setup test database and data"""
        # Create temporary database
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        manager = TodoManager(db_path)

        # Create test list and items
        test_list = manager.create_list(
            "test-project", "Test Project", ["Item 1", "Item 2"]
        )
        items = manager.get_list_items("test-project")

        yield {
            "manager": manager,
            "list": test_list,
            "item1": items[0] if items else None,
            "item2": items[1] if len(items) > 1 else None,
            "item1_key": items[0].item_key if items else None,
            "item2_key": items[1].item_key if len(items) > 1 else None,
        }

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_set_item_property_new(self, setup_test_data):
        """Test setting a new property for an item"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set new property
        result = manager.set_item_property("test-project", item_key, "priority", "high")

        assert result.property_key == "priority"
        assert result.property_value == "high"
        assert result.item_id == data["item1"].id

    def test_set_item_property_update_existing(self, setup_test_data):
        """Test updating an existing property"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set initial property
        manager.set_item_property("test-project", item_key, "priority", "high")

        # Update same property
        result = manager.set_item_property("test-project", item_key, "priority", "low")

        assert result.property_key == "priority"
        assert result.property_value == "low"

    def test_get_item_property_exists(self, setup_test_data):
        """Test getting an existing property"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set property
        manager.set_item_property("test-project", item_key, "priority", "high")

        # Get property
        result = manager.get_item_property("test-project", item_key, "priority")

        assert result == "high"

    def test_get_item_property_not_exists(self, setup_test_data):
        """Test getting a non-existent property"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Get non-existent property
        result = manager.get_item_property("test-project", item_key, "nonexistent")

        assert result is None

    def test_get_item_properties_multiple(self, setup_test_data):
        """Test getting all properties for an item"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set multiple properties
        manager.set_item_property("test-project", item_key, "priority", "high")
        manager.set_item_property("test-project", item_key, "category", "backend")
        manager.set_item_property("test-project", item_key, "hours", "8")

        # Get all properties
        properties = manager.get_item_properties("test-project", item_key)

        assert properties == {"priority": "high", "category": "backend", "hours": "8"}

    def test_get_item_properties_empty(self, setup_test_data):
        """Test getting properties from an item with no properties"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Get properties from item with no properties
        properties = manager.get_item_properties("test-project", item_key)

        assert properties == {}

    def test_delete_item_property_exists(self, setup_test_data):
        """Test deleting an existing property"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set property
        manager.set_item_property("test-project", item_key, "priority", "high")

        # Delete property
        result = manager.delete_item_property("test-project", item_key, "priority")

        assert result is True

        # Verify property is gone
        value = manager.get_item_property("test-project", item_key, "priority")
        assert value is None

    def test_delete_item_property_not_exists(self, setup_test_data):
        """Test deleting a non-existent property"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Delete non-existent property
        result = manager.delete_item_property("test-project", item_key, "nonexistent")

        assert result is False

    def test_item_properties_isolation(self, setup_test_data):
        """Test that properties are isolated between items"""
        data = setup_test_data
        manager = data["manager"]
        item1_key = data["item1_key"]
        item2_key = data["item2_key"]

        # Set property on first item
        manager.set_item_property("test-project", item1_key, "priority", "high")

        # Check second item doesn't have the property
        result = manager.get_item_property("test-project", item2_key, "priority")
        assert result is None

        # Set different value on second item
        manager.set_item_property("test-project", item2_key, "priority", "low")

        # Verify both items have different values
        assert (
            manager.get_item_property("test-project", item1_key, "priority") == "high"
        )
        assert manager.get_item_property("test-project", item2_key, "priority") == "low"

    def test_error_cases_invalid_list(self, setup_test_data):
        """Test error handling for invalid list"""
        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            manager.set_item_property("nonexistent", item_key, "priority", "high")

    def test_error_cases_invalid_item(self, setup_test_data):
        """Test error handling for invalid item"""
        data = setup_test_data
        manager = data["manager"]

        with pytest.raises(ValueError, match="Item 'nonexistent' not found"):
            manager.set_item_property("test-project", "nonexistent", "priority", "high")


class TestItemPropertiesMCP:
    """Test item properties through MCP tools"""

    @pytest.fixture
    def setup_test_data(self):
        """Setup test database and data"""
        # Create temporary database
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        manager = TodoManager(db_path)

        # Create test list and items
        test_list = manager.create_list(
            "test-project", "Test Project", ["Item 1", "Item 2"]
        )
        items = manager.get_list_items("test-project")

        yield {
            "manager": manager,
            "list": test_list,
            "item1": items[0] if items else None,
            "item2": items[1] if len(items) > 1 else None,
            "item1_key": items[0].item_key if items else None,
            "item2_key": items[1].item_key if len(items) > 1 else None,
        }

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_mcp_set_item_property(self, setup_test_data):
        """Test MCP tool for setting item property"""
        from interfaces.mcp_server import todo_set_item_property

        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Mock init_manager to return our test manager
        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_set_item_property(
                list_key="test-project",
                item_key=item_key,
                property_key="priority",
                property_value="high",
            )

        assert result["success"] is True
        assert result["property"]["property_key"] == "priority"
        assert result["property"]["property_value"] == "high"
        assert "Property 'priority' set for item" in result["message"]

    @pytest.mark.asyncio
    async def test_mcp_get_item_property_exists(self, setup_test_data):
        """Test MCP tool for getting existing item property"""
        from interfaces.mcp_server import todo_get_item_property

        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set property first
        manager.set_item_property("test-project", item_key, "priority", "high")

        # Mock init_manager to return our test manager
        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_get_item_property(
                list_key="test-project", item_key=item_key, property_key="priority"
            )

        assert result["success"] is True
        assert result["property_key"] == "priority"
        assert result["property_value"] == "high"
        assert result["list_key"] == "test-project"
        assert result["item_key"] == item_key

    @pytest.mark.asyncio
    async def test_mcp_get_item_property_not_exists(self, setup_test_data):
        """Test MCP tool for getting non-existent item property"""
        from interfaces.mcp_server import todo_get_item_property

        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Mock init_manager to return our test manager
        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_get_item_property(
                list_key="test-project", item_key=item_key, property_key="nonexistent"
            )

        assert result["success"] is False
        assert "Property 'nonexistent' not found" in result["error"]

    @pytest.mark.asyncio
    async def test_mcp_get_item_properties(self, setup_test_data):
        """Test MCP tool for getting all item properties"""
        from interfaces.mcp_server import todo_get_item_properties

        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set multiple properties
        manager.set_item_property("test-project", item_key, "priority", "high")
        manager.set_item_property("test-project", item_key, "category", "backend")

        # Mock init_manager to return our test manager
        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_get_item_properties(
                list_key="test-project", item_key=item_key
            )

        assert result["success"] is True
        assert result["list_key"] == "test-project"
        assert result["item_key"] == item_key
        assert result["properties"] == {"priority": "high", "category": "backend"}
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_mcp_delete_item_property(self, setup_test_data):
        """Test MCP tool for deleting item property"""
        from interfaces.mcp_server import todo_delete_item_property

        data = setup_test_data
        manager = data["manager"]
        item_key = data["item1_key"]

        # Set property first
        manager.set_item_property("test-project", item_key, "priority", "high")

        # Mock init_manager to return our test manager
        with patch("interfaces.mcp_server.init_manager", return_value=manager):
            result = await todo_delete_item_property(
                list_key="test-project", item_key=item_key, property_key="priority"
            )

        assert result["success"] is True
        assert "Property 'priority' deleted from item" in result["message"]

        # Verify property is actually gone
        value = manager.get_item_property("test-project", item_key, "priority")
        assert value is None
