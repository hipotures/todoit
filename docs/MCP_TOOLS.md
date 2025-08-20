# TODOIT MCP Tools Documentation

## Overview

TODOIT MCP provides 51 comprehensive tools for Claude Code integration, offering complete programmatic access to all functionality through the Model Context Protocol.

## 🔧 API Consistency Fix (v2.13.1)
**BREAKING CHANGE**: Fixed parameter naming inconsistency for API consistency:
- **`todo_get_list`** now uses `list_key` parameter (was: `key`)
- **`todo_delete_list`** now uses `list_key` parameter (was: `key`)

This ensures consistent parameter naming across all MCP tools:
- `list_key` - identifies lists
- `item_key` - identifies items  
- `subitem_key` - identifies subitems

## ✨ Natural Sorting (v2.11.0)
All MCP tools now return naturally sorted results:
- **Lists** sorted by `list_key`: `0014_project` before `0037_project`
- **Items** sorted by `item_key`: `scene_0020` before `scene_0021`, `test_2` before `test_10`

## 🎛️ Tools Level Configuration

**NEW**: MCP tools can now be configured at 3 different levels to optimize token usage and system complexity:

### 📦 Levels Available

| Level | Tools Count | Token Savings | Use Case |
|-------|-------------|---------------|----------|
| **MINIMAL** | 9 tools | 82% savings | Essential operations only, maximum performance |
| **STANDARD** | 21 tools | 59% savings | Balanced functionality (default) | 
| **MAX** | 51 tools | 0% savings | Complete feature set |

### 🔧 Configuration

Set the environment variable to choose your level:

```bash
# Minimal set (9 tools) - Essential operations only
export TODOIT_MCP_TOOLS_LEVEL=minimal

# Standard set (21 tools) - Balanced functionality (DEFAULT)
export TODOIT_MCP_TOOLS_LEVEL=standard

# Complete set (51 tools) - All features
export TODOIT_MCP_TOOLS_LEVEL=max
```

**Default**: `STANDARD` level (21 tools) for optimal balance of functionality vs performance.

### ⚡ Performance Impact

- **MINIMAL**: ~500-1000 tokens context vs 3000+ for MAX
- **STANDARD**: ~1200-1700 tokens context (21 tools)
- **MAX**: ~3000+ tokens context (51 tools - full feature set)

### 🛡️ Security Benefits

**MINIMAL** and **STANDARD** levels exclude destructive operations:
- ❌ `todo_delete_list` - List deletion blocked
- ❌ `todo_delete_item` - Item deletion blocked
- ✅ All read/update operations available

Perfect for production environments or when safety is paramount.

## 🚀 Data Optimization 

**NEW**: All MCP tools now return optimized, minimal datasets for better performance:

### Reduced Item Data
- ✅ **Essential fields**: `item_key`, `title`, `status`, `position`
- ✅ **Smart indicators**: `is_subtask: true` for subtasks
- ❌ **Removed**: `id`, `list_id`, `created_at`, `updated_at`, `started_at`, `completed_at`, `completion_states`, `metadata`, `parent_item_id`
- 📉 **Result**: 62-67% reduction (13 fields → 5 fields)

### Reduced List Data  
- ✅ **Essential fields**: `list_key`, `title`, `description`, `list_type`
- ❌ **Removed**: `id`, `created_at`, `updated_at`, `status`, `metadata`, internal fields
- 📉 **Result**: ~50% reduction (8+ fields → 4 fields)

### Reduced Property Data
- ✅ **Essential fields**: `property_key`, `property_value`
- ❌ **Removed**: `id`, `item_id`, `created_at`, `updated_at`
- 📉 **Result**: 67% reduction (6 fields → 2 fields)

### Reduced Tag Data
- ✅ **Essential fields**: `name`, `color`
- ❌ **Removed**: `id`, `created_at`
- 📉 **Result**: 50% reduction (4 fields → 2 fields)

### Reduced Assignment Data
- ✅ **Essential fields**: `id`, `list_id`, `tag_id` (relational IDs)
- ❌ **Removed**: `assigned_at`
- 📉 **Result**: 25% reduction (4 fields → 3 fields)

### Performance Benefits
- **Faster responses** - Less data transfer
- **Lower token usage** - Smaller context in Claude Code
- **Better readability** - Focus on actionable data only

### Before/After Examples

**Item Response BEFORE (13 fields):**
```json
{
  "success": true,
  "item": {
    "id": 3260,
    "list_id": 125,
    "item_key": "scene_style",
    "position": 2,
    "status": "completed",
    "completion_states": {},
    "parent_item_id": 3258,
    "metadata": {},
    "started_at": null,
    "completed_at": "2025-08-17T11:16:26.290684",
    "created_at": "2025-08-17T11:16:25.460898",
    "updated_at": "2025-08-17T20:08:30.958173",
    "title": "Scene styling for scene_0004.yaml"
  }
}
```

**Item Response AFTER (5 fields - 62% reduction):**
```json
{
  "success": true,
  "item": {
    "item_key": "scene_style",
    "status": "completed",
    "position": 2,
    "is_subtask": true,
    "title": "Scene styling for scene_0004.yaml"
  }
}
```

**Property Response BEFORE (6 fields):**
```json
{
  "success": true,
  "property": {
    "id": 3799,
    "item_id": 3434,
    "property_key": "scene_style_pathfile",
    "property_value": "books/0010_great_gatsby/prompts/genimage/scene_0013.yaml",
    "created_at": "2025-08-17T11:20:48.072303",
    "updated_at": "2025-08-17T20:50:57.859394"
  }
}
```

**Property Response AFTER (2 fields - 67% reduction):**
```json
{
  "success": true,
  "property": {
    "property_key": "scene_style_pathfile",
    "property_value": "books/0010_great_gatsby/prompts/genimage/scene_0013.yaml"
  }
}
```

**Tag Response BEFORE (4 fields):**
```json
{
  "tags": [
    {
      "id": 8,
      "name": "37d_old",
      "color": "green",
      "created_at": "2025-08-17T12:52:59.357420"
    }
  ]
}
```

**Tag Response AFTER (2 fields - 50% reduction):**
```json
{
  "tags": [
    {
      "name": "37d_old",
      "color": "green"
    }
  ]
}
```

---

## Tool Categories

### 🔧 Basic Operations (19 tools)
Core functionality for list and item management.

#### List Management
- **`todo_create_list`** - Create new TODO list with optional initial items and tags (tags must exist)
- **`todo_get_list`** - 🆕 **Enhanced** - Retrieve list details with optional items and properties in single call  
- **`todo_rename_list`** - 🆕 **NEW** - Rename list key and/or title
- **`todo_delete_list`** - Delete list with dependency validation
- **`todo_archive_list`** - Archive list (hide from normal view) with completion validation 
- **`todo_unarchive_list`** - Unarchive list (restore to normal view)
- **`todo_list_all`** - List all TODO lists with progress statistics and optional tag filtering

#### Item Management  
- **`todo_add_item`** - 🆕 **UNIFIED** - Add item or subitem to list (smart detection via subitem_key parameter)
- **`todo_update_item_status`** - 🆕 **ENHANCED** - Update item or subitem status (pending/in_progress/completed/failed) with subitem_key support
- **`todo_rename_item`** - 🆕 **NEW** - Rename item key and/or title (supports subitems via subitem_key parameter)
- **`todo_delete_item`** - Delete item permanently from list
- **`todo_get_item`** - 🆕 **UNIFIED** - Get item details or subitems (smart detection via subitem_key parameter)
- **`todo_get_list_items`** - Get all items from list with optional status filter and pagination limit

#### Core Operations
- **`todo_get_next_pending`** - Get next available task with dependency consideration
- **`todo_get_progress`** - Get comprehensive progress statistics
- **`todo_quick_add`** - Add multiple items at once

### 🏗️ Advanced Operations (16 tools)
Extended functionality for complex workflows.

#### Import/Export
- **`todo_import_from_markdown`** - Import lists from markdown files (supports `- [ ]` format)
- **`todo_export_to_markdown`** - Export lists to markdown with checkboxes

#### List Relations & Properties
- **`todo_get_lists_by_relation`** - Get lists by relation type and key
- **`todo_set_list_property`** - Set key-value properties on lists
- **`todo_get_list_property`** - Get specific property value
- **`todo_get_list_properties`** - Get all properties for list
- **`todo_delete_list_property`** - Remove property from list

#### Item Properties
- **`todo_set_item_property`** - Set key-value properties on items (create/update)
- **`todo_get_item_property`** - Get specific property value from item
- **`todo_get_item_properties`** - Get all properties for item
- **`todo_get_all_items_properties`** - 🆕 **STANDARD** Get all properties for all items in list with optional status filter
- **`todo_delete_item_property`** - Remove property from item
- **`todo_find_items_by_property`** - **STANDARD** Search items by property value with optional limit

#### Project Management
- **`todo_project_overview`** - Get comprehensive project status across related lists
- **`todo_get_item_history`** - Get complete change history for items
- **`todo_get_schema_info`** - Get system schema information (available statuses, types, constants)

### 🌳 Subitem Operations (5 tools)
Hierarchical task management with parent-child relationships.

- **`todo_get_item_hierarchy`** - Get complete hierarchy tree for item
- **`todo_move_to_subitem`** - Convert existing task to subitem
- **`todo_get_next_pending_smart`** - Smart next task with subitem prioritization
- **`todo_can_complete_item`** - Check if item can be completed (no pending subitems)
- **`todo_find_subitems_by_status`** - **STANDARD** Find subitems based on sibling status conditions for complex workflow management

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

- **`todo_get_cross_list_progress`** - Progress tracking across multiple related lists
- **`todo_get_dependency_graph`** - Get dependency graph for visualization
- **`todo_get_next_pending_enhanced`** - Enhanced next task with full Phase 2 logic
- **`todo_get_comprehensive_status`** - Complete status combining all features

### 📊 Reports & Analytics (1 tool)
Generate comprehensive reports for project management and troubleshooting.

- **`todo_report_errors`** - Generate report of all failed tasks with regex and tag filtering

## Usage Examples

### 🆕 Unified Commands (v2.0.0)
```python
# NEW UNIFIED APPROACH - Smart item/subitem detection

# Add regular item
item = await todo_add_item("project", "task1", "Main task implementation")

# Add subitem using same command with subitem_key parameter
subitem = await todo_add_item("project", "task1", "Backend work", subitem_key="backend")

# Get regular item
item_data = await todo_get_item("project", "task1")

# Get all subitems of a parent
subitems = await todo_get_item("project", "task1", subitem_key="all")

# Get specific subitem
subitem_data = await todo_get_item("project", "task1", subitem_key="backend")
```

### Basic Workflow
```python
# Create list and add items
await todo_create_list("project", "My Project", items=["Task 1", "Task 2"])

# Create list with tags (tags must exist first)
await todo_create_list("webapp", "Web Application", items=["Setup", "Development", "Testing"], tags=["frontend", "project"])

# Add subitems using NEW unified command
await todo_add_item("project", "task1", "Backend implementation", subitem_key="subtask1")

# Create dependencies
await todo_add_item_dependency("frontend", "ui_task", "backend", "api_task")

# Get smart next task
next_task = await todo_get_next_pending_enhanced("project", smart_subtasks=True)
```


### Enhanced List Retrieval (New in v1.21.0)
```python
# Get complete list information in a single call (default - includes everything)
full_data = await todo_get_list(list_key="project")
# Returns: {
#   "success": True,
#   "list": {"id": 1, "list_key": "project", "title": "My Project", ...},
#   "items": {"count": 2, "data": [{"item_key": "task1", "content": "Task 1", ...}, ...]},
#   "properties": {"count": 1, "data": [{"key": "environment", "value": "production"}]}
# }

# Get only list details (no items or properties)
list_only = await todo_get_list(list_key="project", include_items=False, include_properties=False)
# Returns: {"success": True, "list": {...}}

# Get list with items but no properties
with_items = await todo_get_list(list_key="project", include_items=True, include_properties=False)
# Returns: {"success": True, "list": {...}, "items": {...}}

# Get list with properties but no items  
with_props = await todo_get_list(list_key="project", include_items=False, include_properties=True)
# Returns: {"success": True, "list": {...}, "properties": {...}}
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
await todo_update_item_status("sprint-1", "item_1", status="completed")
await todo_update_item_status("sprint-1", "item_2", status="completed")
# Update subitem status
await todo_update_item_status("sprint-1", "item_1", subitem_key="subtask_1", status="in_progress")

# Try to archive with incomplete tasks (will fail)
result = await todo_archive_list("sprint-1", force=False)
# Returns: {"success": False, "error": "Cannot archive list with incomplete tasks. Incomplete: 1/3 tasks. Use force=True to archive anyway."}

# Complete remaining tasks
await todo_update_item_status("sprint-1", "item_3", status="completed")

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

# Note: Currently there is no direct "get all tags" MCP tool
# Tags are retrieved through list operations or by using CLI commands
# Use todo_get_lists_by_tag with known tag names or CLI for tag management

# Tag deletion is handled through CLI only - no MCP tool available
# Use CLI command: todoit tag delete "beta"
# Colors automatically recalculate when tags are deleted

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
# Set properties for runtime tracking on main items
await todo_set_item_property("project", "task1", "priority", "high")
await todo_set_item_property("project", "task1", "estimated_hours", "8")
await todo_set_item_property("project", "task1", "assignee", "john_doe")

# 🆕 Set properties on subitems (NEW!)
await todo_set_item_property("project", "subtask1", "difficulty", "medium", parent_item_key="task1")
await todo_set_item_property("project", "subtask1", "category", "frontend", parent_item_key="task1")

# Get specific property from main item
priority = await todo_get_item_property("project", "task1", "priority")

# 🆕 Get specific property from subitem (NEW!)
difficulty = await todo_get_item_property("project", "subtask1", "difficulty", parent_item_key="task1")

# Get all properties for a main item
props = await todo_get_item_properties("project", "task1")
# Returns: {"priority": "high", "estimated_hours": "8", "assignee": "john_doe"}

# 🆕 Get all properties for a subitem (NEW!)
subitem_props = await todo_get_item_properties("project", "subtask1", parent_item_key="task1")
# Returns: {"difficulty": "medium", "category": "frontend"}

# Update property (automatically overwrites existing)
await todo_set_item_property("project", "task1", "priority", "critical")

# Remove property when no longer needed
await todo_delete_item_property("project", "task1", "assignee")

# 🆕 Remove property from subitem (NEW!)
await todo_delete_item_property("project", "subtask1", "category", parent_item_key="task1")

# 🆕 SEARCH for items by property values
# Find all items with high priority
high_priority_tasks = await todo_find_items_by_property("project", "priority", "high")
# Returns: {"success": true, "items": [...], "count": 3, "search_criteria": {...}}

# Find items assigned to specific person (with limit)
johns_tasks = await todo_find_items_by_property("project", "assignee", "john", limit=5)

# Find first item by issue ID (using limit=1)
tasks = await todo_find_items_by_property("project", "jira_ticket", "PROJ-123", limit=1)
# Returns: {"success": true, "items": [...], "count": 1} or {"success": true, "items": [], "count": 0}

# Example search use cases:
# - Find tasks by external references: await todo_find_items_by_property("list", "github_issue", "456")
# - Filter by review status: await todo_find_items_by_property("list", "review_status", "approved")
# - Locate by component: await todo_find_items_by_property("backend", "component", "authentication")

# 🆕 BULK PROPERTY ANALYSIS - Get all properties for comprehensive filtering
# Get all properties for all items (useful for complex analysis)
all_props = await todo_get_all_items_properties("project")
# Returns: {"success": true, "properties": [...], "count": 25, "unique_items": 8, "status_filter": null}

# Get properties only for pending items (filter by status)
pending_props = await todo_get_all_items_properties("project", "pending")
# Returns: {"success": true, "properties": [...], "count": 12, "unique_items": 4, "status_filter": "pending"}

# Get properties for completed items
completed_props = await todo_get_all_items_properties("project", "completed")

# Example: Find items with specific multi-property criteria in client code:
# 1. Get all pending item properties
# 2. Filter for image_downloaded=pending AND image_generated=completed
# This allows complex filtering that single-property search cannot handle
```

### Advanced Subtask Search by Sibling Status
```python
# 🆕 Find subitems based on sibling status conditions
# Perfect for complex workflow automation where task relationships matter

# Example: Image processing workflow with multiple stages per item
# Parent tasks have subtasks: generate, download, process, upload

# Find downloads ready to process (where generation is completed but download is pending)
ready_downloads = await todo_find_subitems_by_status(
    "images", 
    {"generate": "completed", "download": "pending"},
    limit=5
)
# Returns grouped matches with parent context - BREAKING CHANGE in v2.3.0

# Find items where upload failed but processing succeeded (needs retry)  
failed_uploads = await todo_find_subitems_by_status(
    "images", 
    {"process": "completed", "upload": "failed"},
    limit=10
)

# Find fully completed workflows (all stages done)
completed_workflows = await todo_find_subitems_by_status(
    "images", 
    {"generate": "completed", "download": "completed", "process": "completed", "upload": "completed"},
    limit=20
)

# Complex multi-stage development workflows
# Find features ready for testing (dev done, test pending)
testing_ready = await todo_find_subitems_by_status(
    "features", 
    {"development": "completed", "testing": "pending", "documentation": "completed"},
    limit=3
)

# Real-world example: CI/CD pipeline status tracking
# Find builds where tests passed but deployment is pending
deployment_ready = await todo_find_subitems_by_status(
    "releases", 
    {"build": "completed", "tests": "completed", "deployment": "pending"},
    limit=5
)

# NEW RESPONSE STRUCTURE (v2.3.0+): Grouped matches with parent context
# {
#   "success": True,
#   "matches": [
#     {
#       "parent": {
#         "id": 15,
#         "item_key": "image_batch_001", 
#         "content": "Process image batch 001",
#         "status": "in_progress",
#         "parent_item_id": null,
#         "created_at": "2025-08-15T10:30:00",
#         # ... full parent item details
#       },
#       "matching_subitems": [
#         {
#           "id": 42,
#           "item_key": "generate", 
#           "content": "Generate thumbnails",
#           "status": "completed",
#           "parent_item_id": 15,
#           "created_at": "2025-08-15T10:31:00",
#           # ... full subitem details
#         },
#         {
#           "id": 43,
#           "item_key": "download", 
#           "content": "Download processed images",
#           "status": "pending", 
#           "parent_item_id": 15,
#           "created_at": "2025-08-15T10:32:00",
#           # ... full subitem details
#         }
#       ]
#     }
#   ],
#   "matches_count": 1,  # Number of parent groups found
#   "list_key": "images",
#   "search_criteria": {
#     "conditions": {"generate": "completed", "download": "pending"},
#     "limit": 5
#   }
# }

# MAJOR IMPROVEMENT: One call replaces two!
# OLD WAY (required 2 API calls):
# 1. Find matching groups
# 2. Get parent + all subitems context
# NEW WAY (single API call):
# - Complete parent context included
# - All matching subitems grouped logically
# - Limit applies to parent groups, not individual subitems
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

All 51 tools are automatically available in Claude Code through MCP integration:

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

### 🥇 MINIMAL Level (9 tools)
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

### 🥈 STANDARD Level (+12 tools)
**Includes MINIMAL + useful extensions (21 tools total)**

**Additional tools in STANDARD:**

| Tool | Purpose |
|------|---------|
| `todo_quick_add` | Add multiple items at once |
| `todo_add_subtask` | Add subtask to existing task |
| `todo_get_subtasks` | Get all subtasks for parent |
| `todo_archive_list` | Archive list (hide from view) |
| `todo_unarchive_list` | Unarchive list (restore) |
| `todo_set_list_property` | Set key-value properties on lists |
| `todo_get_list_property` | Get specific list property |
| `todo_set_item_property` | Set key-value properties on items |
| `todo_get_item_property` | Get specific item property |
| `todo_get_all_items_properties` | 🆕 Get all properties for all items with status filter and optional limit |
| `todo_find_items_by_property` | Search items by property value |
| `todo_find_subitems_by_status` | Find subitems by sibling status conditions |
| `todo_create_tag` | Create new system tag |
| `todo_add_list_tag` | Add tag to list |

### 🥉 MAX Level (+32 tools)  
**Includes STANDARD + advanced features**

**Additional advanced tools (32 more):**
- **Cross-list dependencies** (6 tools): `todo_add_item_dependency`, `todo_remove_item_dependency`, etc.
- **Advanced subtask operations** (4 tools): `todo_get_item_hierarchy`, `todo_move_to_subitem`, etc.
- **Smart algorithms** (5 tools): `todo_get_next_pending_enhanced`, `todo_get_comprehensive_status`, etc.
- **Import/Export** (2 tools): `todo_import_from_markdown`, `todo_export_to_markdown`
- **Relations & Projects** (1 tool): `todo_project_overview`
- **Advanced properties** (4 tools): `todo_get_list_properties`, `todo_delete_item_property`, etc.
- **Analytics & Reports** (1 tool): `todo_report_errors`
- **Advanced tagging** (3 tools): `todo_remove_list_tag`, `todo_get_lists_by_tag`, etc.
- **System metadata** (1 tool): `todo_get_schema_info`
- **Destructive operations** (2 tools): `todo_delete_list`, `todo_delete_item`
- **Other specialized tools** (1 tool): `todo_get_item_history`

## Detailed Function Reference

### todo_create_list
Create a new TODO list with optional initial items and tags.

**Parameters:**
- `list_key` (str, required): Unique identifier for the list
- `title` (str, required): Display title for the list
- `items` (list[str], optional): Initial todo items to add to the list
- `list_type` (str, optional): List organization type, defaults to "sequential"
- `metadata` (dict, optional): Custom metadata for the list
- `tags` (list[str], optional): Tag names to assign to the list (tags must already exist)

**Returns:**
- `success` (bool): Operation success status
- `list` (dict): Created list details with essential fields
- `error` (str): Error message if operation failed

**Examples:**
```python
# Basic list creation
await todo_create_list("project-alpha", "Alpha Project")

# List with initial items
await todo_create_list("tasks", "My Tasks", items=["Setup", "Development", "Testing"])

# List with tags (tags must exist first)
await todo_create_list("webapp", "Web App", tags=["frontend", "urgent"])

# Complete example with all parameters
await todo_create_list(
    "complex-project", 
    "Complex Project",
    items=["Analysis", "Implementation", "Review"],
    metadata={"priority": "high", "deadline": "2024-12-31"},
    tags=["project", "development"]
)
```

**Error Handling:**
- Returns `{"success": false, "error": "Tag 'tagname' does not exist. Create it first using create_tag."}` if any specified tag doesn't exist
- List creation is atomic - if any tag validation fails, the list is not created

## Performance Considerations

- **Database Optimization** - All queries use proper indexes and foreign keys
- **Batch Operations** - `quick_add` for multiple items, bulk status updates
- **Lazy Loading** - Hierarchies and dependencies loaded on-demand
- **Caching** - Progress statistics cached for performance

## Testing Status

✅ **All 51 MCP tools tested and verified working**
- 100% functional coverage
- Error handling validated  
- Integration tested with real workflows
- Performance verified under load

---

*Last updated: August 20, 2025 - API consistency fix: standardized parameter naming across all tools*