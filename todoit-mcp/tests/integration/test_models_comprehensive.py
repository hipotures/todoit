"""
Test Models - Comprehensive Coverage
Tests for core/models.py to improve coverage
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from core.models import (
    TodoList,
    TodoListCreate,
    TodoListUpdate,
    TodoItem,
    TodoItemCreate,
    TodoItemUpdate,
    ItemDependency,
    ItemDependencyCreate,
    ListProperty,
    ListPropertyCreate,
    TodoHistory,
    TodoHistoryCreate,
    ProgressStats,
    CompletionStates,
    BulkOperationResult,
    DependencyGraph,
    BlockedItemsResult,
    ListType,
    ItemStatus,
    HistoryAction,
    DependencyType,
)


class TestModelsComprehensive:
    """Comprehensive tests for Pydantic models"""

    def test_list_type_enum(self):
        """Test ListType enum"""
        assert ListType.SEQUENTIAL == "sequential"

    def test_item_status_enum(self):
        """Test ItemStatus enum"""
        assert ItemStatus.PENDING == "pending"
        assert ItemStatus.IN_PROGRESS == "in_progress"
        assert ItemStatus.COMPLETED == "completed"
        assert ItemStatus.FAILED == "failed"

    def test_relation_type_enum(self):
        """Test RelationType enum"""
        assert RelationType.DEPENDENCY == "dependency"
        assert RelationType.PARENT == "parent"
        assert RelationType.RELATED == "related"
        assert RelationType.PROJECT == "project"

    def test_history_action_enum(self):
        """Test HistoryAction enum"""
        assert HistoryAction.CREATED == "created"
        assert HistoryAction.UPDATED == "updated"
        assert HistoryAction.COMPLETED == "completed"
        assert HistoryAction.FAILED == "failed"
        assert HistoryAction.DELETED == "deleted"

    def test_dependency_type_enum(self):
        """Test DependencyType enum"""
        assert DependencyType.BLOCKS == "blocks"
        assert DependencyType.REQUIRES == "requires"
        assert DependencyType.RELATED == "related"

    def test_completion_states_model(self):
        """Test CompletionStates model"""
        # Create empty completion states
        states = CompletionStates()
        assert states.states == {}
        assert not states.is_fully_completed()
        assert not states.is_partially_completed()
        assert states.completion_percentage() == 0.0

        # Add states
        states.add_state("designed", True)
        states.add_state("implemented", False)
        states.add_state("tested", False)

        assert states.states["designed"] is True
        assert states.states["implemented"] is False
        assert not states.is_fully_completed()
        assert states.is_partially_completed()
        assert states.completion_percentage() == 33.33333333333333

        # Complete all states
        states.add_state("implemented", True)
        states.add_state("tested", True)

        assert states.is_fully_completed()
        assert states.is_partially_completed()
        assert states.completion_percentage() == 100.0

    def test_todo_list_base_validation(self):
        """Test TodoListBase validation"""
        # Valid list key
        valid_data = {"list_key": "valid_key-123", "title": "Valid Title"}
        list_base = TodoListCreate(**valid_data)
        assert list_base.list_key == "valid_key-123"

        # Invalid list key with special characters
        with pytest.raises(ValidationError) as exc_info:
            TodoListCreate(list_key="invalid@key!", title="Title")
        assert "alphanumeric" in str(exc_info.value)

        # Empty list key
        with pytest.raises(ValidationError) as exc_info:
            TodoListCreate(list_key="", title="Title")
        assert "at least" in str(exc_info.value)

        # Too long list key
        with pytest.raises(ValidationError) as exc_info:
            TodoListCreate(list_key="a" * 101, title="Title")
        assert "at most" in str(exc_info.value)

    def test_todo_list_model(self):
        """Test complete TodoList model"""
        now = datetime.now(timezone.utc)

        list_data = {
            "id": 1,
            "list_key": "test_list",
            "title": "Test List",
            "description": "Test Description",
            "list_type": ListType.SEQUENTIAL,
            "metadata": {"project": "test"},
            "created_at": now,
            "updated_at": now,
        }

        todo_list = TodoList(**list_data)
        assert todo_list.id == 1
        assert todo_list.list_key == "test_list"
        assert todo_list.list_type == ListType.SEQUENTIAL

        # Test to_dict method
        dict_repr = todo_list.to_dict()
        assert dict_repr["id"] == 1
        assert dict_repr["list_key"] == "test_list"
        assert dict_repr["metadata"] == {"project": "test"}
        assert "created_at" in dict_repr
        assert "updated_at" in dict_repr

    def test_todo_list_update_model(self):
        """Test TodoListUpdate model"""
        # All fields optional
        update_data = {}
        update = TodoListUpdate(**update_data)
        assert update.title is None

        # Partial update
        update_data = {"title": "New Title", "metadata": {"updated": True}}
        update = TodoListUpdate(**update_data)
        assert update.title == "New Title"
        assert update.description is None
        assert update.metadata == {"updated": True}

    def test_todo_item_base_validation(self):
        """Test TodoItemBase validation"""
        # Valid item
        valid_data = {
            "item_key": "valid_item-123",
            "content": "Valid content",
            "position": 1,
        }
        item_base = TodoItemCreate(list_id=1, **valid_data)
        assert item_base.item_key == "valid_item-123"
        assert item_base.position == 1

        # Invalid item key
        with pytest.raises(ValidationError) as exc_info:
            TodoItemCreate(
                list_id=1, item_key="invalid@key!", content="Content", position=1
            )
        assert "alphanumeric" in str(exc_info.value)

        # Negative position
        with pytest.raises(ValidationError) as exc_info:
            TodoItemCreate(list_id=1, item_key="item", content="Content", position=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

        # Too long content
        with pytest.raises(ValidationError) as exc_info:
            TodoItemCreate(list_id=1, item_key="item", content="a" * 1001, position=1)
        assert "at most" in str(exc_info.value)

    def test_todo_item_model(self):
        """Test complete TodoItem model"""
        now = datetime.now(timezone.utc)

        item_data = {
            "id": 1,
            "list_id": 1,
            "item_key": "test_item",
            "content": "Test content",
            "position": 1,
            "status": ItemStatus.PENDING,
            "completion_states": {"designed": True, "implemented": False},
            "parent_item_id": None,
            "metadata": {"priority": "high"},
            "started_at": None,
            "completed_at": None,
            "created_at": now,
            "updated_at": now,
        }

        todo_item = TodoItem(**item_data)
        assert todo_item.id == 1
        assert todo_item.status == ItemStatus.PENDING
        assert todo_item.completion_states["designed"] is True

        # Test to_dict method
        dict_repr = todo_item.to_dict()
        assert dict_repr["id"] == 1
        assert dict_repr["item_key"] == "test_item"
        assert dict_repr["completion_states"] == {
            "designed": True,
            "implemented": False,
        }

        # Test get_completion_metadata
        completion_meta = todo_item.get_completion_metadata()
        assert completion_meta == {"designed": True, "implemented": False}

    def test_todo_item_update_model(self):
        """Test TodoItemUpdate model"""
        # All fields optional
        update = TodoItemUpdate()
        assert update.content is None
        assert update.status is None

        # Partial update
        update_data = {
            "content": "Updated content",
            "status": ItemStatus.IN_PROGRESS,
            "metadata": {"updated": True},
        }
        update = TodoItemUpdate(**update_data)
        assert update.content == "Updated content"
        assert update.status == ItemStatus.IN_PROGRESS


    def test_item_dependency_validation(self):
        """Test ItemDependency validation"""
        # Valid dependency
        dep_data = {
            "dependent_item_id": 2,
            "required_item_id": 1,
            "dependency_type": DependencyType.BLOCKS,
        }
        dependency = ItemDependencyCreate(**dep_data)
        assert dependency.dependent_item_id == 2
        assert dependency.required_item_id == 1

        # Invalid item IDs (zero or negative)
        with pytest.raises(ValidationError) as exc_info:
            ItemDependencyCreate(
                dependent_item_id=0,
                required_item_id=1,
                dependency_type=DependencyType.BLOCKS,
            )
        assert "greater than 0" in str(exc_info.value)

        # Self-dependency
        with pytest.raises(ValidationError) as exc_info:
            ItemDependencyCreate(
                dependent_item_id=1,
                required_item_id=1,
                dependency_type=DependencyType.BLOCKS,
            )
        assert "itself" in str(exc_info.value).lower()

        # Large metadata should be rejected
        large_metadata = {"data": "x" * 2000}
        with pytest.raises(ValidationError) as exc_info:
            ItemDependencyCreate(
                dependent_item_id=2,
                required_item_id=1,
                dependency_type=DependencyType.BLOCKS,
                metadata=large_metadata,
            )
        assert "too large" in str(exc_info.value)

    def test_item_dependency_model(self):
        """Test complete ItemDependency model"""
        now = datetime.now(timezone.utc)

        dep_data = {
            "id": 1,
            "dependent_item_id": 2,
            "required_item_id": 1,
            "dependency_type": DependencyType.BLOCKS,
            "metadata": {"reason": "UI needs API"},
            "created_at": now,
        }

        dependency = ItemDependency(**dep_data)
        assert dependency.id == 1
        assert dependency.dependency_type == DependencyType.BLOCKS

        # Test to_dict method
        dict_repr = dependency.to_dict()
        assert dict_repr["id"] == 1
        assert dict_repr["dependent_item_id"] == 2
        assert dict_repr["metadata"] == {"reason": "UI needs API"}

    def test_list_property_validation(self):
        """Test ListProperty validation"""
        # Valid property
        prop_data = {"list_id": 1, "property_key": "status", "property_value": "active"}
        prop = ListPropertyCreate(**prop_data)
        assert prop.property_key == "status"

        # Invalid property key with special characters
        with pytest.raises(ValidationError) as exc_info:
            ListPropertyCreate(
                list_id=1, property_key="invalid@key", property_value="value"
            )
        assert "alphanumeric" in str(exc_info.value)

        # Reserved property key
        with pytest.raises(ValidationError) as exc_info:
            ListPropertyCreate(list_id=1, property_key="id", property_value="value")
        assert "reserved" in str(exc_info.value)

        # Too long property value
        with pytest.raises(ValidationError) as exc_info:
            ListPropertyCreate(list_id=1, property_key="key", property_value="x" * 2001)
        assert "2000 characters" in str(exc_info.value)

        # Dangerous content in property value
        with pytest.raises(ValidationError) as exc_info:
            ListPropertyCreate(
                list_id=1,
                property_key="key",
                property_value="<script>alert('xss')</script>",
            )
        assert "dangerous" in str(exc_info.value)

    def test_list_property_model(self):
        """Test complete ListProperty model"""
        now = datetime.now(timezone.utc)

        prop_data = {
            "id": 1,
            "list_id": 1,
            "property_key": "status",
            "property_value": "active",
            "created_at": now,
            "updated_at": now,
        }

        prop = ListProperty(**prop_data)
        assert prop.id == 1
        assert prop.property_key == "status"

        # Test to_dict method
        dict_repr = prop.to_dict()
        assert dict_repr["id"] == 1
        assert dict_repr["property_key"] == "status"
        assert dict_repr["property_value"] == "active"

    def test_todo_history_model(self):
        """Test TodoHistory model"""
        now = datetime.now(timezone.utc)

        # Create history entry
        history_data = {
            "item_id": 1,
            "list_id": 1,
            "action": HistoryAction.UPDATED,
            "old_value": {"status": "pending"},
            "new_value": {"status": "completed"},
            "user_context": "test_user",
        }
        history_create = TodoHistoryCreate(**history_data)
        assert history_create.action == HistoryAction.UPDATED

        # Complete history model
        complete_history_data = {"id": 1, "timestamp": now, **history_data}
        history = TodoHistory(**complete_history_data)
        assert history.id == 1
        assert history.action == HistoryAction.UPDATED

        # Test to_dict method
        dict_repr = history.to_dict()
        assert dict_repr["id"] == 1
        assert dict_repr["action"] == "updated"
        assert dict_repr["old_value"] == {"status": "pending"}

    def test_progress_stats_model(self):
        """Test ProgressStats model"""
        # Basic progress stats
        stats = ProgressStats(
            total=10,
            completed=3,
            in_progress=2,
            pending=4,
            failed=1,
            completion_percentage=30.0,
        )

        assert stats.total == 10
        assert stats.completed == 3
        assert stats.completion_percentage == 30.0

        # Enhanced progress stats (Phase 3)
        enhanced_stats = ProgressStats(
            total=20,
            completed=5,
            in_progress=3,
            pending=10,
            failed=2,
            completion_percentage=25.0,
            blocked=2,
            available=8,
            root_items=15,
            subtasks=5,
            hierarchy_depth=3,
            dependency_count=4,
        )

        assert enhanced_stats.blocked == 2
        assert enhanced_stats.available == 8
        assert enhanced_stats.hierarchy_depth == 3

        # Test to_dict method
        dict_repr = enhanced_stats.to_dict()
        assert dict_repr["total"] == 20
        assert dict_repr["blocked"] == 2
        assert dict_repr["hierarchy_depth"] == 3

    def test_bulk_operation_result_model(self):
        """Test BulkOperationResult model"""
        # Successful bulk operation
        success_result = BulkOperationResult(
            success=True, affected_count=5, errors=[], items=[{"id": 1}, {"id": 2}]
        )

        assert success_result.success is True
        assert success_result.affected_count == 5
        assert len(success_result.errors) == 0

        # Failed bulk operation
        error_result = BulkOperationResult(
            success=False,
            affected_count=0,
            errors=["Item not found", "Invalid status"],
            items=None,
        )

        assert error_result.success is False
        assert len(error_result.errors) == 2

        # Test to_dict method
        dict_repr = success_result.to_dict()
        assert dict_repr["success"] is True
        assert dict_repr["affected_count"] == 5

    def test_dependency_graph_model(self):
        """Test DependencyGraph model"""
        graph = DependencyGraph(
            lists=[{"id": 1, "key": "backend"}, {"id": 2, "key": "frontend"}],
            items=[{"id": 1, "content": "API"}, {"id": 2, "content": "UI"}],
            dependencies=[{"from": 1, "to": 2, "type": "blocks"}],
        )

        assert len(graph.lists) == 2
        assert len(graph.items) == 2
        assert len(graph.dependencies) == 1

        # Test to_dict method
        dict_repr = graph.to_dict()
        assert "lists" in dict_repr
        assert "items" in dict_repr
        assert "dependencies" in dict_repr

    def test_blocked_items_result_model(self):
        """Test BlockedItemsResult model"""
        blocked_result = BlockedItemsResult(
            item_id=1,
            item_key="ui_task",
            content="Create UI component",
            list_key="frontend",
            blockers=[{"item_id": 2, "reason": "API not ready"}],
            is_blocked=True,
        )

        assert blocked_result.item_id == 1
        assert blocked_result.is_blocked is True
        assert len(blocked_result.blockers) == 1

        # Test to_dict method
        dict_repr = blocked_result.to_dict()
        assert dict_repr["item_id"] == 1
        assert dict_repr["is_blocked"] is True
        assert len(dict_repr["blockers"]) == 1

    def test_model_serialization_edge_cases(self):
        """Test model serialization edge cases"""
        # TodoList with None values
        list_data = {
            "id": 1,
            "list_key": "test",
            "title": "Test",
            "description": None,
            "list_type": ListType.SEQUENTIAL,
            "metadata": {},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        todo_list = TodoList(**list_data)
        dict_repr = todo_list.to_dict()
        assert dict_repr["description"] is None

        # TodoItem with None timestamps
        item_data = {
            "id": 1,
            "list_id": 1,
            "item_key": "test",
            "content": "Test",
            "position": 1,
            "status": ItemStatus.PENDING,
            "completion_states": None,
            "parent_item_id": None,
            "metadata": {},
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        todo_item = TodoItem(**item_data)
        dict_repr = todo_item.to_dict()
        assert dict_repr["started_at"] is None
        assert dict_repr["completed_at"] is None

        # CompletionStates with empty dict
        completion_meta = todo_item.get_completion_metadata()
        assert completion_meta == {}

    def test_validation_error_messages(self):
        """Test that validation errors have meaningful messages"""
        # Test various validation errors to ensure good error messages

        # Invalid list key
        try:
            TodoListCreate(list_key="invalid key with spaces", title="Title")
            assert False, "Should have raised validation error"
        except ValidationError as e:
            error_msg = str(e)
            assert "alphanumeric" in error_msg

        # Invalid item position
        try:
            TodoItemCreate(list_id=1, item_key="item", content="Content", position=-5)
            assert False, "Should have raised validation error"
        except ValidationError as e:
            error_msg = str(e)
            assert "greater than or equal to 0" in error_msg

        # Self-dependency
        try:
            ItemDependencyCreate(
                dependent_item_id=1,
                required_item_id=1,
                dependency_type=DependencyType.BLOCKS,
            )
            assert False, "Should have raised validation error"
        except ValidationError as e:
            error_msg = str(e)
            assert "itself" in error_msg.lower()
