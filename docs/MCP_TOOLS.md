# TODOIT MCP Tools Documentation

## Overview

TODOIT MCP provides 47 comprehensive tools for Claude Code integration, offering complete programmatic access to all functionality through the Model Context Protocol.

## Tool Categories

### 🔧 Basic Operations (14 tools)
Core functionality for list and item management.

#### List Management
- **`todo_create_list`** - Create new TODO list with optional initial items
- **`todo_get_list`** - Retrieve list details by key or ID  
- **`todo_delete_list`** - Delete list with dependency validation
- **`todo_list_all`** - List all TODO lists with optional limit

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

All 40 tools are automatically available in Claude Code through MCP integration:

1. **List Management** - Create, organize, and manage task lists
2. **Task Operations** - Add, update, and track individual tasks
3. **Hierarchy Support** - Break down complex tasks into subtasks
4. **Dependency Management** - Coordinate work across different lists
5. **Progress Tracking** - Monitor completion across projects
6. **Smart Algorithms** - Intelligent task prioritization and workflow optimization

## Performance Considerations

- **Database Optimization** - All queries use proper indexes and foreign keys
- **Batch Operations** - `quick_add` for multiple items, bulk status updates
- **Lazy Loading** - Hierarchies and dependencies loaded on-demand
- **Caching** - Progress statistics cached for performance

## Testing Status

✅ **All 40 MCP tools tested and verified working**
- 100% functional coverage
- Error handling validated  
- Integration tested with real workflows
- Performance verified under load

---

*Last updated: August 6, 2025 - All tools production ready*