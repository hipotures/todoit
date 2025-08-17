"""
Integration tests for item rename functionality
Tests the complete item rename workflow through manager, MCP, and CLI interfaces
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from interfaces.cli import cli
from core.manager import TodoManager


class TestItemRename:
    """Integration tests for item rename functionality"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def setup_test_data(self, temp_db_path):
        """Setup test data for rename tests"""
        manager = TodoManager(temp_db_path)

        # Create test list with items and subitems
        list1 = manager.create_list("project", "Project Management")
        
        # Add regular items
        item1 = manager.add_item("project", "task1", "Original Task 1")
        item2 = manager.add_item("project", "task2", "Task Implementation")
        
        # Add subitems to task1
        subitem1 = manager.add_subitem("project", "task1", "design", "Design Phase")
        subitem2 = manager.add_subitem("project", "task1", "code", "Coding Phase")
        
        return manager, list1, item1, item2, subitem1, subitem2

    def test_manager_rename_item_key_only(self, temp_db_path, setup_test_data):
        """Test manager.rename_item with key only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Rename item key only
        updated_item = manager.rename_item(
            list_key="project",
            item_key="task1",
            new_key="renamed_task"
        )
        
        assert updated_item.item_key == "renamed_task"
        assert updated_item.content == "Original Task 1"  # Content unchanged
        
        # Verify old key no longer exists
        old_item = manager.get_item("project", "task1")
        assert old_item is None
        
        # Verify new key exists
        fetched_item = manager.get_item("project", "renamed_task")
        assert fetched_item is not None
        assert fetched_item.item_key == "renamed_task"

    def test_manager_rename_item_title_only(self, temp_db_path, setup_test_data):
        """Test manager.rename_item with title only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Rename item title only
        updated_item = manager.rename_item(
            list_key="project",
            item_key="task1",
            new_title="Updated Task Title"
        )
        
        assert updated_item.item_key == "task1"  # Key unchanged
        assert updated_item.content == "Updated Task Title"
        
        # Verify the change persisted
        fetched_item = manager.get_item("project", "task1")
        assert fetched_item.content == "Updated Task Title"

    def test_manager_rename_item_both_key_and_title(self, temp_db_path, setup_test_data):
        """Test manager.rename_item with both key and title"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Rename both key and title
        updated_item = manager.rename_item(
            list_key="project",
            item_key="task2",
            new_key="auth_task",
            new_title="Authentication Task Implementation"
        )
        
        assert updated_item.item_key == "auth_task"
        assert updated_item.content == "Authentication Task Implementation"
        
        # Verify old key no longer exists
        old_item = manager.get_item("project", "task2")
        assert old_item is None
        
        # Verify new key exists with new content
        fetched_item = manager.get_item("project", "auth_task")
        assert fetched_item.item_key == "auth_task"
        assert fetched_item.content == "Authentication Task Implementation"

    def test_manager_rename_subitem(self, temp_db_path, setup_test_data):
        """Test manager.rename_item for subitems"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Rename subitem
        updated_subitem = manager.rename_item(
            list_key="project",
            item_key="design",
            new_key="ui_design",
            new_title="UI/UX Design Phase",
            parent_item_key="task1"
        )
        
        assert updated_subitem.item_key == "ui_design"
        assert updated_subitem.content == "UI/UX Design Phase"
        assert updated_subitem.parent_item_id is not None
        
        # Verify old subitem key no longer exists
        old_subitem = manager.get_item("project", "design", "task1")
        assert old_subitem is None
        
        # Verify new subitem exists
        fetched_subitem = manager.get_item("project", "ui_design", "task1")
        assert fetched_subitem.item_key == "ui_design"
        assert fetched_subitem.content == "UI/UX Design Phase"

    def test_manager_rename_item_validation_errors(self, temp_db_path, setup_test_data):
        """Test validation errors in manager.rename_item"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Test no parameters provided
        with pytest.raises(ValueError, match="At least one of new_key or new_title must be provided"):
            manager.rename_item("project", "task1")
        
        # Test item not found
        with pytest.raises(ValueError, match="not found"):
            manager.rename_item("project", "nonexistent", new_key="new_key")
        
        # Test duplicate key
        with pytest.raises(ValueError, match="already exists"):
            manager.rename_item("project", "task1", new_key="task2")  # task2 already exists

    def test_cli_item_rename_key_only(self, temp_db_path, setup_test_data):
        """Test CLI item rename with key only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Rename item key via CLI
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename", 
            "--list", "project",
            "--item", "task1",
            "--new-key", "cli_renamed_task",
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Successfully renamed item" in result.output
        assert "cli_renamed_task" in result.output
        
        # Verify in database
        renamed_item = manager.get_item("project", "cli_renamed_task")
        assert renamed_item is not None
        assert renamed_item.item_key == "cli_renamed_task"
        assert renamed_item.content == "Original Task 1"

    def test_cli_item_rename_title_only(self, temp_db_path, setup_test_data):
        """Test CLI item rename with title only"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Rename item title via CLI
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project", 
            "--item", "task1",
            "--new-title", "CLI Updated Title",
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Successfully renamed item" in result.output
        assert "CLI Updated Title" in result.output
        
        # Verify in database
        updated_item = manager.get_item("project", "task1")
        assert updated_item.content == "CLI Updated Title"

    def test_cli_item_rename_both_key_and_title(self, temp_db_path, setup_test_data):
        """Test CLI item rename with both key and title"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Rename both key and title via CLI
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project",
            "--item", "task2", 
            "--new-key", "complete_task",
            "--new-title", "Complete Task Implementation",
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Successfully renamed item" in result.output
        assert "complete_task" in result.output
        assert "Complete Task Implementation" in result.output
        
        # Verify in database
        renamed_item = manager.get_item("project", "complete_task")
        assert renamed_item.item_key == "complete_task"
        assert renamed_item.content == "Complete Task Implementation"

    def test_cli_subitem_rename(self, temp_db_path, setup_test_data):
        """Test CLI subitem rename"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Rename subitem via CLI
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project",
            "--item", "design",
            "--parent", "task1",
            "--new-key", "frontend_design",
            "--new-title", "Frontend Design Phase",
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "✅ Successfully renamed subitem" in result.output
        assert "frontend_design" in result.output
        
        # Verify in database
        renamed_subitem = manager.get_item("project", "frontend_design", "task1")
        assert renamed_subitem.item_key == "frontend_design"
        assert renamed_subitem.content == "Frontend Design Phase"

    def test_cli_item_rename_confirmation(self, temp_db_path, setup_test_data):
        """Test CLI item rename with confirmation prompt"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Test confirmation accepted
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project",
            "--item", "task1",
            "--new-key", "confirmed_rename"
        ], input="y\n")
        
        assert result.exit_code == 0
        assert "Proceed with rename?" in result.output
        assert "✅ Successfully renamed item" in result.output
        
        # Verify rename happened
        renamed_item = manager.get_item("project", "confirmed_rename")
        assert renamed_item is not None

    def test_cli_item_rename_error_no_parameters(self, temp_db_path, setup_test_data):
        """Test CLI error when no new-key or new-title provided"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Try rename without new-key or new-title
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project",
            "--item", "task1"
        ])
        
        assert result.exit_code == 0  # Command runs but shows error message
        assert "At least one of --new-key or --new-title must be provided" in result.output

    def test_cli_item_rename_error_item_not_found(self, temp_db_path, setup_test_data):
        """Test CLI error when item not found"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        runner = CliRunner()
        
        # Try to rename non-existent item
        result = runner.invoke(cli, [
            "--db-path", temp_db_path,
            "item", "rename",
            "--list", "project", 
            "--item", "nonexistent",
            "--new-key", "new_key",
            "--force"
        ])
        
        assert result.exit_code == 0  # Command runs but shows error message
        assert "not found" in result.output

    def test_rename_preserves_item_properties(self, temp_db_path, setup_test_data):
        """Test that renaming preserves item status, position, and other properties"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Use task2 which doesn't have subtasks, so we can change its status
        manager.update_item_status("project", "task2", status="in_progress")
        original_item = manager.get_item("project", "task2")
        original_status = original_item.status
        original_position = original_item.position
        original_created_at = original_item.created_at
        
        # Rename the item
        updated_item = manager.rename_item(
            list_key="project",
            item_key="task2", 
            new_key="renamed_with_props",
            new_title="Renamed Task"
        )
        
        # Verify properties are preserved
        assert updated_item.status == original_status
        assert updated_item.position == original_position
        assert updated_item.created_at == original_created_at
        assert updated_item.item_key == "renamed_with_props"
        assert updated_item.content == "Renamed Task"

    def test_rename_item_with_dependencies_preserved(self, temp_db_path, setup_test_data):
        """Test that renaming items preserves dependencies"""
        manager, list1, item1, item2, subitem1, subitem2 = setup_test_data
        
        # Create another list and item for dependency testing
        list2 = manager.create_list("other_project", "Other Project")
        other_item = manager.add_item("other_project", "dependent_task", "Dependent Task")
        
        # Create dependency: other_project:dependent_task depends on project:task1
        dep = manager.add_item_dependency(
            dependent_list="other_project",
            dependent_item="dependent_task", 
            required_list="project",
            required_item="task1"
        )
        
        # Rename the required item
        manager.rename_item(
            list_key="project",
            item_key="task1",
            new_key="renamed_required"
        )
        
        # Verify dependency still exists and points to the renamed item
        blockers = manager.get_item_blockers("other_project", "dependent_task")
        assert len(blockers) == 1
        
        # Get the renamed item and verify the dependency is maintained
        renamed_item = manager.get_item("project", "renamed_required")
        assert renamed_item is not None
        
        # Verify that the dependent item is still blocked
        is_blocked = manager.is_item_blocked("other_project", "dependent_task")
        assert is_blocked == True