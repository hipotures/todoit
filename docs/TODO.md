# TODOIT - Missing Functionality & TODO Items

## Overview

This document tracks functionality gaps between the core manager/database layer and the user-facing interfaces (MCP tools and CLI commands). While many features exist in the backend, they're not exposed to users.

## Critical Missing Features

### 1. 🗑️ **Item Deletion** ✅ COMPLETED
**Status:** ✅ **IMPLEMENTED** - Available in current version
**Backend:** ✅ Available (`manager.delete_item()`, `database.delete_item()`)

**Impact:** ✅ **RESOLVED** - Users can remove tasks from lists with proper confirmation
**Priority:** ~~HIGH~~ **COMPLETED**

**Implemented:**
- [x] `todo_delete_item` MCP tool (interfaces/mcp_server.py:1443)
- [x] `todoit item delete <list> <item> [--force]` CLI command (cli_modules/item_commands.py:344)  
- [x] Confirmation prompts for safety (with --force flag to skip)
- [x] Cascade deletion handling for subtasks and dependencies
- [x] Comprehensive test coverage in test_item_management.py

### 2. ✏️ **Item Content Editing**
**Status:** ❌ No content editing capability  
**Backend:** ❌ Not implemented in manager

**Impact:** Users cannot fix typos or update task descriptions
**Priority:** HIGH

**Needed:**
- [ ] `manager.update_item_content()` method
- [ ] `todo_update_item` MCP tool (beyond just status)
- [ ] `todoit item edit <list> <item>` CLI command
- [ ] History tracking for content changes

### 3. 📋 **Bulk Operations**
**Status:** ❌ Limited bulk support  
**Backend:** ✅ Partial (`quick_add` only)

**Impact:** Inefficient for managing many tasks
**Priority:** MEDIUM

**Needed:**
- [ ] `todo_bulk_update_status` - update multiple items at once
- [ ] `todo_bulk_delete` - delete multiple items
- [ ] `todo_bulk_move` - move multiple items between lists
- [ ] CLI support for bulk operations with patterns

### 4. 🔍 **Advanced Search & Filtering**
**Status:** ❌ Basic filtering only  
**Backend:** ✅ Partial (status filtering only)

**Impact:** Hard to find specific tasks in large projects
**Priority:** MEDIUM

**Needed:**
- [ ] `todo_search` MCP tool with content search
- [ ] Property-based filtering
- [ ] Date range filtering (created_at, completed_at)
- [ ] `todoit search <query>` CLI command
- [ ] Regex support for advanced queries

### 5. 📦 **Item/List Management**
**Status:** ❌ Missing advanced operations  
**Backend:** ❌ Not implemented

**Impact:** Limited project management capabilities
**Priority:** MEDIUM

**Needed:**
- [ ] `todo_copy_item` - duplicate tasks
- [ ] `todo_copy_list` - duplicate entire lists
- [ ] `todo_move_item_to_list` - transfer between lists
- [ ] `todo_archive_list` - hide completed projects
- [ ] Template system for common task patterns

### 6. 🔄 **Reset Commands for Lists and Items**
**Status:** ❌ Missing reset functionality
**Backend:** ❌ Not implemented

**Impact:** No way to quickly reset failed tasks or restore lists to initial state
**Priority:** HIGH

**Needed:**
- [ ] `list reset errors` command - changes all "failed" status to "pending" (no confirmation)
- [ ] `list reset all` command - changes all statuses to "pending" + clears all item properties (with confirmation, --force to skip)
- [ ] `item reset` command - reset individual items
- [ ] `manager.reset_list()` methods in core
- [ ] `todo_reset_list` MCP tools

### 7. 🏷️ **Tags System for Lists**
**Status:** ❌ Missing tagging system
**Backend:** ❌ Not implemented

**Impact:** Cannot organize and categorize lists by topics/projects
**Priority:** MEDIUM

**Needed:**
- [ ] Database schema for tags (many-to-many relationship)
- [ ] `manager.add_tag()`, `manager.remove_tag()`, `manager.get_lists_by_tag()` methods
- [ ] CLI commands: `list tag add/remove/list`
- [ ] MCP tools for tag management
- [ ] Tag filtering in list views
- [ ] Tag-based search and organization

### 8. 🤖 **JSON Output for Systems/Scripts**
**Status:** ❌ Missing structured output  
**Backend:** ✅ Available (all data models support JSON)

**Impact:** Scripts and automation tools cannot easily parse CLI output
**Priority:** MEDIUM

**Needed:**
- [ ] Extend existing `TODOIT_OUTPUT_FORMAT=json` support to all commands
- [ ] Structured JSON output instead of human-readable text
- [ ] Consistent schema across all commands
- [ ] Error responses in JSON format when JSON mode is enabled
- [ ] Documentation for JSON schemas

### 9. 📊 **Enhanced List Overview with Task Status Counts** ✅ COMPLETED
**Status:** ✅ **IMPLEMENTED** - Enhanced in v1.11.0 (2025-08-09)
**Backend:** ✅ Status information available and now aggregated

**Impact:** ✅ **RESOLVED** - Full visibility into task distribution across statuses for project management
**Priority:** ~~MEDIUM~~ **COMPLETED**

**Implemented:**
- [x] Enhanced `todo_list_all` MCP tool to include comprehensive progress statistics for each list
- [x] Added dedicated status columns in CLI: 📋 (pending), 🔄 (in_progress), ❌ (failed), ✅ (completed)
- [x] Failed column (❌) always visible even when no failed tasks (shows "0")
- [x] Complete status count breakdown in both CLI table and MCP JSON responses
- [x] Percentage completion metrics included in progress data
- [x] Total task count per list with detailed breakdowns
- [x] Optimized performance with proper progress aggregation

**Release:** Available in v1.11.0 with comprehensive test coverage and documentation updates.

## Interface-Specific Gaps

### MCP Tools Missing
```
~~todo_delete_item~~      - ✅ COMPLETED - Remove task from list
todo_update_item_content  - Edit task description  
todo_bulk_update_status   - Update multiple items
todo_bulk_delete         - Delete multiple items
todo_search              - Content-based search
todo_copy_item           - Duplicate tasks
todo_move_item_to_list   - Transfer between lists
todo_reset_list          - Reset list items (errors/all modes)
todo_add_list_tag        - Add tag to list
todo_remove_list_tag     - Remove tag from list
todo_get_lists_by_tag    - Get lists filtered by tag
```

### CLI Commands Missing
```
~~todoit item delete~~   - ✅ COMPLETED - Remove tasks
todoit item edit         - Edit task content
todoit item copy         - Duplicate tasks  
todoit item move         - Transfer between lists
todoit list reset        - Reset list (errors/all modes with --force option)
todoit item reset        - Reset individual items
todoit list tag          - Tag management (add/remove/list tags)
todoit search           - Find tasks by content
todoit bulk             - Bulk operations group
TODOIT_OUTPUT_FORMAT=json - Extend JSON support to all commands
```

## Data Model Enhancements Needed

### 1. **Tags System**
- Add `tags` table with many-to-many relationship to lists
- List-Tag junction table for associations
- Tag-based filtering and organization

### 2. **Soft Deletion**
- Add `deleted_at` timestamp field
- Implement soft delete to prevent data loss
- Allow recovery of deleted items

### 3. **Item Versioning**
- Track content changes over time
- Allow rollback to previous versions
- Enhanced history beyond status changes

### 4. **Templates System**
- Reusable task templates
- Project templates with predefined structure
- Variable substitution in templates

## Implementation Priority

### Phase 1: Critical CRUD Operations
1. **Reset Commands** - List and item reset functionality (errors/all modes)  
2. ~~**Item Deletion**~~ - ✅ **COMPLETED** - Both MCP and CLI implemented
3. **Content Editing** - Manager + interfaces
4. **Basic Search** - Content filtering

### Phase 2: Productivity Features  
1. **Tags System** - List tagging and organization
2. **Bulk Operations** - Multiple item management
3. **Advanced Search** - Property/date filtering
4. **Copy/Move Operations**

### Phase 3: Advanced Features
1. **Template System**
2. **Soft Deletion & Recovery**
3. **Advanced History & Versioning**

## Notes

- All new MCP tools need proper error handling with `@mcp_error_handler`
- CLI commands should follow existing patterns and include `--force` flags
- Database schema changes require migration scripts
- Maintain backward compatibility with existing data
- Add comprehensive tests for all new functionality

## Current Status: 46/50+ Expected Tools  

The system currently provides 46 MCP tools (including completed `todo_delete_item`). Main gaps are now content editing, bulk operations, and advanced search features.

---

*Last updated: 2025-08-09*
*Status: Planning phase - ready for implementation*