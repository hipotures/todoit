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
        assert "Either new_key or new_content must be provided" in result["error"]
        
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

    @pytest.mark.asyncio
    async def test_mcp_rename_subitem_duplicate_keys_different_parents(self, temp_db_path, setup_test_data):
        """Test that todo_rename_item allows duplicate subitem keys across different parents"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Create another parent task
        parent3 = manager.add_item("mcp_project", "task3", "Another Parent Task")
        
        # Add a subitem to the new parent with the same key as existing subitem
        # This should work since they have different parents
        result = await todo_add_item(
            list_key="mcp_project",
            item_key="task3",  # Parent key
            title="Design Phase for Task3",
            subitem_key="design"  # Same key as existing subitem under task1
        )
        
        assert result["success"] == True
        assert "subitem" in result
        assert result["subitem"]["item_key"] == "design"
        assert result["subitem"]["title"] == "Design Phase for Task3"
        
        # Now test renaming: rename "code" subitem under task1 to "design"
        # This should work because "design" under task1 already exists,
        # but we're renaming "code" to "design" under the same parent
        # Wait - this should fail because we can't have two "design" under same parent
        
        # Let's test the correct scenario: rename subitem to a key that exists under different parent
        # Rename subitem2 ("code" under "task1") to "design" - this should fail because 
        # "design" already exists under the same parent "task1"
        
        result_fail = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",  # Parent key
            subitem_key="code",  # Current subitem key to rename
            new_key="design"  # This key already exists under same parent - should fail
        )
        
        assert result_fail["success"] == False
        assert "error" in result_fail
        assert "already exists" in result_fail["error"]
        
        # Now test the valid scenario: rename subitem under task1 to a key that exists under task3
        # but not under task1. First, let's add another subitem under task3
        manager.add_subitem("mcp_project", "task3", "implementation", "Implementation Phase")
        
        # Now rename "code" under task1 to "implementation" - this should work
        # because "implementation" exists under task3 but not under task1
        result_success = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",  # Parent key
            subitem_key="code",  # Current subitem key to rename
            new_key="implementation",  # This key exists under task3 but not under task1
            new_title="Implementation Phase for Task1"
        )
        
        assert result_success["success"] == True
        assert "item" in result_success
        assert result_success["item"]["item_key"] == "implementation"
        assert result_success["item"]["title"] == "Implementation Phase for Task1"
        
        # Verify in database - should have two "implementation" subitems under different parents
        impl_task1 = manager.get_item("mcp_project", "implementation", "task1")
        impl_task3 = manager.get_item("mcp_project", "implementation", "task3") 
        
        assert impl_task1.item_key == "implementation"
        assert impl_task3.item_key == "implementation"
        assert impl_task1.content == "Implementation Phase for Task1"
        assert impl_task3.content == "Implementation Phase"
        assert impl_task1.parent_item_id != impl_task3.parent_item_id
        
        # Test changing title of task3 (parent item) - should not affect subitems
        result_title_change = await todo_rename_item(
            list_key="mcp_project",
            item_key="task3",
            new_title="Updated Parent Task Title"
        )
        
        assert result_title_change["success"] == True
        assert "item" in result_title_change
        assert result_title_change["item"]["item_key"] == "task3"  # Key unchanged
        assert result_title_change["item"]["title"] == "Updated Parent Task Title"
        
        # Verify parent title changed in database
        updated_task3 = manager.get_item("mcp_project", "task3")
        assert updated_task3.content == "Updated Parent Task Title"
        
        # Verify subitems under task3 are unchanged
        design_task3 = manager.get_item("mcp_project", "design", "task3")
        impl_task3_after = manager.get_item("mcp_project", "implementation", "task3")
        
        assert design_task3.content == "Design Phase for Task3"  # Unchanged
        assert impl_task3_after.content == "Implementation Phase"  # Unchanged
        
        # Verify subitems under task1 are also unchanged
        design_task1 = manager.get_item("mcp_project", "design", "task1") 
        impl_task1_after = manager.get_item("mcp_project", "implementation", "task1")
        
        assert design_task1.content == "Design Phase"  # Unchanged
        assert impl_task1_after.content == "Implementation Phase for Task1"  # Unchanged
        
        # Test changing title of subitem1 (design under task1) - should not affect other subitems
        result_subitem1_title = await todo_rename_item(
            list_key="mcp_project",
            item_key="task1",  # Parent key
            subitem_key="design",  # Subitem to rename
            new_title="Updated Design Phase for Task1"
        )
        
        assert result_subitem1_title["success"] == True
        assert "item" in result_subitem1_title
        assert result_subitem1_title["item"]["item_key"] == "design"  # Key unchanged
        assert result_subitem1_title["item"]["title"] == "Updated Design Phase for Task1"
        
        # Verify ALL titles are correct after subitem1 title change
        # Task1 subitems
        design_task1_updated = manager.get_item("mcp_project", "design", "task1")
        impl_task1_check = manager.get_item("mcp_project", "implementation", "task1")
        assert design_task1_updated.content == "Updated Design Phase for Task1"  # Changed
        assert impl_task1_check.content == "Implementation Phase for Task1"  # Unchanged
        
        # Task3 subitems (should be unchanged)
        design_task3_check = manager.get_item("mcp_project", "design", "task3")
        impl_task3_check = manager.get_item("mcp_project", "implementation", "task3")
        assert design_task3_check.content == "Design Phase for Task3"  # Unchanged
        assert impl_task3_check.content == "Implementation Phase"  # Unchanged
        
        # Parent items (should be unchanged)
        task1_check = manager.get_item("mcp_project", "task1")
        task2_check = manager.get_item("mcp_project", "task2")
        task3_check = manager.get_item("mcp_project", "task3")
        assert task1_check.content == "Original Task 1"  # Unchanged
        assert task2_check.content == "Task Implementation"  # Unchanged
        assert task3_check.content == "Updated Parent Task Title"  # From previous test
        
        # Test changing title of subitem3 (design under task3) - should not affect other subitems
        result_subitem3_title = await todo_rename_item(
            list_key="mcp_project",
            item_key="task3",  # Parent key
            subitem_key="design",  # Subitem to rename
            new_title="Updated Design Phase for Task3"
        )
        
        assert result_subitem3_title["success"] == True
        assert "item" in result_subitem3_title
        assert result_subitem3_title["item"]["item_key"] == "design"  # Key unchanged
        assert result_subitem3_title["item"]["title"] == "Updated Design Phase for Task3"
        
        # Verify ALL titles are correct after subitem3 title change
        # Task3 subitems
        design_task3_updated = manager.get_item("mcp_project", "design", "task3")
        impl_task3_final = manager.get_item("mcp_project", "implementation", "task3")
        assert design_task3_updated.content == "Updated Design Phase for Task3"  # Changed
        assert impl_task3_final.content == "Implementation Phase"  # Unchanged
        
        # Task1 subitems (should remain as from previous change)
        design_task1_final = manager.get_item("mcp_project", "design", "task1")
        impl_task1_final = manager.get_item("mcp_project", "implementation", "task1")
        assert design_task1_final.content == "Updated Design Phase for Task1"  # From previous test
        assert impl_task1_final.content == "Implementation Phase for Task1"  # Unchanged
        
        # Parent items (should be unchanged)
        task1_final = manager.get_item("mcp_project", "task1")
        task2_final = manager.get_item("mcp_project", "task2")
        task3_final = manager.get_item("mcp_project", "task3")
        assert task1_final.content == "Original Task 1"  # Unchanged
        assert task2_final.content == "Task Implementation"  # Unchanged
        assert task3_final.content == "Updated Parent Task Title"  # Unchanged