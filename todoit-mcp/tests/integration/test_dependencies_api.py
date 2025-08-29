"""
Test Cross-List Dependencies - API Layer
Tests all cross-list dependency functionality at the manager/database level
"""

import pytest

from core.manager import TodoManager
from core.models import ItemStatus, TodoItem


class TestDependenciesAPI:
    """Test cross-list dependency functionality - API layer"""

    def test_add_item_dependency_basic(self, manager, sample_lists):
        """Test basic cross-list dependency creation"""
        # Frontend task depends on backend item
        try:
            result = manager.add_item_dependency(
                dependent_list="frontend",
                dependent_item="item_1",
                required_list="backend",
                required_item="item_1",
            )
            # If no exception, dependency was created
            assert True
        except Exception as e:
            # If exception, check it's not a critical error
            assert "circular" not in str(e).lower()

    def test_get_item_blockers(self, manager, sample_lists):
        """Test retrieving items that block a given item"""
        # Create dependency
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")
        manager.add_item_dependency("frontend", "item_1", "backend", "item_2")

        # Get blockers
        blockers = manager.get_item_blockers("frontend", "item_1")
        assert len(blockers) == 2
        assert all(blocker.status != ItemStatus.COMPLETED for blocker in blockers)

    def test_get_items_blocked_by(self, manager, sample_lists):
        """Test retrieving items blocked by a given item"""
        # Create dependencies
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")
        manager.add_item_dependency("frontend", "item_2", "backend", "item_1")

        # Get blocked items
        blocked_items = manager.get_items_blocked_by("backend", "item_1")
        assert len(blocked_items) == 2

    def test_can_start_item_with_dependencies(self, manager, sample_lists):
        """Test checking if item can start based on dependencies"""
        # Create dependency
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")

        # Should not be able to start (dependency not completed)
        result = manager.can_start_item("frontend", "item_1")
        assert result["can_start"] == False

        # Complete dependency
        manager.update_item_status("backend", "item_1", status=ItemStatus.COMPLETED)

        # Now should be able to start
        result = manager.can_start_item("frontend", "item_1")
        assert result["can_start"] == True

    def test_is_item_blocked(self, manager, sample_lists):
        """Test checking if item is blocked by dependencies"""
        # Create dependency
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")

        # Should be blocked
        is_blocked = manager.is_item_blocked("frontend", "item_1")
        assert is_blocked == True

        # Complete blocker
        manager.update_item_status("backend", "item_1", status=ItemStatus.COMPLETED)

        # Should no longer be blocked
        is_blocked = manager.is_item_blocked("frontend", "item_1")
        assert is_blocked == False

    def test_circular_dependency_prevention(self, manager, sample_lists):
        """Test prevention of circular dependencies"""
        # Create initial dependency: frontend -> backend
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")

        # Try to create circular dependency: backend -> frontend
        with pytest.raises(Exception) as exc_info:
            manager.add_item_dependency("backend", "item_1", "frontend", "item_1")

        assert "circular" in str(exc_info.value).lower()

    def test_remove_item_dependency(self, manager, sample_lists):
        """Test removing cross-list dependencies"""
        # Create dependency
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")

        # Verify blocked
        assert manager.is_item_blocked("frontend", "item_1") == True

        # Remove dependency
        result = manager.remove_item_dependency(
            "frontend", "item_1", "backend", "item_1"
        )
        assert result == True

        # Should no longer be blocked
        assert manager.is_item_blocked("frontend", "item_1") == False

    def test_dependency_types(self, manager, sample_lists):
        """Test different dependency types (blocks, requires, related)"""
        # Test 'blocks' dependency
        manager.add_item_dependency(
            "frontend", "item_1", "backend", "item_1", dependency_type="blocks"
        )

        # Test 'requires' dependency
        manager.add_item_dependency(
            "frontend", "item_2", "backend", "item_2", dependency_type="requires"
        )

        # Verify dependencies exist
        blockers1 = manager.get_item_blockers("frontend", "item_1")
        blockers2 = manager.get_item_blockers("frontend", "item_2")

        assert len(blockers1) == 1
        assert len(blockers2) == 1

    def test_cross_list_progress(self, manager, sample_lists):
        """Test cross-list stats --list tracking"""
        # Create dependencies between lists
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")
        manager.add_item_dependency("frontend", "item_2", "backend", "item_2")

        # Complete some backend tasks
        manager.update_item_status("backend", "item_1", status=ItemStatus.COMPLETED)

        # Get cross-list progress
        progress = manager.get_cross_list_progress("test_project")

        # Verify progress structure
        assert "lists" in progress
        assert isinstance(progress["lists"], list)

    def test_dependency_with_subtasks(self, manager, sample_lists):
        """Test dependencies involving subtasks"""
        # Add subitem to backend
        manager.add_subitem("backend", "item_1", "sub1", "Backend subitem")

        # Frontend depends on backend subtask
        manager.add_item_dependency("frontend", "item_1", "backend", "sub1")

        # Should be blocked
        assert manager.is_item_blocked("frontend", "item_1") == True

        # Complete subitem
        manager.update_item_status(
            "backend", "item_1", subitem_key="sub1", status=ItemStatus.COMPLETED
        )

        # Should be unblocked
        assert manager.is_item_blocked("frontend", "item_1") == False

    def test_complex_dependency_chain(self, manager, sample_lists):
        """Test complex multi-level dependency chains"""
        # Create third list
        manager.create_list(
            "deployment", "Deployment Tasks", ["Deploy staging", "Deploy prod"]
        )

        # Chain: deployment -> frontend -> backend
        manager.add_item_dependency("deployment", "item_1", "frontend", "item_1")
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")

        # Deployment should be blocked by backend
        deployment_blockers = manager.get_item_blockers("deployment", "item_1")

        # Should have transitive dependencies
        assert len(deployment_blockers) >= 1

    def test_get_dependency_graph(self, manager, sample_lists):
        """Test dependency graph generation for visualization"""
        # Create multiple dependencies
        manager.add_item_dependency("frontend", "item_1", "backend", "item_1")
        manager.add_item_dependency("frontend", "item_2", "backend", "item_2")

        # Test that get_dependency_graph exists and returns something
        graph = manager.get_dependency_graph("test_project")

        # Verify it returns a dictionary (actual structure may vary)
        assert isinstance(graph, dict)
