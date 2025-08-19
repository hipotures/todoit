"""
TODOIT MCP - Todo Manager
Programmatic API for TODO list management - core business logic
"""

import os
from typing import List, Optional, Dict, Any, Union, Set
from datetime import datetime, timezone

from .manager_base import ManagerBase
from .manager_helpers import HelpersMixin
from .manager_lists import ListsMixin
from .manager_tags import TagsMixin
from .manager_properties import PropertiesMixin
from .manager_io import IOMixin
from .security import SecureFileHandler, SecurityError
from .manager_items import ItemsMixin
from .manager_dependencies import DependenciesMixin
from .manager_subtasks import SubtasksMixin
from .database import (
    Database,
    TodoListDB,
    TodoItemDB,
    TodoHistoryDB,
    ListPropertyDB,
    ItemPropertyDB,
    ItemDependencyDB,
    ListTagDB,
    ListTagAssignmentDB,
    utc_now,
)
from .models import (
    TodoList,
    TodoItem,
    TodoHistory,
    ProgressStats,
    ListProperty,
    ItemProperty,
    TodoListCreate,
    TodoItemCreate,
    TodoHistoryCreate,
    ItemDependency,
    DependencyType,
    ListTag,
    ListTagCreate,
    ListTagAssignment,
    ItemStatus,
    ListType,
    HistoryAction,
)


class TodoManager(ManagerBase, HelpersMixin, ListsMixin, TagsMixin, PropertiesMixin, IOMixin, ItemsMixin, DependenciesMixin, SubtasksMixin):
    """Programmatic API for TODO management - core business logic"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize TodoManager with database connection"""
        super().__init__(db_path)

    # === STAGE 1: 10 key functions ===

    def delete_list(self, key: Union[str, int]) -> bool:
        """3. Deletes a list (with relationship validation)"""
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")


        with self.db.get_session() as session:
            # Re-fetch the list in the current session to ensure it's attached
            db_list_in_session = (
                session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            )
            if not db_list_in_session:
                return False

            # Get item IDs for cleanup
            item_ids = [item.id for item in db_list_in_session.items]

            # Delete item dependencies FIRST (before deleting items)
            if item_ids:
                session.query(ItemDependencyDB).filter(
                    (ItemDependencyDB.dependent_item_id.in_(item_ids))
                    | (ItemDependencyDB.required_item_id.in_(item_ids))
                ).delete(synchronize_session=False)

            # Delete item properties FIRST (before deleting items)
            if item_ids:
                session.query(ItemPropertyDB).filter(
                    ItemPropertyDB.item_id.in_(item_ids)
                ).delete(synchronize_session=False)

            # Delete item history
            if item_ids:
                session.query(TodoHistoryDB).filter(
                    TodoHistoryDB.item_id.in_(item_ids)
                ).delete(synchronize_session=False)

            # Delete list history
            session.query(TodoHistoryDB).filter(
                TodoHistoryDB.list_id == db_list.id
            ).delete(synchronize_session=False)

            # Delete list properties
            session.query(ListPropertyDB).filter(
                ListPropertyDB.list_id == db_list.id
            ).delete(synchronize_session=False)


            # Delete list tag assignments
            session.query(ListTagAssignmentDB).filter(
                ListTagAssignmentDB.list_id == db_list.id
            ).delete(synchronize_session=False)

            # Items are deleted via cascade="all, delete-orphan" on the list's items relationship.
            # Deleting the list will trigger the deletion of its items.
            session.delete(db_list_in_session)
            session.commit()
        return True

    def archive_list(self, key: Union[str, int], force: bool = False) -> TodoList:
        """Archive a TODO list (sets status to 'archived')

        Args:
            key: List key or ID to archive
            force: If False, prevents archiving lists with incomplete tasks
        """
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")

        if db_list.status == "archived":
            raise ValueError(f"List '{key}' is already archived")

        # Check if all tasks are completed unless force=True
        if not force:
            progress = self.get_progress(db_list.list_key)
            if progress.total > 0 and progress.completed < progress.total:
                incomplete_count = progress.total - progress.completed
                raise ValueError(
                    f"Cannot archive list with incomplete tasks. "
                    f"Incomplete: {incomplete_count}/{progress.total} tasks. "
                    f"Use force=True to archive anyway."
                )

        with self.db.get_session() as session:
            # Re-fetch the list in the current session
            db_list_in_session = (
                session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            )
            if not db_list_in_session:
                raise ValueError(f"List '{key}' not found")

            # Update status to archived
            db_list_in_session.status = "archived"
            db_list_in_session.updated_at = utc_now()
            session.commit()

            # Convert to Pydantic model and return
            return TodoList(
                id=db_list_in_session.id,
                list_key=db_list_in_session.list_key,
                title=db_list_in_session.title,
                description=db_list_in_session.description,
                list_type=db_list_in_session.list_type,
                status=db_list_in_session.status,
                metadata=db_list_in_session.meta_data or {},
                created_at=db_list_in_session.created_at,
                updated_at=db_list_in_session.updated_at,
            )

    def unarchive_list(self, key: Union[str, int]) -> TodoList:
        """Unarchive a TODO list (sets status to 'active')"""
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")

        if db_list.status == "active":
            raise ValueError(f"List '{key}' is already active")

        with self.db.get_session() as session:
            # Re-fetch the list in the current session
            db_list_in_session = (
                session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            )
            if not db_list_in_session:
                raise ValueError(f"List '{key}' not found")

            # Update status to active
            db_list_in_session.status = "active"
            db_list_in_session.updated_at = utc_now()
            session.commit()

            # Convert to Pydantic model and return
            return TodoList(
                id=db_list_in_session.id,
                list_key=db_list_in_session.list_key,
                title=db_list_in_session.title,
                description=db_list_in_session.description,
                list_type=db_list_in_session.list_type,
                status=db_list_in_session.status,
                metadata=db_list_in_session.meta_data or {},
                created_at=db_list_in_session.created_at,
                updated_at=db_list_in_session.updated_at,
            )

    def rename_list(
        self, 
        current_key: str, 
        new_key: Optional[str] = None, 
        new_title: Optional[str] = None
    ) -> TodoList:
        """Rename list key and/or title"""
        # Validate that at least one parameter is provided
        if new_key is None and new_title is None:
            raise ValueError("At least one of new_key or new_title must be provided")
        
        # Get the current list
        db_list = self.db.get_list_by_key(current_key)
        if not db_list:
            raise ValueError(f"List '{current_key}' does not exist")
        
        # Store old values for history
        old_key = db_list.list_key
        old_title = db_list.title
        
        # Prepare updates dict
        updates = {}
        
        # Validate and set new key if provided
        if new_key is not None:
            # Validate new key - must contain at least one letter
            import re
            if not re.search(r'[a-zA-Z]', new_key):
                raise ValueError(
                    f"List key '{new_key}' must contain at least one letter (a-z) to distinguish from numeric IDs"
                )
            
            # Check if new key already exists (and it's not the same list)
            existing = self.db.get_list_by_key(new_key)
            if existing and existing.id != db_list.id:
                raise ValueError(f"List key '{new_key}' already exists")
                
            updates["list_key"] = new_key
        
        # Set new title if provided
        if new_title is not None:
            updates["title"] = new_title
        
        # Update the list
        updated_db_list = self.db.update_list(db_list.id, updates)
        if not updated_db_list:
            raise ValueError(f"Failed to update list '{current_key}'")
        
        # Save to history
        changes_desc = []
        if new_key is not None:
            changes_desc.append(f"key: {old_key} → {new_key}")
        if new_title is not None:
            changes_desc.append(f"title: {old_title} → {new_title}")
        
        self._record_history(
            list_id=updated_db_list.id,
            action="rename_list",
            old_value={
                "list_key": old_key,
                "title": old_title
            },
            new_value={
                "list_key": new_key or old_key,
                "title": new_title or old_title,
                "changes": "; ".join(changes_desc)
            }
        )
        
        # Convert to Pydantic model and return
        return TodoList(
            id=updated_db_list.id,
            list_key=updated_db_list.list_key,
            title=updated_db_list.title,
            description=updated_db_list.description,
            list_type=updated_db_list.list_type,
            status=updated_db_list.status,
            metadata=updated_db_list.meta_data or {},
            created_at=updated_db_list.created_at,
            updated_at=updated_db_list.updated_at,
        )

    def list_all(
        self,
        limit: Optional[int] = None,
        include_archived: bool = False,
        filter_tags: Optional[List[str]] = None,
    ) -> List[TodoList]:
        """4. Lists all TODO lists with optional tag filtering"""
        if filter_tags:
            # Get lists by tags
            lists = self.get_lists_by_tags(filter_tags)

            # Apply archived filter if needed
            if not include_archived:
                lists = [l for l in lists if l.status != "archived"]

            # Apply limit if specified
            if limit and len(lists) > limit:
                lists = lists[:limit]

            return lists
        else:
            # Use original implementation without tag filtering
            db_lists = self.db.get_all_lists(limit)
            lists = [self._db_to_model(db_list, TodoList) for db_list in db_lists]

            # Filter archived if requested
            if not include_archived:
                lists = [l for l in lists if l.status != "archived"]

            return lists

    def get_archived_lists(self, limit: Optional[int] = None) -> List[TodoList]:
        """Retrieves all lists that have been archived.

        Args:
            limit: The maximum number of archived lists to return.

        Returns:
            A list of TodoList objects with a status of 'archived'.
        """
        db_lists = self.db.get_all_lists(limit=limit)
        archived_lists = [
            db_list for db_list in db_lists if db_list.status == "archived"
        ]
        return [self._db_to_model(db_list, TodoList) for db_list in archived_lists]


    def get_next_pending(
        self,
        list_key: str,
        respect_dependencies: bool = True,
        smart_subtasks: bool = False,
    ) -> Optional[TodoItem]:
        """7. Gets the next task to be executed (enhanced with Phase 2 blocking logic)"""
        # Use smart subtask logic if requested
        if smart_subtasks:
            return self.get_next_pending_with_subtasks(list_key)

        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None

        # Get pending tasks
        pending_items = self.db.get_items_by_status(db_list.id, "pending")

        if not respect_dependencies:
            return (
                self._db_to_model(pending_items[0], TodoItem) if pending_items else None
            )

        # Check dependencies
        for db_item in pending_items:
            # Phase 1: Check parent/child dependencies (subtasks)
            if db_item.parent_item_id:
                parent = self.db.get_item_by_id(db_item.parent_item_id)
                if parent and parent.status != "completed":
                    continue

            # Phase 2: Check cross-list dependencies (item blocked by other items)
            if self.db.is_item_blocked(db_item.id):
                continue  # Skip blocked items


            return self._db_to_model(db_item, TodoItem)

        return None

    def get_progress(self, list_key: str) -> ProgressStats:
        """8. Phase 3: Enhanced progress tracking with hierarchies and dependencies"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Basic stats
        stats = self.db.get_list_stats(db_list.id)

        # Calculate completion percentage
        completion_percentage = 0.0
        if stats["total"] > 0:
            completion_percentage = (stats["completed"] / stats["total"]) * 100

        # Phase 3: Enhanced statistics
        all_items = self.db.get_list_items(db_list.id)

        # Count hierarchy structure
        root_items = [item for item in all_items if item.parent_item_id is None]
        subtasks = [item for item in all_items if item.parent_item_id is not None]

        # Calculate maximum hierarchy depth
        max_depth = 0
        for item in all_items:
            depth = self.db.get_item_depth(item.id)
            max_depth = max(max_depth, depth)

        # Count blocked items (Phase 2 cross-list dependencies)
        blocked_count = 0
        available_count = 0
        for item in all_items:
            if item.status in ["pending"]:
                if self.db.is_item_blocked(item.id):
                    blocked_count += 1
                else:
                    available_count += 1

        # Count cross-list dependencies involving this list
        dependencies = self.db.get_all_dependencies_for_list(db_list.id)

        return ProgressStats(
            total=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            pending=stats["pending"],
            failed=stats["failed"],
            completion_percentage=completion_percentage,
            blocked=blocked_count,
            available=available_count,
            root_items=len(root_items),
            subtasks=len(subtasks),
            hierarchy_depth=max_depth,
            dependency_count=len(dependencies),
        )

    def import_from_markdown(
        self, file_path: str, base_key: Optional[str] = None,
        allowed_base_dirs: Optional[Set[str]] = None
    ) -> List[TodoList]:
        """
        9. Imports lists from a markdown file (supports multi-column)
        
        Args:
            file_path: Path to markdown file to import
            base_key: Base key prefix for imported lists (optional)
            allowed_base_dirs: Set of allowed base directories for security (optional)
            
        Returns:
            List of created TodoList objects
            
        Raises:
            SecurityError: If file path is malicious or violates security constraints
            ValueError: If file format is invalid or other validation errors
        """
        try:
            # Secure file reading with full validation
            content = SecureFileHandler.secure_file_read(file_path, allowed_base_dirs)
        except SecurityError as e:
            raise ValueError(f"Security error reading file: {e}") from e

        lists_data = {}

        # Process file content line by line
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Handle both formats: "[x]" and "- [x]"
            original_line = line
            if line.startswith("- ["):
                line = line[2:].strip()  # Remove "- " prefix

            if line.startswith("["):
                # Parse all columns [ ] or [x]
                columns = []
                content = line

                # Extract all states
                while content.startswith("["):
                    if len(content) < 3:
                        break
                    state = content[1] == "x" or content[1] == "X"
                    columns.append(state)
                    content = content[4:].strip()  # Skip [x] or [ ]

                if not content:
                    continue

                # For each column, we create a separate list
                for i, state in enumerate(columns):
                    if i not in lists_data:
                        lists_data[i] = []
                    lists_data[i].append(
                        {
                            "content": content,
                            "completed": state,
                            "position": len(lists_data[i]) + 1,
                        }
                    )

        if not lists_data:
            raise ValueError("No tasks found in markdown format in the file")

        # Create lists
        created_lists = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_key = base_key or f"import_{timestamp}"

        for i, items in lists_data.items():
            list_key = f"{base_key}_col{i+1}" if len(lists_data) > 1 else base_key
            list_title = (
                f"Imported list {i+1}" if len(lists_data) > 1 else "Imported list"
            )

            # Create the list
            todo_list = self.create_list(
                list_key=list_key,
                title=list_title,
                metadata={"imported_from": file_path, "import_timestamp": timestamp},
            )

            # Add tasks
            for item in items:
                item_obj = self.add_item(
                    list_key=list_key,
                    item_key=f"item_{item['position']}",
                    content=item["content"],
                    position=item["position"],
                )

                # Set status if completed
                if item["completed"]:
                    self.update_item_status(
                        list_key=list_key,
                        item_key=f"item_{item['position']}",
                        status="completed",
                    )

            created_lists.append(todo_list)


        return created_lists

    def export_to_markdown(self, list_key: str, file_path: str, 
                         allowed_base_dirs: Optional[Set[str]] = None) -> None:
        """
        10. Exports a list to markdown format [x] text
        
        Args:
            list_key: Key of the list to export
            file_path: Path where to write the markdown file
            allowed_base_dirs: Set of allowed base directories for security (optional)
            
        Raises:
            SecurityError: If file path is malicious or violates security constraints
            ValueError: If list doesn't exist or other validation errors
        """
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get tasks
        items = self.db.get_list_items(db_list.id)

        # Build content
        content_lines = [f"# {db_list.title}", ""]
        if db_list.description:
            content_lines.extend([db_list.description, ""])

        # Items
        for item in sorted(items, key=lambda x: x.position):
            status_mark = "[x]" if item.status == "completed" else "[ ]"
            content_lines.append(f"{status_mark} {item.content}")

        content = "\n".join(content_lines)

        # Secure export to file
        try:
            SecureFileHandler.secure_file_write(file_path, content, allowed_base_dirs)
        except SecurityError as e:
            raise ValueError(f"Security error writing file: {e}") from e

        # Save to history
        self._record_history(
            list_id=db_list.id,
            action="exported",
            new_value={"file_path": file_path, "format": "markdown"},
        )

    # === Helper functions ===



    def get_item_history(
        self, list_key: str, item_key: str, limit: Optional[int] = None
    ) -> List[TodoHistory]:
        """Gets the change history of a task"""
        item = self.get_item(list_key, item_key)
        if not item:
            return []

        db_history = self.db.get_item_history(item.id, limit=limit)
        return [self._db_to_model(entry, TodoHistory) for entry in db_history]

    def get_all_failed_items(
        self, list_filter: Optional[str] = None, tag_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all failed items from active lists with full context and optional filtering

        Args:
            list_filter: Optional regex pattern to filter lists by list_key
            tag_filter: Optional list of tag names to filter lists by

        Returns:
            List of dictionaries containing failed item details with list context and properties
        """
        import re
        from typing import Dict, Any

        # Get only active lists (not archived) with optional tag filtering
        all_lists = self.list_all(include_archived=False, filter_tags=tag_filter)
        failed_reports = []

        # Apply regex filter if provided
        if list_filter:
            try:
                pattern = re.compile(list_filter)
                all_lists = [
                    todo_list
                    for todo_list in all_lists
                    if pattern.match(todo_list.list_key)
                ]
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{list_filter}': {e}")

        # Collect failed items from all matching lists
        for todo_list in all_lists:
            failed_items = self.get_list_items(todo_list.list_key, status="failed")

            for item in failed_items:
                # Get properties for each failed item
                properties = self.get_item_properties(todo_list.list_key, item.item_key)

                failed_reports.append(
                    {
                        "list_key": todo_list.list_key,
                        "list_title": todo_list.title,
                        "list_type": str(todo_list.list_type)
                        .replace("ListType.", "")
                        .lower(),
                        "item_key": item.item_key,
                        "content": item.content,
                        "position": item.position,
                        "updated_at": item.updated_at,
                        "created_at": item.created_at,
                        "properties": properties,
                    }
                )

        # Sort by list_key first, then by position within each list
        return sorted(failed_reports, key=lambda x: (x["list_key"], x["position"]))

    # === List Properties Methods ===

    def set_list_property(
        self, list_key: str, property_key: str, property_value: str
    ) -> ListProperty:
        """Set a key-value property for a list, creating it if it doesn't exist or updating it if it does.

        Args:
            list_key: The key of the list to set the property for.
            property_key: The key of the property to set.
            property_value: The value to assign to the property.

        Returns:
            The created or updated ListProperty object.

        Raises:
            ValueError: If the specified list is not found.
        """

        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Create or update property
        db_property = self.db.create_list_property(
            db_list.id, property_key, property_value
        )
        return self._db_to_model(db_property, ListProperty)

    def get_list_property(self, list_key: str, property_key: str) -> Optional[str]:
        """Get the value of a specific property for a list.

        Args:
            list_key: The key of the list.
            property_key: The key of the property to retrieve.

        Returns:
            The value of the property as a string, or None if the property or list does not exist.

        Raises:
            ValueError: If the specified list is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get property
        db_property = self.db.get_list_property(db_list.id, property_key)
        return db_property.property_value if db_property else None

    def get_list_properties(self, list_key: str) -> Dict[str, str]:
        """Get all properties for a list as a key-value dictionary.

        Args:
            list_key: The key of the list.

        Returns:
            A dictionary containing all properties of the list. Returns an empty dictionary if the list has no properties.

        Raises:
            ValueError: If the specified list is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get all properties
        db_properties = self.db.get_list_properties(db_list.id)
        return {prop.property_key: prop.property_value for prop in db_properties}

    def delete_list_property(self, list_key: str, property_key: str) -> bool:
        """Delete a specific property from a list.

        Args:
            list_key: The key of the list.
            property_key: The key of the property to delete.

        Returns:
            True if the property was deleted, False if it did not exist.

        Raises:
            ValueError: If the specified list is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Delete property
        return self.db.delete_list_property(db_list.id, property_key)

    # ===== ITEM PROPERTIES METHODS =====

    def set_item_property(
        self, list_key: str, item_key: str, property_key: str, property_value: str,
        parent_item_key: Optional[str] = None
    ) -> ItemProperty:
        """Set a key-value property for an item or subitem, creating or updating it.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to set the property for.
            property_key: The key of the property to set.
            property_value: The value to assign to the property.
            parent_item_key: Optional parent item key (for subitems).

        Returns:
            The created or updated ItemProperty object.

        Raises:
            ValueError: If the list, item, or parent item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get item (handling subitems)
        if parent_item_key:
            # Get parent item first
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            
            # Get subitem
            db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item.id)
            if not db_item:
                raise ValueError(f"Subitem '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
        else:
            # Get main item
            db_item = self.db.get_item_by_key(db_list.id, item_key)
            if not db_item:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Create/update property
        db_property = self.db.create_item_property(
            db_item.id, property_key, property_value
        )
        return self._db_to_model(db_property, ItemProperty)

    def get_item_property(
        self, list_key: str, item_key: str, property_key: str,
        parent_item_key: Optional[str] = None
    ) -> Optional[str]:
        """Get the value of a specific property for an item or subitem.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item.
            property_key: The key of the property to retrieve.
            parent_item_key: Optional parent item key (for subitems).

        Returns:
            The value of the property as a string, or None if the property, item, or list does not exist.

        Raises:
            ValueError: If the list, item, or parent item is not found.
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get item (handling subitems)
        if parent_item_key:
            # Get parent item first
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            
            # Get subitem
            db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item.id)
            if not db_item:
                raise ValueError(f"Subitem '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
        else:
            # Get main item
            db_item = self.db.get_item_by_key(db_list.id, item_key)
            if not db_item:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        return self.db.get_item_property(db_item.id, property_key)

    def get_item_properties(self, list_key: str, item_key: str, 
                           parent_item_key: Optional[str] = None) -> Dict[str, str]:
        """Get all properties for an item or subitem as a key-value dictionary.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item.
            parent_item_key: Optional parent item key (for subitems).

        Returns:
            A dictionary containing all properties of the item. Returns an empty dictionary if the item has no properties.

        Raises:
            ValueError: If the list, item, or parent item is not found.
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get item (handling subitems)
        if parent_item_key:
            # Get parent item first
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            
            # Get subitem
            db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item.id)
            if not db_item:
                raise ValueError(f"Subitem '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
        else:
            # Get main item
            db_item = self.db.get_item_by_key(db_list.id, item_key)
            if not db_item:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        return self.db.get_item_properties(db_item.id)

    def get_all_items_properties(
        self, list_key: str, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all properties for all items in a list, optionally filtered by status.

        Args:
            list_key: The key of the list.
            status: Optional status filter ('pending', 'in_progress', 'completed', 'failed').
                   If None, returns properties for all items regardless of status.
            limit: Optional maximum number of items to return properties for.

        Returns:
            A list of dictionaries, each containing 'item_key', 'property_key', 'property_value', and 'status'.
            Returns an empty list if no items have properties.

        Raises:
            ValueError: If the specified list is not found or invalid status provided.
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Validate status if provided
        if status is not None:
            valid_statuses = ["pending", "in_progress", "completed", "failed"]
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}"
                )

        # Get items filtered by status if specified
        if status is not None:
            items = self.db.get_items_by_status(db_list.id, status)
        else:
            items = self.db.get_list_items(db_list.id)

        # Apply limit to items if specified
        if limit is not None:
            items = items[:limit]

        # Create lookup for parent item keys
        parent_id_to_key = {}
        for item in items:
            if item.parent_item_id is not None:
                # Find parent item key
                parent_item = next((i for i in items if i.id == item.parent_item_id), None)
                if parent_item:
                    parent_id_to_key[item.parent_item_id] = parent_item.item_key

        result = []
        for item_order, item in enumerate(items):
            # Get all properties for this item
            properties = self.db.get_item_properties(item.id)
            parent_item_key = parent_id_to_key.get(item.parent_item_id) if item.parent_item_id else None
            
            if properties:
                # Item has properties - add each property
                for prop_key, prop_value in properties.items():
                    result.append(
                        {
                            "item_key": item.item_key,
                            "property_key": prop_key,
                            "property_value": prop_value,
                            "status": item.status,
                            "item_order": item_order,
                            "parent_item_id": item.parent_item_id,
                            "parent_item_key": parent_item_key,
                            "position": item.position
                        }
                    )
            else:
                # Item has no properties - add placeholder entry to show hierarchy
                result.append(
                    {
                        "item_key": item.item_key,
                        "property_key": "—",
                        "property_value": "—",
                        "status": item.status,
                        "item_order": item_order,
                        "parent_item_id": item.parent_item_id,
                        "parent_item_key": parent_item_key,
                        "position": item.position
                    }
                )

        # Sort by hierarchy: group by parent_item_key, then by position and property_key
        def sort_key(x):
            if x["parent_item_id"] is None:
                # Main item: sort by position, then property_key
                return (x["position"], 0, x["property_key"])
            else:
                # Subitem: find parent's position to group subitems under their parents
                parent_key = x.get("parent_item_key", "")
                parent_item = next((item for item in items if item.item_key == parent_key), None)
                parent_position = parent_item.position if parent_item else 999
                return (parent_position, 1, x["position"], x["property_key"])
        
        result.sort(key=sort_key)
        return result

    def find_items_by_property(
        self,
        list_key: str,
        property_key: str,
        property_value: str,
        limit: Optional[int] = None,
    ) -> List[TodoItem]:
        """Find items by property value with optional limit.

        Args:
            list_key: The key of the list to search in.
            property_key: The property name to match.
            property_value: The property value to match.
            limit: Maximum number of results to return (None = all).

        Returns:
            List of TodoItem objects matching the criteria, ordered by position.

        Raises:
            ValueError: If the specified list is not found.
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Use database layer for efficient search
        db_items = self.db.find_items_by_property(
            db_list.id, property_key, property_value, limit
        )

        # Convert to Pydantic models
        return [self._db_to_model(db_item, TodoItem) for db_item in db_items]

    def find_subitems_by_status(
        self,
        list_key: str,
        conditions: Dict[str, str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find grouped parent-subitem matches based on sibling status conditions.

        Args:
            list_key: The key of the list to search in.
            conditions: Dictionary of {subitem_key: expected_status}.
            limit: Maximum number of parent matches to return.

        Returns:
            List of dictionaries with format:
            [
                {
                    "parent": TodoItem object,
                    "matching_subitems": [TodoItem objects that match conditions]
                },
                ...
            ]

        Raises:
            ValueError: If the specified list is not found.

        Example:
            # Find downloads ready to process (where generation is completed)
            matches = manager.find_subitems_by_status(
                "images",
                {"generate": "completed", "download": "pending"},
                limit=5
            )
            # Returns grouped results with parent context
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        if not conditions:
            raise ValueError("Conditions dictionary cannot be empty")

        # Use database layer for efficient search
        db_matches = self.db.find_subitems_by_status(db_list.id, conditions, limit)

        # Convert to Pydantic models
        matches = []
        for db_match in db_matches:
            parent_model = self._db_to_model(db_match["parent"], TodoItem)
            matching_subitems = [
                self._db_to_model(db_item, TodoItem) 
                for db_item in db_match["matching_subitems"]
            ]
            
            matches.append({
                "parent": parent_model,
                "matching_subitems": matching_subitems
            })

        return matches

    def delete_item_property(
        self, list_key: str, item_key: str, property_key: str,
        parent_item_key: Optional[str] = None
    ) -> bool:
        """Delete a specific property from an item or subitem.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item.
            property_key: The key of the property to delete.
            parent_item_key: Optional parent item key (for subitems).

        Returns:
            True if the property was deleted, False if it did not exist.

        Raises:
            ValueError: If the list, item, or parent item is not found.
        """
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        # Get item (handling subitems)
        if parent_item_key:
            # Get parent item first
            parent_item = self.db.get_item_by_key(db_list.id, parent_item_key)
            if not parent_item:
                raise ValueError(f"Parent item '{parent_item_key}' not found in list '{list_key}'")
            
            # Get subitem
            db_item = self.db.get_item_by_key_and_parent(db_list.id, item_key, parent_item.id)
            if not db_item:
                raise ValueError(f"Subitem '{item_key}' not found under parent '{parent_item_key}' in list '{list_key}'")
        else:
            # Get main item
            db_item = self.db.get_item_by_key(db_list.id, item_key)
            if not db_item:
                raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        return self.db.delete_item_property(db_item.id, property_key)

        """Get all direct subitems for a given parent item.

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

        # Get children
        children = self.db.get_item_children(parent_item.id)
        return [self._db_to_model(child, TodoItem) for child in children]

    def get_item_hierarchy(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """Get the full hierarchy for an item, including all its subitems recursively.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the root item of the hierarchy.

        Returns:
            A dictionary representing the item and its nested subitems.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        def build_hierarchy(item_db) -> Dict[str, Any]:
            """Recursively build hierarchy structure"""
            item_model = self._db_to_model(item_db, TodoItem)
            children = self.db.get_item_children(item_db.id)

            hierarchy = {
                "item": item_model.to_dict(),
                "subitems": [build_hierarchy(child) for child in children],
            }

            return hierarchy

        return build_hierarchy(db_item)

    def get_next_pending_with_subtasks(self, list_key: str) -> Optional[TodoItem]:
        """
        Phase 3: Smart next task algorithm combining Phase 1 + Phase 2
        OPTIMIZED VERSION: Eliminates N+1 queries using bulk loading
        
        1. Find all pending tasks (root and subtasks)
        2. Filter out blocked (cross-list dependencies - Phase 2)
        3. For each unblocked pending task:
           a. If has pending subtasks → return first pending subtask
           b. If no subtasks → return task itself
        4. Priority:
           - Items with in_progress parents (continue working on started items)
           - Items without cross-list dependencies
           - Items by position
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # OPTIMIZATION: Get all root items with children preloaded in single query
        # Fallback to old method if optimized version not available or in testing
        use_optimized = (
            hasattr(self.db, 'get_root_items_with_children_optimized') and
            hasattr(self.db, 'SessionLocal') and
            not str(type(self.db)).startswith("<class 'unittest.mock")
        )
        
        if use_optimized:
            try:
                root_items = self.db.get_root_items_with_children_optimized(db_list.id)
            except (AttributeError, TypeError):
                root_items = self.db.get_root_items(db_list.id)
        else:
            root_items = self.db.get_root_items(db_list.id)
        
        # OPTIMIZATION: Get all pending items with parents preloaded in single query
        if use_optimized:
            try:
                all_pending_items = self.db.get_list_items_with_parents_optimized(db_list.id, status="pending")
            except (AttributeError, TypeError):
                all_pending_items = self.db.get_list_items(db_list.id, status="pending")
        else:
            all_pending_items = self.db.get_list_items(db_list.id, status="pending")
        
        # Collect all item IDs that need dependency checking
        all_candidate_ids = []
        for item in root_items:
            if item.status == "pending":
                # Only check pending parents for blocking, not in_progress ones
                all_candidate_ids.append(item.id)
            
            # Add children IDs for bulk checking (for both pending and in_progress parents)
            if item.status in ["pending", "in_progress"]:
                if use_optimized:
                    try:
                        for child in item.children:
                            if child.status == "pending":
                                all_candidate_ids.append(child.id)
                    except (AttributeError, TypeError):
                        # Fall back to fetching children individually
                        children = self.db.get_item_children(item.id)
                        for child in children:
                            if child.status == "pending":
                                all_candidate_ids.append(child.id)
                else:
                    # Non-optimized path: fetch children individually
                    children = self.db.get_item_children(item.id)
                    for child in children:
                        if child.status == "pending":
                            all_candidate_ids.append(child.id)
        
        # Add orphaned subtasks
        for item in all_pending_items:
            if item.parent_item_id:
                if use_optimized:
                    try:
                        if item.parent and item.parent.status in ["completed", "failed"]:
                            all_candidate_ids.append(item.id)
                    except (AttributeError, TypeError):
                        # Fall back to individual parent lookup
                        parent = self.db.get_item_by_id(item.parent_item_id)
                        if parent and parent.status in ["completed", "failed"]:
                            all_candidate_ids.append(item.id)
                else:
                    # Non-optimized path: fetch parent individually
                    parent = self.db.get_item_by_id(item.parent_item_id)
                    if parent and parent.status in ["completed", "failed"]:
                        all_candidate_ids.append(item.id)
        
        # OPTIMIZATION: Bulk check for blocked items in single query
        # Fallback to individual checks if bulk method not available (for testing)
        if use_optimized:
            try:
                blocked_items = self.db.get_blocked_items_bulk(all_candidate_ids)
            except (AttributeError, TypeError):
                blocked_items = set()
                for item_id in all_candidate_ids:
                    if self.db.is_item_blocked(item_id):
                        blocked_items.add(item_id)
        else:
            blocked_items = set()
            for item_id in all_candidate_ids:
                if self.db.is_item_blocked(item_id):
                    blocked_items.add(item_id)

        # Phase 3: Enhanced algorithm - collect all candidates with priority scoring
        candidates = []

        for item in root_items:
            # Priority 1: In-progress parent with pending subtasks (continue working)
            if item.status == "in_progress":
                # Children loaded via selectinload if optimized, otherwise fetch individually
                if use_optimized:
                    try:
                        # Try to use preloaded children if available (from optimized query)
                        pending_children = [
                            child for child in item.children if child.status == "pending"
                        ]
                        # If no children but item should have children, fall back to database query
                        if not pending_children and item.status in ["in_progress", "pending"]:
                            # This might be a mock or unloaded relationship, fall back
                            children = self.db.get_item_children(item.id)
                            pending_children = [
                                child for child in children if child.status == "pending"
                            ]
                    except (AttributeError, TypeError):
                        children = self.db.get_item_children(item.id)
                        pending_children = [
                            child for child in children if child.status == "pending"
                        ]
                else:
                    children = self.db.get_item_children(item.id)
                    pending_children = [
                        child for child in children if child.status == "pending"
                    ]

                for child in pending_children:
                    # Phase 2: Check if subtask is blocked (already bulk-checked)
                    if child.id not in blocked_items:
                        candidates.append(
                            {
                                "item": child,
                                "priority": 1,  # Highest priority - continue in-progress work
                                "parent_position": item.position,
                                "item_position": child.position,
                            }
                        )

            # Priority 2: Pending parent tasks
            elif item.status == "pending":
                # Phase 2: Check if parent is blocked (already bulk-checked)
                if item.id in blocked_items:
                    continue  # Skip blocked items

                # Children loaded via selectinload if optimized, otherwise fetch individually
                if use_optimized:
                    try:
                        # Try to use preloaded children if available (from optimized query)
                        pending_children = [
                            child for child in item.children if child.status == "pending"
                        ]
                        # If no children but item should have children, fall back to database query
                        if not pending_children and item.status in ["in_progress", "pending"]:
                            # This might be a mock or unloaded relationship, fall back
                            children = self.db.get_item_children(item.id)
                            pending_children = [
                                child for child in children if child.status == "pending"
                            ]
                    except (AttributeError, TypeError):
                        children = self.db.get_item_children(item.id)
                        pending_children = [
                            child for child in children if child.status == "pending"
                        ]
                else:
                    children = self.db.get_item_children(item.id)
                    pending_children = [
                        child for child in children if child.status == "pending"
                    ]

                if pending_children:
                    # Return first unblocked pending subtask
                    for child in pending_children:
                        if child.id not in blocked_items:
                            candidates.append(
                                {
                                    "item": child,
                                    "priority": 2,  # Medium priority - new subtask
                                    "parent_position": item.position,
                                    "item_position": child.position,
                                }
                            )
                            break  # Take first available subtask
                else:
                    # No subtasks, return parent task itself
                    candidates.append(
                        {
                            "item": item,
                            "priority": 3,  # Lower priority - root task
                            "parent_position": item.position,
                            "item_position": 0,
                        }
                    )

        # Phase 3: Check orphaned subtasks (subtasks with completed/failed parents)
        # Parents loaded via selectinload if optimized, otherwise fetch individually
        for item in all_pending_items:
            if item.parent_item_id:  # This is a subtask
                if use_optimized:
                    try:
                        # Try to use preloaded parent if available
                        parent = item.parent
                    except (AttributeError, TypeError):
                        parent = self.db.get_item_by_id(item.parent_item_id)
                else:
                    parent = self.db.get_item_by_id(item.parent_item_id)
                
                if parent and parent.status in ["completed", "failed"]:
                    # Orphaned subtask - can be worked on independently
                    if item.id not in blocked_items:
                        candidates.append(
                            {
                                "item": item,
                                "priority": 4,  # Lowest priority - orphaned subtask
                                "parent_position": parent.position,
                                "item_position": item.position,
                            }
                        )

        # Sort candidates by priority, then parent position, then item position
        candidates.sort(
            key=lambda x: (x["priority"], x["parent_position"], x["item_position"])
        )

        # Return first candidate
        if candidates:
            return self._db_to_model(candidates[0]["item"], TodoItem)

        # No available tasks found
        return None

    def auto_complete_parent(self, list_key: str, item_key: str) -> bool:
        """
        Automatically completes a parent task if all its subtasks are now completed.
        This is typically called after a subtask's status is updated to 'completed'.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item that was just completed (the subtask).

        Returns:
            True if the parent task was auto-completed, False otherwise.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check if this item has a parent
        if not db_item.parent_item_id:
            return False  # This is a root item, no parent to complete

        # Get parent
        parent_item = self.db.get_item_by_id(db_item.parent_item_id)
        if not parent_item or parent_item.status == "completed":
            return False  # Parent doesn't exist or is already completed

        # Check if all children of parent are completed
        if self.db.check_all_children_completed(parent_item.id):
            # Auto-complete the parent
            self.db.update_item(
                parent_item.id,
                {"status": "completed", "completed_at": datetime.now(timezone.utc)},
            )

            # Record history
            self._record_history(
                item_id=parent_item.id,
                list_id=db_list.id,
                action=HistoryAction.COMPLETED,
                old_value={"status": parent_item.status},
                new_value={"status": "completed", "auto_completed": True},
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

        # Prevent circular references
        if parent_item.id == db_item.id:
            raise ValueError("Cannot make item a subitem of itself")

        # Check if new parent is not already a descendant of this item
        parent_path = self.db.get_item_path(parent_item.id)
        if any(path_item.id == db_item.id for path_item in parent_path):
            raise ValueError("Cannot create circular reference in subitem hierarchy")

        # Update the item to have the new parent
        old_parent_id = db_item.parent_item_id
        updated_item = self.db.update_item(
            db_item.id, {"parent_item_id": parent_item.id}
        )

        # Record history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action=HistoryAction.UPDATED,
            old_value={"parent_item_id": old_parent_id},
            new_value={"parent_item_id": parent_item.id},
        )

        return self._db_to_model(updated_item, TodoItem)

    def can_complete_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """
        Check if an item can be marked as complete (i.e., it has no pending subtasks).

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to check.

        Returns:
            A dictionary containing a boolean 'can_complete' flag and other details about its subtasks.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check for pending children
        has_pending = self.db.has_pending_children(db_item.id)
        children = self.db.get_item_children(db_item.id)
        pending_children = [
            child for child in children if child.status in ["pending", "in_progress"]
        ]

        return {
            "can_complete": not has_pending,
            "has_subtasks": len(children) > 0,
            "pending_subtasks": len(pending_children),
            "pending_subtask_keys": [child.item_key for child in pending_children],
            "total_subtasks": len(children),
        }

    # ===== CROSS-LIST DEPENDENCIES METHODS (Phase 2) =====

        return self._db_to_model(db_dependency, ItemDependency)

    def remove_item_dependency(
        self,
        dependent_list: str,
        dependent_item: str,
        required_list: str,
        required_item: str,
    ) -> bool:
        """Remove a specific dependency between two items.

        Args:
            dependent_list: The list key of the formerly blocked item.
            dependent_item: The item key of the formerly blocked item.
            required_list: The list key of the item that was required.
            required_item: The item key of the item that was required.

        Returns:
            True if the dependency was successfully removed, False otherwise.

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
            # Record history
            self._record_history(
                item_id=dependent_db_item.id,
                list_id=dependent_db_list.id,
                action=HistoryAction.UPDATED,
                new_value={
                    "dependency_removed": f"no longer depends on {required_list}:{required_item}"
                },
            )

        return success

    def get_item_blockers(self, list_key: str, item_key: str) -> List["TodoItem"]:
        """Get a list of all items that are currently blocking a specific item.

        An item is a blocker if it is a required dependency and is not yet 'completed'.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to check for blockers.

        Returns:
            A list of TodoItem objects that are blocking the specified item.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get blocking items
        blockers = self.db.get_item_blockers(db_item.id)
        return [self._db_to_model(blocker, TodoItem) for blocker in blockers]

    def get_items_blocked_by(self, list_key: str, item_key: str) -> List["TodoItem"]:
        """Get a list of all items that are dependent on (blocked by) a specific item.

        Args:
            list_key: The key of the list containing the blocking item.
            item_key: The key of the item to check.

        Returns:
            A list of TodoItem objects that depend on the specified item.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Get blocked items
        blocked = self.db.get_items_blocked_by(db_item.id)
        return [self._db_to_model(item, TodoItem) for item in blocked]

    def is_item_blocked(self, list_key: str, item_key: str) -> bool:
        """Check if an item is currently blocked by any incomplete dependencies.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to check.

        Returns:
            True if the item is blocked, False otherwise.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        return self.db.is_item_blocked(db_item.id)

    def can_start_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """
        Comprehensive check to see if a task can be started.

        This combines checks for both cross-list dependencies and pending subtasks.

        Args:
            list_key: The key of the list containing the item.
            item_key: The key of the item to check.

        Returns:
            A dictionary with a 'can_start' boolean and detailed reasons if it cannot.

        Raises:
            ValueError: If the list or item is not found.
        """
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Check if item is already completed or in progress
        if db_item.status in ["completed", "in_progress"]:
            return {
                "can_start": False,
                "reason": f"Item is already {db_item.status}",
                "blocked_by_dependencies": False,
                "blocked_by_subtasks": False,
                "blockers": [],
                "pending_subtasks": [],
            }

        # Check cross-list dependencies
        blockers = self.db.get_item_blockers(db_item.id)
        is_blocked_by_deps = len(blockers) > 0

        # Check subtasks (if this is a parent with pending subtasks)
        pending_children = []
        if db_item.parent_item_id is None:  # Only check for root items
            children = self.db.get_item_children(db_item.id)
            pending_children = [
                child
                for child in children
                if child.status in ["pending", "in_progress"]
            ]

        is_blocked_by_subtasks = len(pending_children) > 0

        can_start = not (is_blocked_by_deps or is_blocked_by_subtasks)

        return {
            "can_start": can_start,
            "blocked_by_dependencies": is_blocked_by_deps,
            "blocked_by_subtasks": is_blocked_by_subtasks,
            "blockers": [
                {"id": b.id, "key": b.item_key, "content": b.content} for b in blockers
            ],
            "pending_subtasks": [
                {"id": s.id, "key": s.item_key, "content": s.content}
                for s in pending_children
            ],
            "reason": self._get_blocking_reason(
                is_blocked_by_deps, is_blocked_by_subtasks, blockers, pending_children
            ),
        }

    def get_cross_list_progress(self, project_key: str) -> Dict[str, Any]:
        """Get aggregated progress - returns empty since list relations were removed.

        Args:
            project_key: The project key (no longer used since relations were removed).

        Returns:
            A dictionary containing empty progress statistics.
        """
        # Since list relations were removed, return empty project structure
        return {
            "project_key": project_key,
            "lists": [],
            "total_items": 0,
            "total_completed": 0,
            "overall_progress": 0.0,
            "dependencies": [],
        }


    def get_dependency_graph(self, project_key: str) -> Dict[str, Any]:
        """Get a dependency graph - returns empty since list relations were removed.

        Args:
            project_key: The project key (no longer used since relations were removed).

        Returns:
            A dictionary representing empty dependency graph.
        """
        return {"lists": [], "dependencies": []}



    # ===== LIST TAG MANAGEMENT METHODS =====

    def get_tag(self, tag_identifier: Union[int, str]) -> Optional[ListTag]:
        """Get a specific tag by its ID or name.

        Args:
            tag_identifier: The ID (integer) or name (string) of the tag to retrieve.

        Returns:
            A ListTag object if found, otherwise None.
        """
        if isinstance(tag_identifier, int):
            db_tag = self.db.get_tag_by_id(tag_identifier)
        else:
            db_tag = self.db.get_tag_by_name(tag_identifier)

        if db_tag:
            return self._db_to_model(db_tag, ListTag)
        return None

    def get_all_tags(self) -> List[ListTag]:
        """Get all available tags with their dynamically assigned colors.

        The color of each tag is determined by its alphabetical position among all existing tags,
        ensuring a consistent and visually distinct color scheme.

        Returns:
            A list of ListTag objects, sorted alphabetically by name.
        """
        db_tags = self.db.get_all_tags()
        tags = []
        for tag in db_tags:
            # Convert to model
            tag_model = self._db_to_model(tag, ListTag)
            # Override with dynamic color
            tag_model.color = self._get_tag_color_by_index(tag_model.name)
            tags.append(tag_model)
        return sorted(tags, key=lambda t: t.name)

    def delete_tag(self, tag_identifier: Union[int, str]) -> bool:
        """Delete a tag by its ID or name.

        This will also remove all assignments of this tag from any lists.

        Args:
            tag_identifier: The ID (integer) or name (string) of the tag to delete.

        Returns:
            True if the tag was deleted, False if it was not found.
        """
        # First get the tag to get its ID
        tag = self.get_tag(tag_identifier)
        if not tag:
            return False

        # Delete tag from database (will also delete all assignments)
        return self.db.delete_tag(tag.id)

    def add_tag_to_list(self, list_key: str, tag_name: str) -> ListTagAssignment:
        """Assign a tag to a list.

        If the tag does not already exist, it will be created automatically.

        Args:
            list_key: The key of the list to tag.
            tag_name: The name of the tag to assign.

        Returns:
            The created ListTagAssignment object.

        Raises:
            ValueError: If the list is not found or if creating a new tag fails (e.g., max tag limit reached).
        """
        # Get list
        list_obj = self.get_list(list_key)
        if not list_obj:
            raise ValueError(f"List '{list_key}' not found")

        # Get or create tag
        tag = self.get_tag(tag_name)
        if not tag:
            tag = self.create_tag(tag_name)

        # Create assignment
        db_assignment = self.db.add_tag_to_list(list_obj.id, tag.id)

        # Convert to Pydantic model and return
        return self._db_to_model(db_assignment, ListTagAssignment)

    def remove_tag_from_list(self, list_key: str, tag_name: str) -> bool:
        """Remove a tag assignment from a list.

        Args:
            list_key: The key of the list.
            tag_name: The name of the tag to remove.

        Returns:
            True if the assignment was removed, False if the list, tag, or assignment did not exist.
        """
        # Get list
        list_obj = self.get_list(list_key)
        if not list_obj:
            return False

        # Get tag
        tag = self.get_tag(tag_name)
        if not tag:
            return False

        # Remove assignment
        return self.db.remove_tag_from_list(list_obj.id, tag.id)

    def get_tags_for_list(self, list_key: str) -> List[ListTag]:
        """Get all tags assigned to a specific list, with their dynamic colors.

        Args:
            list_key: The key of the list.

        Returns:
            A list of ListTag objects assigned to the list, sorted alphabetically by name.
            Returns an empty list if the list is not found or has no tags.
        """
        # Get list
        list_obj = self.get_list(list_key)
        if not list_obj:
            return []

        # Get tags for list
        db_tags = self.db.get_tags_for_list(list_obj.id)
        tags = []
        for tag in db_tags:
            # Convert to model
            tag_model = self._db_to_model(tag, ListTag)
            # Override with dynamic color
            tag_model.color = self._get_tag_color_by_index(tag_model.name)
            tags.append(tag_model)
        return sorted(tags, key=lambda t: t.name)

    def get_lists_by_tags(self, tag_names: List[str]) -> List[TodoList]:
        """Get all lists that are associated with any of the specified tags.

        Args:
            tag_names: A list of tag names to filter by.

        Returns:
            A list of TodoList objects that have at least one of the specified tags.
        """
        if not tag_names:
            return []

        # Get lists from database
        db_lists = self.db.get_lists_by_tags(tag_names)
        return [self._db_to_model(list_obj, TodoList) for list_obj in db_lists]
