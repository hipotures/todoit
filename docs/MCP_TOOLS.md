# TODOIT MCP Tools Documentation

## Overview

TODOIT MCP provides 57 comprehensive tools for Claude Code integration, offering complete programmatic access to all functionality through the Model Context Protocol.

## 🎛️ Tools Level Configuration

**NEW**: MCP tools can now be configured at 3 different levels to optimize token usage and system complexity:

### 📦 Levels Available

| Level | Tools Count | Token Savings | Use Case |
|-------|-------------|---------------|----------|
| **MINIMAL** | 10 tools | 82% savings | Essential operations only, maximum performance |
| **STANDARD** | 24 tools | 57% savings | Balanced functionality (default) | 
| **MAX** | 57 tools | 0% savings | Complete feature set |

### 🔧 Configuration

Set the environment variable to choose your level:

```bash
# Minimal set (10 tools) - Essential operations only
export TODOIT_MCP_TOOLS_LEVEL=minimal

# Standard set (24 tools) - Balanced functionality (DEFAULT)
export TODOIT_MCP_TOOLS_LEVEL=standard

# Complete set (57 tools) - All features
export TODOIT_MCP_TOOLS_LEVEL=max
```

**Default**: `STANDARD` level (24 tools) for optimal balance of functionality vs performance.

### ⚡ Performance Impact

- **MINIMAL**: ~500-1000 tokens context vs 3000+ for MAX
- **STANDARD**: ~1500-2000 tokens context (24 tools)
- **MAX**: ~3000+ tokens context (57 tools - full feature set)

### 🛡️ Security Benefits

**MINIMAL** and **STANDARD** levels exclude destructive operations:
- ❌ `todo_delete_list` - List deletion blocked
- ❌ `todo_delete_item` - Item deletion blocked
- ✅ All read/update operations available

Perfect for production environments or when safety is paramount.

---

## Tool Categories

### 🔧 Basic Operations (17 tools)
Core functionality for list and item management.

#### List Management
- **`todo_create_list`** - Create new TODO list with optional initial items
- **`todo_get_list`** - Retrieve list details by key or ID  
- **`todo_delete_list`** - Delete list with dependency validation
- **`todo_archive_list`** - Archive list (hide from normal view) with completion validation 
- **`todo_unarchive_list`** - Unarchive list (restore to normal view)
- **`todo_list_all`** - List all TODO lists with progress statistics and optional tag filtering
- **`todo_link_list_1to1`** - Create linked copy of list with 1:1 task mapping and automatic relation

#### Item Management  
- **`todo_add_item`** - Add new item to list
- **`todo_update_item_status`** - Update item status (pending/in_progress/completed/failed)
- **`todo_update_item_content`** - Update item description/content text
- **`todo_delete_item`** - Delete item permanently from list
- **`todo_get_item`** - Get specific item details
- **`todo_get_list_items`** - Get all items from list with optional status filter and pagination limit

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
- **`todo_find_items_by_property`** - 🆕 **STANDARD** Search items by property value with optional limit
- **`todo_find_item_by_property`** - 🆕 Find first item by property value (convenience wrapper)

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

### 📊 Reports & Analytics (1 tool)
Generate comprehensive reports for project management and troubleshooting.

- **`todo_report_errors`** - Generate report of all failed tasks with regex and tag filtering

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

### List Items with Limit and Filtering
```python
# Get all items from a list
all_items = await todo_get_list_items("project")
# Returns: {"success": True, "items": [...], "count": 10, "total_count": 10, "more_available": False}

# Get limited number of items (pagination)
first_5 = await todo_get_list_items("project", limit=5)
# Returns: {"success": True, "items": [...], "count": 5, "total_count": 10, "more_available": True}

# Get limited pending items only
pending = await todo_get_list_items("project", status="pending", limit=3)  
# Returns: {"success": True, "items": [...], "count": 3, "total_count": 7, "more_available": True}

# Get completed items with limit
completed = await todo_get_list_items("project", status="completed", limit=0)
# Returns: {"success": True, "items": [], "count": 0, "total_count": 3, "more_available": True}

# Advanced limit usage with hierarchical items
hierarchical = await todo_get_list_items("project", limit=10)
# Limit applies to flat result ordering by position, includes parents and subtasks
# Returns first 10 items regardless of hierarchy level
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
```

## 🏷️ Tag System with Dynamic 12-Color Assignment

TODOIT features an intelligent tag system with dynamic color assignment based on alphabetical sorting for consistent visual organization:

### Dynamic Color Management
- **12 Distinct Colors**: `dim red`, `dim green`, `dim blue`, `dim yellow`, `dim white`, `purple`, `cyan`, `magenta`, `pink`, `grey`, `green`, `red`
- **Alphabetical Assignment**: Colors assigned dynamically based on alphabetical position of tag names
- **Real-time Recalculation**: Colors automatically shift when tags are deleted to maintain sequence
- **Maximum Limit**: System prevents creation of more than 12 tags to maintain visual clarity
- **Visual Display**: Tags appear as colored dots (●) in CLI tables and MCP responses

### Dynamic Color Examples
```python
# Create tags - colors assigned by alphabetical position
await todo_create_tag("zebra")      # Created first, but gets blue (position 2 alphabetically)
await todo_create_tag("alpha")      # Gets red (position 0 alphabetically)  
await todo_create_tag("beta")       # Gets green (position 1 alphabetically)

# Get all tags - colors based on alphabetical order
all_tags = await todo_get_all_tags()
# Result: [{"name": "alpha", "color": "red"}, 
#          {"name": "beta", "color": "green"}, 
#          {"name": "zebra", "color": "blue"}]

# Delete middle tag - colors shift dynamically
await todo_delete_tag("beta")
updated_tags = await todo_get_all_tags()
# Result: [{"name": "alpha", "color": "red"}, 
#          {"name": "zebra", "color": "green"}]  # Shifted from blue to green

# Tag limit enforcement - 13th tag fails
try:
    tag13 = await todo_create_tag("overflow")  # Raises error
except ValueError as e:
    # "Maximum number of tags reached (12). Cannot create more tags with distinct colors."
    pass

# Add tags to lists
await todo_add_list_tag("project-alpha", "frontend")
await todo_add_list_tag("project-alpha", "testing")
```

### Visual Display Features
- **CLI Tables**: List all commands show tags as colored dots in 🏷️ column
- **Legend**: Automatic legend displays below tables: "● frontend ● testing"  
- **MCP Integration**: All tag-related MCP tools include color information
- **Consistent Ordering**: Tags displayed alphabetically for predictable organization

### Tag System Benefits
- **Visual Clarity**: 12-color limit ensures tags remain easily distinguishable
- **Predictable Colors**: Alphabetical ordering provides consistent color assignment
- **Dynamic Adaptation**: Colors automatically recalculate when tags are deleted
- **No Color Conflicts**: System prevents duplicate colors through smart assignment
- **Cross-Interface Consistency**: Same dynamic colors in CLI and MCP tools

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

# 🆕 SEARCH for items by property values
# Find all items with high priority
high_priority_tasks = await todo_find_items_by_property("project", "priority", "high")
# Returns: {"success": true, "items": [...], "count": 3, "search_criteria": {...}}

# Find items assigned to specific person (with limit)
johns_tasks = await todo_find_items_by_property("project", "assignee", "john", limit=5)

# Find first item by issue ID (convenience function)
task = await todo_find_item_by_property("project", "jira_ticket", "PROJ-123")
# Returns: {"success": true, "item": {...}} or {"success": true, "item": null}

# Example search use cases:
# - Find tasks by external references: await todo_find_items_by_property("list", "github_issue", "456")
# - Filter by review status: await todo_find_items_by_property("list", "review_status", "approved")
# - Locate by component: await todo_find_items_by_property("backend", "component", "authentication")
```

### Reports & Analytics
```python
# Generate report of all failed tasks across active lists
report = await todo_report_errors()
# Returns all failed tasks from active (non-archived) lists

# Filter by regex patterns for specific list naming schemes
nnnn_report = await todo_report_errors(list_filter=r"^\d{4}_.*")  # NNNN_* pattern
project_report = await todo_report_errors(list_filter=r".*project.*")  # Contains "project"
sprint_report = await todo_report_errors(list_filter=r"^sprint_.*")  # Sprint lists

# Example response structure:
# {
#   "success": True,
#   "failed_tasks": [
#     {
#       "list_key": "0001_project_alpha", 
#       "list_title": "Project Alpha Tasks",
#       "list_type": "sequential",
#       "item_key": "deploy_001",
#       "content": "Deploy to production server",
#       "position": 5,
#       "updated_at": "2025-08-09T14:30:00",
#       "created_at": "2025-08-05T09:00:00",
#       "properties": {
#         "retry_count": "3",
#         "last_error": "connection timeout",
#         "severity": "high"
#       }
#     }
#   ],
#   "count": 1,
#   "metadata": {
#     "filter_applied": "^\d{4}_.*",
#     "lists_scanned": 25,
#     "lists_matched": 8,
#     "unique_lists_with_failures": 1
#   }
# }
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

All 57 tools are automatically available in Claude Code through MCP integration:

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

### 🏷️ Tag Operations (4 tools)
Organize and categorize lists using tags for better project management.

- **`todo_create_tag`** - Create new tag with optional color
- **`todo_add_list_tag`** - Add tag to list (auto-creates if needed) 
- **`todo_remove_list_tag`** - Remove tag from list
- **`todo_get_lists_by_tag`** - Get all lists with specified tags

### Tag Management
```python
# Create tags for organization
await todo_create_tag("work", "blue")
await todo_create_tag("urgent", "red") 
await todo_create_tag("client", "green")

# Tag lists for categorization
await todo_add_list_tag("project-alpha", "work")
await todo_add_list_tag("project-alpha", "client")
await todo_add_list_tag("hotfix-123", "urgent")

# Find lists by tags (OR logic - lists with ANY of the tags)
result = await todo_get_lists_by_tag(["work", "urgent"])
# Returns lists tagged with either "work" OR "urgent" 

# Use enhanced todo_list_all with tag filtering
result = await todo_list_all(filter_tags=["client"])
# Returns only lists tagged with "client"

# Remove tag from list
await todo_remove_list_tag("project-alpha", "urgent")
```

**Note**: Tag filtering in MCP uses explicit parameters only. Environment variables like `TODOIT_FILTER_TAGS` are CLI-only features and do not affect MCP tools.

## 📋 Detailed Tools by Level

### 🥇 MINIMAL Level (10 tools)
**Essential operations only - Maximum performance**

| Tool | Purpose |
|------|---------|
| `todo_create_list` | Create new TODO list |
| `todo_get_list` | Retrieve list details |
| `todo_list_all` | List all TODO lists |
| `todo_add_item` | Add new item to list |
| `todo_update_item_status` | Update item status |
| `todo_get_list_items` | Get all items from list |
| `todo_get_item` | Get specific item details |
| `todo_get_next_pending` | Get next available task |
| `todo_get_progress` | Get progress statistics |
| `todo_update_item_content` | Update item description |

### 🥈 STANDARD Level (+13 tools)
**Includes MINIMAL + useful extensions**

**Additional tools in STANDARD:**

| Tool | Purpose |
|------|---------|
| `todo_quick_add` | Add multiple items at once |
| `todo_mark_completed` | Quick completion shortcut |
| `todo_start_item` | Quick start shortcut |
| `todo_add_subtask` | Add subtask to existing task |
| `todo_get_subtasks` | Get all subtasks for parent |
| `todo_archive_list` | Archive list (hide from view) |
| `todo_unarchive_list` | Unarchive list (restore) |
| `todo_set_list_property` | Set key-value properties on lists |
| `todo_get_list_property` | Get specific list property |
| `todo_set_item_property` | Set key-value properties on items |
| `todo_get_item_property` | Get specific item property |
| `todo_find_items_by_property` | 🆕 Search items by property value |
| `todo_create_tag` | Create new system tag |
| `todo_add_list_tag` | Add tag to list |

### 🥉 MAX Level (+32 tools)  
**Includes STANDARD + advanced features**

**Additional advanced tools (32 more):**
- **Cross-list dependencies** (6 tools): `todo_add_item_dependency`, `todo_remove_item_dependency`, etc.
- **Advanced subtask operations** (4 tools): `todo_get_item_hierarchy`, `todo_move_to_subtask`, etc.
- **Smart algorithms** (5 tools): `todo_get_next_pending_enhanced`, `todo_get_comprehensive_status`, etc.
- **Import/Export** (2 tools): `todo_import_from_markdown`, `todo_export_to_markdown`
- **Relations & Projects** (3 tools): `todo_create_list_relation`, `todo_project_overview`, etc.
- **Advanced properties** (4 tools): `todo_get_list_properties`, `todo_delete_item_property`, etc.
- **Analytics & Reports** (1 tool): `todo_report_errors`
- **Advanced tagging** (3 tools): `todo_remove_list_tag`, `todo_get_lists_by_tag`, etc.
- **System metadata** (1 tool): `todo_get_schema_info`
- **Destructive operations** (2 tools): `todo_delete_list`, `todo_delete_item`
- **Other specialized tools** (1 tool): `todo_get_item_history`

## Performance Considerations

- **Database Optimization** - All queries use proper indexes and foreign keys
- **Batch Operations** - `quick_add` for multiple items, bulk status updates
- **Lazy Loading** - Hierarchies and dependencies loaded on-demand
- **Caching** - Progress statistics cached for performance

## Testing Status

✅ **All 57 MCP tools tested and verified working**
- 100% functional coverage
- Error handling validated  
- Integration tested with real workflows
- Performance verified under load

---

*Last updated: August 12, 2025 - All 57 tools production ready with 3-level configuration system*