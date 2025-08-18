"""
TODOIT MCP - Dependencies Management Mixin
Collection of dependency and blocking logic for TodoManager
"""

from typing import List, Optional, Dict, Any

from .models import ItemDependency, DependencyType, TodoItem


class DependenciesMixin:
    """Mixin containing dependency management methods for TodoManager"""

    def add_item_dependency(
        self,
        dependent_list: str,
        dependent_item: str,
        required_list: str,
        required_item: str,
        dependency_type: str = "blocks",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ItemDependency":
        """Add a dependency between two items, potentially across different lists.

        This indicates that the 'dependent' item cannot be completed until the 'required' item is complete.

        Args:
            dependent_list: The list key of the item that will be blocked.
            dependent_item: The item key of the item that will be blocked.
            required_list: The list key of the item that must be completed first.
            required_item: The item key of the item that must be completed first.
            dependency_type: The type of dependency (e.g., 'blocks', 'related').
            metadata: Optional dictionary for custom metadata.

        Returns:
            The created ItemDependency object.

        Raises:
            ValueError: If any list or item is not found, or if the dependency would create a circular loop.
        """
        # Get dependent item
        dependent_db_list = self.db.get_list_by_key(dependent_list)
        if not dependent_db_list:
            raise ValueError(f"Dependent list '{dependent_list}' not found")

        dependent_db_item = self.db.get_item_by_key(
            dependent_db_list.id, dependent_item
        )
        if not dependent_db_item:
            raise ValueError(
                f"Dependent item '{dependent_item}' not found in list '{dependent_list}'"
            )

        # Get required item
        required_db_list = self.db.get_list_by_key(required_list)
        if not required_db_list:
            raise ValueError(f"Required list '{required_list}' not found")

        required_db_item = self.db.get_item_by_key(required_db_list.id, required_item)
        if not required_db_item:
            raise ValueError(
                f"Required item '{required_item}' not found in list '{required_list}'"
            )

        # Check for circular dependencies
        if self.db._would_create_circular_dependency(
            dependent_db_item.id, required_db_item.id
        ):
            raise ValueError(
                f"Adding this dependency would create a circular dependency loop"
            )

        # Create dependency
        dependency_data = {
            "dependent_item_id": dependent_db_item.id,
            "required_item_id": required_db_item.id,
            "dependency_type": dependency_type,
            "meta_data": metadata or {},
        }

        db_dependency = self.db.create_item_dependency(dependency_data)

        # Record in history
        self._record_history(
            item_id=dependent_db_item.id,
            list_id=dependent_db_list.id,
            action="dependency_added",
            new_value={
                "required_list": required_list,
                "required_item": required_item,
                "dependency_type": dependency_type,
            },
        )

        return self._db_to_model(db_dependency, ItemDependency)

    def remove_item_dependency(
        self,
        dependent_list: str,
        dependent_item: str,
        required_list: str,
        required_item: str,
    ) -> bool:
        """Remove a dependency between two items.

        Args:
            dependent_list: The list key of the dependent item.
            dependent_item: The item key of the dependent item.
            required_list: The list key of the required item.
            required_item: The item key of the required item.

        Returns:
            True if the dependency was removed, False if it was not found.

        Raises:
            ValueError: If any list or item is not found.
        """
        # Get dependent item
        dependent_db_list = self.db.get_list_by_key(dependent_list)
        if not dependent_db_list:
            raise ValueError(f"Dependent list '{dependent_list}' not found")

        dependent_db_item = self.db.get_item_by_key(
            dependent_db_list.id, dependent_item
        )
        if not dependent_db_item:
            raise ValueError(
                f"Dependent item '{dependent_item}' not found in list '{dependent_list}'"
            )

        # Get required item
        required_db_list = self.db.get_list_by_key(required_list)
        if not required_db_list:
            raise ValueError(f"Required list '{required_list}' not found")

        required_db_item = self.db.get_item_by_key(required_db_list.id, required_item)
        if not required_db_item:
            raise ValueError(
                f"Required item '{required_item}' not found in list '{required_list}'"
            )

        # Remove dependency
        success = self.db.delete_item_dependency(
            dependent_db_item.id, required_db_item.id
        )

        if success:
            # Record in history
            self._record_history(
                item_id=dependent_db_item.id,
                list_id=dependent_db_list.id,
                action="dependency_removed",
                old_value={
                    "required_list": required_list,
                    "required_item": required_item,
                },
            )

        return success

    def get_item_blockers(self, list_key: str, item_key: str) -> List["TodoItem"]:
        """Get all items that are blocking the given item.

        Args:
            list_key: The list key containing the item.
            item_key: The item key to check.

        Returns:
            A list of TodoItem objects that are blocking the given item.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get the item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get blockers
        blocker_items = self.db.get_item_blockers(db_item.id)

        # Convert to Pydantic models
        blockers = []
        for blocker in blocker_items:
            blockers.append(self._db_to_model(blocker, TodoItem))

        return blockers

    def get_items_blocked_by(self, list_key: str, item_key: str) -> List["TodoItem"]:
        """Get all items that are blocked by the given item.

        Args:
            list_key: The list key containing the item.
            item_key: The item key to check.

        Returns:
            A list of TodoItem objects that are blocked by the given item.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get the item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get blocked items
        blocked_items = self.db.get_items_blocked_by(db_item.id)

        # Convert to Pydantic models
        blocked = []
        for item in blocked_items:
            blocked.append(self._db_to_model(item, TodoItem))

        return blocked

    def is_item_blocked(self, list_key: str, item_key: str) -> bool:
        """Check if an item is currently blocked by dependencies.

        Args:
            list_key: The list key containing the item.
            item_key: The item key to check.

        Returns:
            True if the item is blocked, False otherwise.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get the item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        return self.db.is_item_blocked(db_item.id)

    def can_start_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """Check if an item can be started and provide detailed blocking information.

        Args:
            list_key: The list key containing the item.
            item_key: The item key to check.

        Returns:
            A dictionary with 'can_start' (bool), 'reason' (str), and detailed blocking info.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get the item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check if already in progress or completed
        if db_item.status in ["in_progress", "completed"]:
            return {
                "can_start": False,
                "reason": f"Item is already {db_item.status}",
                "current_status": db_item.status,
                "blockers": [],
                "pending_subtasks": [],
            }

        # Check for pending subtasks
        pending_children = self.db.get_items_by_status(db_list.id, "pending")
        pending_subtasks = [
            self._db_to_model(child, TodoItem)
            for child in pending_children
            if child.parent_item_id == db_item.id
        ]

        # Check cross-list dependencies
        blockers = self.get_item_blockers(list_key, item_key)
        incomplete_blockers = [b for b in blockers if b.status != "completed"]

        # Determine blocking status
        is_blocked_by_deps = len(incomplete_blockers) > 0
        is_blocked_by_subtasks = len(pending_subtasks) > 0

        can_start = not (is_blocked_by_deps or is_blocked_by_subtasks)

        return {
            "can_start": can_start,
            "blocked_by_dependencies": is_blocked_by_deps,
            "blocked_by_subtasks": is_blocked_by_subtasks,
            "blockers": incomplete_blockers,
            "pending_subtasks": pending_subtasks,
            "reason": self._get_blocking_reason(
                is_blocked_by_deps, is_blocked_by_subtasks, incomplete_blockers, pending_subtasks
            ),
        }

    def can_complete_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """Check if an item can be completed and provide detailed blocking information.

        Args:
            list_key: The list key containing the item.
            item_key: The item key to check.

        Returns:
            A dictionary with 'can_complete' (bool), 'reason' (str), and detailed blocking info.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get the item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check if already completed
        if db_item.status == "completed":
            return {
                "can_complete": False,
                "reason": "Item is already completed",
                "current_status": db_item.status,
                "incomplete_subtasks": [],
            }

        # Check for incomplete subtasks
        all_children = self.db.get_item_children(db_item.id)
        incomplete_subtasks = [
            self._db_to_model(child, TodoItem)
            for child in all_children
            if child.status != "completed"
        ]

        can_complete = len(incomplete_subtasks) == 0

        return {
            "can_complete": can_complete,
            "blocked_by_subtasks": not can_complete,
            "incomplete_subtasks": incomplete_subtasks,
            "reason": "has incomplete subtasks" if not can_complete else "ready to complete",
        }

    def get_dependency_graph(self, project_key: str) -> Dict[str, Any]:
        """Get aggregated dependency graph - returns empty since list relations were removed.

        Args:
            project_key: The project key (no longer used since relations were removed).

        Returns:
            Empty dictionary as list relations feature was removed.
        """
        return {
            "message": "Dependency graphs are not supported since list relations were removed",
            "project_key": project_key,
            "dependencies": [],
            "lists": [],
        }