"""
CLI tests for list linking functionality
Tests the 'todoit list link' command with various scenarios
"""

import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path


class TestListLinkCLI:
    """Test 'todoit list link' CLI command"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def run_cli_command(self, command, db_path):
        """Run CLI command and return result"""
        import shlex

        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent

        # Build full command using shlex to properly handle quoted arguments
        full_command = [
            sys.executable,
            "-m",
            "interfaces.cli",
            "--db",
            db_path,
        ] + shlex.split(command)

        # Run command
        result = subprocess.run(
            full_command, cwd=project_root, capture_output=True, text=True
        )

        return result

    def test_cli_list_link_command_exists(self, temp_db_path):
        """Test that 'list link' command exists and is accessible"""
        result = self.run_cli_command("list --help", temp_db_path)

        assert result.returncode == 0
        assert "link" in result.stdout

    def test_cli_list_link_help(self, temp_db_path):
        """Test 'list link --help' shows proper help message"""
        result = self.run_cli_command("list link --help", temp_db_path)

        assert result.returncode == 0
        assert "Create a linked copy" in result.stdout
        assert "source list key" in result.stdout.lower()
        assert "target list key" in result.stdout.lower()
        assert "--title" in result.stdout

    def test_cli_list_link_arguments(self, temp_db_path):
        """Test CLI command with proper arguments"""
        # First create a source list
        create_result = self.run_cli_command(
            'list create --list test_source --title "Test Source"', temp_db_path
        )
        assert create_result.returncode == 0

        # Add an item to source list
        item_result = self.run_cli_command(
            'item add --list test_source --item test_item --title "Test item"', temp_db_path
        )
        assert item_result.returncode == 0

        # Now test linking
        link_result = self.run_cli_command(
            'list link --source test_source --target test_target --title "Test Target"', temp_db_path
        )

        assert link_result.returncode == 0
        assert "Successfully linked list" in link_result.stdout
        assert "test_source" in link_result.stdout
        assert "test_target" in link_result.stdout
        assert "Link Statistics" in link_result.stdout

    def test_cli_list_link_error_handling(self, temp_db_path):
        """Test CLI error handling for various failure scenarios"""
        # Test source list not exists
        result = self.run_cli_command("list link --source nonexistent --target target_list", temp_db_path)

        assert (
            result.returncode == 0
        )  # CLI doesn't exit with error, shows error message
        assert "Error" in result.stdout or "does not exist" in result.stdout.lower()

    def test_cli_list_link_output_format(self, temp_db_path):
        """Test CLI output format and statistics display"""
        # Setup: Create source list with multiple items and properties
        setup_commands = [
            'list create --list rich_source --title "Rich Source List"',
            'item add --list rich_source --item item1 --title "First item"',
            'item add --list rich_source --item item2 --title "Second item"',
            'item add --list rich_source --item item3 --title "Third item"',
        ]

        for cmd in setup_commands:
            result = self.run_cli_command(cmd, temp_db_path)
            assert result.returncode == 0

        # Test link command
        result = self.run_cli_command(
            'list link --source rich_source --target rich_target --title "Rich Target List"', temp_db_path
        )

        assert result.returncode == 0

        # Verify output contains expected elements
        output = result.stdout

        # Success indicators
        assert "✅" in output  # Success emoji
        assert "Successfully linked list" in output

        # Source and target information
        assert "rich_source" in output
        assert "rich_target" in output

        # Statistics table
        assert "Link Statistics" in output
        assert "Items copied" in output
        assert "List properties copied" in output
        assert "Item properties copied" in output
        assert "Items set to pending" in output
        assert "Project relation created" in output

        # Relation information
        assert "Relation key" in output
        assert "rich_source_linked" in output

        # Verify the linked list was actually created by listing all lists
        list_all_result = self.run_cli_command("list all", temp_db_path)
        assert "rich_target" in list_all_result.stdout

    def test_cli_list_link_without_title(self, temp_db_path):
        """Test CLI link command without custom title (uses default)"""
        # Create source list
        result = self.run_cli_command(
            'list create --list auto_source --title "Auto Source List"', temp_db_path
        )
        assert result.returncode == 0

        # Link without title
        result = self.run_cli_command("list link --source auto_source --target auto_target", temp_db_path)

        assert result.returncode == 0
        assert "Successfully linked list" in result.stdout

        # Verify default title was used (may be wrapped across lines in table)
        all_result = self.run_cli_command("list all", temp_db_path)
        # Check for both the target list key and parts of the title
        assert "auto_target" in all_result.stdout
        assert "Linked" in all_result.stdout

    def test_cli_list_link_target_already_exists(self, temp_db_path):
        """Test error when target list already exists"""
        # Create both source and target lists
        commands = [
            'list create --list existing_source --title "Existing Source"',
            'list create --list existing_target --title "Existing Target"',
        ]

        for cmd in commands:
            result = self.run_cli_command(cmd, temp_db_path)
            assert result.returncode == 0

        # Try to link when target already exists
        result = self.run_cli_command(
            "list link --source existing_source --target existing_target", temp_db_path
        )

        assert result.returncode == 0  # CLI doesn't crash
        assert "Error" in result.stdout or "already exists" in result.stdout
