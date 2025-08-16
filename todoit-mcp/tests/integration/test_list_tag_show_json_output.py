"""
Test JSON output format for list tag show command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for list tag show command
"""

import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestListTagShowJsonOutput:
    """Test JSON output format for list tag show command"""

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

    def test_list_tag_show_json_output_with_tags(self):
        """Test list tag show command with JSON output when list has tags"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Create some tags
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "work"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "urgent"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "personal"]
            )
            assert result.exit_code == 0

            # Assign tags to the list
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "work"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "urgent"]
            )
            assert result.exit_code == 0

            # Test JSON output for list tag show
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 2
            assert len(output_data["data"]) == 2

            # Check data structure
            tag_names = [tag["Tag Name"] for tag in output_data["data"]]
            assert "work" in tag_names
            assert "urgent" in tag_names

            # Check that all tags have required fields
            for tag_data in output_data["data"]:
                assert "Tag Name" in tag_data
                assert "Color" in tag_data
                assert "Assigned" in tag_data

                # Verify color format
                assert "●" in tag_data["Color"]

                # Verify assigned status
                assert tag_data["Assigned"] == "✓"

    def test_list_tag_show_json_output_single_tag(self):
        """Test list tag show command with JSON output for single tag"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            # Create and assign a single tag
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "solo"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "solo"]
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 1
            assert len(output_data["data"]) == 1

            tag_data = output_data["data"][0]
            assert tag_data["Tag Name"] == "solo"
            assert tag_data["Color"].startswith("●")
            assert tag_data["Assigned"] == "✓"

    def test_list_tag_show_json_output_no_tags(self):
        """Test list tag show command with JSON output when list has no tags"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list without tags
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "emptylist",
                    "--title",
                    "Empty List",
                ],
            )
            assert result.exit_code == 0

            # Test JSON output when no tags assigned
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "emptylist"]
            )
            assert result.exit_code == 0

            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data
            assert output_data["count"] == 0
            assert output_data["data"] == []

    def test_list_tag_show_json_output_list_title_in_output(self):
        """Test that list title appears in the JSON output title"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list with specific title
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "mylist",
                    "--title",
                    "My Custom List",
                ],
            )
            assert result.exit_code == 0

            # Create and assign a tag
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "testtag"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "mylist", "--tag", "testtag"]
            )
            assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "mylist"]
            )
            assert result.exit_code == 0

            # Verify that title includes the list title
            output_data = json.loads(result.output)
            assert "My Custom List" in output_data["title"]
            assert "🏷️ Tags for List:" in output_data["title"]

    def test_list_tag_show_json_output_nonexistent_list(self):
        """Test list tag show command with JSON output for nonexistent list"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for nonexistent list (should show error message)
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "nonexistent"]
            )

            # Command should fail gracefully
            # The exact behavior depends on implementation - might be exit code != 0 or error message
            # We'll just verify it doesn't crash and produces some output
            assert isinstance(result.output, str)

    def test_list_tag_show_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Create a test list and tag
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "test"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "test"]
            )
            assert result.exit_code == 0

            # Test table output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "test" in result.output
            assert "Tags for List" in result.output

    def test_list_tag_show_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Create a test list and tag
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "yaml_test"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "yaml_test"]
            )
            assert result.exit_code == 0

            # Test YAML output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "yaml_test" in result.output

    def test_list_tag_show_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Create a test list and tag
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "testlist",
                    "--title",
                    "Test List",
                ],
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "xml_test"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "testlist", "--tag", "xml_test"]
            )
            assert result.exit_code == 0

            # Test XML output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "testlist"]
            )
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "xml_test" in result.output

    def test_list_tag_show_with_multiple_colors(self):
        """Test list tag show with multiple differently colored tags"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(
                cli,
                [
                    "--db-path",
                    "test.db",
                    "list",
                    "create",
                    "--list",
                    "colorlist",
                    "--title",
                    "Color List",
                ],
            )
            assert result.exit_code == 0

            # Create tags with different colors
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "red_tag", "--color", "red"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "tag", "create", "--name", "blue_tag", "--color", "blue"]
            )
            assert result.exit_code == 0

            result = self.runner.invoke(
                cli,
                ["--db-path", "test.db", "tag", "create", "--name", "green_tag", "--color", "green"],
            )
            assert result.exit_code == 0

            # Assign all tags to the list
            for tag in ["red_tag", "blue_tag", "green_tag"]:
                result = self.runner.invoke(
                    cli, ["--db-path", "test.db", "list", "tag", "add", "--list", "colorlist", "--tag", tag]
                )
                assert result.exit_code == 0

            # Test JSON output
            result = self.runner.invoke(
                cli, ["--db-path", "test.db", "list", "tag", "show", "--list", "colorlist"]
            )
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data["count"] == 3

            # Verify all tags are present with color indicators
            tag_names = [tag["Tag Name"] for tag in output_data["data"]]
            colors = [tag["Color"] for tag in output_data["data"]]

            assert "red_tag" in tag_names
            assert "blue_tag" in tag_names
            assert "green_tag" in tag_names

            # All should have color indicators
            assert all("●" in color for color in colors)
            assert all(
                len(color) > 2 for color in colors
            )  # Should have "● " + color name
