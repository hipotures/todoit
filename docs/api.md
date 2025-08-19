# Programmatic API (TodoManager)

The `TodoManager` class in `core/manager.py` provides the core programmatic API for interacting with the TODOIT system. It encapsulates all business logic and interacts with the database layer.

This document serves as a reference for the main methods available in the `TodoManager` class.

## ✨ Natural Sorting (v2.11.0)

TODOIT now uses **natural sorting** for all lists and items, making numeric sequences sort intuitively:

- **Lists**: `0014_project` comes before `0037_project` (not after)
- **Items**: `scene_0020` comes before `scene_0021`, `test_2` before `test_10`
- **Automatic**: No configuration needed - all MCP tools and CLI commands benefit
- **Backward Compatible**: Existing `position` fields remain but are no longer primary sort criterion

## Core Object Management

### `create_list`
Creates a new TODO list.

**Parameters:**
- `list_key: str`: A unique key for the list.
- `title: str`: A human-readable title.
- `items: Optional[List[str]]`: A list of strings to create as initial items.
- `list_type: str`: The list's ordering and behavior strategy (`"sequential"`).
- `metadata: Optional[Dict]`: A dictionary for custom metadata.

**Returns:** `TodoList` – The created list object.

[Source](../todoit-mcp/core/manager.py)

### `add_item`
Adds a new item to a list.

**Parameters:**
- `list_key: str`: The key of the target list.
- `item_key: str`: A unique key for the item within the list.
- `content: str`: The item's description.
- `position: Optional[int]`: ⚠️ **DEPRECATED**: Position parameter still exists for compatibility but is no longer the primary sort criterion. Items are now sorted naturally by `item_key`.
- `metadata: Optional[Dict]`: A dictionary for custom metadata.

**Returns:** `TodoItem` – The created item object.

[Source](../todoit-mcp/core/manager.py)

### `update_item_status`
Updates the status of an item.

> ⚠️ **Automatic Status Synchronization**: Items with subitems cannot have manually changed status. Their status is automatically calculated from subitem statuses. See [Status Synchronization](#automatic-status-synchronization) for details.

**Parameters:**
- `list_key: str`: The key of the list containing the item.
- `item_key: str`: The key of the item (or parent item if updating subitem).
- `subitem_key: Optional[str]`: The key of the subitem to update (if updating subitem).
- `status: Optional[str]`: The new status (e.g., `"pending"`, `"in_progress"`, `"completed"`, `"failed"`).
- `completion_states: Optional[Dict[str, Any]]`: Custom key-value pairs for completion metadata.

**Returns:** `TodoItem` – The updated item object.

**Raises:** `ValueError` if attempting to manually change status of an item with subitems.

[Source](../todoit-mcp/core/manager.py)

---

## Subitem and Hierarchy Management

### `add_subitem`
Adds a new subitem to an existing parent item.

> 🔄 **Automatic Sync**: Adding a subitem triggers automatic parent status synchronization.

**Parameters:**
- `list_key: str`: The key of the list.
- `parent_key: str`: The key of the parent item.
- `subitem_key: str`: A unique key for the new subitem.
- `content: str`: The content of the subitem.
- `metadata: Optional[Dict]`: Custom metadata.

**Returns:** `TodoItem` – The created subitem object.

[Source](../todoit-mcp/core/manager.py)

### `get_subitems`
Retrieves all direct subitems for a parent item.

**Parameters:**
- `list_key: str`: The key of the list.
- `parent_key: str`: The key of the parent item.

**Returns:** `List[TodoItem]` – A list of subitem objects.

[Source](../todoit-mcp/core/manager.py)

### `get_item_hierarchy`
Retrieves the full hierarchy for an item, including all its subitems recursively.

**Parameters:**
- `list_key: str`: The key of the list.
- `item_key: str`: The key of the root item of the hierarchy.

**Returns:** `Dict[str, Any]` – A nested dictionary representing the hierarchy.

[Source](../todoit-mcp/core/manager.py)

---

## Automatic Status Synchronization

*Added in version 1.20.0*

TODOIT automatically synchronizes the status of parent items based on their subitems. This feature ensures hierarchical item consistency and prevents manual status conflicts.

### Core Rules

**Status Calculation Priority:**
1. **`failed`** - If any subitem is failed → parent becomes `failed`
2. **`pending`** - If all subitems are pending → parent becomes `pending`  
3. **`completed`** - If all subitems are completed → parent becomes `completed`
4. **`in_progress`** - Any other combination → parent becomes `in_progress`

**Manual Update Protection:**
- Items with subitems **cannot** have manually changed status
- Attempting `update_item_status()` on parent items raises `ValueError`
- Use subitem status changes to control parent status instead

### Automatic Triggers

Status synchronization occurs automatically on:
- **`add_subitem()`** - Adding first subitem to parent
- **`update_item_status()`** - Changing any subitem status  
- **`delete_item()`** - Removing subitems from parent

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
# Create parent item
manager.add_item("project", "feature", "Implement new feature")

# Add subitems - parent automatically becomes 'pending'
manager.add_subitem("project", "feature", "design", "Create design")
manager.add_subitem("project", "feature", "code", "Write code")
manager.add_subitem("project", "feature", "test", "Write tests")

# Update subitem status - parent automatically updates
manager.update_item_status("project", "feature", subitem_key="design", status="completed")
# Parent "feature" is now 'in_progress' (mixed statuses)

manager.update_item_status("project", "feature", subitem_key="code", status="completed")  
manager.update_item_status("project", "feature", subitem_key="test", status="completed")
# Parent "feature" is now 'completed' (all children completed)

# This will raise ValueError - manual status change blocked
manager.update_item_status("project", "feature", status="failed")
```

### Error Handling

```python
try:
    manager.update_item_status("project", "parent_item", status="completed")
except ValueError as e:
    print(e)  # "Cannot manually change status of item 'parent_item' because it has subitems..."
```

### Interface Support

Automatic status synchronization works identically across:
- **CLI Interface** - All `todoit item` commands respect sync rules
- **MCP Interface** - All MCP tools handle sync blocking gracefully
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

## Advanced Search

### `find_subitems_by_status`
*Added in version 1.21.0*

Find subitems based on sibling status conditions within their parent groups.

**Parameters:**
- `list_key: str`: The key of the list to search in.
- `conditions: Dict[str, str]`: Dictionary of {subitem_key: expected_status} conditions.
- `limit: int`: Maximum number of results to return (default: 10).

**Returns:** `List[TodoItem]` – Subitems matching the conditions, ordered naturally by `item_key`.

**Raises:** `ValueError` if the specified list is not found or conditions are empty.

**How it works:**
This function finds groups of sibling subitems where ALL conditions are satisfied within the same parent group. It then returns the subitems that are specifically mentioned in the conditions.

**Usage Examples:**

```python
# Workflow automation: Find downloads ready to process
# (where image generation is completed)
ready_downloads = manager.find_subitems_by_status(
    "image_pipeline",
    {"generate": "completed", "download": "pending"},
    limit=10
)

# Development workflow: Find tests ready to run
# (where design and coding are both completed)
ready_tests = manager.find_subitems_by_status(
    "features",
    {"design": "completed", "code": "completed", "test": "pending"},
    limit=5
)

# Sequential workflow: Find next step when previous is done
next_steps = manager.find_subitems_by_status(
    "deployment",
    {"build": "completed", "deploy": "pending"},
    limit=3
)
```

**Real-world scenarios:**
- **Image Processing**: Find downloads ready when generation completes
- **Development**: Find testing tasks when design and code are done
- **Deployment**: Find deployment tasks when build completes
- **Content Creation**: Find publishing tasks when writing and review are complete

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
