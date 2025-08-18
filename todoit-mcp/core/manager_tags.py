"""
TODOIT MCP - Tag Operations Mixin
Collection of tag management methods for TodoManager
"""

from typing import List, Optional, Union

from .models import ListTag


class TagsMixin:
    """Mixin containing tag management methods for TodoManager"""

    def create_tag(self, name: str, color: str = None) -> ListTag:
        """Create a new global tag.

        Tag colors are assigned dynamically based on the alphabetical order of all tags.
        A maximum of 12 tags is supported due to the fixed color palette.

        Args:
            name: The name for the new tag (will be converted to lowercase).
            color: A specific color to assign. If None, a color will be assigned automatically.
                   This is not recommended as dynamic colors will override it.

        Returns:
            The created ListTag object.

        Raises:
            ValueError: If the tag name already exists or if the maximum number of tags (12) has been reached.
        """
        # Check if tag already exists
        existing_tag = self.db.get_tag_by_name(name)
        if existing_tag:
            raise ValueError(f"Tag '{name}' already exists")

        # Auto-assign color if not provided
        if color is None:
            color = self._get_next_available_color()

        # Create tag data
        tag_data = {"name": name.lower(), "color": color.lower()}

        # Create tag in database
        db_tag = self.db.create_tag(tag_data)

        # Convert to Pydantic model and return
        return self._db_to_model(db_tag, ListTag)

    def get_tag(self, tag_identifier: Union[int, str]) -> Optional[ListTag]:
        """Get a specific tag by its ID or name."""
        if isinstance(tag_identifier, int):
            db_tag = self.db.get_tag_by_id(tag_identifier)
        else:
            db_tag = self.db.get_tag_by_name(tag_identifier)

        if db_tag:
            return self._db_to_model(db_tag, ListTag)
        return None

    def get_all_tags(self) -> List[ListTag]:
        """Get all available tags with their dynamically assigned colors."""
        db_tags = self.db.get_all_tags()
        tags = []

        # Sort tags alphabetically for consistent color assignment
        sorted_tags = sorted(db_tags, key=lambda t: t.name)

        for db_tag in sorted_tags:
            tag = self._db_to_model(db_tag, ListTag)
            # Assign color based on alphabetical position
            tag.color = self._get_tag_color_by_index(tag.name)
            tags.append(tag)

        return tags

    def delete_tag(self, tag_identifier: Union[int, str]) -> bool:
        """Delete a tag by its ID or name."""
        # Get the tag first
        if isinstance(tag_identifier, int):
            db_tag = self.db.get_tag_by_id(tag_identifier)
        else:
            db_tag = self.db.get_tag_by_name(tag_identifier)

        if not db_tag:
            return False

        # Delete the tag (this will also delete all list assignments due to CASCADE)
        return self.db.delete_tag(db_tag.id)