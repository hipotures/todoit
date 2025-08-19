"""
Smoke tests for TODOIT MCP - basic system health checks.

These tests verify that the core system functionality works without deep testing.
Smoke tests should be fast and catch major system failures quickly.
"""

import pytest
import tempfile
import os
from core.manager import TodoManager
from core.models import ItemStatus


class TestSmoke:
    """Basic smoke tests for system health"""
    
    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for smoke tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_system_startup(self, temp_manager):
        """Test that system can start up without errors"""
        # If we got here, the system started successfully
        assert temp_manager is not None
        assert hasattr(temp_manager, 'db')
    
    def test_basic_crud_operations(self, temp_manager):
        """Test basic Create-Read-Update-Delete operations work"""
        # Create list
        list_obj = temp_manager.create_list("test", "Test List")
        assert list_obj.list_key == "test"
        
        # Add item  
        item = temp_manager.add_item("test", "task1", "Test Task")
        assert item.item_key == "task1"
        
        # Read item
        retrieved = temp_manager.get_item("test", "task1")
        assert retrieved.content == "Test Task"
        
        # Update status
        temp_manager.update_item_status("test", "task1", ItemStatus.COMPLETED)
        updated = temp_manager.get_item("test", "task1")
        assert updated.status == ItemStatus.COMPLETED
        
        # Delete works via cascade when list is deleted
        temp_manager.delete_list("test")
        with pytest.raises(ValueError):
            temp_manager.get_item("test", "task1")
    
    def test_database_connectivity(self, temp_manager):
        """Test that database operations work"""
        # Test database is responsive
        lists = temp_manager.list_all()
        assert isinstance(lists, list)
        
        # Test transaction works
        temp_manager.create_list("test", "Test")
        lists = temp_manager.list_all()
        assert len([l for l in lists if l.list_key == "test"]) == 1
    
    def test_core_algorithms_work(self, temp_manager):
        """Test that core business logic algorithms work"""
        # Create test data
        temp_manager.create_list("test", "Test")
        temp_manager.add_item("test", "task1", "Task 1")
        temp_manager.add_item("test", "task2", "Task 2")
        
        # Test next pending algorithm
        next_task = temp_manager.get_next_pending("test")
        assert next_task is not None
        assert next_task.item_key in ["task1", "task2"]
        
        # Test status transitions
        temp_manager.update_item_status("test", "task1", ItemStatus.IN_PROGRESS)
        task1 = temp_manager.get_item("test", "task1")
        assert task1.status == ItemStatus.IN_PROGRESS
    
    def test_subtask_hierarchy(self, temp_manager):
        """Test basic subtask functionality works"""
        temp_manager.create_list("test", "Test")
        
        # Add parent task
        parent = temp_manager.add_item("test", "parent", "Parent Task")
        
        # Add subtask
        subtask = temp_manager.add_subitem("test", "parent", "child", "Child Task")
        assert subtask.parent_item_id == parent.id
        
        # Test hierarchy retrieval via get_list_items
        all_items = temp_manager.get_list_items("test")
        children = [item for item in all_items if item.parent_item_id == parent.id]
        assert len(children) == 1
        assert children[0].item_key == "child"
    
    def test_critical_imports(self):
        """Test that critical modules can be imported"""
        # Core modules
        from core.manager import TodoManager
        from core.models import TodoList, TodoItem, ItemStatus
        from core.database import Database
        
        # Interface modules
        from interfaces.mcp_server import mcp
        from interfaces.cli import cli
        
        # All imports successful
        assert True
    
    def test_model_validation(self):
        """Test that basic model validation works"""
        from core.models import TodoList, TodoItem, ItemStatus
        from datetime import datetime
        
        # Test valid model creation
        list_data = {
            'id': 1,
            'list_key': 'test',
            'title': 'Test List',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'active',
            'list_type': 'sequential'
        }
        
        todo_list = TodoList(**list_data)
        assert todo_list.list_key == 'test'
        assert todo_list.title == 'Test List'
    
    def test_mcp_server_basic(self):
        """Test that MCP server can be initialized"""
        from interfaces.mcp_server import mcp
        
        # Server should be initialized without errors
        assert mcp is not None
        assert hasattr(mcp, 'list_tools')
        
        # Basic MCP server functionality test (can't easily test async list_tools in sync test)
        assert hasattr(mcp, 'tool')
        assert hasattr(mcp, 'run')


class TestSmokePerformance:
    """Basic performance smoke tests"""
    
    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for smoke tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_reasonable_response_time(self, temp_manager):
        """Test that basic operations complete in reasonable time"""
        import time
        
        # Create list should be fast
        start = time.time()
        temp_manager.create_list("test", "Test List")
        list_time = time.time() - start
        assert list_time < 1.0  # Should be under 1 second
        
        # Add item should be fast
        start = time.time()
        temp_manager.add_item("test", "task1", "Test Task")
        item_time = time.time() - start
        assert item_time < 1.0  # Should be under 1 second
        
        # Get item should be very fast
        start = time.time()
        temp_manager.get_item("test", "task1")
        get_time = time.time() - start
        assert get_time < 0.5  # Should be under 0.5 seconds
    
    def test_small_dataset_performance(self, temp_manager):
        """Test performance with small dataset"""
        import time
        
        temp_manager.create_list("test", "Test")
        
        # Add 10 items quickly
        start = time.time()
        for i in range(10):
            temp_manager.add_item("test", f"task{i}", f"Task {i}")
        bulk_time = time.time() - start
        
        # Should complete 10 items in reasonable time
        assert bulk_time < 5.0  # Should be under 5 seconds
        
        # List all should be fast
        start = time.time()
        items = temp_manager.get_list_items("test")
        list_time = time.time() - start
        
        assert len(items) == 10
        assert list_time < 1.0  # Should be under 1 second