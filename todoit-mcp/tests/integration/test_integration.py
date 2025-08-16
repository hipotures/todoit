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
            "list", "create", "--list", "test-list", "--title",
            "My Test List",
        ],
    )
    assert result.exit_code == 0
    assert "List Created" in result.output

    # Show the list
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "--list", "test-list", "--tree"]
    )
    assert result.exit_code == 0
    assert "My Test List" in result.output


def test_item_add_and_list(temp_db_path):
    """Test adding an item to a list and verifying it's there."""
    runner = CliRunner()
    # Create a list first
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "--list", "item-list"])

    # Add an item
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item", "add", "--list", "item-list", "--item", "test-item", "--title", "My first item",
        ],
    )
    assert result.exit_code == 0
    assert "Added item" in result.output

    # Show the list and check for the item
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "--list", "item-list", "--tree"]
    )
    assert result.exit_code == 0
    assert "My first item" in result.output


def test_item_status_update(temp_db_path):
    """Test updating the status of an item."""
    runner = CliRunner()
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "--list", "status-list"])
    runner.invoke(
        cli,
        ["--db", temp_db_path, "item", "add", "--list", "status-list", "--item", "task1", "--title", "Item to update"],
    )

    # Update status to 'in_progress'
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item", "status", "--list", "status-list", "--item", "task1", "--status",
            "in_progress",
        ],
    )
    assert result.exit_code == 0
    assert "Updated 'task1'" in result.output

    # Verify the status change
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "--list", "status-list", "--tree"]
    )
    assert "🔄" in result.output


def test_subtask_creation_and_hierarchy(temp_db_path):
    """Test creating a subitem and viewing the hierarchy."""
    runner = CliRunner()
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "--list", "hier-list"])
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "--list", "hier-list", "--item", "parent", "--title", "Parent Item"]
    )

    # Add a subitem
    result = runner.invoke(
        cli,
        [
            "--db",
            temp_db_path,
            "item", "add", "--list", "hier-list", "--item", "parent", "--subitem", "child", "--title", "Child Item",
        ],
    )
    assert result.exit_code == 0
    assert "Added subitem" in result.output

    # Check the tree view
    result = runner.invoke(
        cli, ["--db", temp_db_path, "list", "show", "--list", "hier-list", "--tree"]
    )
    assert "Parent Item" in result.output
    assert "Child Item" in result.output


def test_dependency_management(temp_db_path):
    """Test adding and removing dependencies between items."""
    runner = CliRunner()
    # Create two lists
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "--list", "backend"])
    runner.invoke(cli, ["--db", temp_db_path, "list", "create", "--list", "frontend"])
    # Add items to each list
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "--list", "backend", "--item", "api", "--title", "API endpoint"]
    )
    runner.invoke(
        cli, ["--db", temp_db_path, "item", "add", "--list", "frontend", "--item", "ui", "--title", "UI component"]
    )

    # Add a dependency
    result = runner.invoke(
        cli,
        ["--db", temp_db_path, "dep", "add", "--dependent", "frontend:ui", "--required", "backend:api"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Dependency added" in result.output

    # Check if the item is blocked
    result = runner.invoke(cli, ["--db", temp_db_path, "dep", "show", "--item", "frontend:ui"])
    assert "Blocked By" in result.output  # Updated to match new table header
    assert "api" in result.output

    # Remove the dependency
    result = runner.invoke(
        cli,
        ["--db", temp_db_path, "dep", "remove", "--dependent", "frontend:ui", "--required", "backend:api"],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "Dependency removed" in result.output
