"""
TODOIT MCP - List Operations Mixin
Collection of list management methods for TodoManager
"""

import re
from typing import List, Optional, Dict, Any, Union

from .models import TodoList, ListTag, ListTagAssignment


class ListsMixin:
    """Mixin containing list management methods for TodoManager"""

    def create_list(
        self,
        list_key: str,
        title: str,
        items: Optional[List[str]] = None,
        list_type: str = "sequential",
        metadata: Optional[Dict] = None,
    ) -> TodoList:
        """1. Creates a new TODO list with optional tasks"""
        # Validate list key - must contain at least one letter a-z to distinguish from IDs
        if not re.search(r"[a-zA-Z]", list_key):
            raise ValueError(
                f"List key '{list_key}' must contain at least one letter (a-z) to distinguish from numeric IDs"
            )

        # Check if the list already exists
        existing = self.db.get_list_by_key(list_key)
        if existing:
            raise ValueError(f"List '{list_key}' already exists")

        # Prepare list data
        list_data = {
            "list_key": list_key,
            "title": title,
            "list_type": list_type,
            "meta_data": metadata or {},
        }

        # Create the list
        db_list = self.db.create_list(list_data)

        # Add tasks if provided
        if items:
            for position, content in enumerate(items):
                item_key = f"item_{position + 1}"
                item_data = {
                    "list_id": db_list.id,
                    "item_key": item_key,
                    "content": content,
                    "position": position + 1,
                    "meta_data": {},
                }
                self.db.create_item(item_data)

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
        if self.force_tags:
            # Get all tags for this list
            list_tags = self.db.get_list_tags(db_list.id)
            list_tag_names = [assignment.tag.name for assignment in list_tags]

            # Check if the list has any of the required force_tags
            has_force_tag = any(tag in list_tag_names for tag in self.force_tags)
            if not has_force_tag:
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
        # FORCE_TAGS filtering
        if self.force_tags:
            # Override tags parameter with force_tags
            tags = self.force_tags

        # Get lists from database
        if tags:
            db_lists = self.db.get_lists_by_tags(tags, limit, include_archived)
        else:
            db_lists = self.db.get_all_lists(limit)
            
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

        # Get or create the tag
        tag_name = tag_name.lower()
        db_tag = self.db.get_tag_by_name(tag_name)
        if not db_tag:
            # Auto-create tag if it doesn't exist
            tag_data = {"name": tag_name, "color": self._get_next_available_color()}
            db_tag = self.db.create_tag(tag_data)

        # Check if assignment already exists
        existing = self.db.get_list_tag_assignment(db_list.id, db_tag.id)
        if existing:
            raise ValueError(f"List '{list_key}' already has tag '{tag_name}'")

        # Create assignment
        assignment_data = {"list_id": db_list.id, "tag_id": db_tag.id}
        db_assignment = self.db.create_list_tag_assignment(assignment_data)

        return self._db_to_model(db_assignment, ListTagAssignment)

    def remove_tag_from_list(self, list_key: str, tag_name: str) -> bool:
        """Remove a tag from a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get the tag
        db_tag = self.db.get_tag_by_name(tag_name.lower())
        if not db_tag:
            return False  # Tag doesn't exist

        # Remove assignment
        return self.db.delete_list_tag_assignment(db_list.id, db_tag.id)

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