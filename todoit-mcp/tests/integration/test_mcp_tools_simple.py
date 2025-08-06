"""
Test MCP Tools - Simple functionality test
Tests that MCP tools are properly defined and can be imported
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestMCPToolsSimple:
    """Simple tests for MCP tools functionality"""
    
    def test_mcp_server_imports(self):
        """Test that mcp_server can be imported without errors"""
        from interfaces import mcp_server
        assert hasattr(mcp_server, 'mcp')
    
    def test_mcp_tools_count(self):
        """Test that we have expected number of MCP tools"""
        import subprocess
        result = subprocess.run(['grep', '-c', '@mcp.tool()', 'interfaces/mcp_server.py'], 
                              capture_output=True, text=True)
        tool_count = int(result.stdout.strip())
        
        # We found 40 tools, expecting around 40+
        assert tool_count >= 40, f"Expected at least 40 MCP tools, found {tool_count}"
    
    def test_mcp_tool_categories_exist(self):
        """Test that expected categories of tools exist"""
        import subprocess
        
        # Check for basic CRUD tools
        result = subprocess.run(['grep', '-E', 'todo_(create|get|delete|list)', 'interfaces/mcp_server.py'], 
                              capture_output=True, text=True)
        basic_tools = result.stdout.count('async def')
        assert basic_tools >= 4, "Missing basic CRUD tools"
        
        # Check for subtask tools
        result = subprocess.run(['grep', '-E', 'subtask|hierarchy', 'interfaces/mcp_server.py'], 
                              capture_output=True, text=True)
        subtask_tools = result.stdout.count('async def')
        assert subtask_tools >= 3, "Missing subtask tools"
        
        # Check for dependency tools
        result = subprocess.run(['grep', '-E', 'dependency|blocked|blocker', 'interfaces/mcp_server.py'], 
                              capture_output=True, text=True)
        dependency_tools = result.stdout.count('async def')
        assert dependency_tools >= 3, "Missing dependency tools"
    
    def test_key_mcp_tools_exist(self):
        """Test that key MCP tools are defined"""
        with open('interfaces/mcp_server.py', 'r') as f:
            content = f.read()
        
        # Essential tools that must exist
        essential_tools = [
            'todo_create_list',
            'todo_add_item', 
            'todo_get_progress',
            'todo_add_subtask',
            'todo_get_subtasks',
            'todo_add_item_dependency',
            'todo_get_item_blockers',
            'todo_can_start_item'
        ]
        
        for tool in essential_tools:
            assert f'async def {tool}(' in content, f"Missing essential tool: {tool}"
    
    def test_mcp_tool_error_handler_exists(self):
        """Test that MCP error handler exists"""
        from interfaces.mcp_server import mcp_error_handler
        assert callable(mcp_error_handler)
    
    def test_mcp_manager_initialization(self):
        """Test that MCP manager can be initialized"""
        from interfaces.mcp_server import init_manager
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = init_manager(db_path)
            assert manager is not None
            assert hasattr(manager, 'create_list')
            assert hasattr(manager, 'add_item')
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_subtask_mcp_tools_exist(self):
        """Test that subtask-related MCP tools exist"""
        with open('interfaces/mcp_server.py', 'r') as f:
            content = f.read()
        
        subtask_tools = [
            'todo_add_subtask',
            'todo_get_subtasks', 
            'todo_get_item_hierarchy',
            'todo_move_to_subtask'
        ]
        
        for tool in subtask_tools:
            assert f'async def {tool}(' in content, f"Missing subtask tool: {tool}"
    
    def test_dependency_mcp_tools_exist(self):
        """Test that dependency-related MCP tools exist"""
        with open('interfaces/mcp_server.py', 'r') as f:
            content = f.read()
        
        dependency_tools = [
            'todo_add_item_dependency',
            'todo_remove_item_dependency',
            'todo_get_item_blockers',
            'todo_get_items_blocked_by',
            'todo_is_item_blocked',
            'todo_can_start_item'
        ]
        
        for tool in dependency_tools:
            assert f'async def {tool}(' in content, f"Missing dependency tool: {tool}"
    
    def test_smart_algorithm_mcp_tools_exist(self):
        """Test that smart algorithm MCP tools exist"""
        with open('interfaces/mcp_server.py', 'r') as f:
            content = f.read()
        
        smart_tools = [
            'todo_get_next_pending_smart',
            'todo_get_next_pending_enhanced',
            'todo_can_complete_item'
        ]
        
        found_tools = []
        for tool in smart_tools:
            if f'async def {tool}(' in content:
                found_tools.append(tool)
        
        # At least some smart algorithm tools should exist
        assert len(found_tools) >= 1, f"Missing smart algorithm tools. Found: {found_tools}"
    
    def test_progress_tracking_mcp_tools_exist(self):
        """Test that progress tracking MCP tools exist"""
        with open('interfaces/mcp_server.py', 'r') as f:
            content = f.read()
        
        progress_tools = [
            'todo_get_progress',
            'todo_get_cross_list_progress',
            'todo_get_comprehensive_status'
        ]
        
        found_tools = []
        for tool in progress_tools:
            if f'async def {tool}(' in content:
                found_tools.append(tool)
        
        # At least basic progress tracking should exist
        assert len(found_tools) >= 1, f"Missing progress tools. Found: {found_tools}"