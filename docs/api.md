# Programmatic API (TodoManager)

The `TodoManager` class in `core/manager.py` provides a programmatic API for managing TODO lists and items. It encapsulates all business logic and interacts with the database layer.

## Key Methods

*   `create_list()`: Creates a new TODO list.
*   `get_list()`: Retrieves a TODO list by key or ID.
*   `delete_list()`: Deletes a TODO list.
*   `list_all()`: Lists all TODO lists.
*   `add_item()`: Adds an item to a TODO list.
*   `update_item_status()`: Updates the status of an item.
*   `get_next_pending()`: Retrieves the next pending item from a list.
*   `get_progress()`: Retrieves progress statistics for a list.
*   `import_from_markdown()`: Imports TODO lists from a Markdown file.
*   `export_to_markdown()`: Exports a TODO list to a Markdown file.

For a complete list of methods and their parameters, please refer to the source code in `core/manager.py`.
