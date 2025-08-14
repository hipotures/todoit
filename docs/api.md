# Programmatic API (TodoManager)

The `TodoManager` class in `core/manager.py` provides the core programmatic API for interacting with the TODOIT system. It encapsulates all business logic and interacts with the database layer.

This document serves as a reference for the main methods available in the `TodoManager` class.

## Core Object Management

### `create_list`
Creates a new TODO list.

**Parameters:**
- `list_key: str`: A unique key for the list.
- `title: str`: A human-readable title.
- `items: Optional[List[str]]`: A list of strings to create as initial tasks.
- `list_type: str`: The list's ordering and behavior strategy (`"sequential"`, `"parallel"`, `"hierarchical"`).
- `metadata: Optional[Dict]`: A dictionary for custom metadata.

**Returns:** `TodoList` – The created list object.

[Source](../todoit-mcp/core/manager.py)

### `add_item`
Adds a new task to a list.

**Parameters:**
- `list_key: str`: The key of the target list.
- `item_key: str`: A unique key for the item within the list.
- `content: str`: The task's description.
- `position: Optional[int]`: The insertion position. If omitted, it's added to the end.
- `metadata: Optional[Dict]`: A dictionary for custom metadata.

**Returns:** `TodoItem` – The created item object.

[Source](../todoit-mcp/core/manager.py)

### `update_item_status`
Updates the status of a task.

> ⚠️ **Automatic Status Synchronization**: Tasks with subtasks cannot have manually changed status. Their status is automatically calculated from subtask statuses. See [Status Synchronization](#automatic-status-synchronization) for details.

**Parameters:**
- `list_key: str`: The key of the list containing the item.
- `item_key: str`: The key of the item to update.
- `status: Optional[str]`: The new status (e.g., `"pending"`, `"in_progress"`, `"completed"`, `"failed"`).
- `completion_states: Optional[Dict[str, Any]]`: Custom key-value pairs for completion metadata.

**Returns:** `TodoItem` – The updated item object.

**Raises:** `ValueError` if attempting to manually change status of a task with subtasks.

[Source](../todoit-mcp/core/manager.py)

---

## Subtask and Hierarchy Management

### `add_subtask`
Adds a new subtask to an existing parent task.

> 🔄 **Automatic Sync**: Adding a subtask triggers automatic parent status synchronization.

**Parameters:**
- `list_key: str`: The key of the list.
- `parent_key: str`: The key of the parent task.
- `subtask_key: str`: A unique key for the new subtask.
- `content: str`: The content of the subtask.
- `metadata: Optional[Dict]`: Custom metadata.

**Returns:** `TodoItem` – The created subtask object.

[Source](../todoit-mcp/core/manager.py)

### `get_subtasks`
Retrieves all direct subtasks for a parent task.

**Parameters:**
- `list_key: str`: The key of the list.
- `parent_key: str`: The key of the parent task.

**Returns:** `List[TodoItem]` – A list of subtask objects.

[Source](../todoit-mcp/core/manager.py)

### `get_item_hierarchy`
Retrieves the full hierarchy for an item, including all its subtasks recursively.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the root item of the hierarchy.

**Returns:** `Dict[str, Any]` – A nested dictionary representing the hierarchy.

[Source](../todoit-mcp/core/manager.py)

---

## Automatic Status Synchronization

*Added in version 1.20.0*

TODOIT automatically synchronizes the status of parent tasks based on their subtasks. This feature ensures hierarchical task consistency and prevents manual status conflicts.

### Core Rules

**Status Calculation Priority:**
1. **`failed`** - If any subtask is failed → parent becomes `failed`
2. **`pending`** - If all subtasks are pending → parent becomes `pending`  
3. **`completed`** - If all subtasks are completed → parent becomes `completed`
4. **`in_progress`** - Any other combination → parent becomes `in_progress`

**Manual Update Protection:**
- Tasks with subtasks **cannot** have manually changed status
- Attempting `update_item_status()` on parent tasks raises `ValueError`
- Use subtask status changes to control parent status instead

### Automatic Triggers

Status synchronization occurs automatically on:
- **`add_subtask()`** - Adding first subtask to parent
- **`update_item_status()`** - Changing any subtask status  
- **`delete_item()`** - Removing subtasks from parent

### Recursive Propagation

- Changes propagate **upward** through entire hierarchy
- Circular dependency protection with visited-set mechanism
- Maximum 10 levels of recursion for safety
- All operations are **atomic** within database transactions

### Performance

- **Single SQL query** per hierarchy level using covering indexes
- **O(1) lookup** with `idx_todo_items_parent_status` index
- **Bulk aggregation** using `get_children_status_summary()`
- Tested with 100+ subtasks completing in <5 seconds

### Usage Examples

```python
# Create parent task
manager.add_item("project", "feature", "Implement new feature")

# Add subtasks - parent automatically becomes 'pending'
manager.add_subtask("project", "feature", "design", "Create design")
manager.add_subtask("project", "feature", "code", "Write code")
manager.add_subtask("project", "feature", "test", "Write tests")

# Update subtask status - parent automatically updates
manager.update_item_status("project", "design", status="completed")
# Parent "feature" is now 'in_progress' (mixed statuses)

manager.update_item_status("project", "code", status="completed")  
manager.update_item_status("project", "test", status="completed")
# Parent "feature" is now 'completed' (all children completed)

# This will raise ValueError - manual status change blocked
manager.update_item_status("project", "feature", status="failed")
```

### Error Handling

```python
try:
    manager.update_item_status("project", "parent_task", status="completed")
except ValueError as e:
    print(e)  # "Cannot manually change status of task 'parent_task' because it has subtasks..."
```

### Interface Support

Automatic status synchronization works identically across:
- **CLI Interface** - All `todoit item` commands respect sync rules
- **MCP Interface** - All 55+ MCP tools handle sync blocking gracefully
- **Programmatic API** - Direct `TodoManager` method calls

---

## Dependency Management

### `add_item_dependency`
Adds a dependency between two items, indicating one must be completed before the other.

**Parameters:**
- `dependent_list: str`: The list of the item that will be blocked.
- `dependent_item: str`: The item that will be blocked.
- `required_list: str`: The list of the item that is required.
- `required_item: str`: The item that is required.
- `dependency_type: str`: The type of dependency (e.g., `"blocks"`).

**Returns:** `ItemDependency` – The created dependency object.

[Source](../todoit-mcp/core/manager.py)

### `remove_item_dependency`
Removes a dependency between two items.

**Parameters:**
- `dependent_list: str`: The list of the formerly blocked item.
- `dependent_item: str`: The formerly blocked item.
- `required_list: str`: The list of the item that was required.
- `required_item: str`: The item that was required.

**Returns:** `bool` – `True` if the dependency was removed.

[Source](../todoit-mcp/core/manager.py)

### `get_item_blockers`
Gets a list of all items that are currently blocking a specific item.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the item to check.

**Returns:** `List[TodoItem]` – A list of items that are blocking the specified item.

[Source](../todoit-mcp/core/manager.py)

### `is_item_blocked`
Checks if an item is blocked by any incomplete dependencies.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the item to check.

**Returns:** `bool` – `True` if the item is blocked.

[Source](../todoit-mcp/core/manager.py)

---

## Tag Management

### `create_tag`
Creates a new global tag.

**Parameters:**
- `name: str`: The name for the new tag.
- `color: Optional[str]`: A specific color. If `None`, a color is assigned dynamically.

**Returns:** `ListTag` – The created tag object.

[Source](../todoit-mcp/core/manager.py)

### `add_tag_to_list`
Assigns a tag to a list. If the tag doesn't exist, it's created.

**Parameters:**
- `list_key: str`: The key of the list to tag.
- `tag_name: str`: The name of the tag to assign.

**Returns:** `ListTagAssignment` – The created assignment object.

[Source](../todoit-mcp/core/manager.py)

### `get_tags_for_list`
Gets all tags assigned to a specific list.

**Parameters:**
- `list_key: str`: The key of the list.

**Returns:** `List[ListTag]` – A list of tags assigned to the list.

[Source](../todoit-mcp/core/manager.py)

### `get_lists_by_tags`
Gets all lists that have any of the specified tags.

**Parameters:**
- `tag_names: List[str]`: A list of tag names to filter by.

**Returns:** `List[TodoList]` – A list of lists that have at least one of the specified tags.

[Source](../todoit-mcp/core/manager.py)

---

## Property Management

### `set_list_property`
Sets a key-value property for a list.

**Parameters:**
- `list_key: str`: The key of the list.
- `property_key: str`: The key of the property.
- `property_value: str`: The value to assign.

**Returns:** `ListProperty` – The created or updated property object.

[Source](../todoit-mcp/core/manager.py)

### `get_list_properties`
Gets all properties for a list as a dictionary.

**Parameters:**
- `list_key: str`: The key of the list.

**Returns:** `Dict[str, str]` – A dictionary of the list's properties.

[Source](../todoit-mcp/core/manager.py)

### `set_item_property`
Sets a key-value property for an item.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the item.
- `property_key: str`: The key of the property.
- `property_value: str`: The value to assign.

**Returns:** `ItemProperty` – The created or updated property object.

[Source](../todoit-mcp/core/manager.py)

### `get_item_properties`
Gets all properties for an item as a dictionary.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the item.

**Returns:** `Dict[str, str]` – A dictionary of the item's properties.

[Source](../todoit-mcp/core/manager.py)

---

## Import / Export

### `import_from_markdown`
Imports lists and tasks from a markdown file.

**Parameters:**
- `file_path: str`: Path to the markdown file.
- `base_key: Optional[str]`: A base key to use for the created lists.

**Returns:** `List[TodoList]` – A list of the created list objects.

[Source](../todoit-mcp/core/manager.py)

### `export_to_markdown`
Exports a list to a markdown file.

**Parameters:**
- `list_key: str`: The key of the list to export.
- `file_path: str`: The destination file path.

**Returns:** `None`

[Source](../todoit-mcp/core/manager.py)
