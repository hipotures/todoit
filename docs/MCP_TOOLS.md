# TODOIT MCP Tools Documentation

## Overview

TODOIT MCP provides 50 comprehensive tools for Claude Code integration, offering complete programmatic access to all functionality through the Model Context Protocol.

## Tool Categories

### 🔧 Basic Operations (17 tools)
Core functionality for list and item management.

#### List Management
- **`todo_create_list`** - Create new TODO list with optional initial items
- **`todo_get_list`** - Retrieve list details by key or ID  
- **`todo_delete_list`** - Delete list with dependency validation
- **`todo_archive_list`** - Archive list (hide from normal view) with completion validation 
- **`todo_unarchive_list`** - Unarchive list (restore to normal view)
- **`todo_list_all`** - List all TODO lists with progress statistics including failed status counts
- **`todo_link_list_1to1`** - Create linked copy of list with 1:1 task mapping and automatic relation

#### Item Management  
- **`todo_add_item`** - Add new item to list
- **`todo_update_item_status`** - Update item status (pending/in_progress/completed/failed)
- **`todo_update_item_content`** - Update item description/content text
- **`todo_delete_item`** - Delete item permanently from list
- **`todo_get_item`** - Get specific item details
- **`todo_get_list_items`** - Get all items from list with optional status filter

#### Core Operations
- **`todo_get_next_pending`** - Get next available task with dependency consideration
- **`todo_get_progress`** - Get comprehensive progress statistics
- **`todo_quick_add`** - Add multiple items at once
- **`todo_mark_completed`** - Quick completion shortcut
- **`todo_start_item`** - Quick start shortcut

### 🏗️ Advanced Operations (16 tools)
Extended functionality for complex workflows.

#### Import/Export
- **`todo_import_from_markdown`** - Import lists from markdown files (supports `- [ ]` format)
- **`todo_export_to_markdown`** - Export lists to markdown with checkboxes

#### List Relations & Properties
- **`todo_create_list_relation`** - Create relationships between lists
- **`todo_get_lists_by_relation`** - Get lists by relation type and key
- **`todo_set_list_property`** - Set key-value properties on lists
- **`todo_get_list_property`** - Get specific property value
- **`todo_get_list_properties`** - Get all properties for list
- **`todo_delete_list_property`** - Remove property from list

#### Item Properties
- **`todo_set_item_property`** - Set key-value properties on items (create/update)
- **`todo_get_item_property`** - Get specific property value from item
- **`todo_get_item_properties`** - Get all properties for item
- **`todo_delete_item_property`** - Remove property from item

#### Project Management
- **`todo_project_overview`** - Get comprehensive project status across related lists
- **`todo_get_item_history`** - Get complete change history for items
- **`todo_get_schema_info`** - Get system schema information (available statuses, types, constants)

### 🌳 Subtask Operations (6 tools)
Hierarchical task management with parent-child relationships.

- **`todo_add_subtask`** - Add subtask to existing task
- **`todo_get_subtasks`** - Get all subtasks for parent task
- **`todo_get_item_hierarchy`** - Get complete hierarchy tree for item
- **`todo_move_to_subtask`** - Convert existing task to subtask
- **`todo_get_next_pending_smart`** - Smart next task with subtask prioritization
- **`todo_can_complete_item`** - Check if item can be completed (no pending subtasks)

### 🔗 Dependency Operations (6 tools)  
Cross-list task dependencies for complex project coordination.

- **`todo_add_item_dependency`** - Create dependency between tasks from different lists
- **`todo_remove_item_dependency`** - Remove dependency relationship
- **`todo_get_item_blockers`** - Get all items blocking this task
- **`todo_get_items_blocked_by`** - Get all items blocked by this task
- **`todo_is_item_blocked`** - Check if item is blocked by dependencies
- **`todo_can_start_item`** - Combined check for subtasks + dependencies

### 🧠 Smart Algorithms (5 tools)
Advanced algorithms for intelligent task management.

- **`todo_get_list_items_hierarchical`** - Get items with hierarchical organization
- **`todo_get_cross_list_progress`** - Progress tracking across multiple related lists
- **`todo_get_dependency_graph`** - Get dependency graph for visualization
- **`todo_get_next_pending_enhanced`** - Enhanced next task with full Phase 2 logic
- **`todo_get_comprehensive_status`** - Complete status combining all features

## Usage Examples

### Basic Workflow
```python
# Create list and add items
await todo_create_list("project", "My Project", items=["Task 1", "Task 2"])

# Add subtasks
await todo_add_subtask("project", "task1", "subtask1", "Backend implementation")

# Create dependencies
await todo_add_item_dependency("frontend", "ui_task", "backend", "api_task")

# Get smart next task
next_task = await todo_get_next_pending_enhanced("project", smart_subtasks=True)
```

### Archive Management with Completion Validation
```python
# Create project and work on tasks
await todo_create_list("sprint-1", "Sprint 1 Tasks", items=["Feature A", "Feature B", "Bug fixes"])

# Complete some tasks
await todo_update_item_status("sprint-1", "item_1", "completed")
await todo_update_item_status("sprint-1", "item_2", "completed") 

# Try to archive with incomplete tasks (will fail)
result = await todo_archive_list("sprint-1", force=False)
# Returns: {"success": False, "error": "Cannot archive list with incomplete tasks. Incomplete: 1/3 tasks. Use force=True to archive anyway."}

# Complete remaining tasks
await todo_update_item_status("sprint-1", "item_3", "completed")

# Archive completed list (will succeed)
result = await todo_archive_list("sprint-1", force=False)
# Returns: {"success": True, "list": {"status": "archived", ...}}

# Or force archive with incomplete tasks
result = await todo_archive_list("sprint-1", force=True)
# Always succeeds regardless of task completion status
```

### List Linking (1:1 Relationships)
```python
# Create development list with tasks and properties
await todo_create_list("api-dev", "API Development")
await todo_quick_add("api-dev", ["Setup environment", "Implement endpoints", "Write tests"])
await todo_set_list_property("api-dev", "project_id", "proj-123")
await todo_set_item_property("api-dev", "item1", "priority", "high")

# Link to create testing list with identical structure
result = await todo_link_list_1to1("api-dev", "api-test", "API Testing Tasks")

# Result contains:
# {
#   "success": true,
#   "source_list": "api-dev",
#   "target_list": "api-test", 
#   "items_copied": 3,
#   "list_properties_copied": 1,
#   "item_properties_copied": 1,
#   "all_items_set_to_pending": true,
#   "relation_created": true,
#   "relation_key": "api-dev_linked"
# }

# Both lists now have identical tasks and properties
# Testing tasks are all "pending" status (reset from source statuses)
# Automatic project relationship created between lists
```

### Project Coordination
```python
# Get comprehensive project status
status = await todo_get_comprehensive_status("project")

# Check cross-list progress  
progress = await todo_get_cross_list_progress("my-project")

# Visualize dependencies
graph = await todo_get_dependency_graph("my-project")
```

### Item Properties Management
```python
# Set properties for runtime tracking
await todo_set_item_property("project", "task1", "priority", "high")
await todo_set_item_property("project", "task1", "estimated_hours", "8")
await todo_set_item_property("project", "task1", "assignee", "john_doe")

# Get specific property
priority = await todo_get_item_property("project", "task1", "priority")

# Get all properties for an item
props = await todo_get_item_properties("project", "task1")
# Returns: {"priority": "high", "estimated_hours": "8", "assignee": "john_doe"}

# Update property (automatically overwrites existing)
await todo_set_item_property("project", "task1", "priority", "critical")

# Remove property when no longer needed
await todo_delete_item_property("project", "task1", "assignee")
```

## Error Handling

All MCP tools include comprehensive error handling:
- **Validation errors** - Invalid parameters or missing resources
- **Business rule violations** - Circular dependencies, invalid state transitions
- **Database errors** - Connection issues, constraint violations

Error responses include:
```json
{
  "success": false,
  "error": "Descriptive error message", 
  "error_type": "validation|business|internal"
}
```

## Integration with Claude Code

All 50 tools are automatically available in Claude Code through MCP integration:

1. **List Management** - Create, organize, and manage task lists
2. **Task Operations** - Add, update, and track individual tasks
3. **Hierarchy Support** - Break down complex tasks into subtasks
4. **Dependency Management** - Coordinate work across different lists
5. **Progress Tracking** - Monitor completion across projects
6. **Smart Algorithms** - Intelligent task prioritization and workflow optimization

### Enhanced List Overview

The `todo_list_all` tool now provides comprehensive progress statistics for each list:

```json
{
  "success": true,
  "lists": [
    {
      "id": 1,
      "list_key": "my_project",
      "title": "My Project Tasks",
      "list_type": "sequential",
      "progress": {
        "total": 10,
        "completed": 6,
        "in_progress": 2,
        "pending": 1,
        "failed": 1,
        "completion_percentage": 60.0,
        "blocked": 0,
        "available": 3
      }
    }
  ],
  "count": 1
}
```

This enhanced data enables better project management visibility, including failed task tracking and dependency-aware progress monitoring.

## Performance Considerations

- **Database Optimization** - All queries use proper indexes and foreign keys
- **Batch Operations** - `quick_add` for multiple items, bulk status updates
- **Lazy Loading** - Hierarchies and dependencies loaded on-demand
- **Caching** - Progress statistics cached for performance

## Testing Status

✅ **All 50 MCP tools tested and verified working**
- 100% functional coverage
- Error handling validated  
- Integration tested with real workflows
- Performance verified under load

---

*Last updated: August 6, 2025 - All tools production ready*