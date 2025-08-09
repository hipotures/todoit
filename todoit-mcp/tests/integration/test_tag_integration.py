"""
Integration tests for tag functionality
Tests CLI and MCP integration with tag system
"""
import pytest
import asyncio
from core.manager import TodoManager
from interfaces.mcp_server import (
    todo_create_tag, todo_add_list_tag, todo_remove_list_tag, 
    todo_get_lists_by_tag, todo_list_all, init_manager
)
import tempfile
import os


@pytest.fixture
def integration_manager():
    """Create a temporary TodoManager for integration testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    try:
        manager = TodoManager(db_path)
        # Initialize global manager for MCP tools
        import interfaces.mcp_server
        interfaces.mcp_server.manager = manager
        yield manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


class TestMCPTagIntegration:
    """Test MCP tag tools integration"""
    
    @pytest.mark.asyncio
    async def test_mcp_tag_creation_flow(self, integration_manager):
        """Test complete MCP tag creation and assignment flow"""
        # Create tag via MCP
        result = await todo_create_tag("work", "blue", mgr=integration_manager)
        assert result["success"] is True
        assert result["tag"]["name"] == "work"
        
        # Create list
        integration_manager.create_list("test_project", "Test Project")
        
        # Add tag to list via MCP
        result = await todo_add_list_tag("test_project", "work", mgr=integration_manager)
        assert result["success"] is True
        
        # Get lists by tag via MCP
        result = await todo_get_lists_by_tag(["work"], mgr=integration_manager)
        assert result["success"] is True
        assert result["count"] == 1
        assert result["lists"][0]["list_key"] == "test_project"
        assert len(result["lists"][0]["tags"]) == 1
        assert result["lists"][0]["tags"][0]["name"] == "work"
    
    @pytest.mark.asyncio
    async def test_mcp_list_all_with_tag_filtering(self, integration_manager):
        """Test todo_list_all with tag filtering"""
        # Setup data
        integration_manager.create_list("work1", "Work List 1")
        integration_manager.create_list("work2", "Work List 2") 
        integration_manager.create_list("personal1", "Personal List")
        
        integration_manager.add_tag_to_list("work1", "work")
        integration_manager.add_tag_to_list("work2", "work")
        integration_manager.add_tag_to_list("personal1", "personal")
        
        # Test filtering via MCP
        result = await todo_list_all(filter_tags=["work"], mgr=integration_manager)
        assert result["success"] is True
        assert result["count"] == 2
        assert "filter_applied" in result
        assert result["filter_applied"]["tag_filter"] == ["work"]
        
        # Verify all returned lists have tags
        for list_data in result["lists"]:
            assert "tags" in list_data
            assert len(list_data["tags"]) > 0
    
    @pytest.mark.asyncio  
    async def test_mcp_tag_removal(self, integration_manager):
        """Test tag removal via MCP"""
        # Setup
        integration_manager.create_list("test_list", "Test List")
        integration_manager.add_tag_to_list("test_list", "temp_tag")
        
        # Remove tag via MCP
        result = await todo_remove_list_tag("test_list", "temp_tag", mgr=integration_manager)
        assert result["success"] is True
        
        # Verify removal
        tags = integration_manager.get_tags_for_list("test_list")
        assert len(tags) == 0


class TestCLITagIntegration:
    """Test CLI tag integration"""
    
    def test_cli_environment_variable_integration(self, integration_manager, monkeypatch):
        """Test that CLI respects TODOIT_FILTER_TAGS environment variable"""
        from interfaces.cli_modules.tag_commands import _get_filter_tags
        
        # Test with environment variable only
        monkeypatch.setenv('TODOIT_FILTER_TAGS', 'work,urgent')
        tags = _get_filter_tags()
        assert set(tags) == {'work', 'urgent'}
        
        # Test with CLI tags only
        monkeypatch.delenv('TODOIT_FILTER_TAGS', raising=False)
        tags = _get_filter_tags(['personal', 'home'])
        assert set(tags) == {'personal', 'home'}
        
        # Test with both (should be union)
        monkeypatch.setenv('TODOIT_FILTER_TAGS', 'work,urgent')
        tags = _get_filter_tags(['personal', 'work'])  # work appears in both
        assert set(tags) == {'work', 'urgent', 'personal'}  # unique union
    
    def test_tag_normalization_consistency(self, integration_manager):
        """Test that tags are consistently normalized across CLI and MCP"""
        # Create tag via manager (simulating CLI)
        tag1 = integration_manager.create_tag("WORK", "blue")
        assert tag1.name == "work"
        
        # Try to create same tag with different case - should fail
        with pytest.raises(ValueError):
            integration_manager.create_tag("Work", "red")
        
        # Test case-insensitive retrieval
        retrieved = integration_manager.get_tag("WORK")
        assert retrieved is not None
        assert retrieved.name == "work"


class TestTagFilteringEdgeCases:
    """Test edge cases in tag filtering"""
    
    def test_empty_tag_filtering(self, integration_manager):
        """Test behavior with empty tag filters"""
        integration_manager.create_list("test1", "Test 1")
        integration_manager.create_list("test2", "Test 2")
        
        # Test empty filter should return all lists
        all_lists = integration_manager.list_all(filter_tags=[])
        assert len(all_lists) == 2
        
        # Test None filter should return all lists  
        all_lists = integration_manager.list_all(filter_tags=None)
        assert len(all_lists) == 2
        
        # Test non-existent tag should return empty
        no_lists = integration_manager.list_all(filter_tags=["nonexistent"])
        assert len(no_lists) == 0
    
    def test_archived_lists_with_tags(self, integration_manager):
        """Test tag filtering with archived lists"""
        # Setup
        integration_manager.create_list("active_work", "Active Work")
        integration_manager.create_list("archived_work", "Archived Work")
        
        integration_manager.add_tag_to_list("active_work", "work")
        integration_manager.add_tag_to_list("archived_work", "work")
        
        # Archive one list
        integration_manager.archive_list("archived_work", force=True)
        
        # Test filtering should only return active lists by default
        work_lists = integration_manager.list_all(filter_tags=["work"])
        assert len(work_lists) == 1
        assert work_lists[0].list_key == "active_work"
        
        # Test with include_archived
        all_work_lists = integration_manager.list_all(filter_tags=["work"], include_archived=True)
        assert len(all_work_lists) == 2