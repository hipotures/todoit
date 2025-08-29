"""
TODOIT MCP - List Operations Mixin
Collection of list management methods for TodoManager
"""

import re
from typing import Any, Dict, List, Optional, Union

from .models import ListTag, ListTagAssignment, TodoList


class ListsMixin:
    """Mixin containing list management methods for TodoManager"""

    def create_list(
        self,
        list_key: str,
        title: str,
        items: Optional[List[str]] = None,
        list_type: str = "sequential",
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> TodoList:
        """1. Creates a new TODO list with optional tasks and tags

        Args:
            list_key: Unique identifier for the list
            title: Display title for the list
            items: Optional list of initial todo items to add
            list_type: List organization type, defaults to "sequential"
            metadata: Optional dictionary of custom metadata for the list
            tags: Optional list of tag names to assign to the list (tags must already exist)
        """
        # Validate list key - must contain at least one letter a-z to distinguish from IDs
        if not re.search(r"[a-zA-Z]", list_key):
            raise ValueError(
                f"List key '{list_key}' must contain at least one letter (a-z) to distinguish from numeric IDs"
            )

        # Check if the list already exists
        existing = self.db.get_list_by_key(list_key)
        if existing:
            raise ValueError(f"List '{list_key}' already exists")

        # Validate that all provided tags exist
        if tags:
            for tag_name in tags:
                tag_name = tag_name.lower()
                if not self.db.get_tag_by_name(tag_name):
                    raise ValueError(
                        f"Tag '{tag_name}' does not exist. Create it first using create_tag."
                    )

        # Prepare list data
        list_data = {
            "list_key": list_key,
            "title": title,
            "list_type": list_type,
            "meta_data": metadata or {},
        }

        # Create the list
        db_list = self.db.create_list(list_data)

        # Add tasks if provided (OPTIMIZED: bulk insert in single transaction)
        if items:
            items_data = []
            for position, content in enumerate(items):
                item_key = f"item_{position + 1}"
                item_data = {
                    "list_id": db_list.id,
                    "item_key": item_key,
                    "content": content,
                    "position": position + 1,
                    "meta_data": {},
                }
                items_data.append(item_data)

            # Bulk create all items in single transaction
            self.db.create_items_bulk(items_data)

        # Apply tags if provided
        if tags:
            for tag_name in tags:
                tag_name = tag_name.lower()
                # Get the tag (we already validated it exists)
                db_tag = self.db.get_tag_by_name(tag_name)
                # Create tag assignment
                self.db.add_tag_to_list(db_list.id, db_tag.id)

        # Auto-tag with FORCE_TAGS if set (environment isolation)
        if self.force_tags:
            for tag_name in self.force_tags:
                # Get or create the tag
                db_tag = self.db.get_tag_by_name(tag_name)
                if not db_tag:
                    # Auto-create tag if it doesn't exist
                    tag_data = {"name": tag_name, "color": self._get_next_available_color()}
                    db_tag = self.db.create_tag(tag_data)
                
                # Create tag assignment (add_tag_to_list handles duplicates)
                self.db.add_tag_to_list(db_list.id, db_tag.id)

        # Save to history
        self._record_history(
            list_id=db_list.id,
            action="created",
            new_value={"list_key": list_key, "title": title},
        )

        return self._db_to_model(db_list, TodoList)

    def get_list(self, key: Union[str, int]) -> Optional[TodoList]:
        """2. Gets a list by key or ID"""
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if db_list:
            # Check force_tags access
            if not self._check_force_tags_access(db_list.list_key):
                return None  # Access denied
            return self._db_to_model(db_list, TodoList)
        return None

    def delete_list(self, key: Union[str, int]) -> bool:
        """3. Deletes a list and all its items"""
        # Get the list first to get its title for history
        db_list = None
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            return False

        # FORCE_TAGS validation - if enabled, must be allowed to delete
        if not self._check_force_tags_access(db_list.list_key):
            # List is not in force_tags scope - cannot delete
            return False

        # Record deletion in history before deleting
        self._record_history(
            list_id=db_list.id,
            action="deleted",
            old_value={"list_key": db_list.list_key, "title": db_list.title},
        )

        # Delete the list
        success = self.db.delete_list(db_list.id)

        return success

    def list_all(
        self,
        limit: Optional[int] = None,
        include_archived: bool = False,
        tags: Optional[List[str]] = None,
    ) -> List[TodoList]:
        """4. Lists all TODO lists with optional filtering

        Args:
            limit: Maximum number of lists to return
            include_archived: Whether to include archived lists
            tags: Filter by lists containing ANY of these tags
        """
        # Get lists from database based on filtering logic
        if self.force_tags:
            # FORCE_TAGS uses AND logic - list must have ALL force_tags
            db_lists = self.db.get_lists_by_tags_all(self.force_tags)
        elif tags:
            # Regular tag filtering uses OR logic - list needs ANY of these tags
            db_lists = self.db.get_lists_by_tags(tags)
        else:
            # No filtering - get all lists
            db_lists = self.db.get_all_lists(limit)

        # Apply limit if specified and not already applied
        if limit and len(db_lists) > limit:
            db_lists = db_lists[:limit]

        # Filter out archived lists if not requested
        if not include_archived:
            db_lists = [lst for lst in db_lists if lst.status != "archived"]

        # Convert to Pydantic models
        lists = []
        for db_list in db_lists:
            lists.append(self._db_to_model(db_list, TodoList))

        return lists

    def add_tag_to_list(self, list_key: str, tag_name: str) -> ListTagAssignment:
        """Add a tag to a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # FORCE_TAGS validation - block modification of lists that don't have access
        if self.force_tags and not self._check_force_tags_access(list_key):
            raise ValueError(f"Access denied: List '{list_key}' does not have required force tags: {', '.join(self.force_tags)}")

        # Get or create the tag
        tag_name = tag_name.lower()
        db_tag = self.db.get_tag_by_name(tag_name)
        if not db_tag:
            # Auto-create tag if it doesn't exist
            tag_data = {"name": tag_name, "color": self._get_next_available_color()}
            db_tag = self.db.create_tag(tag_data)

        # Check if assignment already exists
        existing_tags = self.db.get_tags_for_list(db_list.id)
        existing_tag_names = [tag.name for tag in existing_tags]
        if tag_name in existing_tag_names:
            raise ValueError(f"List '{list_key}' already has tag '{tag_name}'")

        # Create assignment
        db_assignment = self.db.add_tag_to_list(db_list.id, db_tag.id)

        return self._db_to_model(db_assignment, ListTagAssignment)

    def remove_tag_from_list(self, list_key: str, tag_name: str) -> bool:
        """Remove a tag from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # FORCE_TAGS validation - block removal of force tags or modification of inaccessible lists
        if self.force_tags:
            if not self._check_force_tags_access(list_key):
                raise ValueError(f"Access denied: List '{list_key}' does not have required force tags: {', '.join(self.force_tags)}")
            if tag_name.lower() in self.force_tags:
                raise ValueError(f"Cannot remove force tag '{tag_name}' from list '{list_key}' - required by environment isolation")

        # Get the tag
        db_tag = self.db.get_tag_by_name(tag_name.lower())
        if not db_tag:
            return False  # Tag doesn't exist

        # Remove assignment
        return self.db.remove_tag_from_list(db_list.id, db_tag.id)

    def get_tags_for_list(self, list_key: str) -> List[ListTag]:
        """Get all tags for a specific list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get tag assignments for this list
        assignments = self.db.get_list_tags(db_list.id)

        # Extract tags and sort alphabetically
        tags = []
        for assignment in assignments:
            tag = self._db_to_model(assignment.tag, ListTag)
            # Assign dynamic color based on position
            tag.color = self._get_tag_color_by_index(tag.name)
            tags.append(tag)

        # Sort by name
        tags.sort(key=lambda t: t.name)
        return tags

    def get_lists_by_tags(self, tag_names: List[str]) -> List[TodoList]:
        """Get lists that have ANY of the specified tags"""
        # Convert to lowercase for consistency
        tag_names = [name.lower() for name in tag_names]

        # Get lists from database
        db_lists = self.db.get_lists_by_tags(tag_names)

        # Convert to Pydantic models
        lists = []
        for db_list in db_lists:
            lists.append(self._db_to_model(db_list, TodoList))

        return lists
