"""
TODOIT MCP - Subtasks and Hierarchy Management Mixin
Collection of subtask and hierarchy methods for TodoManager
"""

from typing import Any, Dict, List, Optional

from .models import TodoItem


class SubtasksMixin:
    """Mixin containing subtask and hierarchy management methods for TodoManager"""

    def add_subitem(
        self,
        list_key: str,
        parent_key: str,
        subitem_key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TodoItem:
        """Add a new subitem to an existing parent item.

        Args:
            list_key: The key of the list containing the parent item.
            parent_key: The key of the parent item.
            subitem_key: The unique key for the new subitem.
            content: The description or content of the subitem.
            metadata: Optional dictionary for custom metadata.

        Returns:
            The newly created TodoItem object for the subitem.

        Raises:
            ValueError: If the list, parent item, or subitem key already exists.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item
        parent_item = self.db.get_item_by_key(db_list.id, parent_key)
        if not parent_item:
            raise ValueError(
                f"Parent item '{parent_key}' not found in list '{list_key}'"
            )

        # Check if subitem_key already exists among siblings of same parent
        existing_item = self.db.get_item_by_key_and_parent(
            db_list.id, subitem_key, parent_item.id
        )
        if existing_item:
            raise ValueError(
                f"Subitem key '{subitem_key}' already exists for parent '{parent_key}'"
            )

        # Get next position for this parent
        position = self.db.get_next_position(db_list.id, parent_item.id)

        # Create subitem
        subitem_data = {
            "list_id": db_list.id,
            "item_key": subitem_key,
            "content": content,
            "parent_item_id": parent_item.id,
            "position": position,
            "meta_data": metadata or {},
        }

        db_subitem = self.db.create_item(subitem_data)

        # Synchronize parent status
        with self.db.get_session() as session:
            self._sync_parent_status(parent_item.id, session)
            session.commit()

        # Record in history
        self._record_history(
            item_id=db_subitem.id,
            list_id=db_list.id,
            action="subitem_created",
            new_value={
                "parent_key": parent_key,
                "subitem_key": subitem_key,
                "content": content,
            },
        )

        return self._db_to_model(db_subitem, TodoItem)

    def get_subitems(self, list_key: str, parent_key: str) -> List[TodoItem]:
        """Get all subitems for a given parent item.

        Args:
            list_key: The key of the list containing the parent item.
            parent_key: The key of the parent item.

        Returns:
            A list of TodoItem objects representing the subitems.

        Raises:
            ValueError: If the list or parent item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item
        parent_item = self.db.get_item_by_key(db_list.id, parent_key)
        if not parent_item:
            raise ValueError(
                f"Parent item '{parent_key}' not found in list '{list_key}'"
            )

        # Get subitems
        db_subitems = self.db.get_item_children(parent_item.id)

        # Convert to Pydantic models
        subitems = []
        for db_subitem in db_subitems:
            subitems.append(self._db_to_model(db_subitem, TodoItem))

        return subitems

    def get_item_hierarchy(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """Get the hierarchical structure of an item and its subitems.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item.

        Returns:
            A dictionary representing the hierarchical structure with the item and all its nested subitems.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get the item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        def build_hierarchy(item_id: int, session=None) -> Dict[str, Any]:
            """Recursively build hierarchy for an item"""
            if session is None:
                session = self.db.get_session()

            # Get the item
            from sqlalchemy.orm import selectinload

            db_item = (
                session.query(self.db.TodoItemDB)
                .options(selectinload(self.db.TodoItemDB.children))
                .filter(self.db.TodoItemDB.id == item_id)
                .first()
            )

            if not db_item:
                return {}

            # Convert to Pydantic model
            item = self._db_to_model(db_item, TodoItem)

            # Build hierarchy structure
            hierarchy = {
                "item": item.model_dump(),
                "subitems": [],
                "stats": {
                    "total_subitems": 0,
                    "completed_subitems": 0,
                    "pending_subitems": 0,
                    "in_progress_subitems": 0,
                    "failed_subitems": 0,
                },
            }

            # Get direct children
            children = self.db.get_item_children(item_id)
            hierarchy["stats"]["total_subitems"] = len(children)

            for child in children:
                child_hierarchy = build_hierarchy(child.id, session)
                hierarchy["subitems"].append(child_hierarchy)

                # Update stats
                if child.status == "completed":
                    hierarchy["stats"]["completed_subitems"] += 1
                elif child.status == "pending":
                    hierarchy["stats"]["pending_subitems"] += 1
                elif child.status == "in_progress":
                    hierarchy["stats"]["in_progress_subitems"] += 1
                elif child.status == "failed":
                    hierarchy["stats"]["failed_subitems"] += 1

                # Add nested stats
                nested_stats = child_hierarchy.get("stats", {})
                for stat_key in [
                    "total_subitems",
                    "completed_subitems",
                    "pending_subitems",
                    "in_progress_subitems",
                    "failed_subitems",
                ]:
                    hierarchy["stats"][stat_key] += nested_stats.get(stat_key, 0)

            return hierarchy

        # Build and return hierarchy
        with self.db.get_session() as session:
            return build_hierarchy(db_item.id, session)

    def auto_complete_parent(self, list_key: str, item_key: str) -> bool:
        """Automatically complete a parent item if all its subitems are completed.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to check.

        Returns:
            True if the parent was auto-completed, False otherwise.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get the item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check if item has subitems
        subitems = self.db.get_item_children(db_item.id)
        if not subitems:
            return False  # No subitems to check

        # Check if all subitems are completed
        all_completed = all(subitem.status == "completed" for subitem in subitems)

        if all_completed and db_item.status != "completed":
            # Auto-complete the parent
            updates = {"status": "completed"}
            self.db.update_item(db_item.id, updates)

            # Record in history
            self._record_history(
                item_id=db_item.id,
                list_id=db_list.id,
                action="auto_completed",
                old_value={"status": db_item.status},
                new_value={"status": "completed"},
                user_context="auto_completion_on_subitems_complete",
            )

            return True

        return False

    def move_to_subitem(
        self, list_key: str, item_key: str, new_parent_key: str
    ) -> TodoItem:
        """Convert an existing root item to be a subitem of another item.

        Args:
            list_key: The key of the list containing the items.
            item_key: The key of the item to move.
            new_parent_key: The key of the item that will become the new parent.

        Returns:
            The updated TodoItem object.

        Raises:
            ValueError: If the list, item, or new parent is not found, or if the move would create a circular dependency.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get item to move
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get new parent
        parent_item = self.db.get_item_by_key(db_list.id, new_parent_key)
        if not parent_item:
            raise ValueError(
                f"Parent item '{new_parent_key}' not found in list '{list_key}'"
            )

        # Check for circular dependency
        if self._would_create_circular_hierarchy(db_item.id, parent_item.id):
            raise ValueError(
                f"Cannot move '{item_key}' under '{new_parent_key}' as it would create a circular dependency"
            )

        # Check if item_key already exists as a subitem of the new parent
        existing_subitem = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item.id
        )
        if existing_subitem:
            raise ValueError(
                f"Item with key '{item_key}' already exists as a subitem of '{new_parent_key}'"
            )

        # Get new position for this parent
        new_position = self.db.get_next_position(db_list.id, parent_item.id)

        # Update the item
        updates = {
            "parent_item_id": parent_item.id,
            "position": new_position,
        }
        updated_item = self.db.update_item(db_item.id, updates)

        # Synchronize both old and new parent statuses
        with self.db.get_session() as session:
            # Sync new parent
            self._sync_parent_status(parent_item.id, session)

            # If item had an old parent, sync it too
            if db_item.parent_item_id:
                self._sync_parent_status(db_item.parent_item_id, session)

            session.commit()

        # Record in history
        self._record_history(
            item_id=updated_item.id,
            list_id=db_list.id,
            action="moved_to_subitem",
            old_value={
                "parent_item_id": db_item.parent_item_id,
                "position": db_item.position,
            },
            new_value={
                "parent_item_id": parent_item.id,
                "new_parent_key": new_parent_key,
                "position": new_position,
            },
        )

        return self._db_to_model(updated_item, TodoItem)

    def _would_create_circular_hierarchy(
        self, item_id: int, potential_parent_id: int
    ) -> bool:
        """Check if making potential_parent_id a parent of item_id would create a circular dependency."""
        # Start from the potential parent and walk up the hierarchy
        current_id = potential_parent_id
        visited = set()

        while current_id:
            if current_id == item_id:
                return True  # Circular dependency found

            if current_id in visited:
                # Infinite loop detected (shouldn't happen with proper data)
                break

            visited.add(current_id)

            # Get parent of current item
            db_item = self.db.get_item_by_id(current_id)
            if not db_item:
                break

            current_id = db_item.parent_item_id

        return False
