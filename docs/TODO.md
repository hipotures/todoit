# TODOIT - Missing Functionality & TODO Items

## Overview

This document tracks functionality gaps between the core manager/database layer and the user-facing interfaces (MCP tools and CLI commands). While many features exist in the backend, they're not exposed to users.

## Critical Missing Features

### 1. 🗑️ **Item Deletion**
**Status:** ❌ Missing from both MCP and CLI  
**Backend:** ✅ Available (`manager.delete_item()`, `database.delete_item()`)

**Impact:** Users cannot remove tasks from lists once created
**Priority:** HIGH

**Needed:**
- [ ] `todo_delete_item` MCP tool
- [ ] `todoit item delete <list> <item>` CLI command
- [ ] Confirmation prompts for safety
- [ ] Cascade deletion handling for subtasks

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

### 6. 🤖 **JSON Output for Systems/Scripts**
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

## Interface-Specific Gaps

### MCP Tools Missing
```
todo_delete_item          - Remove task from list
todo_update_item_content  - Edit task description  
todo_bulk_update_status   - Update multiple items
todo_bulk_delete         - Delete multiple items
todo_search              - Content-based search
todo_copy_item           - Duplicate tasks
todo_move_item_to_list   - Transfer between lists
```

### CLI Commands Missing
```
todoit item delete       - Remove tasks
todoit item edit         - Edit task content
todoit item copy         - Duplicate tasks  
todoit item move         - Transfer between lists
todoit search           - Find tasks by content
todoit bulk             - Bulk operations group
TODOIT_OUTPUT_FORMAT=json - Extend JSON support to all commands
```

## Data Model Enhancements Needed

### 1. **Soft Deletion**
- Add `deleted_at` timestamp field
- Implement soft delete to prevent data loss
- Allow recovery of deleted items

### 2. **Item Versioning**
- Track content changes over time
- Allow rollback to previous versions
- Enhanced history beyond status changes

### 3. **Templates System**
- Reusable task templates
- Project templates with predefined structure
- Variable substitution in templates

## Implementation Priority

### Phase 1: Critical CRUD Operations
1. **Item Deletion** - Both MCP and CLI
2. **Content Editing** - Manager + interfaces
3. **Basic Search** - Content filtering

### Phase 2: Productivity Features  
1. **Bulk Operations** - Multiple item management
2. **Advanced Search** - Property/date filtering
3. **Copy/Move Operations**

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

## Current Status: 45/50+ Expected Tools

The system currently provides 45 MCP tools but lacks several fundamental CRUD operations that users expect from a task management system.

---

*Last updated: 2025-08-07*
*Status: Planning phase - ready for implementation*