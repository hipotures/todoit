"""
Integration tests for MCP rename tools
Tests todo_rename_item and todo_rename_list MCP tools
"""

import pytest
import tempfile
import os
import asyncio
from core.manager import TodoManager
from interfaces.mcp_server import todo_rename_item, todo_rename_list, todo_add_item
import interfaces.mcp_server as mcp_server


class TestMCPRename:
    """Integration tests for MCP rename tools"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def setup_test_data(self, temp_db_path):
        """Setup test data for MCP rename tests"""
        # Store original env var if it exists
        original_db_path = os.environ.get("TODOIT_DB_PATH")
        
        # Set environment variable for database
        os.environ["TODOIT_DB_PATH"] = temp_db_path
        
        # Reset the global manager instance to ensure clean state
        mcp_server.manager = None
        
        manager = TodoManager(temp_db_path)
        
        # Create test list with items and subitems
        list1 = manager.create_list("mcp_project", "MCP Project")
        
        # Add regular items
        item1 = manager.add_item("mcp_project", "task1", "Original Task 1")
        item2 = manager.add_item("mcp_project", "task2", "Task Implementation")
        
        # Add subitems to task1
        subitem1 = manager.add_subitem("mcp_project", "task1", "design", "Design Phase")
        subitem2 = manager.add_subitem("mcp_project", "task1", "code", "Coding Phase")
        
        yield manager, list1, item1, item2, subitem1, subitem2
        
        # Restore original env var
        if original_db_path is not None:
            os.environ["TODOIT_DB_PATH"] = original_db_path
        else:
            os.environ.pop("TODOIT_DB_PATH", None)

    @pytest.mark.asyncio
    async def test_mcp_rename_item_key_only(self, temp_db_path, setup_test_data):
        """Test todo_rename_item MCP tool with key only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename item key only via MCP
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",
            new_key="mcp_renamed_task"
        )
        
        assert result["success"] == True
        assert "item" in result
        assert result["item"]["item_key"] == "mcp_renamed_task"
        assert result["item"]["title"] == "Original Task 1"  # MCP should return title, not content
        
        # Verify in database
        renamed_item = manager.get_item("mcp_project", "mcp_renamed_task")
        assert renamed_item.item_key == "mcp_renamed_task"
        assert renamed_item.content == "Original Task 1"

    @pytest.mark.asyncio
    async def test_mcp_rename_item_title_only(self, temp_db_path, setup_test_data):
        """Test todo_rename_item MCP tool with title only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename item title only via MCP
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",
            new_title="MCP Updated Title"
        )
        
        assert result["success"] == True
        assert "item" in result
        assert result["item"]["item_key"] == "task1"
        assert result["item"]["title"] == "MCP Updated Title"  # MCP should return title
        
        # Verify in database
        updated_item = manager.get_item("mcp_project", "task1")
        assert updated_item.content == "MCP Updated Title"

    @pytest.mark.asyncio
    async def test_mcp_rename_item_both_key_and_title(self, temp_db_path, setup_test_data):
        """Test todo_rename_item MCP tool with both key and title"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename both key and title via MCP
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="task2",
            new_key="mcp_complete_task",
            new_title="MCP Complete Task Implementation"
        )
        
        assert result["success"] == True
        assert "item" in result
        assert result["item"]["item_key"] == "mcp_complete_task"
        assert result["item"]["title"] == "MCP Complete Task Implementation"
        
        # Verify in database
        renamed_item = manager.get_item("mcp_project", "mcp_complete_task")
        assert renamed_item.item_key == "mcp_complete_task"
        assert renamed_item.content == "MCP Complete Task Implementation"

    @pytest.mark.asyncio
    async def test_mcp_rename_subitem(self, temp_db_path, setup_test_data):
        """Test todo_rename_item MCP tool for subitems"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename subitem via MCP
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",  # Parent key
            new_key="mcp_ui_design",
            new_title="MCP UI/UX Design Phase",
            subitem_key="design"  # Current subitem key
        )
        
        assert result["success"] == True
        assert "item" in result
        assert result["item"]["item_key"] == "mcp_ui_design"
        assert result["item"]["title"] == "MCP UI/UX Design Phase"
        
        # Verify in database
        renamed_subitem = manager.get_item("mcp_project", "mcp_ui_design", "task1")
        assert renamed_subitem.item_key == "mcp_ui_design"
        assert renamed_subitem.content == "MCP UI/UX Design Phase"

    @pytest.mark.asyncio
    async def test_mcp_rename_item_validation_errors(self, temp_db_path, setup_test_data):
        """Test validation errors in todo_rename_item MCP tool"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test no parameters provided
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1"
        )
        
        assert result["success"] == False
        assert "error" in result
        assert "At least one of new_key or new_title must be provided" in result["error"]
        
        # Test item not found
        result = await todo_rename_item(
            list_key="mcp_project",
            item_key="nonexistent",
            new_key="new_key"
        )
        
        assert result["success"] == False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mcp_rename_list(self, temp_db_path, setup_test_data):
        """Test todo_rename_list MCP tool"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename list via MCP
        result = await todo_rename_list(
            list_key="mcp_project",
            new_key="mcp_renamed_project",
            new_title="MCP Renamed Project"
        )
        
        assert result["success"] == True
        assert "list" in result
        assert result["list"]["list_key"] == "mcp_renamed_project"
        assert result["list"]["title"] == "MCP Renamed Project"
        
        # Verify in database
        renamed_list = manager.get_list("mcp_renamed_project")
        assert renamed_list.list_key == "mcp_renamed_project"
        assert renamed_list.title == "MCP Renamed Project"
        
        # Verify old key no longer exists
        old_list = manager.get_list("mcp_project")
        assert old_list is None

    @pytest.mark.asyncio
    async def test_mcp_rename_list_key_only(self, temp_db_path, setup_test_data):
        """Test todo_rename_list MCP tool with key only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename list key only via MCP
        result = await todo_rename_list(
            list_key="mcp_project",
            new_key="mcp_key_only"
        )
        
        assert result["success"] == True
        assert "list" in result
        assert result["list"]["list_key"] == "mcp_key_only"
        assert result["list"]["title"] == "MCP Project"  # Title unchanged
        
        # Verify in database
        renamed_list = manager.get_list("mcp_key_only")
        assert renamed_list.list_key == "mcp_key_only"
        assert renamed_list.title == "MCP Project"

    @pytest.mark.asyncio
    async def test_mcp_rename_list_title_only(self, temp_db_path, setup_test_data):
        """Test todo_rename_list MCP tool with title only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test rename list title only via MCP
        result = await todo_rename_list(
            list_key="mcp_project",
            new_title="MCP Title Only"
        )
        
        assert result["success"] == True
        assert "list" in result
        assert result["list"]["list_key"] == "mcp_project"  # Key unchanged
        assert result["list"]["title"] == "MCP Title Only"
        
        # Verify in database
        updated_list = manager.get_list("mcp_project")
        assert updated_list.list_key == "mcp_project"
        assert updated_list.title == "MCP Title Only"

    @pytest.mark.asyncio
    async def test_mcp_add_item_uses_title_parameter(self, temp_db_path, setup_test_data):
        """Test that todo_add_item MCP tool now uses title parameter instead of content"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test add item with title parameter
        result = await todo_add_item(
            list_key="mcp_project",
            item_key="new_item",
            title="New Item Title"
        )
        
        assert result["success"] == True
        assert "item" in result
        assert result["item"]["item_key"] == "new_item"
        assert result["item"]["title"] == "New Item Title"  # MCP should return title
        
        # Verify in database (content field should contain the title value)
        new_item = manager.get_item("mcp_project", "new_item")
        assert new_item.item_key == "new_item"
        assert new_item.content == "New Item Title"  # Internally stored as content

    @pytest.mark.asyncio 
    async def test_mcp_add_subitem_uses_title_parameter(self, temp_db_path, setup_test_data):
        """Test that todo_add_item MCP tool works for subitems with title parameter"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test add subitem with title parameter
        result = await todo_add_item(
            list_key="mcp_project",
            item_key="task1",  # Parent key
            title="New Subitem Title",
            subitem_key="new_subitem"
        )
        
        assert result["success"] == True
        assert "subitem" in result
        assert result["subitem"]["item_key"] == "new_subitem"
        assert result["subitem"]["title"] == "New Subitem Title"
        
        # Verify in database
        new_subitem = manager.get_item("mcp_project", "new_subitem", "task1")
        assert new_subitem.item_key == "new_subitem"
        assert new_subitem.content == "New Subitem Title"

    @pytest.mark.asyncio
    async def test_mcp_content_to_title_mapping_consistency(self, temp_db_path, setup_test_data):
        """Test that all MCP tools consistently map content to title in responses"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Add an item via MCP
        add_result = await todo_add_item(
            list_key="mcp_project", 
            item_key="mapping_test",
            title="Mapping Test Item"
        )
        
        # Verify add response uses title
        assert "title" in add_result["item"]
        assert "content" not in add_result["item"]
        assert add_result["item"]["title"] == "Mapping Test Item"
        
        # Rename the item via MCP
        rename_result = await todo_rename_item(
            list_key="mcp_project",
            item_key="mapping_test",
            new_title="Renamed Mapping Test"
        )
        
        # Verify rename response uses title
        assert "title" in rename_result["item"] 
        assert "content" not in rename_result["item"]
        assert rename_result["item"]["title"] == "Renamed Mapping Test"
        
        # Verify internal storage still uses content
        db_item = manager.get_item("mcp_project", "mapping_test")
        assert hasattr(db_item, "content")
        assert db_item.content == "Renamed Mapping Test"