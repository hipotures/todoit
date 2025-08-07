# Programmatic API (TodoManager)

The `TodoManager` class in `core/manager.py` provides a programmatic API for managing TODO lists and items. It encapsulates all business logic and interacts with the database layer.

Below is a reference of the most commonly used methods. Each section lists parameters, return values, a short usage example and a link to the implementation.

### `create_list`

**Parameters**

* `list_key: str` – unique key for the list.
* `title: str` – human‑readable title.
* `items: Optional[List[str]]` – optional initial task contents.
* `list_type: str` – list ordering strategy (`"sequential"` by default).
* `metadata: Optional[Dict]` – optional custom metadata.

**Returns**

`TodoList` – the created list object.

**Example**

```python
from core.manager import TodoManager

mgr = TodoManager()
todo_list = mgr.create_list("work", "Work tasks", items=["Docs", "Tests"])
```

[Source](../todoit-mcp/core/manager.py#L69-L117)

### `get_list`

**Parameters**

* `key: Union[str, int]` – list key or numeric ID.

**Returns**

`Optional[TodoList]` – the matching list or `None`.

**Example**

```python
todo_list = mgr.get_list("work")
```

[Source](../todoit-mcp/core/manager.py#L119-L126)

### `delete_list`

**Parameters**

* `key: Union[str, int]` – list key or ID to delete.

**Returns**

`bool` – `True` if the list was removed.

**Example**

```python
mgr.delete_list("work")
```

[Source](../todoit-mcp/core/manager.py#L128-L196)

### `list_all`

**Parameters**

* `limit: Optional[int]` – maximum number of lists to return.

**Returns**

`List[TodoList]` – all lists ordered by creation.

**Example**

```python
all_lists = mgr.list_all()
```

[Source](../todoit-mcp/core/manager.py#L198-L201)

### `add_item`

**Parameters**

* `list_key: str` – key of the target list.
* `item_key: str` – unique key for the item.
* `content: str` – task description.
* `position: Optional[int]` – insertion position (auto‑incremented when omitted).
* `metadata: Optional[Dict]` – optional metadata.

**Returns**

`TodoItem` – the created item.

**Example**

```python
item = mgr.add_item("work", "write_docs", "Write API docs")
```

[Source](../todoit-mcp/core/manager.py#L203-L244)

### `update_item_status`

**Parameters**

* `list_key: str` – list containing the item.
* `item_key: str` – item identifier.
* `status: Optional[str]` – new status (`pending`, `in_progress`, `completed`, `failed`).
* `completion_states: Optional[Dict[str, Any]]` – custom completion info.

**Returns**

`TodoItem` – the updated item.

**Example**

```python
mgr.update_item_status("work", "write_docs", status="completed")
```

[Source](../todoit-mcp/core/manager.py#L246-L304)

### `get_next_pending`

**Parameters**

* `list_key: str` – list key to inspect.
* `respect_dependencies: bool` – ignore blocking dependencies if `False`.
* `smart_subtasks: bool` – when `True`, use the smart subtask algorithm.

**Returns**

`Optional[TodoItem]` – next available task or `None`.

**Example**

```python
next_item = mgr.get_next_pending("work")
```

[Source](../todoit-mcp/core/manager.py#L306-L356)

### `get_progress`

**Parameters**

* `list_key: str` – list key to analyze.

**Returns**

`ProgressStats` – aggregated completion statistics.

**Example**

```python
stats = mgr.get_progress("work")
```

[Source](../todoit-mcp/core/manager.py#L358-L399)

### `import_from_markdown`

**Parameters**

* `file_path: str` – path to a markdown file.
* `base_key: Optional[str]` – base key for created lists.

**Returns**

`List[TodoList]` – list objects created from the file.

**Example**

```python
imported = mgr.import_from_markdown("tasks.md")
```

[Source](../todoit-mcp/core/manager.py#L414-L503)

### `export_to_markdown`

**Parameters**

* `list_key: str` – list to export.
* `file_path: str` – destination file path.

**Returns**

`None`

**Example**

```python
mgr.export_to_markdown("work", "work.md")
```

[Source](../todoit-mcp/core/manager.py#L505-L533)
