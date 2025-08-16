"""
End-to-End (E2E) tests for the TODOIT CLI.

These tests simulate a complete user workflow, from creating lists and tasks
to managing dependencies and checking status, ensuring all components
(CLI, Manager, Database) work together correctly.
"""

import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestE2EWorkflow:
    """End-to-end workflow tests using the CliRunner."""

    def test_complete_project_workflow(self, temp_db):
        """
        Tests a complete, realistic project workflow:
        1.  Create two lists for a project.
        2.  Add tasks and subtasks.
        3.  Create a dependency between tasks in different lists.
        4.  Verify that the dependent task is blocked.
        5.  Complete the prerequisite task.
        6.  Verify that the dependent item is now unblocked.
        """
        runner = CliRunner()
        db_arg = ["--db-path", temp_db]

        # STEP 1: Create project lists
        res_create_backend = runner.invoke(
            cli,
            [*db_arg, "list", "create", "--list", "backend", "--title", "Backend Development"],
        )
        assert res_create_backend.exit_code == 0
        assert "List Created" in res_create_backend.output

        res_create_frontend = runner.invoke(
            cli,
            [*db_arg, "list", "create", "--list", "frontend", "--title", "Frontend Development"],
        )
        assert res_create_frontend.exit_code == 0
        assert "List Created" in res_create_frontend.output

        # STEP 2: Add tasks and subtasks
        runner.invoke(cli, [*db_arg, "item", "add", "--list", "backend", "--item", "api", "--title", "REST API"])
        runner.invoke(
            cli,
            [
                *db_arg,
                "item",
                "add",
                "--list", "backend",
                "--item", "api",
                "--subitem", "auth",
                "--title", "Authentication endpoints",
            ],
        )
        runner.invoke(cli, [*db_arg, "item", "add", "--list", "frontend", "--item", "ui", "--title", "User Interface"])

        # STEP 3: Create a cross-list dependency
        res_dep_add = runner.invoke(
            cli,
            [*db_arg, "dep", "add", "--dependent", "frontend:ui", "--required", "backend:api"],
            input="y\n",
        )
        assert res_dep_add.exit_code == 0
        assert "Dependency added" in res_dep_add.output

        # STEP 4: Verify the frontend item is blocked
        res_next_frontend_blocked = runner.invoke(
            cli, [*db_arg, "item", "next", "--list", "frontend"]
        )
        assert res_next_frontend_blocked.exit_code == 0
        # The output should indicate that the item is blocked or no items are available
        assert (
            "No next item for list 'frontend' found" in res_next_frontend_blocked.output
        )

        # STEP 5: Complete the backend tasks
        # Complete the subitem first
        res_done_subtask = runner.invoke(
            cli, [*db_arg, "item", "status", "--list", "backend", "--item", "api", "--subitem", "auth", "--status", "completed"]
        )
        assert res_done_subtask.exit_code == 0

        # When the last subitem is completed, the parent should auto-complete
        res_show_backend = runner.invoke(
            cli, [*db_arg, "list", "show", "--list", "backend"]
        )
        output = res_show_backend.output.lower()
        assert "rest api" in output and "✅" in output
        assert "authentication endpoints" in output

        # STEP 6: Verify the frontend item is now unblocked
        res_next_frontend_unblocked = runner.invoke(
            cli, [*db_arg, "item", "next", "--list", "frontend"]
        )
        assert res_next_frontend_unblocked.exit_code == 0
        assert "ui" in res_next_frontend_unblocked.output
        assert "User Interface" in res_next_frontend_unblocked.output
