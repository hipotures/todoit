"""
Integration tests for list linking functionality
Tests end-to-end linking with real database and TodoManager
"""

import pytest
import tempfile
import os
from core.manager import TodoManager
from core.models import ItemStatus


class TestListLinkIntegration:
    """Test list linking with real database operations"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def manager(self, temp_db_path):
        """Create TodoManager with temporary database"""
        return TodoManager(temp_db_path)

    def test_cli_list_link_basic(self, manager):
        """Test basic list linking with real database"""
        # Create source list with items
        source_list = manager.create_list("source_test", "Source Test List")
        manager.add_item("source_test", "task1", "Complete setup")
        manager.add_item("source_test", "task2", "Write tests")
        manager.add_item("source_test", "task3", "Deploy app")

        # Mark some items as completed for status reset test
        manager.update_item_status("source_test", "task1", "completed")
        manager.update_item_status("source_test", "task2", "in_progress")

        # Link the list
        result = manager.link_list_1to1("source_test", "target_test")

        # Verify result
        assert result["success"] is True
        assert result["source_list"] == "source_test"
        assert result["target_list"] == "target_test"
        assert result["items_copied"] == 3
        assert result["relation_created"] is True

        # Verify target list exists
        target_list = manager.get_list("target_test")
        assert target_list is not None
        assert target_list.title == "Source Test List - Linked"

        # Verify items were copied with pending status
        target_items = manager.get_list_items("target_test")
        assert len(target_items) == 3
        for item in target_items:
            assert item.status == ItemStatus.PENDING  # All should be reset to pending

        # Verify relation was created
        related_lists = manager.get_lists_by_relation("project", "source_test_linked")
        assert len(related_lists) == 2  # source and target

    def test_cli_list_link_with_title(self, manager):
        """Test list linking with custom title"""
        # Create source list
        manager.create_list("api_dev", "API Development Tasks")
        manager.add_item("api_dev", "endpoint1", "Create user endpoint")

        # Link with custom title
        result = manager.link_list_1to1("api_dev", "api_test", "API Testing Tasks")

        assert result["success"] is True

        # Verify custom title
        target_list = manager.get_list("api_test")
        assert target_list.title == "API Testing Tasks"

    def test_mcp_list_link_basic(self, manager):
        """Test MCP tool functionality with real operations"""
        # Setup source list
        manager.create_list("mcp_source", "MCP Source List")
        manager.add_item("mcp_source", "item1", "First task")
        manager.add_item("mcp_source", "item2", "Second task")

        # Test linking
        result = manager.link_list_1to1("mcp_source", "mcp_target")

        assert result["success"] is True
        assert result["items_copied"] == 2
        assert result["target_list"] == "mcp_target"

        # Verify via get operations
        target_list = manager.get_list("mcp_target")
        assert target_list is not None

        target_items = manager.get_list_items("mcp_target")
        assert len(target_items) == 2

    def test_list_link_preserves_metadata(self, manager):
        """Test that list and item metadata is preserved"""
        # Create source with metadata
        source_list = manager.create_list(
            "meta_source",
            "Metadata Test List",
            metadata={"project_id": "proj-123", "environment": "test"},
        )

        # Add item with metadata
        item = manager.add_item(
            "meta_source",
            "meta_item",
            "Item with metadata",
            metadata={"priority": "high", "category": "feature"},
        )

        # Link the list
        result = manager.link_list_1to1("meta_source", "meta_target")

        assert result["success"] is True

        # Verify list metadata preserved
        target_list = manager.get_list("meta_target")
        assert target_list.metadata["project_id"] == "proj-123"
        assert target_list.metadata["environment"] == "test"

        # Verify item metadata preserved
        target_items = manager.get_list_items("meta_target")
        target_item = target_items[0]
        assert target_item.metadata["priority"] == "high"
        assert target_item.metadata["category"] == "feature"

    def test_list_link_complex_properties(self, manager):
        """Test linking with complex list and item properties"""
        # Create source list
        manager.create_list("prop_source", "Properties Test")
        manager.add_item("prop_source", "prop_item", "Test item")

        # Add list properties
        manager.set_list_property("prop_source", "book_folder", "test_folder")
        manager.set_list_property("prop_source", "project_id", "proj-456")
        manager.set_list_property("prop_source", "owner", "test_user")

        # Add item properties
        manager.set_item_property("prop_source", "prop_item", "thread_id", "thread-789")
        manager.set_item_property("prop_source", "prop_item", "difficulty", "medium")

        # Link the list
        result = manager.link_list_1to1("prop_source", "prop_target")

        assert result["success"] is True
        assert result["list_properties_copied"] == 3
        assert result["item_properties_copied"] == 2

        # Verify list properties copied
        target_list_props = manager.get_list_properties("prop_target")
        assert target_list_props["book_folder"] == "test_folder"
        assert target_list_props["project_id"] == "proj-456"
        assert target_list_props["owner"] == "test_user"

        # Verify item properties copied
        target_item_props = manager.get_item_properties("prop_target", "prop_item")
        assert target_item_props["thread_id"] == "thread-789"
        assert target_item_props["difficulty"] == "medium"

    def test_list_link_performance(self, manager):
        """Test performance with larger lists (50 items)"""
        # Create source list with many items
        manager.create_list("perf_source", "Performance Test")

        # Add 50 items
        for i in range(50):
            item_key = f"item_{i:03d}"
            content = f"Performance test item {i+1}"
            manager.add_item("perf_source", item_key, content)

            # Add properties to some items
            if i % 10 == 0:  # Every 10th item gets properties
                manager.set_item_property(
                    "perf_source", item_key, "batch", f"batch_{i//10}"
                )

        # Add list properties
        for i in range(5):
            manager.set_list_property("perf_source", f"config_{i}", f"value_{i}")

        # Time the linking operation (should complete quickly)
        import time

        start_time = time.time()

        result = manager.link_list_1to1("perf_source", "perf_target")

        end_time = time.time()
        operation_time = end_time - start_time

        # Verify results
        assert result["success"] is True
        assert result["items_copied"] == 50
        assert result["list_properties_copied"] == 5
        assert result["item_properties_copied"] == 5  # 5 items with 1 property each

        # Performance assertion - should complete within reasonable time
        assert operation_time < 5.0  # Should take less than 5 seconds

        # Verify all items copied correctly
        target_items = manager.get_list_items("perf_target")
        assert len(target_items) == 50

        # Verify all items are pending
        for item in target_items:
            assert item.status == ItemStatus.PENDING
