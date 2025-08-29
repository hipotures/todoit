"""
TODOIT MCP - Item Operations Mixin
Collection of basic item management methods for TodoManager
"""

from typing import Any, Dict, List, Optional, Union

from .models import ProgressStats, TodoHistory, TodoItem


class ItemsMixin:
    """Mixin containing basic item management methods for TodoManager"""

    def add_item(
        self,
        list_key: str,
        item_key: str,
        content: str,
        position: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> TodoItem:
        """5. Adds a task to a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Check if the task already exists
        existing_item = self.db.get_item_by_key(db_list.id, item_key)
        if existing_item:
            raise ValueError(f"Item '{item_key}' already exists in list '{list_key}'")

        # Set position if not provided (for main tasks, parent_item_id=None)
        if position is None:
            position = self.db.get_next_position(db_list.id, parent_item_id=None)

        # Prepare task data
        item_data = {
            "list_id": db_list.id,
            "item_key": item_key,
            "content": content,
            "position": position,
            "meta_data": metadata or {},
        }

        # Create the task
        db_item = self.db.create_item(item_data)

        # Save to history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="created",
            new_value={"item_key": item_key, "content": content},
        )

        return self._db_to_model(db_item, TodoItem)

    def update_item_status(
        self,
        list_key: str,
        item_key: str,
        status: str,
        parent_item_key: Optional[str] = None,
        completion_states: Optional[Dict[str, bool]] = None,
        subitem_key: Optional[str] = None,
    ) -> TodoItem:
        """6. Updates the status of a task"""
        # Handle subitem_key parameter for backward compatibility
        if subitem_key:
            # When subitem_key is provided, item_key is the parent and subitem_key is the actual item
            actual_item_key = subitem_key
            parent_item_key = item_key
        else:
            actual_item_key = item_key

        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(
                    f"Parent item '{parent_item_key}' not found in list '{list_key}'"
                )
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, actual_item_key, parent_item_id
        )
        if not db_item:
            if parent_item_key:
                raise ValueError(
                    f"Item '{actual_item_key}' not found under parent '{parent_item_key}' in list '{list_key}'"
                )
            else:
                raise ValueError(
                    f"Item '{actual_item_key}' not found in list '{list_key}'"
                )

        # Check if item has subtasks - items with subtasks cannot have their status manually changed
        children = self.db.get_item_children(db_item.id)
        if children:
            raise ValueError(
                f"Cannot manually change status of item '{actual_item_key}' because it has subtasks. Status is automatically synchronized based on subtask statuses."
            )

        # Store old status for history
        old_status = db_item.status

        # Prepare updates
        updates = {"status": status}
        if completion_states is not None:
            # Merge with existing completion states
            existing_states = db_item.completion_states or {}
            merged_states = {**existing_states, **completion_states}
            updates["completion_states"] = merged_states

        # Set timestamps based on status changes
        if status == "in_progress" and db_item.started_at is None:
            # Set started_at when first moving to in_progress
            from .database import utc_now

            updates["started_at"] = utc_now()
        elif status == "completed":
            # Set completed_at when moving to completed
            from .database import utc_now

            updates["completed_at"] = utc_now()

        # Update the item
        with self.db.get_session() as session:
            db_item = self.db.update_item(db_item.id, updates)

            # Sync parent status if this item has a parent
            if db_item.parent_item_id:
                self._sync_parent_status(db_item.parent_item_id, session)

            session.commit()

        # Save to history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="status_updated",
            old_value={"status": old_status},
            new_value={"status": status},
        )

        return self._db_to_model(db_item, TodoItem)

    def clear_item_completion_states(
        self,
        list_key: str,
        item_key: str,
        parent_item_key: Optional[str] = None,
        state_keys: Optional[List[str]] = None,
    ) -> TodoItem:
        """Clear completion states for an item"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(
                    f"Parent item '{parent_item_key}' not found in list '{list_key}'"
                )
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item_id
        )
        if not db_item:
            if parent_item_key:
                raise ValueError(
                    f"Item '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'"
                )
            else:
                raise ValueError(f"Item '{item_key}' does not exist")

        # Store old states for history
        old_states = db_item.completion_states or {}

        # Clear completion states - either specific keys or all
        if state_keys is not None:
            if state_keys:  # Non-empty list
                # Clear only specific keys
                new_states = {
                    k: v for k, v in old_states.items() if k not in state_keys
                }
            else:  # Empty list
                # Don't clear anything
                new_states = old_states.copy()
        else:
            # Clear all states (None was passed)
            new_states = {}

        updates = {"completion_states": new_states}
        db_item = self.db.update_item(db_item.id, updates)

        # Record in history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="states_cleared",
            old_value={"completion_states": old_states},
            new_value={"completion_states": new_states},
        )

        return self._db_to_model(db_item, TodoItem)

    def get_item(
        self, list_key: str, item_key: str, parent_item_key: Optional[str] = None
    ) -> Optional[TodoItem]:
        """Get a specific item from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                return None
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item_id
        )
        if db_item:
            return self._db_to_model(db_item, TodoItem)
        return None

    def get_list_items(
        self,
        list_key: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TodoItem]:
        """Get all items from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get items
        db_items = self.db.get_list_items(
            list_id=db_list.id,
            status=status,
            limit=limit,
        )

        # Convert to Pydantic models
        items = []
        for db_item in db_items:
            items.append(self._db_to_model(db_item, TodoItem))

        return items

    def delete_item(
        self, list_key: str, item_key: str, parent_item_key: Optional[str] = None
    ) -> bool:
        """Delete an item from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(
                    f"Parent item '{parent_item_key}' not found in list '{list_key}'"
                )
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item_id
        )
        if not db_item:
            return False

        # Check if item has children - cannot delete items with subtasks
        children = self.db.get_item_children(db_item.id)
        if children:
            raise ValueError(
                f"Cannot delete item '{item_key}' because it has subtasks. Delete subtasks first."
            )

        # Record deletion in history before deleting
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="deleted",
            old_value={"item_key": item_key, "content": db_item.content},
        )

        # Delete the item
        success = self.db.delete_item(db_item.id)

        # Sync parent status if this item had a parent
        if success and db_item.parent_item_id:
            self._sync_parent_status(db_item.parent_item_id)

        return success

    def update_item_content(
        self,
        list_key: str,
        item_key: str,
        content: str,
        parent_item_key: Optional[str] = None,
    ) -> TodoItem:
        """Update the content of an item"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(
                    f"Parent item '{parent_item_key}' not found in list '{list_key}'"
                )
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item_id
        )
        if not db_item:
            if parent_item_key:
                raise ValueError(
                    f"Item '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'"
                )
            else:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Store old content for history
        old_content = db_item.content

        # Update the item
        updates = {"content": content}
        db_item = self.db.update_item(db_item.id, updates)

        # Save to history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="content_updated",
            old_value={"content": old_content},
            new_value={"content": content},
        )

        return self._db_to_model(db_item, TodoItem)

    def rename_item(
        self,
        list_key: str,
        item_key: str,
        new_key: Optional[str] = None,
        new_content: Optional[str] = None,
        parent_item_key: Optional[str] = None,
    ) -> TodoItem:
        """Rename item key and/or content"""
        if not new_key and not new_content:
            raise ValueError("Either new_key or new_content must be provided")

        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get parent item ID if specified
        parent_item_id = None
        if parent_item_key:
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(
                    f"Parent item '{parent_item_key}' not found in list '{list_key}'"
                )
            parent_item_id = parent_item.id

        # Get the item
        db_item = self.db.get_item_by_key_and_parent(
            db_list.id, item_key, parent_item_id
        )
        if not db_item:
            if parent_item_key:
                raise ValueError(
                    f"Item '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'"
                )
            else:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Prepare updates and changes for history
        updates = {}
        changes = {}

        if new_key and new_key != item_key:
            # Check if new key already exists
            existing = self.db.get_item_by_key_and_parent(
                db_list.id, new_key, parent_item_id
            )
            if existing:
                if parent_item_key:
                    raise ValueError(
                        f"Item with key '{new_key}' already exists under parent '{parent_item_key}' in list '{list_key}'"
                    )
                else:
                    raise ValueError(
                        f"Item with key '{new_key}' already exists in list '{list_key}'"
                    )

            updates["item_key"] = new_key
            changes["item_key"] = {"from": item_key, "to": new_key}

        if new_content and new_content != db_item.content:
            updates["content"] = new_content
            changes["content"] = {"from": db_item.content, "to": new_content}

        if not updates:
            # No changes needed
            return self._db_to_model(db_item, TodoItem)

        # Update the item
        updated_item = self.db.update_item(db_item.id, updates)

        # Save to history
        self._record_history(
            item_id=updated_item.id,
            list_id=db_list.id,
            action="renamed",
            old_value={
                "item_key": item_key,
                "content": db_item.content,
            },
            new_value={
                "item_key": updated_item.item_key,
                "content": updated_item.content,
            },
            user_context=f"rename: {', '.join(changes.keys())}",
        )

        return self._db_to_model(updated_item, TodoItem)
