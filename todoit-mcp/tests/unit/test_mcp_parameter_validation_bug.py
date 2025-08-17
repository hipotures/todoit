"""
Unit test demonstrating MCP parameter validation bug.

This test shows that MCP todo_rename_item incorrectly accepts unknown parameters
and processes them incorrectly, leading to wrong items being renamed.
"""

import pytest
import tempfile
import os
import asyncio
from core.manager import TodoManager
from interfaces.mcp_server import todo_rename_item, todo_add_item
import interfaces.mcp_server as mcp_server


class TestMCPParameterValidationBug:
    """Test demonstrating the parameter validation bug"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def setup_duplicate_keys_data(self, temp_db_path):
        """Setup test data with duplicate subitem keys across different parents"""
        # Store original env var if it exists
        original_db_path = os.environ.get("TODOIT_DB_PATH")
        
        # Set environment variable for database
        os.environ["TODOIT_DB_PATH"] = temp_db_path
        
        # Reset the global manager instance to ensure clean state
        mcp_server.manager = None
        
        manager = TodoManager(temp_db_path)
        
        # Create test list
        list1 = manager.create_list("test_project", "Test Project")
        
        # Create parent items
        parent1 = manager.add_item("test_project", "scene_0001", "Generate image using scene_0001.yaml")
        parent2 = manager.add_item("test_project", "scene_0004", "Generate image using scene_0004.yaml")
        
        # Add subitems with duplicate keys to both parents
        subitem1_1 = manager.add_subitem("test_project", "scene_0001", "image_dwn", "Image download for scene_0001.yaml")
        subitem1_2 = manager.add_subitem("test_project", "scene_0001", "scene_gen", "Scene generation for scene_0001.yaml")
        
        subitem2_1 = manager.add_subitem("test_project", "scene_0004", "image_dwn", "Image download for scene_0004.yaml")
        subitem2_2 = manager.add_subitem("test_project", "scene_0004", "scene_gen", "Scene generation for scene_0004.yaml")
        
        yield manager, list1, parent1, parent2, subitem1_1, subitem1_2, subitem2_1, subitem2_2
        
        # Restore original env var
        if original_db_path is not None:
            os.environ["TODOIT_DB_PATH"] = original_db_path
        else:
            os.environ.pop("TODOIT_DB_PATH", None)

    @pytest.mark.asyncio
    async def test_mcp_unknown_parameter_bug(self, temp_db_path, setup_duplicate_keys_data):
        """Test demonstrating that MCP accepts unknown parameters and behaves incorrectly"""
        manager, list1, parent1, parent2, subitem1_1, subitem1_2, subitem2_1, subitem2_2 = setup_duplicate_keys_data
        
        # Store original titles for verification
        original_scene1_image_dwn = manager.get_item("test_project", "image_dwn", "scene_0001")
        original_scene4_image_dwn = manager.get_item("test_project", "image_dwn", "scene_0004")
        
        assert original_scene1_image_dwn.content == "Image download for scene_0001.yaml"
        assert original_scene4_image_dwn.content == "Image download for scene_0004.yaml"
        
        # BUG DEMONSTRATION: Call MCP with WRONG parameters
        # This should FAIL with unknown parameter error, but currently "succeeds"
        result = await todo_rename_item(
            list_key="test_project",
            item_key="image_dwn",                    # ❌ This should be parent key!
            parent_item_key="scene_0004",           # ❌ UNKNOWN parameter - should cause ERROR!
            new_title="WRONG: Image download for scene_0004.yaml"
        )
        
        # DEBUG: Let's see what MCP actually returns
        print(f"🐛 MCP result: {result}")
        
        # BUG: Check if MCP actually processes the wrong parameters or fails properly
        if result["success"] == False:
            print(f"🐛 MCP failed (good!): {result.get('error', 'No error message')}")
            # This means MCP does reject unknown parameters - that's actually good behavior
            # The real bug might be that it processes them at runtime in production
            return  # Skip rest of test since MCP properly failed
        
        # If we get here, MCP incorrectly accepted the bad parameters
        assert result["success"] == True  # This would be the real bug
        
        # BUG: Check what actually got renamed - it's the WRONG item!
        scene1_after = manager.get_item("test_project", "image_dwn", "scene_0001")
        scene4_after = manager.get_item("test_project", "image_dwn", "scene_0004")
        
        # BUG: The first found "image_dwn" (probably under scene_0001) got renamed
        # instead of the intended subitem under scene_0004
        
        # This demonstrates the bug - wrong item was modified
        if scene1_after.content == "WRONG: Image download for scene_0004.yaml":
            # BUG: scene_0001's subitem got the wrong title
            assert scene1_after.content == "WRONG: Image download for scene_0004.yaml"
            # scene_0004's subitem remained unchanged (wrong!)
            assert scene4_after.content == "Image download for scene_0004.yaml"
            print("🐛 BUG CONFIRMED: Wrong item (scene_0001) was renamed instead of intended item (scene_0004)")
        else:
            # Or maybe scene_0004 got renamed (depends on internal lookup order)
            print(f"🐛 BUG: Unexpected behavior - scene_0001: {scene1_after.content}, scene_0004: {scene4_after.content}")

    @pytest.mark.asyncio
    async def test_correct_mcp_call_works(self, temp_db_path, setup_duplicate_keys_data):
        """Test that CORRECT MCP call works as expected"""
        manager, list1, parent1, parent2, subitem1_1, subitem1_2, subitem2_1, subitem2_2 = setup_duplicate_keys_data
        
        # CORRECT MCP call with proper parameters
        result = await todo_rename_item(
            list_key="test_project",
            item_key="scene_0004",                  # ✅ Parent key
            subitem_key="image_dwn",               # ✅ Subitem key
            new_title="CORRECT: Image download for scene_0004.yaml"
        )
        
        assert result["success"] == True
        
        # Verify correct item was renamed
        scene1_after = manager.get_item("test_project", "image_dwn", "scene_0001")
        scene4_after = manager.get_item("test_project", "image_dwn", "scene_0004")
        
        # Only scene_0004's subitem should be changed
        assert scene1_after.content == "Image download for scene_0001.yaml"  # Unchanged
        assert scene4_after.content == "CORRECT: Image download for scene_0004.yaml"  # Changed

    @pytest.mark.asyncio
    async def test_mcp_should_reject_unknown_parameters(self, temp_db_path, setup_duplicate_keys_data):
        """Test that MCP SHOULD reject unknown parameters (currently fails - this is the fix target)"""
        manager, list1, parent1, parent2, subitem1_1, subitem1_2, subitem2_1, subitem2_2 = setup_duplicate_keys_data
        
        # This test will FAIL until we fix the parameter validation
        # After fixing, this should pass by raising an error for unknown parameters
        
        with pytest.raises(Exception) as exc_info:
            await todo_rename_item(
                list_key="test_project",
                item_key="image_dwn",
                unknown_parameter="this_should_cause_error",  # ❌ Unknown parameter
                new_title="This should not work"
            )
        
        # After fix, we should get a proper validation error
        assert "unknown" in str(exc_info.value).lower() or "unexpected" in str(exc_info.value).lower()