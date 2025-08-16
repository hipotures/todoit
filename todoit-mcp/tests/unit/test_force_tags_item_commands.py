"""
Unit tests for FORCE_TAGS functionality in item commands
Tests environment isolation for all item operations
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from interfaces.cli_modules.item_commands import (
    item_status,
    item_add,
    item_next,
    item_tree,
)


class TestFORCETagsItemCommands:
    """Test FORCE_TAGS environment isolation in item commands"""

    @pytest.fixture
    def runner(self):
        """Create Click test runner"""
        return CliRunner()

    def test_item_status_blocked_by_force_tags(self, runner):
        """Test that item status --list is --item blocked --status when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Mock get_lists_by_tags to return empty list (no lists with required tags)
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]  # FORCE_TAGS=dev

                result = runner.invoke(
                    item_status,
                    ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                    obj={"db_path": "test.db"},
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                assert "TODOIT_FORCE_TAGS" in result.output
                # Should not call update_item_status
                mock_manager.update_item_status.assert_not_called()

    def test_item_status_allowed_by_force_tags(self, runner):
        """Test that item status --list works --item when --status list has required tags"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Mock list with correct tags
            mock_list = MagicMock()
            mock_list.list_key = "test_list"
            mock_manager.get_lists_by_tags.return_value = [mock_list]

            mock_item = MagicMock()
            mock_item.item_key = "test_item"
            mock_manager.update_item_status.return_value = mock_item
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]  # FORCE_TAGS=dev

                result = runner.invoke(
                    item_status,
                    ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                    obj={"db_path": "test.db"},
                )

                # Should work
                assert "Updated item 'test_item'" in result.output
                # Should call update_item_status
                mock_manager.update_item_status.assert_called_once()

    def test_item_add_blocked_by_force_tags(self, runner):
        """Test that item add is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = (
                []
            )  # No lists with required tags
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    item_add,
                    ["--list", "test_list", "--item", "test_item", "--title", "Test content"],
                    obj={"db_path": "test.db"},
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                assert "TODOIT_FORCE_TAGS" in result.output
                mock_manager.add_item.assert_not_called()

    def test_item_next_blocked_by_force_tags(self, runner):
        """Test that item next --list is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    item_next, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                mock_manager.get_next_pending.assert_not_called()

    def test_item_tree_blocked_by_force_tags(self, runner):
        """Test that item list --list is --item blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    item_tree, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                mock_manager.get_list.assert_not_called()

    def test_no_force_tags_allows_all_access(self, runner):
        """Test that without FORCE_TAGS all lists are accessible"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_item = MagicMock()
            mock_item.item_key = "test_item"
            mock_manager.update_item_status.return_value = mock_item
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = []  # No FORCE_TAGS

                result = runner.invoke(
                    item_status,
                    ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                    obj={"db_path": "test.db"},
                )

                # Should work without checking tags
                assert "Updated item 'test_item'" in result.output
                mock_manager.update_item_status.assert_called_once()
                # Should not call get_lists_by_tags when no filtering
                mock_manager.get_lists_by_tags.assert_not_called()

    def test_check_list_access_function_error_handling(self, runner):
        """Test _check_list_access handles errors gracefully"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Simulate error in get_lists_by_tags
            mock_manager.get_lists_by_tags.side_effect = Exception("Database error")
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.item_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    item_status,
                    ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                    obj={"db_path": "test.db"},
                )

                # Should be blocked when error occurs
                assert "not found or not accessible" in result.output
                mock_manager.update_item_status.assert_not_called()
