"""
Unit tests for list synchronization functionality
Tests the add_item synchronization with 1:1 linked lists
"""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime
from core.manager import TodoManager
from core.models import TodoList, TodoItem


class TestSyncAddFunctionality:
    """Test add_item synchronization with 1:1 linked lists"""

    @pytest.fixture
    def manager(self):
        """Create TodoManager instance with mocked database"""
        with patch("core.manager.Database"):
            manager = TodoManager(":memory:")
            return manager

    @pytest.fixture
    def sample_parent_list(self):
        """Sample parent list for testing"""
        return TodoList(
            id=1,
            list_key="parent_list",
            title="Parent List",
            list_type="sequential",
            metadata={"project": "test"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def sample_child_list(self):
        """Sample child list for testing"""
        return TodoList(
            id=2,
            list_key="child_list",
            title="Child List",
            list_type="sequential",
            metadata={"project": "test"},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def mock_relation(self):
        """Mock 1:1 relation"""
        relation = Mock()
        relation.source_list_id = 1
        relation.target_list_id = 2
        relation.relation_type = "project"
        relation.meta_data = {"relationship": "1:1", "created_by": "link_command"}
        return relation

    def test_sync_add_with_1to1_child(
        self, manager, sample_parent_list, sample_child_list, mock_relation
    ):
        """Test that adding item to parent syncs to 1:1 child"""
        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(
            side_effect=[None, None]
        )  # Item doesn't exist
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(return_value=Mock(id=1))
        manager.db.get_list_relations = Mock(return_value=[mock_relation])
        manager.db.get_list_by_id = Mock(return_value=Mock(id=2, list_key="child_list"))
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute add_item
        manager.add_item("parent_list", "new_task", "New task content")

        # Verify main item was created
        manager.db.create_item.assert_any_call(
            {
                "list_id": 1,
                "item_key": "new_task",
                "content": "New task content",
                "position": 1,
                "meta_data": {},
            }
        )

        # Verify sync to child was attempted
        manager.db.get_list_relations.assert_called_once_with(1, as_source=True)
        assert manager.db.create_item.call_count == 2  # Parent + Child

    def test_sync_add_no_children(self, manager, sample_parent_list):
        """Test that adding item with no 1:1 children works normally"""
        # Mock database methods - no relations
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(return_value=None)
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(return_value=Mock(id=1))
        manager.db.get_list_relations = Mock(return_value=[])  # No relations
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute
        manager.add_item("parent_list", "solo_task", "Solo task")

        # Verify only main item created
        assert manager.db.create_item.call_count == 1
        manager.db.get_list_relations.assert_called_once_with(1, as_source=True)

    def test_sync_add_non_1to1_relation(self, manager, mock_relation):
        """Test that non-1:1 relations don't trigger sync"""
        # Change relation to non-1:1
        mock_relation.meta_data = {"relationship": "related"}

        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(return_value=None)
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(return_value=Mock(id=1))
        manager.db.get_list_relations = Mock(return_value=[mock_relation])
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute
        manager.add_item("parent_list", "no_sync_task", "Should not sync")

        # Verify only main item created (no sync)
        assert manager.db.create_item.call_count == 1

    def test_sync_add_item_exists_in_child(self, manager, mock_relation):
        """Test that sync skips if item already exists in child"""
        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(
            side_effect=[None, Mock(id=99)]
        )  # Exists in child
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(return_value=Mock(id=1))
        manager.db.get_list_relations = Mock(return_value=[mock_relation])
        manager.db.get_list_by_id = Mock(return_value=Mock(id=2))
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute
        manager.add_item("parent_list", "existing_task", "Already exists in child")

        # Verify only main item created (child skipped)
        assert manager.db.create_item.call_count == 1

    def test_sync_add_multiple_children(self, manager):
        """Test sync to multiple 1:1 children"""
        # Create multiple relations
        relation1 = Mock()
        relation1.source_list_id = 1
        relation1.target_list_id = 2
        relation1.relation_type = "project"
        relation1.meta_data = {"relationship": "1:1"}

        relation2 = Mock()
        relation2.source_list_id = 1
        relation2.target_list_id = 3
        relation2.relation_type = "project"
        relation2.meta_data = {"relationship": "1:1"}

        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(side_effect=[None, None, None])  # None exist
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(return_value=Mock(id=1))
        manager.db.get_list_relations = Mock(return_value=[relation1, relation2])
        manager.db.get_list_by_id = Mock(side_effect=[Mock(id=2), Mock(id=3)])
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute
        manager.add_item("parent_list", "multi_task", "Sync to multiple children")

        # Verify synced to both children
        assert manager.db.create_item.call_count == 3  # Parent + 2 children
        assert manager.db.get_list_by_id.call_count == 2

    def test_sync_add_with_properties_and_metadata(self, manager, mock_relation):
        """Test sync with metadata and properties"""
        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(side_effect=[None, None])
        manager.db.get_next_position = Mock(return_value=1)
        parent_item = Mock(id=1)
        child_item = Mock(id=2)
        manager.db.create_item = Mock(side_effect=[parent_item, child_item])
        manager.db.get_list_relations = Mock(return_value=[mock_relation])
        manager.db.get_list_by_id = Mock(return_value=Mock(id=2))

        # Mock property operations
        prop_mock = Mock()
        prop_mock.property_key = "priority"
        prop_mock.property_value = "high"
        manager.db.get_item_properties = Mock(return_value=[prop_mock])
        manager.db.create_item_property = Mock()

        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute with metadata
        manager.add_item(
            "parent_list",
            "priority_task",
            "High priority task",
            metadata={"priority": "high"},
        )

        # Verify child item created with pending status
        child_call = manager.db.create_item.call_args_list[1]
        child_data = child_call[0][0]
        assert child_data["status"] == "pending"
        assert child_data["item_key"] == "priority_task"
        assert child_data["content"] == "High priority task"

    def test_sync_add_error_handling(self, manager, mock_relation):
        """Test that sync errors don't break main add_item operation"""
        # Mock database methods
        manager.db.get_list_by_key = Mock(return_value=Mock(id=1))
        manager.db.get_item_by_key = Mock(return_value=None)
        manager.db.get_next_position = Mock(return_value=1)
        manager.db.create_item = Mock(
            side_effect=[Mock(id=1), Exception("Child DB error")]
        )
        manager.db.get_list_relations = Mock(return_value=[mock_relation])
        manager.db.get_list_by_id = Mock(return_value=Mock(id=2))
        manager._record_history = Mock()
        manager._db_to_model = Mock(return_value=Mock())

        # Execute - should not raise exception
        result = manager.add_item("parent_list", "error_task", "Task with sync error")

        # Verify main operation succeeded despite sync error
        assert result is not None
        assert manager.db.create_item.call_count == 2  # Parent + failed child

    def test_get_1to1_child_lists_helper(self, manager):
        """Test the helper method for finding 1:1 child lists"""
        # Create mix of relations
        relation_1to1 = Mock()
        relation_1to1.relation_type = "project"
        relation_1to1.meta_data = {"relationship": "1:1"}

        relation_normal = Mock()
        relation_normal.relation_type = "project"
        relation_normal.meta_data = {"relationship": "related"}

        manager.db.get_list_relations = Mock(
            return_value=[relation_1to1, relation_normal]
        )

        # Execute
        children = manager._get_1to1_child_lists(1)

        # Verify only 1:1 relation returned
        assert len(children) == 1
        assert children[0].meta_data["relationship"] == "1:1"
