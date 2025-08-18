"""
TODOIT MCP - Helper Methods Mixin
Collection of helper methods for TodoManager
"""

from typing import List
from datetime import datetime, timezone
from sqlalchemy import text

from .database import TodoItemDB


class HelpersMixin:
    """Mixin containing helper methods for TodoManager"""

    def _sync_parent_status(
        self, parent_item_id: int, session=None, visited=None
    ) -> bool:
        """
        Synchronize parent status based on children statuses with optimal performance

        Args:
            parent_item_id: ID of parent item to synchronize
            session: Optional SQLAlchemy session (creates new if None)
            visited: Set of visited item IDs to prevent circular dependencies

        Returns:
            True if status was changed, False otherwise
        """
        if visited is None:
            visited = set()

        if parent_item_id in visited:
            return False  # Circular dependency detected

        visited.add(parent_item_id)

        # Use provided session or create new one
        if session:
            return self._sync_parent_status_with_session(
                parent_item_id, session, visited
            )
        else:
            with self.db.get_session() as new_session:
                return self._sync_parent_status_with_session(
                    parent_item_id, new_session, visited
                )

    def _sync_parent_status_with_session(
        self, parent_item_id: int, session, visited: set
    ) -> bool:
        """Internal method to sync parent status within existing session"""

        # Get children status summary
        summary = self.db.get_children_status_summary(parent_item_id, session)

        if not summary:
            return False  # No children, no sync needed

        # Calculate new parent status based on rules:
        # 1. Any failed -> failed
        # 2. All pending -> pending
        # 3. All completed -> completed
        # 4. Any other combination -> in_progress
        if summary["failed"] > 0:
            new_status = "failed"
        elif summary["pending"] == summary["total"]:
            new_status = "pending"
        elif summary["completed"] == summary["total"]:
            new_status = "completed"
        else:
            new_status = "in_progress"

        # Get current parent status
        result = session.execute(
            text("SELECT status, parent_item_id FROM todo_items WHERE id = :id"),
            {"id": parent_item_id},
        ).fetchone()

        if not result:
            return False

        current_status = result[0]
        grandparent_id = result[1]

        # Only update if status actually changed
        if current_status != new_status:
            session.execute(
                text(
                    "UPDATE todo_items SET status = :status, updated_at = :updated_at WHERE id = :id"
                ),
                {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc),
                    "id": parent_item_id,
                },
            )

            # Recursively sync grandparent if exists and not visited
            if grandparent_id and grandparent_id not in visited:
                self._sync_parent_status_with_session(grandparent_id, session, visited)

            return True

        return False

    def _get_blocking_reason(
        self,
        blocked_by_deps: bool,
        blocked_by_subtasks: bool,
        blockers: List,
        pending_subtasks: List,
    ) -> str:
        """Generate human-readable blocking reason"""
        reasons = []

        if blocked_by_deps:
            blocker_names = [f"{b.item_key}" for b in blockers[:3]]  # Show first 3
            if len(blockers) > 3:
                blocker_names.append(f"and {len(blockers) - 3} more")
            reasons.append(f"blocked by dependencies: {', '.join(blocker_names)}")

        if blocked_by_subtasks:
            subtask_names = [
                f"{s.item_key}" for s in pending_subtasks[:3]
            ]  # Show first 3
            if len(pending_subtasks) > 3:
                subtask_names.append(f"and {len(pending_subtasks) - 3} more")
            reasons.append(f"has pending subtasks: {', '.join(subtask_names)}")

        if not reasons:
            return "ready to start"

        return "; ".join(reasons)

    def _get_all_subtasks_recursive(self, item_id: int) -> List:
        """Get all subtasks of an item recursively"""
        all_subtasks = []
        children = self.db.get_item_children(item_id)

        for child in children:
            all_subtasks.append(child)
            # Get subtasks of this child recursively
            all_subtasks.extend(self._get_all_subtasks_recursive(child.id))

        return all_subtasks

    def _get_item_and_subtasks_recursive(self, session, item_id: int) -> List:
        """Helper method to get item and all its subtasks recursively"""
        items = []

        # Get the item itself
        item = session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
        if item:
            items.append(item)

            # Get all children recursively
            children = (
                session.query(TodoItemDB)
                .filter(TodoItemDB.parent_item_id == item_id)
                .all()
            )
            for child in children:
                items.extend(self._get_item_and_subtasks_recursive(session, child.id))

        return items

    def _get_item_depth(self, session, item_id: int) -> int:
        """Helper method to get the depth of an item in the hierarchy"""
        depth = 0
        current_id = item_id

        while current_id:
            item = session.query(TodoItemDB).filter(TodoItemDB.id == current_id).first()
            if not item or not item.parent_item_id:
                break
            current_id = item.parent_item_id
            depth += 1

        return depth

    def _get_tag_color_by_index(self, tag_name: str) -> str:
        """Get tag color based on its position in sorted tag list (dynamic assignment)"""
        available_colors = [
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "cyan",
            "magenta",
            "pink",
            "grey",
            "bright_green",
            "bright_red",
        ]

        # Get all existing tags from database (avoid recursion)
        db_tags = self.db.get_all_tags()
        sorted_tag_names = sorted([tag.name for tag in db_tags])

        # Find position of this tag in sorted list
        try:
            tag_index = sorted_tag_names.index(tag_name)
        except ValueError:
            # Tag not found, return default
            return available_colors[0]

        # Return color by index (cycle if more than 12 tags)
        return available_colors[tag_index % len(available_colors)]

    def _get_next_available_color(self) -> str:
        """Get next available color for new tags (checks 12 tag limit)"""
        available_colors = [
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "cyan",
            "magenta",
            "pink",
            "grey",
            "bright_green",
            "bright_red",
        ]

        # Check if we exceed the 12 color limit
        db_tags = self.db.get_all_tags()
        if len(db_tags) >= len(available_colors):
            raise ValueError(
                f"Maximum number of tags reached ({len(available_colors)}). Cannot create more tags with distinct colors."
            )

        # Return placeholder - actual color will be determined dynamically
        return available_colors[0]