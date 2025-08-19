"""
TODOIT MCP - Import/Export Operations Mixin
Collection of I/O methods for TodoManager
"""

import os
from typing import Dict, List, Optional, Set

from .models import TodoList
from .security import SecureFileHandler, SecurityError


class IOMixin:
    """Mixin containing import/export methods for TodoManager"""

    def import_from_markdown(self, file_path: str, list_key: str, title: str = None, 
                           allowed_base_dirs: Optional[Set[str]] = None) -> TodoList:
        """
        Create a new list by importing items from a Markdown file
        
        Args:
            file_path: Path to markdown file to import
            list_key: Key for the new list
            title: Title for the new list (optional)
            allowed_base_dirs: Set of allowed base directories for security (optional)
            
        Returns:
            Created TodoList object
            
        Raises:
            SecurityError: If file path is malicious or violates security constraints
            ValueError: If list_key already exists or other validation errors
        """
        try:
            # Secure file reading with full validation
            content = SecureFileHandler.secure_file_read(file_path, allowed_base_dirs)
        except SecurityError as e:
            raise ValueError(f"Security error reading file: {e}") from e

        # Parse markdown content to extract items
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for list items (lines starting with -, *, or +)
            if line.startswith(('- ', '* ', '+ ')):
                # Remove the list marker and add to items
                item_text = line[2:].strip()
                if item_text:
                    items.append(item_text)

        # Use filename as title if not provided
        if title is None:
            title = os.path.splitext(os.path.basename(file_path))[0]

        # Create the list with parsed items
        return self.create_list(list_key, title, items)

    def export_to_markdown(self, list_key: str, file_path: str, 
                         allowed_base_dirs: Optional[Set[str]] = None) -> None:
        """
        Export list items to a Markdown file
        
        Args:
            list_key: Key of the list to export
            file_path: Path where to write the markdown file
            allowed_base_dirs: Set of allowed base directories for security (optional)
            
        Raises:
            SecurityError: If file path is malicious or violates security constraints
            ValueError: If list doesn't exist or other validation errors
        """
        # Get the list
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"List '{list_key}' does not exist")

        # Get all items in the list
        items = self.get_list_items(list_key)

        # Generate markdown content
        markdown_lines = [
            f"# {todo_list.title}",
            "",
        ]

        if todo_list.description:
            markdown_lines.extend([
                todo_list.description,
                "",
            ])

        # Add items
        for item in items:
            status_marker = ""
            if item.status == "completed":
                status_marker = "[x] "
            elif item.status in ["pending", "in_progress"]:
                status_marker = "[ ] "
            elif item.status == "failed":
                status_marker = "[!] "
            
            # Determine indentation based on hierarchy
            indent = "  " * (getattr(item, 'depth', 0) if hasattr(item, 'depth') else 0)
            markdown_lines.append(f"{indent}- {status_marker}{item.content}")

        # Write to file securely
        markdown_content = "\n".join(markdown_lines)
        
        try:
            # Use secure file writing with validation
            SecureFileHandler.secure_file_write(file_path, markdown_content, allowed_base_dirs)
        except SecurityError as e:
            raise ValueError(f"Security error writing file: {e}") from e