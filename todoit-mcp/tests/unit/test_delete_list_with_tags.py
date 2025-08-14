"""
Unit tests for list deletion with tags to reproduce FOREIGN KEY constraint bug
"""

import pytest
import tempfile
import os
from core.manager import TodoManager


class TestDeleteListWithTags:
    """Test list deletion scenarios involving tags"""

    @pytest.fixture
    def temp_manager(self):
        """Create manager with temporary database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        manager = TodoManager(db_path)
        yield manager
        os.unlink(db_path)

    def test_delete_list_with_single_tag(self, temp_manager):
        """Test deleting list with a single tag - should reproduce the bug"""
        # Create list
        todo_list = temp_manager.create_list("tagged_list", "Tagged List")

        # Create tag and assign to list
        tag = temp_manager.create_tag("dev", "blue")
        temp_manager.add_tag_to_list("tagged_list", "dev")

        # Verify tag is assigned
        tags = temp_manager.get_tags_for_list("tagged_list")
        assert len(tags) == 1
        assert tags[0].name == "dev"

        # This should work without errors once the bug is fixed
        # Currently FAILS due to missing ListTagAssignmentDB cleanup
        success = temp_manager.delete_list("tagged_list")
        assert success is True

        # Verify list is actually gone
        deleted_list = temp_manager.get_list("tagged_list")
        assert deleted_list is None

    def test_delete_list_with_multiple_tags(self, temp_manager):
        """Test deleting list with multiple tags"""
        # Create list
        todo_list = temp_manager.create_list("multi_tagged_list", "Multi Tagged List")

        # Create multiple tags and assign to list
        temp_manager.create_tag("work", "blue")
        temp_manager.create_tag("urgent", "red")
        temp_manager.create_tag("client", "green")

        temp_manager.add_tag_to_list("multi_tagged_list", "work")
        temp_manager.add_tag_to_list("multi_tagged_list", "urgent")
        temp_manager.add_tag_to_list("multi_tagged_list", "client")

        # Verify tags are assigned
        tags = temp_manager.get_tags_for_list("multi_tagged_list")
        assert len(tags) == 3
        tag_names = [tag.name for tag in tags]
        assert "work" in tag_names
        assert "urgent" in tag_names
        assert "client" in tag_names

        # This should work without errors now that the bug is fixed
        success = temp_manager.delete_list("multi_tagged_list")
        assert success is True

        # Verify list is actually gone
        deleted_list = temp_manager.get_list("multi_tagged_list")
        assert deleted_list is None

    def test_delete_list_with_tags_and_complex_data(self, temp_manager):
        """Test deleting list with tags + items + properties (comprehensive scenario)"""
        # Create list
        todo_list = temp_manager.create_list(
            "complex_tagged_list", "Complex Tagged List"
        )

        # Add tags
        temp_manager.create_tag("project", "blue")
        temp_manager.add_tag_to_list("complex_tagged_list", "project")

        # Add items with properties (these work fine in existing tests)
        temp_manager.add_item("complex_tagged_list", "task1", "Task 1")
        temp_manager.set_item_property(
            "complex_tagged_list", "task1", "priority", "high"
        )

        # Add list properties
        temp_manager.set_list_property("complex_tagged_list", "team", "backend")

        # Verify everything exists
        tags = temp_manager.get_tags_for_list("complex_tagged_list")
        assert len(tags) == 1

        items = temp_manager.get_list_items("complex_tagged_list")
        assert len(items) == 1

        # This should work without errors now that the bug is fixed
        success = temp_manager.delete_list("complex_tagged_list")
        assert success is True

        # Verify list is actually gone
        deleted_list = temp_manager.get_list("complex_tagged_list")
        assert deleted_list is None

    def test_delete_list_without_tags_works_fine(self, temp_manager):
        """Control test - list without tags should delete fine"""
        # Create list without tags
        todo_list = temp_manager.create_list("no_tags_list", "No Tags List")

        # Add items and properties (known to work from existing tests)
        temp_manager.add_item("no_tags_list", "task1", "Task 1")
        temp_manager.set_item_property("no_tags_list", "task1", "priority", "high")
        temp_manager.set_list_property("no_tags_list", "team", "backend")

        # This should work fine (existing functionality)
        success = temp_manager.delete_list("no_tags_list")
        assert success is True

        # Verify list is gone
        deleted_list = temp_manager.get_list("no_tags_list")
        assert deleted_list is None

    def test_reproduce_cli_error_scenario(self, temp_manager):
        """Reproduce the exact CLI error scenario from user report"""
        # Create list that would be auto-tagged in CLI environment
        todo_list = temp_manager.create_list("test_project", "Test Project")

        # Simulate CLI auto-tagging with dev tag (like FORCE_TAGS=dev)
        temp_manager.create_tag("dev", "blue")
        temp_manager.add_tag_to_list("test_project", "dev")

        # Verify the setup matches CLI scenario
        assert todo_list.title == "Test Project"
        tags = temp_manager.get_tags_for_list("test_project")
        assert len(tags) == 1
        assert tags[0].name == "dev"

        # This should now work without errors (reproduces the CLI scenario but fixed)
        success = temp_manager.delete_list("test_project")
        assert success is True

        # Verify list is actually gone
        deleted_list = temp_manager.get_list("test_project")
        assert deleted_list is None
