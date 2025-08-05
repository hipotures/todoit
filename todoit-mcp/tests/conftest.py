"""
Pytest configuration and fixtures for TODOIT MCP tests
"""
import pytest
import tempfile
import os
from pathlib import Path
from core.manager import TodoManager
from core.database import Database


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def manager(temp_db):
    """Create TodoManager with temporary database"""
    return TodoManager(temp_db)


@pytest.fixture
def sample_list(manager):
    """Create sample list with items for testing"""
    list_obj = manager.create_list(
        list_key="test_list",
        title="Test List",
        items=["Task 1", "Task 2", "Task 3"]
    )
    return list_obj


@pytest.fixture
def sample_lists(manager):
    """Create multiple lists for cross-list dependency testing"""
    backend_list = manager.create_list(
        list_key="backend",
        title="Backend Tasks",
        items=["Setup DB", "Create API", "Write tests"]
    )
    
    frontend_list = manager.create_list(
        list_key="frontend", 
        title="Frontend Tasks",
        items=["Setup UI", "Connect API", "User testing"]
    )
    
    return {"backend": backend_list, "frontend": frontend_list}