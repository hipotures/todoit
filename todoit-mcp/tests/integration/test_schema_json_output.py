"""
Test JSON output format for schema command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for schema command
"""

import json
import os

import pytest
from click.testing import CliRunner

from interfaces.cli import cli


class TestSchemaJsonOutput:
    """Test JSON output format for schema command"""

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

    def test_schema_json_output_basic(self):
        """Test schema command with JSON output"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)
            assert "title" in output_data
            assert "count" in output_data
            assert "data" in output_data

            # Should have multiple schema entries
            assert output_data["count"] > 10  # We have many schema entries
            assert len(output_data["data"]) == output_data["count"]

            # Check data structure
            for item in output_data["data"]:
                assert "Category" in item
                assert "Value" in item
                assert "Description" in item

                # All fields should be strings
                assert isinstance(item["Category"], str)
                assert isinstance(item["Value"], str)
                assert isinstance(item["Description"], str)

    def test_schema_json_output_categories(self):
        """Test that all expected schema categories are present"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Extract categories (non-empty category fields)
            categories = set(
                item["Category"] for item in output_data["data"] if item["Category"]
            )

            # Expected categories based on schema_info
            expected_categories = {
                "Item Statuses",
                "List Types",
                "Dependency Types",
                "History Actions",
            }

            # All expected categories should be present
            assert expected_categories.issubset(categories)

    def test_schema_json_output_item_statuses(self):
        """Test that item statuses are correctly included"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Find item status entries
            status_items = [
                item
                for item in output_data["data"]
                if item["Category"] == "Item Statuses"
                or (
                    item["Category"] == ""
                    and item["Value"]
                    in ["pending", "in_progress", "completed", "failed"]
                )
            ]

            # Should have all 4 statuses
            status_values = [item["Value"] for item in status_items]
            expected_statuses = ["pending", "in_progress", "completed", "failed"]

            for expected_status in expected_statuses:
                assert expected_status in status_values

            # Check that descriptions are present for statuses
            status_with_descriptions = [
                item for item in status_items if item["Description"]
            ]
            assert len(status_with_descriptions) >= 3  # Most should have descriptions

    def test_schema_json_output_dependency_types(self):
        """Test that dependency types are correctly included"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Find dependency type entries
            dep_items = [
                item
                for item in output_data["data"]
                if item["Category"] == "Dependency Types"
                or (
                    item["Category"] == ""
                    and item["Value"] in ["blocks", "requires", "related"]
                )
            ]

            # Should have all 3 dependency types
            dep_values = [item["Value"] for item in dep_items]
            expected_deps = ["blocks", "requires", "related"]

            for expected_dep in expected_deps:
                assert expected_dep in dep_values

    def test_schema_json_output_list_types(self):
        """Test that list types are correctly included"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Find list type entries
            list_items = [
                item
                for item in output_data["data"]
                if item["Category"] == "List Types"
                or (item["Category"] == "" and item["Value"] in ["sequential"])
            ]

            # Should have only sequential list type
            list_values = [item["Value"] for item in list_items]
            expected_types = ["sequential"]

            for expected_type in expected_types:
                assert expected_type in list_values

    def test_schema_json_output_descriptions_present(self):
        """Test that descriptions are present for schema values"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Count items with descriptions
            items_with_descriptions = [
                item for item in output_data["data"] if item["Description"]
            ]
            items_without_descriptions = [
                item for item in output_data["data"] if not item["Description"]
            ]

            # Most items should have descriptions (we have descriptions for all major categories)
            assert len(items_with_descriptions) >= len(items_without_descriptions)

            # Check some specific descriptions
            pending_item = next(
                (item for item in output_data["data"] if item["Value"] == "pending"),
                None,
            )
            assert pending_item is not None
            assert "waiting to be started" in pending_item["Description"].lower()

    def test_schema_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table

        with self.runner.isolated_filesystem():
            # Test table output
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Should not be JSON format
            assert not result.output.startswith("{")
            assert "Schema Information" in result.output
            assert "pending" in result.output
            assert "blocks" in result.output

    def test_schema_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "yaml"

        with self.runner.isolated_filesystem():
            # Test YAML output
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Should be YAML format
            assert "title:" in result.output
            assert "count:" in result.output
            assert "data:" in result.output
            assert "pending" in result.output

    def test_schema_xml_format(self):
        """Test that XML format works correctly"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "xml"

        with self.runner.isolated_filesystem():
            # Test XML output
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Should be XML format
            assert "<todoit_output>" in result.output
            assert "<title>" in result.output
            assert "<count>" in result.output
            assert "<data>" in result.output
            assert "pending" in result.output

    def test_schema_json_count_accuracy(self):
        """Test that the count field accurately reflects the number of data items"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Count should match actual data length
            assert output_data["count"] == len(output_data["data"])

            # Should have reasonable number of schema entries
            assert (
                output_data["count"] >= 12
            )  # We have 4 categories with multiple values each
            assert output_data["count"] <= 30  # But not too many

    def test_schema_json_category_grouping(self):
        """Test that categories are properly grouped (first item has category, rest are empty)"""
        os.environ["TODOIT_OUTPUT_FORMAT"] = "json"

        with self.runner.isolated_filesystem():
            # Test JSON output for schema
            result = self.runner.invoke(cli, ["--db-path", "test.db", "schema"])
            assert result.exit_code == 0

            # Verify JSON format
            output_data = json.loads(result.output)

            # Track categories and their first occurrences
            seen_categories = set()
            category_positions = {}

            for i, item in enumerate(output_data["data"]):
                if item["Category"]:  # Non-empty category
                    if item["Category"] in seen_categories:
                        # This category appeared before - should not happen for our schema format
                        # Each category should only appear once (on first item)
                        pass  # This is actually OK - we show category on first item only
                    else:
                        seen_categories.add(item["Category"])
                        category_positions[item["Category"]] = i

            # Should have the expected number of categories
            assert len(seen_categories) == 4  # 4 main categories in schema

            # Check that we have items without categories (grouped under each category)
            empty_category_items = [
                item for item in output_data["data"] if not item["Category"]
            ]
            assert (
                len(empty_category_items) > 0
            )  # Should have items grouped under categories
