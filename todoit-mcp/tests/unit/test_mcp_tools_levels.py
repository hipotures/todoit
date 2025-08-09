"""
Unit tests for MCP tools level configuration system
Tests MINIMAL/STANDARD/MAX levels and tool registration
"""

import pytest
import os
from unittest.mock import patch


class TestMCPToolsLevels:
    """Test MCP tools level configuration and registration"""

    def test_tools_minimal_level(self):
        """Test that MINIMAL level registers correct tools"""
        
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'minimal'}):
            # Need to reload the module to pick up new env var
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import should_register_tool, TOOLS_MINIMAL
            
            # Test that MINIMAL tools should register
            assert should_register_tool('todo_create_list') == True
            assert should_register_tool('todo_get_list') == True
            assert should_register_tool('todo_add_item') == True
            assert should_register_tool('todo_update_item_status') == True
            assert should_register_tool('todo_get_progress') == True
            
            # Test that STANDARD/MAX tools should NOT register
            assert should_register_tool('todo_add_subtask') == False
            assert should_register_tool('todo_archive_list') == False
            assert should_register_tool('todo_add_item_dependency') == False
            assert should_register_tool('todo_delete_list') == False
            
            # Verify MINIMAL has exactly 10 tools
            assert len(TOOLS_MINIMAL) == 10

    def test_tools_standard_level(self):
        """Test that STANDARD level registers correct tools"""
        
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'standard'}):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import should_register_tool, TOOLS_STANDARD, TOOLS_MINIMAL
            
            # Test that MINIMAL tools should register
            assert should_register_tool('todo_create_list') == True
            assert should_register_tool('todo_add_item') == True
            
            # Test that STANDARD tools should register
            assert should_register_tool('todo_add_subtask') == True
            assert should_register_tool('todo_archive_list') == True
            assert should_register_tool('todo_quick_add') == True
            assert should_register_tool('todo_set_list_property') == True
            
            # Test that MAX-only tools should NOT register
            assert should_register_tool('todo_add_item_dependency') == False
            assert should_register_tool('todo_delete_list') == False
            assert should_register_tool('todo_delete_item') == False
            
            # Verify STANDARD has 23 tools (10 MINIMAL + 13 additional)
            assert len(TOOLS_STANDARD) == 23
            assert len(TOOLS_STANDARD) - len(TOOLS_MINIMAL) == 13

    def test_tools_max_level(self):
        """Test that MAX level registers all tools"""
        
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'max'}):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import should_register_tool
            
            # Test that all levels of tools should register
            assert should_register_tool('todo_create_list') == True  # MINIMAL
            assert should_register_tool('todo_add_subtask') == True  # STANDARD
            assert should_register_tool('todo_add_item_dependency') == True  # MAX
            assert should_register_tool('todo_delete_list') == True  # MAX
            assert should_register_tool('todo_delete_item') == True  # MAX
            assert should_register_tool('todo_report_errors') == True  # MAX
            assert should_register_tool('todo_get_comprehensive_status') == True  # MAX
            
            # Test some random tool names - should all return True for MAX
            assert should_register_tool('any_tool_name') == True

    def test_default_level_is_standard(self):
        """Test that default level is STANDARD when no env var is set"""
        
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import MCP_TOOLS_LEVEL, should_register_tool
            
            # Should default to 'standard'
            assert MCP_TOOLS_LEVEL == 'standard'
            
            # Should behave like STANDARD level
            assert should_register_tool('todo_create_list') == True  # MINIMAL
            assert should_register_tool('todo_add_subtask') == True  # STANDARD
            assert should_register_tool('todo_add_item_dependency') == False  # MAX only

    def test_unknown_level_defaults_to_standard(self):
        """Test that unknown level values default to STANDARD behavior"""
        
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'unknown_level'}):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import should_register_tool
            
            # Should behave like STANDARD level for unknown values
            assert should_register_tool('todo_create_list') == True  # MINIMAL
            assert should_register_tool('todo_add_subtask') == True  # STANDARD
            assert should_register_tool('todo_add_item_dependency') == False  # MAX only

    def test_level_case_insensitive(self):
        """Test that level configuration is case insensitive"""
        
        # Test uppercase
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'MINIMAL'}):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import MCP_TOOLS_LEVEL
            
            assert MCP_TOOLS_LEVEL == 'minimal'  # Should be normalized to lowercase

    def test_conditional_tool_decorator_registration(self):
        """Test that conditional_tool decorator works correctly"""
        
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'minimal'}):
            import importlib
            import interfaces.mcp_server
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import conditional_tool, should_register_tool
            
            # Mock function for testing
            def mock_tool_minimal():
                """Mock tool that should be registered in minimal"""
                return "minimal_result"
                
            def mock_tool_max_only():
                """Mock tool that should NOT be registered in minimal"""
                return "max_result"
            
            # Temporarily modify the tool name checking
            mock_tool_minimal.__name__ = 'todo_create_list'  # MINIMAL tool
            mock_tool_max_only.__name__ = 'todo_delete_list'  # MAX-only tool
            
            # Apply decorator
            registered_minimal = conditional_tool(mock_tool_minimal)
            registered_max_only = conditional_tool(mock_tool_max_only)
            
            # Check that the functions still work
            assert registered_minimal() == "minimal_result"
            assert registered_max_only() == "max_result"

    def test_tools_minimal_contains_essential_operations(self):
        """Test that MINIMAL level includes all essential operations"""
        
        import interfaces.mcp_server
        from interfaces.mcp_server import TOOLS_MINIMAL
        
        # Essential list operations
        assert 'todo_create_list' in TOOLS_MINIMAL
        assert 'todo_get_list' in TOOLS_MINIMAL
        assert 'todo_list_all' in TOOLS_MINIMAL
        
        # Essential item operations
        assert 'todo_add_item' in TOOLS_MINIMAL
        assert 'todo_update_item_status' in TOOLS_MINIMAL
        assert 'todo_get_list_items' in TOOLS_MINIMAL
        assert 'todo_get_item' in TOOLS_MINIMAL
        
        # Essential workflow
        assert 'todo_get_next_pending' in TOOLS_MINIMAL
        assert 'todo_get_progress' in TOOLS_MINIMAL
        assert 'todo_update_item_content' in TOOLS_MINIMAL

    def test_tools_standard_adds_useful_extensions(self):
        """Test that STANDARD level adds useful extensions to MINIMAL"""
        
        import interfaces.mcp_server
        from interfaces.mcp_server import TOOLS_STANDARD, TOOLS_MINIMAL
        
        # Should include all MINIMAL tools
        for tool in TOOLS_MINIMAL:
            assert tool in TOOLS_STANDARD
        
        # Should add convenience operations
        assert 'todo_quick_add' in TOOLS_STANDARD
        assert 'todo_mark_completed' in TOOLS_STANDARD
        assert 'todo_start_item' in TOOLS_STANDARD
        
        # Should add basic subtasks
        assert 'todo_add_subtask' in TOOLS_STANDARD
        assert 'todo_get_subtasks' in TOOLS_STANDARD
        
        # Should add archive management
        assert 'todo_archive_list' in TOOLS_STANDARD
        assert 'todo_unarchive_list' in TOOLS_STANDARD
        
        # Should add basic properties
        assert 'todo_set_list_property' in TOOLS_STANDARD
        assert 'todo_get_list_property' in TOOLS_STANDARD
        assert 'todo_set_item_property' in TOOLS_STANDARD
        assert 'todo_get_item_property' in TOOLS_STANDARD
        
        # Should add basic tagging
        assert 'todo_create_tag' in TOOLS_STANDARD
        assert 'todo_add_list_tag' in TOOLS_STANDARD

    def test_destructive_operations_excluded_from_minimal_and_standard(self):
        """Test that destructive operations are only available in MAX level"""
        
        import interfaces.mcp_server
        from interfaces.mcp_server import TOOLS_MINIMAL, TOOLS_STANDARD
        
        destructive_tools = ['todo_delete_list', 'todo_delete_item']
        
        # Should NOT be in MINIMAL
        for tool in destructive_tools:
            assert tool not in TOOLS_MINIMAL
            
        # Should NOT be in STANDARD
        for tool in destructive_tools:
            assert tool not in TOOLS_STANDARD
            
        # Should be available in MAX (test with max level)
        with patch.dict(os.environ, {'TODOIT_MCP_TOOLS_LEVEL': 'max'}):
            import importlib
            importlib.reload(interfaces.mcp_server)
            from interfaces.mcp_server import should_register_tool
            
            for tool in destructive_tools:
                assert should_register_tool(tool) == True