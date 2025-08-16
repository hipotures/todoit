"""
Unit tests for CLI error handling improvements
Tests the enhanced status command error messages
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from interfaces.cli_modules.item_commands import item_status


class TestCLIErrorHandling:
    """Test improved error handling for CLI commands"""

    @pytest.fixture
    def runner(self):
        """Create Click test runner"""
        return CliRunner()

    def test_status_command_missing_status_shows_help(self, runner):
        """Test that --status flag without value shows helpful error message"""

        # Mock the manager and context
        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            # Test --status flag without value (uses flag_value='_show_help')
            result = runner.invoke(
                item_status,
                ["--list", "test_list", "--item", "test_item", "--status"],
                obj={"db_path": "test.db"},
            )

            # Should show standard Click error message
            assert "Option '--status' requires an argument" in result.output
            assert result.exit_code == 2

    def test_status_command_with_valid_status_works(self, runner):
        """Test that valid status argument works correctly"""

        with (
            patch(
                "interfaces.cli_modules.item_commands.get_manager"
            ) as mock_get_manager,
            patch(
                "interfaces.cli_modules.item_commands._check_list_access"
            ) as mock_check_access,
        ):
            mock_manager = MagicMock()
            mock_item = MagicMock()
            mock_item.item_key = "test_item"
            mock_manager.update_item_status.return_value = mock_item
            mock_get_manager.return_value = mock_manager
            mock_check_access.return_value = True  # Allow access

            result = runner.invoke(
                item_status,
                ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                obj={"db_path": "test.db"},
            )

            # Should call update_item_status with correct parameters
            mock_manager.update_item_status.assert_called_once_with(
                list_key="test_list",
                item_key="test_item",
                status="completed",
                completion_states=None,
                parent_item_key=None,
            )

            # Should show success message
            assert "Updated item 'test_item'" in result.output
            assert result.exit_code == 0

    def test_status_command_with_states(self, runner):
        """Test status command with completion states"""

        with (
            patch(
                "interfaces.cli_modules.item_commands.get_manager"
            ) as mock_get_manager,
            patch(
                "interfaces.cli_modules.item_commands._check_list_access"
            ) as mock_check_access,
        ):
            mock_manager = MagicMock()
            mock_item = MagicMock()
            mock_item.item_key = "test_item"
            mock_manager.update_item_status.return_value = mock_item
            mock_get_manager.return_value = mock_manager
            mock_check_access.return_value = True  # Allow access

            result = runner.invoke(
                item_status,
                [
                    "--list",
                    "test_list",
                    "--item",
                    "test_item",
                    "--status",
                    "in_progress",
                    "--state",
                    "tested=true",
                    "--state",
                    "reviewed=false",
                ],
                obj={"db_path": "test.db"},
            )

            # Should call update_item_status with states
            expected_states = {"tested": True, "reviewed": False}
            mock_manager.update_item_status.assert_called_once_with(
                list_key="test_list",
                item_key="test_item",
                status="in_progress",
                completion_states=expected_states,
                parent_item_key=None,
            )

            # Should show success and states
            assert "Updated item 'test_item'" in result.output
            assert "States:" in result.output
            assert result.exit_code == 0

    def test_status_command_handles_manager_errors(self, runner):
        """Test that manager errors are properly displayed"""

        with (
            patch(
                "interfaces.cli_modules.item_commands.get_manager"
            ) as mock_get_manager,
            patch(
                "interfaces.cli_modules.item_commands._check_list_access"
            ) as mock_check_access,
        ):
            mock_manager = MagicMock()
            mock_manager.update_item_status.side_effect = ValueError("Item not found")
            mock_get_manager.return_value = mock_manager
            mock_check_access.return_value = True  # Allow access

            result = runner.invoke(
                item_status,
                ["--list", "test_list", "--item", "test_item", "--status", "completed"],
                obj={"db_path": "test.db"},
            )

            # Should show error message
            assert "Error:" in result.output
            assert "Item not found" in result.output

    def test_status_command_with_invalid_status_shows_help(self, runner):
        """Test that invalid status value shows helpful error message"""

        with patch(
            "interfaces.cli_modules.item_commands.get_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            result = runner.invoke(
                item_status,
                ["--list", "test_list", "--item", "test_item", "--status", "invalid_status"],
                obj={"db_path": "test.db"},
            )

            # Should show Click Choice validation error
            assert "Invalid value for '--status'" in result.output or "invalid_status" in result.output
            assert result.exit_code == 2
