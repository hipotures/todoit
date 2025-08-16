"""
Integration tests for emoji to readable names mapping in JSON output.

Tests that emoji symbols in table headers are properly mapped to human-readable
field names in JSON, YAML, and XML output formats for better API usability.
"""

import pytest
import json
import yaml
import tempfile
import os
from click.testing import CliRunner
from interfaces.cli import cli


class TestEmojiMappingJSON:
    """Integration tests for emoji mapping in JSON output"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_list_all_json_emoji_mapping(self, runner):
        """Test that list all JSON output maps emoji to readable names"""
        with runner.isolated_filesystem():
            # Create test list with items
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Item 1"]
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task2", "--title", "Item 2"]
            )
            assert result.exit_code == 0

            # Mark one item as completed
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item", "status", "--list", "testlist", "--item", "task1", "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output
            result = runner.invoke(
                cli,
                ["--db", "test.db", "list", "all"],
                env={"TODOIT_OUTPUT_FORMAT": "json"},
            )
            assert result.exit_code == 0

            # Parse JSON output
            json_data = json.loads(result.output)
            assert "data" in json_data
            assert len(json_data["data"]) == 1

            # Check that emoji keys are mapped to readable names
            list_record = json_data["data"][0]

            # These should be readable names, not emoji
            assert "tags" in list_record  # was 🏷️
            assert "type" in list_record  # was 🔀
            assert "pending_count" in list_record  # was 📋
            assert "in_progress_count" in list_record  # was 🔄
            assert "failed_count" in list_record  # was ❌
            assert "completed_count" in list_record  # was ✅
            assert "completion_percentage" in list_record  # was ⏳

            # These should NOT contain emoji
            assert "🏷️" not in list_record
            assert "🔀" not in list_record
            assert "📋" not in list_record
            assert "🔄" not in list_record
            assert "❌" not in list_record
            assert "✅" not in list_record
            assert "⏳" not in list_record

            # Verify actual values make sense
            assert list_record["pending_count"] == "1"
            assert list_record["completed_count"] == "1"
            assert list_record["in_progress_count"] == "0"
            assert list_record["failed_count"] == "0"

    def test_yaml_output_emoji_mapping(self, runner):
        """Test that YAML output also maps emoji to readable names"""
        with runner.isolated_filesystem():
            # Create test list
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Item 1"]
            )
            assert result.exit_code == 0

            # Test YAML output
            result = runner.invoke(
                cli,
                ["--db", "test.db", "list", "all"],
                env={"TODOIT_OUTPUT_FORMAT": "yaml"},
            )
            assert result.exit_code == 0

            # Parse YAML output
            yaml_data = yaml.safe_load(result.output)
            assert "data" in yaml_data
            assert len(yaml_data["data"]) == 1

            # Check that emoji keys are mapped to readable names in YAML too
            list_record = yaml_data["data"][0]
            assert "tags" in list_record
            assert "type" in list_record
            assert "pending_count" in list_record
            assert "completed_count" in list_record

            # Should not contain emoji keys in data records (title may contain emoji)
            data_str = str(yaml_data["data"])
            assert "🏷️" not in data_str
            assert "📋" not in data_str

    def test_xml_output_emoji_mapping(self, runner):
        """Test that XML output also maps emoji to readable names"""
        with runner.isolated_filesystem():
            # Create test list
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "testlist", "--item", "task1", "--title", "Item 1"]
            )
            assert result.exit_code == 0

            # Test XML output
            result = runner.invoke(
                cli,
                ["--db", "test.db", "list", "all"],
                env={"TODOIT_OUTPUT_FORMAT": "xml"},
            )
            assert result.exit_code == 0

            # Check that XML contains readable names, not emoji
            xml_output = result.output
            assert "<tags>" in xml_output or "<tags />" in xml_output
            assert "<type>" in xml_output
            assert "<pending_count>" in xml_output
            assert "<completed_count>" in xml_output

            # Should not contain emoji in XML data tags (but title may contain emoji)
            # Extract just the data section to check
            import re

            data_section = re.search(r"<data>.*?</data>", xml_output, re.DOTALL)
            if data_section:
                data_content = data_section.group(0)
                assert "🏷️" not in data_content
                assert "📋" not in data_content
                assert "✅" not in data_content

    def test_table_output_still_uses_emoji(self, runner):
        """Test that table output still uses emoji for visual appeal"""
        with runner.isolated_filesystem():
            # Create test list
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "list", "create", "--list", "testlist", "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Test table output (default)
            result = runner.invoke(cli, ["--db", "test.db", "list", "all"])
            assert result.exit_code == 0

            # Table output should still contain emoji for visual appeal
            table_output = result.output
            assert "🏷️" in table_output or "📋" in table_output or "✅" in table_output

    def test_mapping_completeness(self):
        """Test that EMOJI_TO_NAME_MAPPING covers all expected emoji"""
        from interfaces.cli_modules.display import EMOJI_TO_NAME_MAPPING

        # All the emoji used in list display should be mapped
        expected_emoji = ["🏷️", "🔀", "📋", "🔄", "❌", "✅", "⏳", "📦"]

        for emoji in expected_emoji:
            assert emoji in EMOJI_TO_NAME_MAPPING, f"Missing mapping for emoji: {emoji}"

        # All mapped names should be valid identifiers (no spaces, special chars)
        for emoji, name in EMOJI_TO_NAME_MAPPING.items():
            assert isinstance(name, str), f"Name for {emoji} should be string"
            assert name.replace(
                "_", ""
            ).isalnum(), (
                f"Name '{name}' for {emoji} should be alphanumeric with underscores"
            )
            assert not name.startswith(
                "_"
            ), f"Name '{name}' for {emoji} should not start with underscore"

    def test_empty_list_json_mapping(self, runner):
        """Test emoji mapping works with empty lists"""
        with runner.isolated_filesystem():
            # Test with no lists
            result = runner.invoke(
                cli,
                ["--db", "test.db", "list", "all"],
                env={"TODOIT_OUTPUT_FORMAT": "json"},
            )
            assert result.exit_code == 0

            # Parse JSON output
            json_data = json.loads(result.output)
            assert "data" in json_data
            assert json_data["data"] == []
            assert json_data["count"] == 0

    def test_multiple_lists_json_mapping(self, runner):
        """Test emoji mapping with multiple lists having different statuses"""
        with runner.isolated_filesystem():
            # Create multiple lists with different content
            result = runner.invoke(
                cli, ["--db", "test.db", "list", "create", "--list", "list1", "--title", "List 1"]
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "list", "create", "--list", "list2", "--title", "List 2"]
            )
            assert result.exit_code == 0

            # Add items to first list
            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "list1", "--item", "task1", "--title", "Item 1"]
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli, ["--db", "test.db", "item", "add", "--list", "list1", "--item", "task2", "--title", "Item 2"]
            )
            assert result.exit_code == 0

            # Mark one as failed, one as completed
            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item", "status", "--list", "list1", "--item", "task1", "--status",
                    "completed",
                ],
            )
            assert result.exit_code == 0

            result = runner.invoke(
                cli,
                [
                    "--db",
                    "test.db",
                    "item", "status", "--list", "list1", "--item", "task2", "--status",
                    "failed",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output
            result = runner.invoke(
                cli,
                ["--db", "test.db", "list", "all"],
                env={"TODOIT_OUTPUT_FORMAT": "json"},
            )
            assert result.exit_code == 0

            # Parse JSON output
            json_data = json.loads(result.output)
            assert len(json_data["data"]) == 2

            # Check both lists have mapped field names
            for list_record in json_data["data"]:
                assert "completed_count" in list_record
                assert "failed_count" in list_record
                assert "pending_count" in list_record

                # No emoji keys should be present
                assert "✅" not in list_record
                assert "❌" not in list_record
                assert "📋" not in list_record
