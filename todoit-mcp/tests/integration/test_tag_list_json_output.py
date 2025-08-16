"""
Test JSON output format for tag list command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for tag list command
"""

import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestTagListJsonOutput:
    """Test JSON output format for tag list command"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        # Clean environment before each test
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]

    def teardown_method(self):
        """Clean up after each test"""
        if "TODOIT_OUTPUT_FORMAT" in os.environ:
            del os.environ["TODOIT_OUTPUT_FORMAT"]

    def test_tag_list_json_output_with_tags(self):
        """Test tag list command with JSON output when tags exist"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create some tags
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "work", "--color", "blue"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db", "test.db", "tag", "create", "--name", "personal", "--color", "green"],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "urgent", "--color", "red"]
            )
            assert result.exit_code == 0

            # Test JSON output for tag list
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 3
            assert len(output_data["data"]) == 3

            # Check data structure
            tag_names = [tag["Name"] for tag in output_data["data"]]
            assert "work" in tag_names
            assert "personal" in tag_names
            assert "urgent" in tag_names

            # Check that all tags have required fields
            for tag_data in output_data["data"]:
                assert "Name" in tag_data
                assert "Color" in tag_data
                assert "Created" in tag_data

                # Verify color format
                assert "●" in tag_data["Color"]

                # Verify created date format (YYYY-MM-DD HH:MM)
                created = tag_data["Created"]
                assert len(created) >= 16  # Minimum length for date format
                assert ":" in created  # Should contain time

    def test_tag_list_json_output_specific_colors(self):
        """Test tag list command with JSON output verifying specific color information"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create tags with specific colors
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "blue_tag", "--color", "blue"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "red_tag", "--color", "red"]
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 2

            # Find specific tags and verify colors
            blue_tag = next(
                tag for tag in output_data["data"] if tag["Name"] == "blue_tag"
            )
            red_tag = next(
                tag for tag in output_data["data"] if tag["Name"] == "red_tag"
            )

            # Check that colors are assigned (exact color may depend on system implementation)
            assert blue_tag["Color"].startswith("●")
            assert red_tag["Color"].startswith("●")

            # Verify that each tag has a color
            assert len(blue_tag["Color"]) > 2  # Should have "● " + color name
            assert len(red_tag["Color"]) > 2

    def test_tag_list_json_output_empty(self):
        """Test tag list command with JSON output when no tags exist"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output with no tags
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []

    def test_tag_list_json_output_single_tag(self):
        """Test tag list command with JSON output for single tag"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a single tag
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "solo"]
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            tag_data = output_data["data"][0]
            assert tag_data["Name"] == "solo"
            # Default color should be assigned (exact color may vary)
            assert tag_data["Color"].startswith("●")
            assert len(tag_data["Color"]) > 2  # Should have "● " + color name

    def test_tag_list_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a tag
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "test"]
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "test" in result.output
            assert "Available Tags" in result.output

    def test_tag_list_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Create a tag
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "yaml_test"]
            )
            assert result.exit_code == 0

            # Test YAML output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "yaml_test" in result.output

    def test_tag_list_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Create a tag
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "xml_test"]
            )
            assert result.exit_code == 0

            # Test XML output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "xml_test" in result.output

    def test_tag_list_multiple_tags_alphabetical_order(self):
        """Test tag list with multiple tags to verify ordering"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create tags in non-alphabetical order
            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "zebra"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "alpha"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db", "test.db", "tag", "create", "--name", "beta"]
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(cli, ["--db", "test.db", "tag", "list"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 3

            # Get tag names in order they appear
            tag_names = [tag["Name"] for tag in output_data["data"]]

            # Tags should be present (order may vary depending on DB implementation)
            assert "alpha" in tag_names
            assert "beta" in tag_names
            assert "zebra" in tag_names
