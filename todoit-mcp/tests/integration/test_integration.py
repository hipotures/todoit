"""
Integration Tests
End-to-end tests that verify the CLI commands against a temporary database file.
"""

import pytest
import tempfile
import os
from click.testing import CliRunner
from interfaces.cli import cli


@pytest.fixture
def temp_db_path():
    """Fixture to create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


def test_list_create_and_show(temp_db_path):
    """Test creating a list and then showing it."""
    runner = CliRunner()
    # Create a list
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "list",
            "create",
            "test-list",
            "--title",
            "My Test List",
        ],
    )
    assert result.exit_code == 0
    assert "List Created" in result.output

    # Show the list
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "test-list", "--tree"]
    )
    assert result.exit_code == 0
    assert "My Test List" in result.output


def test_item_add_and_list(temp_db_path):
    """Test adding an item to a list and verifying it's there."""
    runner = CliRunner()
    # Create a list first
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "item-list"])

    # Add an item
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item",
            "add",
            "item-list",
            "test-item",
            "My first task",
        ],
    )
    assert result.exit_code == 0
    assert "Added item" in result.output

    # Show the list and check for the item
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "item-list", "--tree"]
    )
    assert result.exit_code == 0
    assert "My first task" in result.output


def test_item_status_update(temp_db_path):
    """Test updating the status of an item."""
    runner = CliRunner()
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "status-list"])
    runner.invoke(
        cli,
        ["--db", temp_db_path, "item", "add", "status-list", "task1", "Task to update"],
    )

    # Update status to 'in_progress'
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item",
            "status",
            "status-list",
            "task1",
            "--status",
            "in_progress",
        ],
    )
    assert result.exit_code == 0
    assert "Updated 'task1'" in result.output

    # Verify the status change
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "status-list", "--tree"]
    )
    assert "🔄" in result.output


def test_subtask_creation_and_hierarchy(temp_db_path):
    """Test creating a subtask and viewing the hierarchy."""
    runner = CliRunner()
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "hier-list"])
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "hier-list", "parent", "Parent Task"]
    )

    # Add a subtask
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item",
            "add-subtask",
            "hier-list",
            "parent",
            "child",
            "Child Task",
        ],
    )
    assert result.exit_code == 0
    assert "Added subtask" in result.output

    # Check the tree view
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "hier-list", "--tree"]
    )
    assert "Parent Task" in result.output
    assert "Child Task" in result.output


def test_dependency_management(temp_db_path):
    """Test adding and removing dependencies between items."""
    runner = CliRunner()
    # Create two lists
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "backend"])
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "frontend"])
    # Add items to each list
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "backend", "api", "API endpoint"]
    )
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "frontend", "ui", "UI component"]
    )

    # Add a dependency
    result = runner.invoke(
        cli,
        ["--db", temp_db_path, "dep", "add", "frontend:ui", "requires", "backend:api"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Dependency added" in result.output

    # Check if the item is blocked
    result = runner.invoke(cli, ["--db", temp_db_path, "dep", "show", "frontend:ui"])
    assert "Blocked By" in result.output  # Updated to match new table header
    assert "api" in result.output

    # Remove the dependency
    result = runner.invoke(
        cli,
        ["--db", temp_db_path, "dep", "remove", "frontend:ui", "backend:api"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Dependency removed" in result.output
