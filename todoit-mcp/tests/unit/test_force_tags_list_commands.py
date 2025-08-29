"""
Unit tests for FORCE_TAGS functionality in list commands
Tests environment isolation for all list operations
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from interfaces.cli_modules.list_commands import (
    list_archive,
    list_delete,
    list_show,
    list_unarchive,
)


class TestFORCETagsListCommands:
    """Test FORCE_TAGS environment isolation in list commands"""

    @pytest.fixture
    def runner(self):
        """Create Click test runner"""
        return CliRunner()

    def test_list_show_blocked_by_force_tags(self, runner):
        """Test that list show --list is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Mock get_lists_by_tags to return empty list (no lists with required tags)
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]  # FORCE_TAGS=dev

                result = runner.invoke(
                    list_show, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                assert "TODOIT_FORCE_TAGS" in result.output
                # Should not call get_list
                mock_manager.get_list.assert_not_called()

    def test_list_show_allowed_by_force_tags(self, runner):
        """Test that list show --list works when list has required tags"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Mock list with correct tags
            mock_list = MagicMock()
            mock_list.list_key = "test_list"
            mock_manager.get_lists_by_tags.return_value = [mock_list]

            # Mock get_list and related calls
            mock_todo_list = MagicMock()
            mock_todo_list.list_key = "test_list"
            mock_todo_list.title = "Test List"
            mock_manager.get_list.return_value = mock_todo_list
            mock_manager.get_list_items.return_value = []
            mock_manager.get_list_properties.return_value = {}
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]  # FORCE_TAGS=dev

                result = runner.invoke(
                    list_show, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should work - no error message
                assert "not found or not accessible" not in result.output
                # Should call get_list
                mock_manager.get_list.assert_called_once_with("test_list")

    def test_list_delete_blocked_by_force_tags(self, runner):
        """Test that list delete is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = (
                []
            )  # No lists with required tags
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    list_delete,
                    ["--list", "test_list", "--force"],
                    obj={"db_path": "test.db"},
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                assert "TODOIT_FORCE_TAGS" in result.output
                mock_manager.delete_list.assert_not_called()

    def test_list_archive_blocked_by_force_tags(self, runner):
        """Test that list archive --list is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    list_archive,
                    ["--list", "test_list", "--force"],
                    obj={"db_path": "test.db"},
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                mock_manager.archive_list.assert_not_called()

    def test_list_unarchive_blocked_by_force_tags(self, runner):
        """Test that list unarchive is blocked when list doesn't have required tags"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_lists_by_tags.return_value = []
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    list_unarchive, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should be blocked
                assert "not found or not accessible" in result.output
                mock_manager.unarchive_list.assert_not_called()

    def test_no_force_tags_allows_all_access(self, runner):
        """Test that without FORCE_TAGS all lists are accessible"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_todo_list = MagicMock()
            mock_todo_list.list_key = "test_list"
            mock_todo_list.title = "Test List"
            mock_manager.get_list.return_value = mock_todo_list
            mock_manager.get_list_items.return_value = []
            mock_manager.get_list_properties.return_value = {}
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = []  # No FORCE_TAGS

                result = runner.invoke(
                    list_show, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should work without checking tags
                mock_manager.get_list.assert_called_once()
                # Should not call get_lists_by_tags when no filtering
                mock_manager.get_lists_by_tags.assert_not_called()

    def test_check_list_access_function_error_handling(self, runner):
        """Test _check_list_access handles errors gracefully"""

        with patch(
            "interfaces.cli_modules.list_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            # Simulate error in get_lists_by_tags
            mock_manager.get_lists_by_tags.side_effect = Exception("Database error")
            mock_get_manager.return_value = mock_manager

            with patch(
                "interfaces.cli_modules.list_commands._get_filter_tags"
            ) as mock_get_tags:
                mock_get_tags.return_value = ["dev"]

                result = runner.invoke(
                    list_show, ["--list", "test_list"], obj={"db_path": "test.db"}
                )

                # Should be blocked when error occurs
                assert "not found or not accessible" in result.output
                mock_manager.get_list.assert_not_called()
