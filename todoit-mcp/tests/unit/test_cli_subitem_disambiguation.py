"""Tests for CLI commands correctly handling duplicate subitem names across different parents"""

import pytest
import tempfile
import os
from unittest.mock import patch
from click.testing import CliRunner
from core.manager import TodoManager
from interfaces.cli_modules.item_commands import item_status, item_edit, item_delete
from interfaces.cli_modules.item_commands import state_list, state_clear, state_remove


@pytest.fixture
def temp_db_path():
    """Create temporary database file path"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def setup_duplicate_subitems(temp_db_path):
    """Setup scenario with duplicate subitem names across different parents"""
    manager = TodoManager(db_path=temp_db_path)
    
    # Create a list
    manager.create_list("test_list", "Test List")
    
    # Create two parent tasks
    manager.add_item("test_list", "scene_0001", "Generate image using scene_01.yaml")
    manager.add_item("test_list", "scene_0002", "Generate image using scene_02.yaml")
    
    # Add subitems with same names to both parents
    manager.add_subitem("test_list", "scene_0001", "image_gen", "Image generation for scene 1")
    manager.add_subitem("test_list", "scene_0001", "audio_sync", "Audio sync for scene 1")
    
    manager.add_subitem("test_list", "scene_0002", "image_gen", "Image generation for scene 2")
    manager.add_subitem("test_list", "scene_0002", "audio_sync", "Audio sync for scene 2")
    
    return temp_db_path, manager


class TestCLISubitemDisambiguation:
    """Test CLI commands correctly target subitems by parent+subitem combination"""

    def test_item_status_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item status command updates the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        # Mock the context and database path
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # Update scene_0002/image_gen to failed
                result = runner.invoke(item_status, [
                    '--list', 'test_list',
                    '--item', 'scene_0002', 
                    '--subitem', 'image_gen',
                    '--status', 'failed'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Updated subitem 'image_gen' status to failed" in result.output
                
                # Verify scene_0002/image_gen is failed
                scene2_image_gen = manager.get_item("test_list", "image_gen", "scene_0002")
                assert scene2_image_gen.status == "failed"
                
                # Verify scene_0001/image_gen is still pending
                scene1_image_gen = manager.get_item("test_list", "image_gen", "scene_0001")
                assert scene1_image_gen.status == "pending"

    def test_item_edit_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item edit command updates the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # Edit scene_0001/audio_sync title
                result = runner.invoke(item_edit, [
                    '--list', 'test_list',
                    '--item', 'scene_0001',
                    '--subitem', 'audio_sync', 
                    '--title', 'UPDATED: Audio sync for scene 1'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Title updated for subitem 'audio_sync'" in result.output
                
                # Verify scene_0001/audio_sync was updated
                scene1_audio = manager.get_item("test_list", "audio_sync", "scene_0001")
                assert scene1_audio.content == "UPDATED: Audio sync for scene 1"
                
                # Verify scene_0002/audio_sync was NOT updated
                scene2_audio = manager.get_item("test_list", "audio_sync", "scene_0002")
                assert scene2_audio.content == "Audio sync for scene 2"

    def test_item_delete_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item delete command deletes the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # Delete scene_0002/image_gen with force flag
                result = runner.invoke(item_delete, [
                    '--list', 'test_list',
                    '--item', 'scene_0002',
                    '--subitem', 'image_gen',
                    '--force'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Subitem 'image_gen' deleted from list 'test_list'" in result.output
                
                # Verify scene_0002/image_gen was deleted
                scene2_image_gen = manager.get_item("test_list", "image_gen", "scene_0002")
                assert scene2_image_gen is None
                
                # Verify scene_0001/image_gen still exists
                scene1_image_gen = manager.get_item("test_list", "image_gen", "scene_0001")
                assert scene1_image_gen is not None
                assert scene1_image_gen.content == "Image generation for scene 1"

    def test_item_state_list_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item state list command targets the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        # Add some completion states to scene_0001/image_gen
        manager.update_item_status(
            "test_list", "image_gen", completion_states={"reviewed": True, "approved": False},
            parent_item_key="scene_0001"
        )
        
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # List states for scene_0001/image_gen
                result = runner.invoke(state_list, [
                    '--list', 'test_list',
                    '--item', 'scene_0001',
                    '--subitem', 'image_gen'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Completion states for subitem 'image_gen'" in result.output
                assert "reviewed" in result.output
                assert "approved" in result.output

    def test_item_state_clear_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item state clear command targets the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        # Add completion states to both subitems
        manager.update_item_status(
            "test_list", "image_gen", completion_states={"reviewed": True},
            parent_item_key="scene_0001"
        )
        manager.update_item_status(
            "test_list", "image_gen", completion_states={"tested": True},
            parent_item_key="scene_0002"
        )
        
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # Clear states for scene_0001/image_gen with force
                result = runner.invoke(state_clear, [
                    '--list', 'test_list',
                    '--item', 'scene_0001',
                    '--subitem', 'image_gen',
                    '--force'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Cleared all completion states from subitem 'image_gen'" in result.output
                
                # Verify scene_0001/image_gen states were cleared
                scene1_item = manager.get_item("test_list", "image_gen", "scene_0001")
                assert not scene1_item.completion_states
                
                # Verify scene_0002/image_gen states are still there
                scene2_item = manager.get_item("test_list", "image_gen", "scene_0002")
                assert scene2_item.completion_states == {"tested": True}

    def test_item_state_remove_targets_correct_subitem(self, setup_duplicate_subitems):
        """Test that item state remove command targets the correct subitem"""
        db_path, manager = setup_duplicate_subitems
        runner = CliRunner()
        
        # Add multiple completion states to both subitems
        manager.update_item_status(
            "test_list", "image_gen", 
            completion_states={"reviewed": True, "approved": False, "tested": True},
            parent_item_key="scene_0001"
        )
        manager.update_item_status(
            "test_list", "image_gen",
            completion_states={"reviewed": False, "deployed": True},
            parent_item_key="scene_0002"
        )
        
        with patch('interfaces.cli_modules.item_commands.get_manager') as mock_get_manager:
            with patch('interfaces.cli_modules.item_commands._check_list_access', return_value=True):
                mock_get_manager.return_value = manager
                
                # Remove specific states from scene_0001/image_gen with force
                result = runner.invoke(state_remove, [
                    '--list', 'test_list',
                    '--item', 'scene_0001',
                    '--subitem', 'image_gen',
                    '--state-keys', 'reviewed,tested',
                    '--force'
                ], obj={'db_path': db_path})
                
                assert result.exit_code == 0
                assert "Removed 2 completion state(s) from subitem 'image_gen'" in result.output
                
                # Verify scene_0001/image_gen had specific states removed
                scene1_item = manager.get_item("test_list", "image_gen", "scene_0001")
                assert scene1_item.completion_states == {"approved": False}  # Only this should remain
                
                # Verify scene_0002/image_gen states are untouched
                scene2_item = manager.get_item("test_list", "image_gen", "scene_0002")
                assert scene2_item.completion_states == {"reviewed": False, "deployed": True}


class TestManagerFunctionsWithParentKey:
    """Test manager functions correctly use parent_item_key parameter"""

    def test_get_item_with_parent_key(self, setup_duplicate_subitems):
        """Test manager.get_item() with parent_item_key parameter"""
        db_path, manager = setup_duplicate_subitems
        
        # Get specific subitems using parent_key
        scene1_image_gen = manager.get_item("test_list", "image_gen", "scene_0001")
        scene2_image_gen = manager.get_item("test_list", "image_gen", "scene_0002")
        
        assert scene1_image_gen is not None
        assert scene2_image_gen is not None
        assert scene1_image_gen.content == "Image generation for scene 1"
        assert scene2_image_gen.content == "Image generation for scene 2"
        
        # Verify they are different items
        assert scene1_image_gen.id != scene2_image_gen.id

    def test_update_item_status_with_parent_key(self, setup_duplicate_subitems):
        """Test manager.update_item_status() with parent_item_key parameter"""
        db_path, manager = setup_duplicate_subitems
        
        # Update scene_0001/image_gen to completed
        updated_item = manager.update_item_status(
            "test_list", "image_gen", "completed", parent_item_key="scene_0001"
        )
        
        assert updated_item.status == "completed"
        assert updated_item.content == "Image generation for scene 1"
        
        # Verify scene_0002/image_gen is still pending
        scene2_item = manager.get_item("test_list", "image_gen", "scene_0002")
        assert scene2_item.status == "pending"

    def test_update_item_content_with_parent_key(self, setup_duplicate_subitems):
        """Test manager.update_item_content() with parent_item_key parameter"""
        db_path, manager = setup_duplicate_subitems
        
        # Update scene_0002/audio_sync content
        updated_item = manager.update_item_content(
            "test_list", "audio_sync", "NEW: Audio sync for scene 2", parent_item_key="scene_0002"
        )
        
        assert updated_item.content == "NEW: Audio sync for scene 2"
        
        # Verify scene_0001/audio_sync is unchanged
        scene1_item = manager.get_item("test_list", "audio_sync", "scene_0001")
        assert scene1_item.content == "Audio sync for scene 1"

    def test_delete_item_with_parent_key(self, setup_duplicate_subitems):
        """Test manager.delete_item() with parent_item_key parameter"""
        db_path, manager = setup_duplicate_subitems
        
        # Delete scene_0001/audio_sync
        success = manager.delete_item("test_list", "audio_sync", parent_item_key="scene_0001")
        
        assert success is True
        
        # Verify scene_0001/audio_sync was deleted
        scene1_item = manager.get_item("test_list", "audio_sync", "scene_0001")
        assert scene1_item is None
        
        # Verify scene_0002/audio_sync still exists
        scene2_item = manager.get_item("test_list", "audio_sync", "scene_0002")
        assert scene2_item is not None
        assert scene2_item.content == "Audio sync for scene 2"

    def test_clear_item_completion_states_with_parent_key(self, setup_duplicate_subitems):
        """Test manager.clear_item_completion_states() with parent_item_key parameter"""
        db_path, manager = setup_duplicate_subitems
        
        # Add states to both subitems
        manager.update_item_status(
            "test_list", "image_gen", completion_states={"state1": True, "state2": False},
            parent_item_key="scene_0001"
        )
        manager.update_item_status(
            "test_list", "image_gen", completion_states={"state3": True},
            parent_item_key="scene_0002"
        )
        
        # Clear states from scene_0001/image_gen only
        updated_item = manager.clear_item_completion_states(
            "test_list", "image_gen", parent_item_key="scene_0001"
        )
        
        assert not updated_item.completion_states
        
        # Verify scene_0002/image_gen states are preserved
        scene2_item = manager.get_item("test_list", "image_gen", "scene_0002")
        assert scene2_item.completion_states == {"state3": True}


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_nonexistent_parent_item_key(self, setup_duplicate_subitems):
        """Test error handling when parent_item_key doesn't exist"""
        db_path, manager = setup_duplicate_subitems
        
        # Manager returns None for nonexistent parent instead of raising error
        result = manager.get_item("test_list", "image_gen", "nonexistent")
        assert result is None

    def test_nonexistent_subitem_under_valid_parent(self, setup_duplicate_subitems):
        """Test error handling when subitem doesn't exist under valid parent"""
        db_path, manager = setup_duplicate_subitems
        
        # This should return None (not raise exception)
        result = manager.get_item("test_list", "nonexistent_subitem", "scene_0001")
        assert result is None

    def test_parent_key_none_behavior(self, setup_duplicate_subitems):
        """Test that parent_key=None still works for main items"""
        db_path, manager = setup_duplicate_subitems
        
        # Get main item with explicit parent_key=None
        scene1 = manager.get_item("test_list", "scene_0001", None)
        assert scene1 is not None
        assert scene1.content == "Generate image using scene_01.yaml"
        
        # Get main item without parent_key (default None)
        scene2 = manager.get_item("test_list", "scene_0002")
        assert scene2 is not None
        assert scene2.content == "Generate image using scene_02.yaml"