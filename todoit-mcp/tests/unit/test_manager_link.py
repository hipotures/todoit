"""
Unit tests for list linking functionality in TodoManager
Tests the link_list_1to1 method with various scenarios
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from core.manager import TodoManager
from core.models import TodoList, TodoItem, ProgressStats


class TestTodoManagerLink:
    """Test TodoManager.link_list_1to1 functionality"""
    
    @pytest.fixture
    def manager(self):
        """Create TodoManager instance with mocked database"""
        with patch('core.manager.Database'):
            manager = TodoManager(':memory:')
            return manager
    
    @pytest.fixture
    def sample_source_list(self):
        """Sample source list for testing"""
        return TodoList(
            id=1,
            list_key="source_list",
            title="Source List", 
            list_type="sequential",
            metadata={"project": "test"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_items(self):
        """Sample items for testing"""
        now = datetime.now()
        return [
            TodoItem(id=1, list_id=1, item_key="item1", content="Task 1", position=1, status="completed", created_at=now, updated_at=now),
            TodoItem(id=2, list_id=1, item_key="item2", content="Task 2", position=2, status="in_progress", created_at=now, updated_at=now),
            TodoItem(id=3, list_id=1, item_key="item3", content="Task 3", position=3, status="pending", created_at=now, updated_at=now)
        ]

    def test_link_list_basic(self, manager, sample_source_list):
        """Test basic list linking functionality"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Source List - Linked", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=[])
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Assertions
        assert result["success"] is True
        assert result["source_list"] == "source_list"
        assert result["target_list"] == "target_list"
        assert result["target_list_created"] is True
        assert result["relation_created"] is True
        assert result["relation_key"] == "source_list_linked"
        
        # Verify mocks called
        manager.get_list.assert_any_call("source_list")
        manager.get_list.assert_any_call("target_list")
        manager.create_list.assert_called_once()
        manager.create_list_relation.assert_called_once()

    def test_link_list_with_properties(self, manager, sample_source_list):
        """Test linking list with list properties"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={"prop1": "value1", "prop2": "value2"})
        manager.set_list_property = Mock()
        manager.get_list_items = Mock(return_value=[])
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Assertions
        assert result["list_properties_copied"] == 2
        assert manager.set_list_property.call_count == 2

    def test_link_list_with_item_properties(self, manager, sample_source_list, sample_items):
        """Test linking list with item properties"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=sample_items)
        manager.add_item = Mock(side_effect=[
            TodoItem(id=4, list_id=2, item_key="item1", content="Task 1", position=1, created_at=datetime.now(), updated_at=datetime.now()),
            TodoItem(id=5, list_id=2, item_key="item2", content="Task 2", position=2, created_at=datetime.now(), updated_at=datetime.now()),
            TodoItem(id=6, list_id=2, item_key="item3", content="Task 3", position=3, created_at=datetime.now(), updated_at=datetime.now())
        ])
        manager.get_item_properties = Mock(return_value={"thread_id": "test-123"})
        manager.set_item_property = Mock()
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Assertions
        assert result["items_copied"] == 3
        assert result["item_properties_copied"] == 3  # 3 items × 1 property each
        assert manager.add_item.call_count == 3
        assert manager.set_item_property.call_count == 3

    def test_link_list_status_reset(self, manager, sample_source_list, sample_items):
        """Test that all items are reset to pending status"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=sample_items)
        manager.add_item = Mock(side_effect=[Mock(item_key="item1"), Mock(item_key="item2"), Mock(item_key="item3")])
        manager.get_item_properties = Mock(return_value={})
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Verify all add_item calls don't specify status (defaults to pending)
        for call in manager.add_item.call_args_list:
            args, kwargs = call
            # Status should not be in kwargs (defaults to pending in add_item)
            assert 'status' not in kwargs
        
        assert result["all_items_set_to_pending"] is True

    def test_link_list_relation_created(self, manager, sample_source_list):
        """Test that project relation is created correctly"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        target_list = TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now())
        manager.create_list = Mock(return_value=target_list)
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=[])
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Verify relation creation
        manager.create_list_relation.assert_called_once_with(
            source_list_id=1,  # source_list.id
            target_list_id=2,  # target_list.id
            relation_type="project",
            relation_key="source_list_linked",
            metadata={
                "linked_from": "source_list",
                "relationship": "1:1", 
                "created_by": "link_command"
            }
        )

    def test_link_list_source_not_exists(self, manager):
        """Test error when source list doesn't exist"""
        manager.get_list = Mock(return_value=None)
        
        with pytest.raises(ValueError, match="Source list 'nonexistent' does not exist"):
            manager.link_list_1to1("nonexistent", "target_list")

    def test_link_list_target_exists(self, manager, sample_source_list):
        """Test error when target list already exists"""
        existing_target = TodoList(id=2, list_key="target_list", title="Existing", created_at=datetime.now(), updated_at=datetime.now())
        manager.get_list = Mock(side_effect=lambda key: {
            "source_list": sample_source_list,
            "target_list": existing_target
        }.get(key))
        
        with pytest.raises(ValueError, match="Target list 'target_list' already exists"):
            manager.link_list_1to1("source_list", "target_list")

    def test_link_list_empty_source(self, manager, sample_source_list):
        """Test linking empty source list"""
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=[])  # Empty list
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Assertions
        assert result["success"] is True
        assert result["items_copied"] == 0
        assert result["list_properties_copied"] == 0
        assert result["item_properties_copied"] == 0

    def test_link_list_with_subtasks(self, manager, sample_source_list):
        """Test linking list with subtasks (hierarchical items)"""
        # Create items with parent-child relationships
        now = datetime.now()
        parent_item = TodoItem(id=1, list_id=1, item_key="parent", content="Parent Task", position=1, created_at=now, updated_at=now)
        child_item = TodoItem(id=2, list_id=1, item_key="child", content="Child Task", position=2, parent_item_id=1, created_at=now, updated_at=now)
        
        # Mock methods
        manager.get_list = Mock(side_effect=lambda key: sample_source_list if key == "source_list" else None)
        manager.create_list = Mock(return_value=TodoList(id=2, list_key="target_list", title="Target", created_at=datetime.now(), updated_at=datetime.now()))
        manager.get_list_properties = Mock(return_value={})
        manager.get_list_items = Mock(return_value=[parent_item, child_item])
        manager.add_item = Mock(side_effect=[
            TodoItem(id=3, list_id=2, item_key="parent", content="Parent Task", position=1, created_at=datetime.now(), updated_at=datetime.now()),
            TodoItem(id=4, list_id=2, item_key="child", content="Child Task", position=2, created_at=datetime.now(), updated_at=datetime.now())
        ])
        manager.get_item_properties = Mock(return_value={})
        manager.create_list_relation = Mock()
        
        # Execute
        result = manager.link_list_1to1("source_list", "target_list")
        
        # Assertions
        assert result["items_copied"] == 2
        assert manager.add_item.call_count == 2