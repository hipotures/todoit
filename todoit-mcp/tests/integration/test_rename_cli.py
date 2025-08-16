"""
Integration tests for CLI rename functionality
Tests the complete rename workflow through the CLI interface
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from interfaces.cli import cli
from core.manager import TodoManager


class TestRenameCLI:
    """Integration tests for rename CLI commands"""

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
        """Setup test lists for rename tests"""
        manager = TodoManager(temp_db_path)

        # Create test lists
        list1 = manager.create_list("test_list_1", "Test List 1", items=["Item 1", "Item 2"])
        list2 = manager.create_list("test_list_2", "Test List 2", items=["Item A"])
        list3 = manager.create_list("rename_me", "Original Title", items=["Old Item"])

        return manager, [list1, list2, list3]

    def test_rename_key_only_cli(self, temp_db_path, setup_test_lists):
        """Test 'todoit list rename' CLI command with key only"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename list key
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "renamed_list",
            "--yes"
        ])

        assert result.exit_code == 0
        assert "✅ List renamed successfully!" in result.output
        assert "renamed_list" in result.output
        assert "Original Title" in result.output

        # Verify in database
        renamed_list = manager.get_list("renamed_list")
        assert renamed_list is not None
        assert renamed_list.list_key == "renamed_list"
        assert renamed_list.title == "Original Title"

        # Verify old key no longer exists
        old_list = manager.get_list("rename_me")
        assert old_list is None

    def test_rename_title_only_cli(self, temp_db_path, setup_test_lists):
        """Test rename with title only"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename list title
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--title", "New Awesome Title",
            "--yes"
        ])

        assert result.exit_code == 0
        assert "✅ List renamed successfully!" in result.output
        assert "New Awesome Title" in result.output

        # Verify in database
        renamed_list = manager.get_list("rename_me")
        assert renamed_list is not None
        assert renamed_list.list_key == "rename_me"
        assert renamed_list.title == "New Awesome Title"

    def test_rename_both_key_and_title_cli(self, temp_db_path, setup_test_lists):
        """Test rename with both key and title"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename both key and title
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "complete_rename",
            "--title", "Completely New Title",
            "--yes"
        ])

        assert result.exit_code == 0
        assert "✅ List renamed successfully!" in result.output
        assert "complete_rename" in result.output
        assert "Completely New Title" in result.output

        # Verify in database
        renamed_list = manager.get_list("complete_rename")
        assert renamed_list is not None
        assert renamed_list.list_key == "complete_rename"
        assert renamed_list.title == "Completely New Title"

    def test_rename_shows_changes_preview(self, temp_db_path, setup_test_lists):
        """Test that CLI shows changes preview table"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename without --yes to see preview
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "preview_test",
            "--title", "Preview Title"
        ], input="n\n")  # Say no to confirmation

        assert result.exit_code == 0
        assert "Changes to be made" in result.output
        assert "rename_me" in result.output
        assert "preview_test" in result.output
        assert "Original Title" in result.output
        assert "Preview Title" in result.output
        assert "Continue with rename?" in result.output
        assert "❌ Rename cancelled" in result.output

    def test_rename_confirmation_yes(self, temp_db_path, setup_test_lists):
        """Test rename with confirmation accepted"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename with confirmation
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "confirmed_rename"
        ], input="y\n")  # Say yes to confirmation

        assert result.exit_code == 0
        assert "✅ List renamed successfully!" in result.output
        assert "confirmed_rename" in result.output

        # Verify rename happened
        renamed_list = manager.get_list("confirmed_rename")
        assert renamed_list is not None

    def test_rename_error_no_parameters(self, temp_db_path, setup_test_lists):
        """Test error when no --key or --title provided"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Try rename without parameters
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me"
        ])

        assert result.exit_code != 0
        assert "At least one of --key or --title must be provided" in result.output

    def test_rename_error_nonexistent_list(self, temp_db_path, setup_test_lists):
        """Test error when list doesn't exist"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Try to rename non-existent list
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "nonexistent",
            "--key", "new_key",
            "--yes"
        ])

        assert result.exit_code != 0
        assert "Access denied" in result.output or "does not exist" in result.output

    def test_rename_error_duplicate_key(self, temp_db_path, setup_test_lists):
        """Test error when new key already exists"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Try to rename to existing key
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "test_list_1",  # This key already exists
            "--yes"
        ])

        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_rename_error_invalid_key(self, temp_db_path, setup_test_lists):
        """Test error when new key is invalid (no letters)"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Try to rename to invalid key
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "123",  # Invalid - no letters
            "--yes"
        ])

        assert result.exit_code != 0
        assert "must contain at least one letter" in result.output

    def test_rename_preserves_items_and_relationships(self, temp_db_path, setup_test_lists):
        """Test that rename preserves items and other relationships"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Get original items
        original_items = manager.get_list_items("rename_me")
        assert len(original_items) == 1
        assert original_items[0].content == "Old Item"

        # Add some properties for testing
        manager.set_list_property("rename_me", "test_prop", "test_value")

        # Rename the list
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "preserved_list",
            "--yes"
        ])

        assert result.exit_code == 0

        # Verify items are preserved
        new_items = manager.get_list_items("preserved_list")
        assert len(new_items) == 1
        assert new_items[0].content == "Old Item"

        # Verify properties are preserved
        prop_value = manager.get_list_property("preserved_list", "test_prop")
        assert prop_value == "test_value"

    def test_rename_cli_basic_output_format(self, temp_db_path, setup_test_lists):
        """Test rename CLI with basic output format"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Rename with standard output
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "format_test",
            "--yes"
        ])

        assert result.exit_code == 0
        
        # Should contain success message and new key
        output = result.output
        assert "✅ List renamed successfully!" in output
        assert "format_test" in output

    def test_rename_with_force_tags_environment(self, temp_db_path, setup_test_lists):
        """Test rename with FORCE_TAGS environment variable"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Add a tag to the list
        manager.add_tag_to_list("rename_me", "test_tag")

        # Set TODOIT_FORCE_TAGS environment and try rename
        env = {"TODOIT_FORCE_TAGS": "test_tag"}
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "rename_me",
            "--key", "tagged_rename",
            "--yes"
        ], env=env)

        assert result.exit_code == 0
        assert "✅ List renamed successfully!" in result.output

        # Verify rename succeeded
        renamed_list = manager.get_list("tagged_rename")
        assert renamed_list is not None

    def test_rename_blocked_by_force_tags(self, temp_db_path, setup_test_lists):
        """Test rename blocked by FORCE_TAGS when list doesn't have required tag"""
        manager, lists = setup_test_lists
        runner = CliRunner()

        # Create a list via CLI (which auto-tags with 'dev')
        runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "create", "--list", "tagged_list",
            "--title", "Tagged List"
        ])

        # Set TODOIT_FORCE_TAGS to a tag the list doesn't have (not 'dev')
        env = {"TODOIT_FORCE_TAGS": "production"}
        result = runner.invoke(cli, [
            "--db", temp_db_path,
            "list", "rename", "tagged_list",
            "--key", "blocked_rename",
            "--yes"
        ], env=env)

        assert result.exit_code != 0
        assert "Access denied" in result.output