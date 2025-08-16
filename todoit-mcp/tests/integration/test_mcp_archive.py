"""
MCP Tools Tests for Archive Functionality
Tests the MCP interface for archiving with validation
"""

import pytest
import tempfile
import os
import asyncio
from core.manager import TodoManager
from interfaces.mcp_server import todo_archive_list, todo_unarchive_list, init_manager
from unittest.mock import patch, MagicMock


class TestMCPArchiveTools:
    """Test MCP archive tools with validation"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def setup_test_lists(self, temp_db_path):
        """Setup test lists for archiving tests"""
        manager = TodoManager(temp_db_path)

        # Create test lists with different completion states
        empty_list = manager.create_list("empty-list", "Empty List")

        completed_list = manager.create_list(
            "completed-list", "Completed List", items=["Item 1", "Item 2"]
        )
        manager.update_item_status("completed-list", "item_1", "completed")
        manager.update_item_status("completed-list", "item_2", "completed")

        incomplete_list = manager.create_list(
            "incomplete-list", "Incomplete List", items=["Item A", "Item B", "Item C"]
        )
        manager.update_item_status(
            "incomplete-list", "item_1", "completed"
        )  # 1/3 completed

        return temp_db_path, manager

    def test_mcp_archive_empty_list_without_force(self, setup_test_lists):
        """Test MCP archiving empty list succeeds without force"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Archive empty list without force
            result = asyncio.run(todo_archive_list("empty-list", force=False))

            assert result["success"] is True
            assert result["list"]["list_key"] == "empty-list"
            assert result["list"]["status"] == "archived"
            assert "archived successfully" in result["message"]

    def test_mcp_archive_completed_list_without_force(self, setup_test_lists):
        """Test MCP archiving completed list succeeds without force"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Archive completed list without force
            result = asyncio.run(todo_archive_list("completed-list", force=False))

            assert result["success"] is True
            assert result["list"]["list_key"] == "completed-list"
            assert result["list"]["status"] == "archived"

    def test_mcp_archive_incomplete_list_without_force_fails(self, setup_test_lists):
        """Test MCP archiving incomplete list fails without force"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Try to archive incomplete list without force
            result = asyncio.run(todo_archive_list("incomplete-list", force=False))

            assert result["success"] is False
            assert "Cannot archive list with incomplete tasks" in result["error"]
            assert "Incomplete: 2/3 tasks" in result["error"]
            assert "Use force=True to archive anyway" in result["error"]

    def test_mcp_archive_incomplete_list_with_force_succeeds(self, setup_test_lists):
        """Test MCP archiving incomplete list succeeds with force=True"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Archive incomplete list with force=True
            result = asyncio.run(todo_archive_list("incomplete-list", force=True))

            assert result["success"] is True
            assert result["list"]["list_key"] == "incomplete-list"
            assert result["list"]["status"] == "archived"

    def test_mcp_archive_nonexistent_list(self, setup_test_lists):
        """Test MCP archiving non-existent list fails"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Try to archive non-existent list
            result = asyncio.run(todo_archive_list("nonexistent", force=False))

            assert result["success"] is False
            assert "does not exist" in result["error"]

    def test_mcp_archive_already_archived_list_fails(self, setup_test_lists):
        """Test MCP archiving already archived list fails"""
        temp_db_path, manager = setup_test_lists

        # First archive a list
        manager.archive_list("empty-list", force=True)

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Try to archive again
            result = asyncio.run(todo_archive_list("empty-list", force=False))

            assert result["success"] is False
            assert "is already archived" in result["error"]

    def test_mcp_unarchive_list_still_works(self, setup_test_lists):
        """Test that MCP unarchive functionality is unchanged"""
        temp_db_path, manager = setup_test_lists

        # Archive a list first
        manager.archive_list("empty-list", force=True)

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Unarchive it
            result = asyncio.run(todo_unarchive_list("empty-list"))

            assert result["success"] is True
            assert result["list"]["list_key"] == "empty-list"
            assert result["list"]["status"] == "active"

    def test_mcp_archive_force_parameter_defaults_to_false(self, setup_test_lists):
        """Test that force parameter defaults to False when not specified"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Archive incomplete list without specifying force (should default to False)
            result = asyncio.run(
                todo_archive_list("incomplete-list")
            )  # No force parameter

            assert result["success"] is False
            assert "Cannot archive list with incomplete tasks" in result["error"]

    def test_mcp_archive_handles_manager_exceptions(self, setup_test_lists):
        """Test that MCP tool handles manager exceptions properly"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            # Mock manager to raise an exception
            mock_manager = MagicMock()
            mock_manager.archive_list.side_effect = Exception("Database error")
            mock_init.return_value = mock_manager

            # Should return error response
            result = asyncio.run(todo_archive_list("any-list", force=False))

            assert result["success"] is False
            assert "Database error" in result["error"]

    def test_mcp_archive_with_various_force_values(self, setup_test_lists):
        """Test MCP archive with different force parameter values"""
        temp_db_path, manager = setup_test_lists

        with patch("interfaces.mcp_server.init_manager") as mock_init:
            mock_init.return_value = manager

            # Test with explicit False
            result = asyncio.run(todo_archive_list("incomplete-list", force=False))
            assert result["success"] is False

            # Test with explicit True
            result = asyncio.run(todo_archive_list("incomplete-list", force=True))
            assert result["success"] is True
