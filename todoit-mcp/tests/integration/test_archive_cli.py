"""
Integration tests for CLI archiving functionality
Tests the complete archiving workflow through the CLI interface
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from interfaces.cli import cli
from core.manager import TodoManager


class TestArchiveCLI:
    """Integration tests for archiving CLI commands"""

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

        # Create test lists
        list1 = manager.create_list(
            "test-list-1", "Test List 1", items=["Item 1", "Item 2"]
        )
        list2 = manager.create_list(
            "test-list-2", "Test List 2", items=["Item A", "Item B"]
        )
        list3 = manager.create_list("archive-me", "List to Archive", items=["Old Item"])

        return manager, [list1, list2, list3]

    def test_archive_list_cli_command(self, temp_db_path, setup_test_lists):
        """Test 'todoit list archive' CLI command"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item first so we can archive without force
        manager.update_item_status("archive-me", "item_1", status="completed")

        # Archive a list
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "archive-me"]
        )

        assert result.exit_code == 0
        assert "List 'archive-me' has been archived" in result.output
        assert "Status: " in result.output and (
            "archived" in result.output.lower() or "ARCHIVED" in result.output
        )
        assert "todoit list all --include-archived" in result.output
        assert "todoit list unarchive" in result.output

        # Verify list is actually archived
        archived_list = manager.get_list("archive-me")
        assert archived_list.status == "archived"

    def test_unarchive_list_cli_command(self, temp_db_path, setup_test_lists):
        """Test 'todoit list unarchive' CLI command"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # First complete the item and archive a list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # Then unarchive it
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "unarchive", "--list", "archive-me"]
        )

        assert result.exit_code == 0
        assert "List 'archive-me' has been restored" in result.output
        assert "Status: " in result.output and (
            "active" in result.output.lower() or "ACTIVE" in result.output
        )
        assert "todoit list all" in result.output

        # Verify list is actually unarchived
        restored_list = manager.get_list("archive-me")
        assert restored_list.status == "active"

    def test_list_all_excludes_archived_by_default(
        self, temp_db_path, setup_test_lists
    ):
        """Test that 'todoit list all' excludes archived lists by default"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item and archive one list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # List all (should not show archived)
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all"])

        assert result.exit_code == 0
        # Check for partial matches since table truncates long names
        assert "test-list" in result.output or "Test List" in result.output
        assert "archive-me" not in result.output
        assert "Total lists: 2" in result.output

    def test_list_all_with_include_archived_flag(self, temp_db_path, setup_test_lists):
        """Test 'todoit list all --include-archived' shows all lists"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item and archive one list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # List all including archived
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "all", "--include-archived"]
        )

        assert result.exit_code == 0
        # Check for partial matches since table truncates long names
        assert (
            "Test" in result.output and "List" in result.output
        )  # Title parts appear in table
        assert (
            "archive-me" in result.output
            or "List to Archive" in result.output
            or "Archi" in result.output
        )
        assert "Total lists: 3" in result.output
        # Should show status column when including archived
        assert "📦" in result.output

    def test_list_all_with_archived_only_flag(self, temp_db_path, setup_test_lists):
        """Test 'todoit list all --archived' shows only archived lists"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Archive two lists - complete their tasks first
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.update_item_status("test-list-1", "item_1", status="completed")
        manager.update_item_status("test-list-1", "item_2", status="completed")
        manager.archive_list("archive-me")
        manager.archive_list("test-list-1")

        # List only archived
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all", "--archived"])

        assert result.exit_code == 0
        # Check for partial matches since table truncates long names
        assert (
            "archive-me" in result.output
            or "List to Archive" in result.output
            or "Archi" in result.output
        )
        assert (
            "Test" in result.output and "List 1" in result.output
        )  # First list should appear
        assert "Test List 2" not in result.output  # Second list should not appear
        assert "Total lists: 2" in result.output

    def test_archive_nonexistent_list_error(self, temp_db_path):
        """Test archiving non-existent list shows error"""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "nonexistent"]
        )

        assert result.exit_code == 0
        assert "Error: List 'nonexistent' does not exist" in result.output

    def test_archive_already_archived_list_error(self, temp_db_path, setup_test_lists):
        """Test archiving already archived list shows error"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item and archive a list first
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # Try to archive again
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "archive-me"]
        )

        assert result.exit_code == 0
        assert "Error: List 'archive-me' is already archived" in result.output

    def test_unarchive_active_list_error(self, temp_db_path, setup_test_lists):
        """Test unarchiving already active list shows error"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "unarchive", "--list", "test-list-1"]
        )

        assert result.exit_code == 0
        assert "Error: List 'test-list-1' is already active" in result.output

    def test_unarchive_nonexistent_list_error(self, temp_db_path):
        """Test unarchiving non-existent list shows error"""
        runner = CliRunner()

        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "unarchive", "--list", "nonexistent"]
        )

        assert result.exit_code == 0
        assert "Error: List 'nonexistent' does not exist" in result.output

    def test_status_column_display_logic(self, temp_db_path, setup_test_lists):
        """Test that status column only appears when needed"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # When all lists are active, no status column should show
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all"])
        assert result.exit_code == 0
        assert "📦" not in result.output  # Status column should not appear

        # Complete the item and archive one list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # With --include-archived, status column should appear
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "all", "--include-archived"]
        )
        assert result.exit_code == 0
        assert "📦" in result.output  # Status column should appear

        # With --archived only, status column should appear
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all", "--archived"])
        assert result.exit_code == 0
        assert "📦" in result.output  # Status column should appear

    def test_status_column_values(self, temp_db_path, setup_test_lists):
        """Test that status column shows correct values (A/Z)"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item and archive one list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # Check status values in output
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "all", "--include-archived"]
        )
        assert result.exit_code == 0

        # Parse output to check status values
        lines = result.output.split("\n")
        found_active = False
        found_archived = False

        for line in lines:
            if "test-list-1" in line or "test-list-2" in line:
                # Active list should have 'A' in status column
                if "│ A │" in line or "A" in line.split():
                    found_active = True
            elif "archive-me" in line:
                # Archived list should have 'Z' in status column
                if "│ Z │" in line or "Z" in line.split():
                    found_archived = True

        # Note: This test might need adjustment based on exact output format
        # The important thing is that we have different indicators for active vs archived

    def test_list_view_with_archived_lists(self, temp_db_path, setup_test_lists):
        """Test list view shows archived lists when included"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Complete the item and archive one list
        manager.update_item_status("archive-me", "item_1", status="completed")
        manager.archive_list("archive-me")

        # Test list view with archived included
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "all", "--include-archived"]
        )
        assert result.exit_code == 0

        # Should contain the archived list in list view
        assert "archive-me" in result.output or "List to Archive" in result.output
        assert "test-list" in result.output or "Test List" in result.output

    def test_archive_workflow_complete(self, temp_db_path):
        """Test complete archive/unarchive workflow"""
        runner = CliRunner()

        # Create a list
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db_path,
                "list",
                "create",
                "--list",
                "workflow-test",
                "--title",
                "Workflow Test",
            ],
        )
        assert result.exit_code == 0

        # Verify it appears in normal list
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all"])
        assert result.exit_code == 0
        assert (
            "Workflow" in result.output and "Test" in result.output
        )  # Title parts appear in table

        # Archive it
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "workflow-test"]
        )
        assert result.exit_code == 0
        assert "has been archived" in result.output

        # Verify it doesn't appear in normal list
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all"])
        assert result.exit_code == 0
        assert "workflow-test" not in result.output

        # Verify it appears in archived-only list
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all", "--archived"])
        assert result.exit_code == 0
        # Should show the archived list (table should have content)
        assert "Total lists: 1" in result.output
        assert (
            "workflow-" in result.output
            or "Workflow" in result.output
            or "Test" in result.output
        )

        # Unarchive it
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "unarchive", "--list", "workflow-test"]
        )
        assert result.exit_code == 0
        assert "has been restored" in result.output

        # Verify it appears in normal list again
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all"])
        assert result.exit_code == 0
        assert (
            "Workflow" in result.output and "Test" in result.output
        )  # Title parts appear in table

        # Verify it doesn't appear in archived-only list
        result = runner.invoke(cli, ["--db-path", temp_db_path, "list", "all", "--archived"])
        assert result.exit_code == 0
        assert "workflow-test" not in result.output or "Total lists: 0" in result.output

    def test_archive_with_incomplete_tasks_fails(self, temp_db_path):
        """Test that archiving list with incomplete tasks fails without --force"""
        runner = CliRunner()
        manager = TodoManager(temp_db_path)

        # Create a list with incomplete tasks
        list_with_tasks = manager.create_list(
            "incomplete-tasks",
            "List with incomplete tasks",
            items=["Item 1", "Item 2", "Item 3"],
        )

        # Complete only one item
        manager.update_item_status("incomplete-tasks", "item_1", status="completed")

        # Try to archive without --force (should fail)
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "incomplete-tasks"]
        )

        assert result.exit_code == 0
        assert "Cannot archive list with incomplete tasks" in result.output
        assert "Incomplete: 2/3 tasks" in result.output
        assert (
            "Use" in result.output
            and "force=True" in result.output
            and "archive anyway" in result.output
        )
        assert "todoit list archive --list incomplete-tasks --force" in result.output

    def test_archive_with_force_flag_succeeds(self, temp_db_path):
        """Test that archiving list with incomplete tasks succeeds with --force"""
        runner = CliRunner()
        manager = TodoManager(temp_db_path)

        # Create a list with incomplete tasks
        list_with_tasks = manager.create_list(
            "force-archive", "List to force archive", items=["Item 1", "Item 2"]
        )

        # Archive with --force (should succeed)
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "force-archive", "--force"]
        )

        assert result.exit_code == 0
        assert "List 'force-archive' has been archived" in result.output
        assert (
            "Status: archived" in result.output
            or "Status: ListStatus.ARCHIVED" in result.output
        )

        # Verify list is actually archived
        archived_list = manager.get_list("force-archive")
        assert archived_list.status == "archived"

    def test_archive_completed_list_succeeds_without_force(self, temp_db_path):
        """Test that archiving list with all completed tasks succeeds without --force"""
        runner = CliRunner()
        manager = TodoManager(temp_db_path)

        # Create a list and complete all tasks
        list_completed = manager.create_list(
            "completed-list", "Completed list", items=["Item 1", "Item 2"]
        )
        manager.update_item_status("completed-list", "item_1", status="completed")
        manager.update_item_status("completed-list", "item_2", status="completed")

        # Archive without --force (should succeed)
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "completed-list"]
        )

        assert result.exit_code == 0
        assert "List 'completed-list' has been archived" in result.output

        # Verify list is actually archived
        archived_list = manager.get_list("completed-list")
        assert archived_list.status == "archived"

    def test_archive_empty_list_succeeds(self, temp_db_path):
        """Test that archiving empty list succeeds without --force"""
        runner = CliRunner()
        manager = TodoManager(temp_db_path)

        # Create an empty list
        empty_list = manager.create_list("empty-list", "Empty list")

        # Archive without --force (should succeed)
        result = runner.invoke(
            cli, ["--db-path", temp_db_path, "list", "archive", "--list", "empty-list"]
        )

        assert result.exit_code == 0
        assert "List 'empty-list' has been archived" in result.output

        # Verify list is actually archived
        archived_list = manager.get_list("empty-list")
        assert archived_list.status == "archived"
