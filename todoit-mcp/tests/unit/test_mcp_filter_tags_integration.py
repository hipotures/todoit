"""Integration tests for filter_tags parameter in MCP tools.

This module tests the filter_tags functionality using real TodoManager instances
following the established testing pattern for MCP functions.
"""

import os
import pytest
import tempfile
from pathlib import Path

from core.manager import TodoManager
from interfaces.mcp_server import (
    todo_get_list,
    todo_create_list,
    todo_list_all,
    todo_get_list_items,
    todo_add_item_dependency,
    todo_get_item_blockers,
    _check_list_access,
)


@pytest.fixture
def manager_with_tagged_lists():
    """Create TodoManager with test lists that have different tags."""
    # Use temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    try:
        manager = TodoManager(db_path)
        
        # Create lists with different tags
        dev_list = manager.create_list('dev_project', 'Development Project')
        prod_list = manager.create_list('prod_release', 'Production Release')
        test_list = manager.create_list('test_features', 'Test Features')
        
        # Add tags to lists
        manager.add_tag_to_list('dev_project', 'development')
        manager.add_tag_to_list('dev_project', 'urgent')
        
        manager.add_tag_to_list('prod_release', 'production')
        manager.add_tag_to_list('prod_release', 'stable')
        
        manager.add_tag_to_list('test_features', 'testing')
        manager.add_tag_to_list('test_features', 'development')  # Shared tag
        
        # Add some items
        manager.add_item('dev_project', 'feature1', 'New feature')
        manager.add_item('prod_release', 'fix1', 'Bug fix')
        manager.add_item('test_features', 'test1', 'Test case')
        
        yield manager
        
    finally:
        # Clean up
        Path(db_path).unlink(missing_ok=True)


class TestMCPFilterTagsIntegration:
    """Integration tests for MCP filter_tags functionality."""
    
    def _setup_mcp_manager(self, manager):
        """Helper to set up global manager for MCP tests"""
        import interfaces.mcp_server
        old_manager = interfaces.mcp_server.manager
        interfaces.mcp_server.manager = manager
        return old_manager
    
    def _restore_mcp_manager(self, old_manager):
        """Helper to restore global manager after MCP tests"""
        import interfaces.mcp_server
        interfaces.mcp_server.manager = old_manager
    
    def test_check_list_access_helper_real_data(self, manager_with_tagged_lists):
        """Test _check_list_access helper with real tag data."""
        manager = manager_with_tagged_lists
        
        # Test no filter_tags (always accessible)
        assert _check_list_access(manager, 'dev_project', None) is True
        assert _check_list_access(manager, 'dev_project', []) is True
        
        # Test with matching tags
        assert _check_list_access(manager, 'dev_project', ['development']) is True
        assert _check_list_access(manager, 'dev_project', ['urgent']) is True
        assert _check_list_access(manager, 'dev_project', ['development', 'testing']) is True  # OR logic
        
        # Test with non-matching tags
        assert _check_list_access(manager, 'dev_project', ['production']) is False
        assert _check_list_access(manager, 'dev_project', ['nonexistent']) is False
        
        # Test case insensitive
        assert _check_list_access(manager, 'dev_project', ['DEVELOPMENT']) is True
    
    @pytest.mark.asyncio
    async def test_todo_list_all_with_filter_tags(self, manager_with_tagged_lists):
        """Test todo_list_all with filter_tags filtering."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Test with no filter_tags (should return all lists)
            result = await todo_list_all(mgr=manager)
            assert result['success'] is True
            assert len(result['lists']) == 3
            
            # Test with development tag (should return dev_project and test_features)
            result = await todo_list_all(filter_tags=['development'], mgr=manager)
            assert result['success'] is True
            assert len(result['lists']) == 2
            list_keys = [lst['list_key'] for lst in result['lists']]
            assert 'dev_project' in list_keys
            assert 'test_features' in list_keys
            assert 'prod_release' not in list_keys
            
            # Test with production tag (should return only prod_release)
            result = await todo_list_all(filter_tags=['production'], mgr=manager)
            assert result['success'] is True
            assert len(result['lists']) == 1
            assert result['lists'][0]['list_key'] == 'prod_release'
            
            # Test with non-existent tag (should return empty list)
            result = await todo_list_all(filter_tags=['nonexistent'], mgr=manager)
            assert result['success'] is True
            assert len(result['lists']) == 0
            
        finally:
            self._restore_mcp_manager(old_manager)
    
    @pytest.mark.asyncio
    async def test_todo_get_list_with_filter_tags(self, manager_with_tagged_lists):
        """Test todo_get_list with filter_tags access control."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Test with no filter_tags (should always work)
            result = await todo_get_list('dev_project', mgr=manager)
            assert result['success'] is True
            
            # Test with matching filter_tags
            result = await todo_get_list('dev_project', filter_tags=['development'], mgr=manager)
            assert result['success'] is True
            
            # Test with non-matching filter_tags
            result = await todo_get_list('dev_project', filter_tags=['production'], mgr=manager)
            assert result['success'] is False
            assert 'does not match tag filter' in result['error']
            
            # Test with multiple filter_tags (OR logic)
            result = await todo_get_list('dev_project', filter_tags=['production', 'development'], mgr=manager)
            assert result['success'] is True  # Matches 'development'
            
        finally:
            self._restore_mcp_manager(old_manager)
    
    # Note: todo_create_list uses 'tags' parameter, not 'filter_tags'
    # The 'tags' parameter is for assigning tags to the created list, 
    # not for filtering access like 'filter_tags' in other functions.
    # Since todo_create_list doesn't accept mgr parameter, we can't test it in isolation.
    
    @pytest.mark.asyncio
    async def test_todo_get_list_items_with_filter_tags(self, manager_with_tagged_lists):
        """Test todo_get_list_items with filter_tags access control."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Test with matching filter_tags
            result = await todo_get_list_items('dev_project', filter_tags=['development'], mgr=manager)
            assert result['success'] is True
            assert len(result['items']) == 1
            assert result['items'][0]['item_key'] == 'feature1'
            
            # Test with non-matching filter_tags
            result = await todo_get_list_items('dev_project', filter_tags=['production'], mgr=manager)
            assert result['success'] is False
            assert 'does not match tag filter' in result['error']
            
        finally:
            self._restore_mcp_manager(old_manager)
    
    @pytest.mark.asyncio
    async def test_cross_list_dependency_with_filter_tags(self, manager_with_tagged_lists):
        """Test cross-list dependency functions with filter_tags."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Test adding dependency with both lists matching filter_tags
            result = await todo_add_item_dependency(
                'dev_project', 'feature1', 
                'test_features', 'test1',
                filter_tags=['development'], 
                mgr=manager
            )
            assert result['success'] is True
            
            # Test adding dependency with one list not matching
            result = await todo_add_item_dependency(
                'dev_project', 'feature1', 
                'prod_release', 'fix1',
                filter_tags=['development'], 
                mgr=manager
            )
            assert result['success'] is False
            assert 'Required list' in result['error'] and 'does not match tag filter' in result['error']
            
            # Test getting item blockers
            result = await todo_get_item_blockers(
                'test_features', 'test1',
                filter_tags=['development'], 
                mgr=manager
            )
            assert result['success'] is True
            
            # Test getting item blockers with non-matching tags
            result = await todo_get_item_blockers(
                'test_features', 'test1',
                filter_tags=['production'], 
                mgr=manager
            )
            assert result['success'] is False
            
        finally:
            self._restore_mcp_manager(old_manager)


class TestMCPFilterTagsEdgeCases:
    """Test edge cases for MCP filter_tags functionality."""
    
    def _setup_mcp_manager(self, manager):
        """Helper to set up global manager for MCP tests"""
        import interfaces.mcp_server
        old_manager = interfaces.mcp_server.manager
        interfaces.mcp_server.manager = manager
        return old_manager
    
    def _restore_mcp_manager(self, old_manager):
        """Helper to restore global manager after MCP tests"""
        import interfaces.mcp_server
        interfaces.mcp_server.manager = old_manager
    
    @pytest.mark.asyncio
    async def test_empty_filter_tags(self, manager_with_tagged_lists):
        """Test behavior with empty filter_tags list."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Empty list should behave like None (no filtering)
            result = await todo_get_list('dev_project', filter_tags=[], mgr=manager)
            assert result['success'] is True
            
        finally:
            self._restore_mcp_manager(old_manager)
    
    @pytest.mark.asyncio 
    async def test_case_insensitive_matching(self, manager_with_tagged_lists):
        """Test that filter_tags matching is case-insensitive."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Test with uppercase filter_tags
            result = await todo_get_list('dev_project', filter_tags=['DEVELOPMENT'], mgr=manager)
            assert result['success'] is True
            
            # Test with mixed case
            result = await todo_get_list('dev_project', filter_tags=['Development'], mgr=manager)
            assert result['success'] is True
            
        finally:
            self._restore_mcp_manager(old_manager)
    
    def test_list_with_no_tags(self, manager_with_tagged_lists):
        """Test behavior when list has no tags."""
        manager = manager_with_tagged_lists
        
        # Create list without tags
        manager.create_list('no_tags_list', 'List Without Tags')
        
        # Should not match any filter_tags
        assert _check_list_access(manager, 'no_tags_list', ['development']) is False
        
        # Should always be accessible without filter_tags
        assert _check_list_access(manager, 'no_tags_list', None) is True
        assert _check_list_access(manager, 'no_tags_list', []) is True


class TestFilterTagsDocumentationExamples:
    """Test realistic scenarios from documentation."""
    
    def _setup_mcp_manager(self, manager):
        """Helper to set up global manager for MCP tests"""
        import interfaces.mcp_server
        old_manager = interfaces.mcp_server.manager
        interfaces.mcp_server.manager = manager
        return old_manager
    
    def _restore_mcp_manager(self, old_manager):
        """Helper to restore global manager after MCP tests"""
        import interfaces.mcp_server
        interfaces.mcp_server.manager = old_manager
    
    @pytest.mark.asyncio
    async def test_development_environment_scenario(self, manager_with_tagged_lists):
        """Test development environment isolation scenario."""
        manager = manager_with_tagged_lists
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Developer working in development environment
            # Should only see development-tagged lists
            result = await todo_list_all(filter_tags=['development'], mgr=manager)
            
            assert result['success'] is True
            assert len(result['lists']) == 2  # dev_project and test_features both have 'development'
            
            list_keys = [lst['list_key'] for lst in result['lists']]
            assert 'dev_project' in list_keys
            assert 'test_features' in list_keys
            assert 'prod_release' not in list_keys  # Production list filtered out
            
            # Developer tries to access production list directly
            result = await todo_get_list('prod_release', filter_tags=['development'], mgr=manager)
            assert result['success'] is False
            assert 'does not match tag filter' in result['error']
            
        finally:
            self._restore_mcp_manager(old_manager)