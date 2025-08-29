"""
Pytest configuration and fixtures for TODOIT MCP tests
"""

import os
import tempfile
from pathlib import Path

import pytest

from core.database import Database
from core.manager import TodoManager


@pytest.fixture(scope="session", autouse=True)
def disable_force_tags_for_tests():
    """Disable FORCE_TAGS environment isolation during tests"""
    # Save original value if it exists
    original_force_tags = os.environ.get("TODOIT_FORCE_TAGS")

    # Remove FORCE_TAGS to disable environment isolation during tests
    if "TODOIT_FORCE_TAGS" in os.environ:
        del os.environ["TODOIT_FORCE_TAGS"]

    yield

    # Restore original value if it existed
    if original_force_tags is not None:
        os.environ["TODOIT_FORCE_TAGS"] = original_force_tags


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
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
        list_key="test_list", title="Test List", items=["Item 1", "Item 2", "Item 3"]
    )
    return list_obj


@pytest.fixture
def sample_lists(manager):
    """Create multiple lists for cross-list dependency testing"""
    backend_list = manager.create_list(
        list_key="backend",
        title="Backend Tasks",
        items=["Setup DB", "Create API", "Write tests"],
    )

    frontend_list = manager.create_list(
        list_key="frontend",
        title="Frontend Tasks",
        items=["Setup UI", "Connect API", "User testing"],
    )

    return {"backend": backend_list, "frontend": frontend_list}
