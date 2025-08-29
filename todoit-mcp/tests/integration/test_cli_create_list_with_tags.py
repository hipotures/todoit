"""
Integration tests for CLI list create command with tags functionality
"""

import os
import tempfile

import pytest
from click.testing import CliRunner

from core.manager import TodoManager
from interfaces.cli import cli


class TestCLICreateListWithTags:
    """Integration tests for CLI list create with --tag option"""

    @pytest.fixture
    def runner(self):
        """Click test runner"""
        return CliRunner()

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def manager_with_tags(self, temp_db):
        """Create a manager with some test tags"""
        manager = TodoManager(temp_db)
        manager.create_tag("frontend", "blue")
        manager.create_tag("backend", "green")
        manager.create_tag("mobile", "red")
        return manager

    def test_cli_create_list_without_tags(self, runner, temp_db):
        """Test CLI create list without --tag option (backward compatibility)"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "test-list",
                "--title",
                "Test List",
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "test-list" in result.output
        assert "Test List" in result.output

        # Verify no tags line in output
        assert "Tags:" not in result.output

        # Verify in database
        manager = TodoManager(temp_db)
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 0

    def test_cli_create_list_with_single_tag(self, runner, temp_db, manager_with_tags):
        """Test CLI create list with single --tag option"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "webapp",
                "--title",
                "Web Application",
                "--tag",
                "frontend",
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "webapp" in result.output
        assert "Web Application" in result.output
        assert "Tags: frontend" in result.output

        # Verify in database
        tags = manager_with_tags.get_tags_for_list("webapp")
        assert len(tags) == 1
        assert tags[0].name == "frontend"

    def test_cli_create_list_with_multiple_tags(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with multiple --tag options"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "fullstack-app",
                "--title",
                "Fullstack Application",
                "--tag",
                "frontend",
                "--tag",
                "backend",
                "--tag",
                "mobile",
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "fullstack-app" in result.output
        assert "Fullstack Application" in result.output
        assert "Tags: frontend, backend, mobile" in result.output

        # Verify in database
        tags = manager_with_tags.get_tags_for_list("fullstack-app")
        tag_names = [tag.name for tag in tags]
        assert len(tags) == 3
        assert "frontend" in tag_names
        assert "backend" in tag_names
        assert "mobile" in tag_names

    def test_cli_create_list_with_nonexistent_tag(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with non-existent tag shows error"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "error-test",
                "--title",
                "Error Test",
                "--tag",
                "nonexistent",
            ],
        )

        assert (
            result.exit_code == 0
        )  # CLI doesn't exit with error code, just shows message
        assert "Error: Tag 'nonexistent' does not exist" in result.output
        assert "todoit tag create nonexistent" in result.output
        assert "List Created" not in result.output

        # Verify list was not created
        list_obj = manager_with_tags.get_list("error-test")
        assert list_obj is None

    def test_cli_create_list_with_mixed_valid_invalid_tags(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with mix of existing and non-existent tags"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "mixed-test",
                "--title",
                "Mixed Test",
                "--tag",
                "frontend",  # exists
                "--tag",
                "nonexistent",  # doesn't exist
            ],
        )

        assert result.exit_code == 0
        assert "Error: Tag 'nonexistent' does not exist" in result.output
        assert "List Created" not in result.output

        # Verify list was not created
        list_obj = manager_with_tags.get_list("mixed-test")
        assert list_obj is None

    def test_cli_create_list_with_tags_and_items(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with both tags and items"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "project-with-tasks",
                "--title",
                "Project with Tasks",
                "--tag",
                "frontend",
                "--tag",
                "backend",
                "--items",
                "Setup project",
                "--items",
                "Create UI",
                "--items",
                "Add API",
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "Tags: frontend, backend" in result.output
        assert "Items: 3" in result.output

        # Verify in database
        tags = manager_with_tags.get_tags_for_list("project-with-tasks")
        items = manager_with_tags.get_list_items("project-with-tasks")

        assert len(tags) == 2
        assert len(items) == 3

    def test_cli_create_list_with_tags_and_metadata(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with tags and metadata"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "urgent-project",
                "--title",
                "Urgent Project",
                "--tag",
                "frontend",
                "--metadata",
                '{"priority": "high", "deadline": "2024-12-31"}',
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "Tags: frontend" in result.output

        # Verify in database
        tags = manager_with_tags.get_tags_for_list("urgent-project")
        assert len(tags) == 1
        assert tags[0].name == "frontend"

    def test_cli_create_list_case_insensitive_tags(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with case-insensitive tag names"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "case-test",
                "--title",
                "Case Test",
                "--tag",
                "FRONTEND",  # uppercase
                "--tag",
                "Backend",  # mixed case
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "Tags: FRONTEND, Backend" in result.output  # Shows as input

        # Verify in database (should be normalized to lowercase)
        tags = manager_with_tags.get_tags_for_list("case-test")
        tag_names = [tag.name for tag in tags]
        assert len(tags) == 2
        assert "frontend" in tag_names  # normalized
        assert "backend" in tag_names  # normalized

    def test_cli_create_list_with_from_folder_and_tags(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with --from-folder and --tag options"""
        # Create a temporary directory with files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("test")
            with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
                f.write("test")

            result = runner.invoke(
                cli,
                [
                    "--db-path",
                    temp_db,
                    "list",
                    "create",
                    "--list",
                    "folder-project",
                    "--title",
                    "Folder Project",
                    "--from-folder",
                    temp_dir,
                    "--tag",
                    "frontend",
                ],
            )

            assert result.exit_code == 0
            assert "List Created" in result.output
            assert "Tags: frontend" in result.output
            assert "Items: 2" in result.output  # Two files processed

            # Verify in database
            tags = manager_with_tags.get_tags_for_list("folder-project")
            items = manager_with_tags.get_list_items("folder-project")

            assert len(tags) == 1
            assert tags[0].name == "frontend"
            assert len(items) == 2

    def test_cli_create_list_help_shows_tag_option(self, runner, temp_db):
        """Test that CLI help shows the new --tag option"""
        result = runner.invoke(cli, ["--db-path", temp_db, "list", "create", "--help"])

        assert result.exit_code == 0
        assert "--tag" in result.output
        assert "Tags to assign" in result.output
        assert "must already exist" in result.output

    def test_cli_create_list_duplicate_tags_in_command(
        self, runner, temp_db, manager_with_tags
    ):
        """Test CLI create list with duplicate tags in command"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "duplicate-test",
                "--title",
                "Duplicate Test",
                "--tag",
                "frontend",
                "--tag",
                "frontend",  # duplicate
                "--tag",
                "FRONTEND",  # case variant
            ],
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert (
            "Tags: frontend, frontend, FRONTEND" in result.output
        )  # Shows input as-is

        # Verify in database (duplicates should be handled)
        tags = manager_with_tags.get_tags_for_list("duplicate-test")
        assert len(tags) == 1  # Only one instance
        assert tags[0].name == "frontend"

    def test_cli_create_list_error_message_format(self, runner, temp_db):
        """Test CLI error message format for non-existent tags"""
        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "error-format-test",
                "--title",
                "Error Format Test",
                "--tag",
                "missing-tag",
            ],
        )

        assert result.exit_code == 0
        assert "Error: Tag 'missing-tag' does not exist" in result.output
        assert "Create it first using:" in result.output
        assert "todoit tag create missing-tag" in result.output

        # Should use red color for error
        assert "❌" in result.output

    def test_cli_create_list_preserves_force_tags_functionality(self, runner, temp_db):
        """Test that --tag option works alongside TODOIT_FORCE_TAGS"""
        # Create tags
        manager = TodoManager(temp_db)
        manager.create_tag("env-tag", "blue")
        manager.create_tag("user-tag", "green")

        # Set environment variable for force tags
        env = os.environ.copy()
        env["TODOIT_FORCE_TAGS"] = "env-tag"

        result = runner.invoke(
            cli,
            [
                "--db-path",
                temp_db,
                "list",
                "create",
                "--list",
                "force-test",
                "--title",
                "Force Test",
                "--tag",
                "user-tag",
            ],
            env=env,
        )

        assert result.exit_code == 0
        assert "List Created" in result.output
        assert "Tags: user-tag" in result.output
        assert "Auto-tagged with: env-tag" in result.output

        # Verify both tags are applied
        tags = manager.get_tags_for_list("force-test")
        tag_names = [tag.name for tag in tags]
        assert len(tags) == 2
        assert "env-tag" in tag_names
        assert "user-tag" in tag_names
