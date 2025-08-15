"""
Tests for JSON output fixes in CLI and MCP
"""

import pytest
import json
import os
from core.manager import TodoManager
from interfaces.cli_modules.display import _render_table_view, _get_output_format
from interfaces.mcp_server import todo_get_list


@pytest.fixture
def manager_with_test_list(tmp_path):
    """Create manager with test list and properties"""
    db_path = tmp_path / "test_json_output.db"
    manager = TodoManager(str(db_path))

    # Create test list with unique name to avoid conflicts
    list_key = "json_test_list"
    # Create test list
    test_list = manager.create_list(list_key, "Test List")
    
    # Add some items
    manager.add_item(list_key, "item1", "First item")
    manager.add_item(list_key, "item2", "Second item")
    manager.update_item_status(list_key, "item1", status="completed")
    
    # Add properties
    manager.set_list_property(list_key, "project_id", "test-123")
    manager.set_list_property(list_key, "environment", "development")

    return manager, list_key


class TestCLIJSONOutputFix:
    """Test CLI JSON output fixes"""

    def test_cli_json_single_output(self, manager_with_test_list, monkeypatch, capsys):
        """Test that CLI list show returns single JSON in JSON mode"""
        manager, list_key = manager_with_test_list
        
        # Set JSON output format
        monkeypatch.setenv("TODOIT_OUTPUT_FORMAT", "json")
        
        # Get test data
        todo_list = manager.get_list(list_key)
        items = manager.get_list_items(list_key)
        properties = manager.get_list_properties(list_key)
        
        # Call the fixed function
        _render_table_view(todo_list, items, properties, manager)
        
        # Capture output
        captured = capsys.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        # Should be single JSON output (not multiple)
        json_outputs = []
        current_json = ""
        
        for line in output_lines:
            current_json += line + "\n"
            try:
                # Try to parse as complete JSON
                parsed = json.loads(current_json.strip())
                json_outputs.append(parsed)
                current_json = ""
            except json.JSONDecodeError:
                # Continue building JSON
                continue
        
        # Should have exactly 1 JSON output
        assert len(json_outputs) == 1, f"Expected 1 JSON output, got {len(json_outputs)}"
        
        # Verify structure
        output = json_outputs[0]
        assert "list_info" in output
        assert "items" in output
        assert "properties" in output
        
        # Verify list_info
        assert output["list_info"]["list_key"] == list_key
        assert output["list_info"]["title"] == "Test List"
        assert output["list_info"]["id"] is not None
        
        # Verify items
        assert output["items"]["count"] == 2
        assert len(output["items"]["data"]) == 2
        
        # Verify properties
        assert output["properties"]["count"] == 2
        assert len(output["properties"]["data"]) == 2
        
        # Check property data structure
        prop_keys = {prop["Key"] for prop in output["properties"]["data"]}
        assert prop_keys == {"project_id", "environment"}

    def test_cli_table_mode_unchanged(self, manager_with_test_list, monkeypatch, capsys):
        """Test that table mode still works normally (separate displays)"""
        manager, list_key = manager_with_test_list
        
        # Set table output format
        monkeypatch.setenv("TODOIT_OUTPUT_FORMAT", "table")
        
        # Get test data
        todo_list = manager.get_list(list_key)
        items = manager.get_list_items(list_key)
        properties = manager.get_list_properties(list_key)
        
        # Call function
        _render_table_view(todo_list, items, properties, manager)
        
        # Capture output
        captured = capsys.readouterr()
        
        # In table mode, should not contain JSON
        assert "{" not in captured.out  # No JSON brackets
        assert "}" not in captured.out


class TestMCPEnhancedGetList:
    """Test enhanced MCP todo_get_list functionality"""
    
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
    async def test_mcp_get_list_with_all_data(self, manager_with_test_list):
        """Test MCP todo_get_list returns complete data"""
        manager, list_key = manager_with_test_list
        
        # Set global manager for MCP functions
        old_manager = self._setup_mcp_manager(manager)
        
        try:
            # Call enhanced function
            result = await todo_get_list(
                key=list_key,
                include_items=True,
                include_properties=True,
                mgr=manager
            )
        finally:
            # Restore old manager
            self._restore_mcp_manager(old_manager)
        
        # Verify structure
        assert result["success"] is True
        assert "list" in result
        assert "items" in result
        assert "properties" in result
        
        # Verify list info
        assert result["list"]["list_key"] == list_key
        assert result["list"]["title"] == "Test List"
        
        # Verify items
        assert result["items"]["count"] == 2
        assert len(result["items"]["data"]) == 2
        
        # Check item structure
        item_keys = {item["item_key"] for item in result["items"]["data"]}
        assert item_keys == {"item1", "item2"}
        
        # Verify one item has completed status
        completed_items = [
            item for item in result["items"]["data"] 
            if item["status"] == "completed"
        ]
        assert len(completed_items) == 1
        assert completed_items[0]["item_key"] == "item1"
        
        # Verify properties
        assert result["properties"]["count"] == 2
        assert len(result["properties"]["data"]) == 2
        
        # Check property structure
        prop_keys = {prop["key"] for prop in result["properties"]["data"]}
        assert prop_keys == {"project_id", "environment"}

    @pytest.mark.asyncio
    async def test_mcp_get_list_items_only(self, manager_with_test_list):
        """Test MCP todo_get_list with only items (no properties)"""
        manager, list_key = manager_with_test_list
        
        old_manager = self._setup_mcp_manager(manager)
        try:
            result = await todo_get_list(
                key=list_key,
                include_items=True,
                include_properties=False,
                mgr=manager
            )
        finally:
            self._restore_mcp_manager(old_manager)
        
        assert result["success"] is True
        assert "list" in result
        assert "items" in result
        assert "properties" not in result

    @pytest.mark.asyncio
    async def test_mcp_get_list_properties_only(self, manager_with_test_list):
        """Test MCP todo_get_list with only properties (no items)"""
        manager, list_key = manager_with_test_list
        
        old_manager = self._setup_mcp_manager(manager)
        try:
            result = await todo_get_list(
                key=list_key,
                include_items=False,
                include_properties=True,
                mgr=manager
            )
        finally:
            self._restore_mcp_manager(old_manager)
        
        assert result["success"] is True
        assert "list" in result
        assert "items" not in result
        assert "properties" in result

    @pytest.mark.asyncio
    async def test_mcp_get_list_basic_only(self, manager_with_test_list):
        """Test MCP todo_get_list with only basic list info"""
        manager, list_key = manager_with_test_list
        
        old_manager = self._setup_mcp_manager(manager)
        try:
            result = await todo_get_list(
                key=list_key,
                include_items=False,
                include_properties=False,
                mgr=manager
            )
        finally:
            self._restore_mcp_manager(old_manager)
        
        assert result["success"] is True
        assert "list" in result
        assert "items" not in result
        assert "properties" not in result

    @pytest.mark.asyncio
    async def test_mcp_get_list_nonexistent(self, manager_with_test_list):
        """Test MCP todo_get_list with non-existent list"""
        manager, list_key = manager_with_test_list
        
        old_manager = self._setup_mcp_manager(manager)
        try:
            result = await todo_get_list(
                key="nonexistent",
                include_items=True,
                include_properties=True,
                mgr=manager
            )
        finally:
            self._restore_mcp_manager(old_manager)
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestBackwardCompatibility:
    """Test that changes don't break existing functionality"""
    
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
    async def test_mcp_defaults_are_backward_compatible(self, manager_with_test_list):
        """Test that default parameters maintain backward compatibility"""
        manager, list_key = manager_with_test_list
        
        old_manager = self._setup_mcp_manager(manager)
        try:
            # Call without explicit parameters (should default to include everything)
            result = await todo_get_list(key=list_key, mgr=manager)
        finally:
            self._restore_mcp_manager(old_manager)
        
        # Should include everything by default
        assert result["success"] is True
        assert "list" in result
        assert "items" in result  # Default: True
        assert "properties" in result  # Default: True

    def test_cli_other_formats_unchanged(self, manager_with_test_list, monkeypatch, capsys):
        """Test that YAML and XML formats are unchanged"""
        manager, list_key = manager_with_test_list
        
        # Test YAML format
        monkeypatch.setenv("TODOIT_OUTPUT_FORMAT", "yaml")
        
        todo_list = manager.get_list(list_key)
        items = manager.get_list_items(list_key)
        properties = manager.get_list_properties(list_key)
        
        _render_table_view(todo_list, items, properties, manager)
        captured = capsys.readouterr()
        
        # Should contain YAML-like output
        assert "title:" in captured.out
        assert "count:" in captured.out