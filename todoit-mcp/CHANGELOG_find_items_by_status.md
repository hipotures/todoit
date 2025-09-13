# CHANGELOG - find_items_by_status Implementation

## New Feature: Universal Item Search Function

### Summary
Added `todo_find_items_by_status` - a universal function that replaces and extends `todo_find_subitems_by_status` with support for multiple search modes.

### 🎯 Core Implementation

#### 1. **Manager API (core/manager.py)**
```python
def find_items_by_status(
    self,
    conditions: Union[str, List[str], Dict[str, Any]],
    list_key: Optional[str] = None,
    limit: int = 10,
) -> Union[List[TodoItem], List[Dict[str, Any]]]:
```

**Modes:**
- **Simple**: `find_items_by_status("pending")`
- **Multiple**: `find_items_by_status(["pending", "in_progress"])`
- **Complex**: `find_items_by_status({"item": {"status": "in_progress"}, "subitem": {"download": "pending"}})`
- **Legacy**: `find_items_by_status({"download": "pending"}, "list1")` (backwards compatible)

#### 2. **Database Layer (core/database.py)**
New optimized methods:
- `get_items_by_status()` - single status, single list
- `get_items_by_status_all_lists()` - single status, all lists
- `get_items_by_statuses()` - multiple statuses (OR), single list
- `get_items_by_statuses_all_lists()` - multiple statuses (OR), all lists
- `find_items_by_complex_conditions()` - item+subitem conditions, single list
- `find_items_by_complex_conditions_all_lists()` - item+subitem conditions, all lists

**Performance:** Leverages existing composite indexes:
- `idx_todo_items_list_status` - for (list_id, status) queries
- `idx_todo_items_parent_status` - for subitem status queries

### 🛠️ MCP Integration

#### New MCP Tool: `todo_find_items_by_status`
```python
# Simple search
await todo_find_items_by_status("pending")

# Multiple statuses
await todo_find_items_by_status(["pending", "in_progress"], limit=20)

# Complex conditions
await todo_find_items_by_status({
    "item": {"status": "in_progress"},
    "subitem": {"download": "pending", "generate": "completed"}
})
```

**Features:**
- Cross-list searching (`list_key=None`)
- Environment isolation (`filter_tags`)
- Intelligent response formatting based on query type
- Full backwards compatibility with `todo_find_subitems_by_status`

**Response Formats:**
```python
# Simple/Multiple modes
{
    "success": true,
    "mode": "simple|multiple",
    "items": [...],
    "count": 10,
    "statistics": {...}
}

# Complex mode
{
    "success": true,
    "mode": "complex|subitems",
    "matches": [{"parent": {...}, "matching_subitems": [...]}],
    "count": 5
}
```

### 📱 CLI Integration

#### New Command: `todoit item find-status`
```bash
# Simple status search
todoit item find-status --status pending

# Multiple statuses (OR logic)
todoit item find-status --status pending --status in_progress --list myproject

# Complex conditions
todoit item find-status --complex '{"item": {"status": "in_progress"}, "subitem": {"download": "pending"}}'

# Advanced options
todoit item find-status --status completed --export json --limit 50
todoit item find-status --status pending --no-subitems --group-by-list
```

**Features:**
- Rich table formatting with conditional columns
- Cross-list search with list context
- JSON/CSV export capabilities
- Environment isolation support
- Subitem filtering options

### ✅ Testing Coverage

#### Comprehensive Test Suite: `tests/integration/test_find_items_by_status.py`

**Test Categories:**
1. **Simple Status Search** - string conditions
2. **Multiple Status Search** - list conditions with OR logic
3. **Complex Conditions** - dict with item/subitem combinations
4. **Backwards Compatibility** - legacy dict format
5. **Edge Cases** - error conditions, empty results
6. **Cross-List Search** - multi-list functionality

**Test Scenarios:**
- ✅ 15+ test methods covering all modes
- ✅ Error condition handling
- ✅ Backwards compatibility verification
- ✅ Cross-list search validation
- ✅ Limit and pagination testing

### 🔄 Migration & Compatibility

#### Backwards Compatibility
- **100% compatible** with existing `todo_find_subitems_by_status` calls
- Automatic detection of legacy format (dict without 'item'/'subitem' keys)
- Legacy MCP alias: `todo_find_subitems_by_status_legacy` (deprecated)

#### Migration Examples
```python
# OLD (still works)
manager.find_subitems_by_status("images", {"download": "pending", "generate": "completed"})

# NEW (recommended)
manager.find_items_by_status({"download": "pending", "generate": "completed"}, "images")

# NEW (with explicit structure)
manager.find_items_by_status({
    "subitem": {"download": "pending", "generate": "completed"}
}, "images")
```

### 📊 Performance Improvements

#### SQL Optimizations
- **Existing indexes utilized** - no schema changes needed
- **Efficient queries** - proper use of composite indexes
- **Bulk operations** - single queries instead of N+1 patterns
- **Cross-list optimization** - single query for multi-list searches

#### Query Examples
```sql
-- Simple status (single list)
SELECT * FROM todo_items
WHERE list_id = ? AND status = ?
ORDER BY position, item_key LIMIT ?;

-- Multiple statuses (OR logic)
SELECT * FROM todo_items
WHERE list_id = ? AND status IN (?, ?)
ORDER BY position, item_key LIMIT ?;

-- Complex conditions (item + subitems)
SELECT DISTINCT parent.* FROM todo_items parent
WHERE parent.status = ? AND parent.parent_item_id IS NULL
  AND EXISTS (SELECT 1 FROM todo_items sub
             WHERE sub.parent_item_id = parent.id
               AND sub.item_key = ? AND sub.status = ?)
LIMIT ?;
```

### 📝 Documentation

#### Updated Files
- `docs/MCP_TOOLS.md` - New MCP tool documentation
- `docs/CLI_GUIDE.md` - New CLI command examples
- `docs/api.md` - Manager API documentation
- `CHANGELOG.md` - Release notes with migration guide

#### Key Examples Added
- All search modes with real-world scenarios
- Performance considerations and best practices
- Migration path from legacy functions
- Error handling and edge cases

### 🚀 Usage Examples

#### Real-world Scenarios

**1. Find Ready-to-Process Items**
```python
# Find items that are in_progress with completed generation and pending download
await todo_find_items_by_status({
    "item": {"status": "in_progress"},
    "subitem": {"generate": "completed", "download": "pending"}
}, "images")
```

**2. Cross-List Status Report**
```python
# Get all failed items across all projects for review
await todo_find_items_by_status("failed", filter_tags=["production"])
```

**3. Workflow Management**
```bash
# Find all pending work in active projects
todoit item find-status --status pending --status in_progress --export csv
```

**4. Quality Assurance**
```python
# Find completed items that might need review
completed_items = manager.find_items_by_status(["completed"], limit=50)
```

This implementation provides a powerful, flexible, and backwards-compatible solution for item searching across the TODOIT ecosystem.