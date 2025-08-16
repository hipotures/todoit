"""
Integration tests for property list JSON format.

Tests the new grouped JSON format for item property list command.
"""

import pytest
import json
import os
from click.testing import CliRunner
from core.manager import TodoManager
from interfaces.cli_modules.property_commands import item_property_list


class TestPropertyJsonFormat:
    """Integration tests for property list JSON format"""

    @pytest.fixture
    def manager(self, temp_db):
        """Create TodoManager with temporary database."""
        return TodoManager(temp_db)

    @pytest.fixture
    def setup_test_data(self, manager):
        """Setup test data with multiple items and properties."""
        # Create test list
        manager.create_list("testlist", "Test List")

        # Add test items
        manager.add_item("testlist", "scene_01", "Scene 1")
        manager.add_item("testlist", "item_0001", "Item 1")
        manager.add_item("testlist", "item_0002", "Item 2")

        # Add properties to scene_01
        manager.set_item_property(
            "testlist", "scene_01", "image_downloaded", "completed"
        )
        manager.set_item_property(
            "testlist", "scene_01", "image_generated", "completed"
        )
        manager.set_item_property(
            "testlist", "scene_01", "thread_id", "test-thread-123"
        )

        # Add properties to item_0001
        manager.set_item_property(
            "testlist", "item_0001", "image_downloaded", "pending"
        )
        manager.set_item_property(
            "testlist", "item_0001", "thread_id", "test-thread-456"
        )

        # Add properties to item_0002
        manager.set_item_property(
            "testlist", "item_0002", "image_downloaded", "completed"
        )
        manager.set_item_property("testlist", "item_0002", "image_generated", "pending")
        manager.set_item_property("testlist", "item_0002", "priority", "high")

        return {"list_key": "testlist"}

    def test_json_format_grouped_by_item(self, manager, setup_test_data):
        """Test that JSON output groups properties by item_key."""
        runner = CliRunner()

        # Set JSON output format
        env = {"TODOIT_OUTPUT_FORMAT": "json"}

        result = runner.invoke(
            item_property_list,
            ["--list", "testlist"],
            obj={"db_path": manager.db.db_path},
            env=env,
        )

        assert result.exit_code == 0

        # Parse JSON output
        json_data = json.loads(result.output)

        # Verify structure: item_key -> {property_key: property_value}
        assert "scene_01" in json_data
        assert "item_0001" in json_data
        assert "item_0002" in json_data

        # Verify scene_01 properties
        scene_01_props = json_data["scene_01"]
        assert scene_01_props["image_downloaded"] == "completed"
        assert scene_01_props["image_generated"] == "completed"
        assert scene_01_props["thread_id"] == "test-thread-123"
        assert len(scene_01_props) == 3

        # Verify item_0001 properties
        item_0001_props = json_data["item_0001"]
        assert item_0001_props["image_downloaded"] == "pending"
        assert item_0001_props["thread_id"] == "test-thread-456"
        assert len(item_0001_props) == 2

        # Verify item_0002 properties
        item_0002_props = json_data["item_0002"]
        assert item_0002_props["image_downloaded"] == "completed"
        assert item_0002_props["image_generated"] == "pending"
        assert item_0002_props["priority"] == "high"
        assert len(item_0002_props) == 3

    def test_table_format_unchanged(self, manager, setup_test_data):
        """Test that table format remains unchanged."""
        runner = CliRunner()

        # Default table format
        result = runner.invoke(
            item_property_list, ["--list", "testlist"], obj={"db_path": manager.db.db_path}
        )

        assert result.exit_code == 0

        # Should contain table headers and data
        output = result.output
        assert "Item Key" in output
        assert "Property Key" in output
        assert "Value" in output
        assert "scene_01" in output
        assert "item_0001" in output
        assert "item_0002" in output
        assert "thread_id" in output
        assert "image_downloaded" in output

    def test_tree_format_unchanged(self, manager, setup_test_data):
        """Test that tree format remains unchanged."""
        runner = CliRunner()

        result = runner.invoke(
            item_property_list,
            ["--list", "testlist", "--tree"],
            obj={"db_path": manager.db.db_path},
        )

        assert result.exit_code == 0

        # Should contain tree structure
        output = result.output
        assert "📋 All Item Properties" in output
        assert "📝 scene_01" in output
        assert "📝 item_0001" in output
        assert "📝 item_0002" in output
        assert "image_downloaded:" in output
        assert "thread_id:" in output

    def test_json_format_single_item_with_properties(self, manager):
        """Test JSON format with a single item having multiple properties."""
        manager.create_list("singletest", "Single Test")
        manager.add_item("singletest", "onlyitem", "Only Item")

        manager.set_item_property("singletest", "onlyitem", "prop1", "value1")
        manager.set_item_property("singletest", "onlyitem", "prop2", "value2")
        manager.set_item_property("singletest", "onlyitem", "prop3", "value3")

        runner = CliRunner()
        env = {"TODOIT_OUTPUT_FORMAT": "json"}

        result = runner.invoke(
            item_property_list,
            ["--list", "singletest"],
            obj={"db_path": manager.db.db_path},
            env=env,
        )

        assert result.exit_code == 0

        json_data = json.loads(result.output)
        assert "onlyitem" in json_data
        assert len(json_data) == 1

        onlyitem_props = json_data["onlyitem"]
        assert onlyitem_props["prop1"] == "value1"
        assert onlyitem_props["prop2"] == "value2"
        assert onlyitem_props["prop3"] == "value3"
        assert len(onlyitem_props) == 3

    def test_json_format_empty_list(self, manager):
        """Test JSON format with list having no items with properties."""
        manager.create_list("emptytest", "Empty Test")

        runner = CliRunner()
        env = {"TODOIT_OUTPUT_FORMAT": "json"}

        result = runner.invoke(
            item_property_list,
            ["--list", "emptytest"],
            obj={"db_path": manager.db.db_path},
            env=env,
        )

        assert result.exit_code == 0

        # Should output empty JSON object for empty properties
        json_data = json.loads(result.output)
        assert json_data == {}

    def test_json_format_items_without_properties(self, manager):
        """Test JSON format with items that have no properties."""
        manager.create_list("nopropstest", "No Props Test")
        manager.add_item("nopropstest", "item1", "Item 1")
        manager.add_item("nopropstest", "item2", "Item 2")

        runner = CliRunner()
        env = {"TODOIT_OUTPUT_FORMAT": "json"}

        result = runner.invoke(
            item_property_list,
            ["--list", "nopropstest"],
            obj={"db_path": manager.db.db_path},
            env=env,
        )

        assert result.exit_code == 0

        # Should output empty JSON object since no properties exist
        json_data = json.loads(result.output)
        assert json_data == {}

    def test_yaml_xml_formats_use_original_structure(self, manager, setup_test_data):
        """Test that YAML and XML formats still use original table structure."""
        runner = CliRunner()

        # Test YAML format
        result_yaml = runner.invoke(
            item_property_list,
            ["--list", "testlist"],
            obj={"db_path": manager.db.db_path},
            env={"TODOIT_OUTPUT_FORMAT": "yaml"},
        )

        assert result_yaml.exit_code == 0
        assert "Item Key:" in result_yaml.output
        assert "Property Key:" in result_yaml.output
        assert "Value:" in result_yaml.output

        # Test XML format
        result_xml = runner.invoke(
            item_property_list,
            ["--list", "testlist"],
            obj={"db_path": manager.db.db_path},
            env={"TODOIT_OUTPUT_FORMAT": "xml"},
        )

        assert result_xml.exit_code == 0
        assert "<todoit_output>" in result_xml.output
        assert "Item_Key" in result_xml.output  # XML converts spaces to underscores
        assert "Property_Key" in result_xml.output
