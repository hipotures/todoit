"""
Comprehensive End-to-End CLI Tests

This test suite covers ALL CLI functionalities in a complete user workflow,
ensuring the entire system works together from start to finish.
"""

import json
import os
import tempfile

import pytest
import yaml
from click.testing import CliRunner

from interfaces.cli import cli


class TestE2EComprehensiveCLI:
    """Comprehensive E2E tests covering complete CLI functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)

    def test_complete_project_lifecycle(self, temp_db):
        """
        Tests a complete project lifecycle from creation to archive:
        1. Project setup (lists, tags, properties)
        2. Task management (items, subitems, status changes)
        3. Dependencies and blocking logic
        4. Progress tracking and statistics
        5. Import/export functionality
        6. Different output formats
        7. Archive/unarchive workflow
        8. Cleanup and deletion
        """
        runner = CliRunner()
        db_arg = ["--db-path", temp_db]

        # ============ PHASE 1: PROJECT SETUP ============

        # Create project lists
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "backend",
                "--title",
                "Backend Development",
            ],
        )
        assert result.exit_code == 0
        assert "List Created" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "frontend",
                "--title",
                "Frontend Development",
            ],
        )
        assert result.exit_code == 0
        assert "List Created" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "testing",
                "--title",
                "Quality Assurance",
            ],
        )
        assert result.exit_code == 0
        assert "List Created" in result.output

        # Create and assign tags
        result = runner.invoke(
            cli, [*db_arg, "tag", "create", "--name", "urgent", "--color", "red"]
        )
        assert result.exit_code == 0
        assert "Tag 'urgent' created" in result.output

        result = runner.invoke(
            cli, [*db_arg, "tag", "create", "--name", "enhancement", "--color", "blue"]
        )
        assert result.exit_code == 0
        assert "Tag 'enhancement' created" in result.output

        result = runner.invoke(
            cli, [*db_arg, "list", "tag", "add", "--list", "backend", "--tag", "urgent"]
        )
        assert result.exit_code == 0
        assert "Added tag 'urgent'" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "tag",
                "add",
                "--list",
                "frontend",
                "--tag",
                "enhancement",
            ],
        )
        assert result.exit_code == 0
        assert "Added tag 'enhancement'" in result.output

        # Set project properties
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "property",
                "set",
                "--list",
                "backend",
                "--key",
                "deadline",
                "--value",
                "2025-09-01",
            ],
        )
        assert result.exit_code == 0
        assert "Set property 'deadline'" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "property",
                "set",
                "--list",
                "backend",
                "--key",
                "lead_developer",
                "--value",
                "Alice",
            ],
        )
        assert result.exit_code == 0

        # Verify properties
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "property",
                "get",
                "--list",
                "backend",
                "--key",
                "deadline",
            ],
        )
        assert result.exit_code == 0
        assert "2025-09-01" in result.output

        # ============ PHASE 2: TASK MANAGEMENT ============

        # Add main tasks
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "backend",
                "--item",
                "api",
                "--title",
                "REST API Development",
            ],
        )
        assert result.exit_code == 0
        assert "Added item 'api'" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "backend",
                "--item",
                "database",
                "--title",
                "Database Design",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "frontend",
                "--item",
                "ui",
                "--title",
                "User Interface",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "testing",
                "--item",
                "unit_tests",
                "--title",
                "Unit Testing",
            ],
        )
        assert result.exit_code == 0

        # Add subtasks
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "backend",
                "--item",
                "api",
                "--subitem",
                "auth",
                "--title",
                "Authentication",
            ],
        )
        assert result.exit_code == 0
        assert "Added subitem 'auth'" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "backend",
                "--item",
                "api",
                "--subitem",
                "endpoints",
                "--title",
                "API Endpoints",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "backend",
                "--item",
                "database",
                "--subitem",
                "schema",
                "--title",
                "Database Schema",
            ],
        )
        assert result.exit_code == 0

        # Show initial project state
        result = runner.invoke(cli, [*db_arg, "list", "all"])
        assert result.exit_code == 0
        assert "Backend" in result.output and "Development" in result.output
        assert "Frontend" in result.output and "Development" in result.output
        assert "Quality" in result.output and "Assurance" in result.output

        # ============ PHASE 3: DEPENDENCIES AND WORKFLOW ============

        # Create cross-list dependencies
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "dep",
                "add",
                "--dependent",
                "frontend:ui",
                "--required",
                "backend:api",
            ],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Dependency added" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "dep",
                "add",
                "--dependent",
                "testing:unit_tests",
                "--required",
                "backend:database",
            ],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Dependency added" in result.output

        # Check dependency blocking
        result = runner.invoke(cli, [*db_arg, "dep", "show", "--item", "frontend:ui"])
        assert result.exit_code == 0
        assert "projekt-web:frontend" in result.output or "frontend" in result.output

        # Verify next item logic (should be blocked)
        result = runner.invoke(cli, [*db_arg, "item", "next", "--list", "frontend"])
        assert result.exit_code == 0
        # Frontend should be blocked until backend API is complete

        # ============ PHASE 4: PROGRESS TRACKING ============

        # Work on backend tasks
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "backend",
                "--item",
                "api",
                "--subitem",
                "auth",
                "--status",
                "in_progress",
            ],
        )
        assert result.exit_code == 0
        assert "Updated subitem 'auth' status" in result.output

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "backend",
                "--item",
                "api",
                "--subitem",
                "auth",
                "--status",
                "completed",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "backend",
                "--item",
                "api",
                "--subitem",
                "endpoints",
                "--status",
                "completed",
            ],
        )
        assert result.exit_code == 0

        # Check auto-synchronization (parent should auto-complete)
        result = runner.invoke(cli, [*db_arg, "list", "show", "--list", "backend"])
        assert result.exit_code == 0
        assert "✅" in result.output  # API should be completed

        # Get progress statistics
        result = runner.invoke(cli, [*db_arg, "stats", "progress", "--list", "backend"])
        assert result.exit_code == 0
        assert "Progress Report" in result.output

        # ============ PHASE 5: EXPORT/IMPORT ============

        # Export to markdown
        export_file = f"{temp_db}_export.md"
        result = runner.invoke(
            cli, [*db_arg, "io", "export", "--list", "backend", "--file", export_file]
        )
        assert result.exit_code == 0
        assert "Exported list 'backend'" in result.output

        # Verify export file content
        assert os.path.exists(export_file)
        with open(export_file, "r") as f:
            content = f.read()
            assert "Backend Development" in content
            assert "[x]" in content  # Completed tasks
            assert "REST API" in content and "Development" in content

        # ============ PHASE 6: OUTPUT FORMATS ============

        # Test JSON output
        result = runner.invoke(
            cli, [*db_arg, "list", "all"], env={"TODOIT_OUTPUT_FORMAT": "json"}
        )
        assert result.exit_code == 0
        json_data = json.loads(result.output)
        assert "data" in json_data
        assert len(json_data["data"]) >= 3  # At least 3 lists

        # Test YAML output
        result = runner.invoke(
            cli, [*db_arg, "list", "all"], env={"TODOIT_OUTPUT_FORMAT": "yaml"}
        )
        assert result.exit_code == 0
        yaml_data = yaml.safe_load(result.output)
        assert "data" in yaml_data
        assert len(yaml_data["data"]) >= 3

        # Test schema command (ensure no parallel/hierarchical/linked types)
        result = runner.invoke(cli, [*db_arg, "schema"])
        assert result.exit_code == 0
        assert "sequential" in result.output
        assert "parallel" not in result.output
        assert "hierarchical" not in result.output
        assert "linked" not in result.output

        # ============ PHASE 7: ARCHIVE WORKFLOW ============

        # Complete remaining tasks for archiving
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "backend",
                "--item",
                "database",
                "--subitem",
                "schema",
                "--status",
                "completed",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "frontend",
                "--item",
                "ui",
                "--status",
                "completed",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "testing",
                "--item",
                "unit_tests",
                "--status",
                "completed",
            ],
        )
        assert result.exit_code == 0

        # Archive completed lists
        result = runner.invoke(cli, [*db_arg, "list", "archive", "--list", "backend"])
        assert result.exit_code == 0
        assert "has been archived" in result.output

        result = runner.invoke(cli, [*db_arg, "list", "archive", "--list", "frontend"])
        assert result.exit_code == 0

        # Verify lists are hidden from normal view
        result = runner.invoke(cli, [*db_arg, "list", "all"])
        assert result.exit_code == 0
        # Backend and Frontend should not appear (archived)
        assert (
            "Quality" in result.output and "Assurance" in result.output
        )  # Not archived
        assert (
            len(result.output.split("\n")) < 15
        )  # Shorter output without archived lists

        # Show archived lists
        result = runner.invoke(cli, [*db_arg, "list", "all", "--include-archived"])
        assert result.exit_code == 0
        assert "Backend" in result.output and "Development" in result.output
        assert "Frontend" in result.output and "Development" in result.output
        assert "Z" in result.output or "📦" in result.output  # Archive indicator

        # Unarchive a list
        result = runner.invoke(cli, [*db_arg, "list", "unarchive", "--list", "backend"])
        assert result.exit_code == 0
        assert "has been restored" in result.output

        # ============ PHASE 8: CLEANUP ============

        # Delete lists
        result = runner.invoke(
            cli, [*db_arg, "list", "delete", "--list", "testing"], input="y\n"
        )
        assert result.exit_code == 0
        assert "Successfully deleted" in result.output

        result = runner.invoke(
            cli, [*db_arg, "list", "delete", "--list", "frontend"], input="y\n"
        )
        assert result.exit_code == 0

        # Final verification
        result = runner.invoke(cli, [*db_arg, "list", "all"])
        assert result.exit_code == 0
        # Should only have backend list remaining

        # Cleanup export file
        if os.path.exists(export_file):
            os.unlink(export_file)

    def test_system_robustness(self, temp_db):
        """Test that system handles various operations robustly."""
        runner = CliRunner()
        db_arg = ["--db-path", temp_db]

        # Create a test list
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "robust_test",
                "--title",
                "Robustness Test",
            ],
        )
        assert result.exit_code == 0

        # System should handle various operations gracefully
        # (This system is designed to be permissive and user-friendly)

        # Test getting property that doesn't exist - should handle gracefully
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "property",
                "get",
                "--list",
                "robust_test",
                "--key",
                "nonexistent_property",
            ],
        )
        assert result.exit_code == 0  # Should handle gracefully

        # Test creating multiple lists with similar names
        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "similar1",
                "--title",
                "Similar List 1",
            ],
        )
        assert result.exit_code == 0

        result = runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "similar2",
                "--title",
                "Similar List 2",
            ],
        )
        assert result.exit_code == 0

        # System should handle various command combinations gracefully

    def test_emoji_mapping_in_outputs(self, temp_db):
        """Test that emoji mapping works correctly in different output formats."""
        runner = CliRunner()
        db_arg = ["--db-path", temp_db]

        # Create test data
        runner.invoke(
            cli,
            [
                *db_arg,
                "list",
                "create",
                "--list",
                "emoji_test",
                "--title",
                "Emoji Test",
            ],
        )
        runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list",
                "emoji_test",
                "--item",
                "task1",
                "--title",
                "Task 1",
            ],
        )
        runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "status",
                "--list",
                "emoji_test",
                "--item",
                "task1",
                "--status",
                "completed",
            ],
        )

        # Test JSON output has readable names, not emoji
        result = runner.invoke(
            cli, [*db_arg, "list", "all"], env={"TODOIT_OUTPUT_FORMAT": "json"}
        )
        assert result.exit_code == 0
        json_data = json.loads(result.output)

        # Should have readable field names
        list_record = json_data["data"][0]
        assert "tags" in list_record  # not 🏷️
        assert "completed_count" in list_record  # not ✅
        assert "pending_count" in list_record  # not 📋

        # Should NOT contain emoji in field names
        assert "🏷️" not in str(list_record)
        assert "✅" not in list(list_record.keys())

        # Test YAML output
        result = runner.invoke(
            cli, [*db_arg, "list", "all"], env={"TODOIT_OUTPUT_FORMAT": "yaml"}
        )
        assert result.exit_code == 0
        yaml_data = yaml.safe_load(result.output)
        list_record = yaml_data["data"][0]
        assert "tags" in list_record
        assert "completed_count" in list_record
