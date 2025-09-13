# TODOIT MCP v2.14.0 Release Notes
*Released: September 13, 2025*

## 🚀 Major Release: Universal Item Search Revolution

This release introduces a game-changing universal search function that replaces and extends the previous subitem search functionality with powerful new capabilities.

---

## ⭐ **Key Highlights**

### 🎯 **Universal Search Function: `todo_find_items_by_status`**
One function, four powerful modes:
- **Simple**: `todo_find_items_by_status("pending")`
- **Multiple**: `todo_find_items_by_status(["pending", "in_progress"])` (OR logic)
- **Complex**: `todo_find_items_by_status({"item": {"status": "in_progress"}, "subitem": {"download": "pending"}})`
- **Legacy**: `todo_find_items_by_status({"download": "pending"}, "list1")` (100% backwards compatible)

### 📱 **New CLI Command: `todoit item find-status`**
Rich, powerful search with modern features:
```bash
# Multiple statuses with OR logic
todoit item find-status --status pending --status in_progress

# Complex conditions for workflows
todoit item find-status --complex '{"item": {"status": "in_progress"}, "subitem": {"download": "pending"}}'

# Export capabilities
todoit item find-status --status completed --export json
```

### 🔍 **Cross-List Search**
Search across ALL your lists simultaneously when `--list` is not specified - no more manual list-by-list searching!

---

## ⚠️ **Breaking Changes**

### Removed: `todo_find_subitems_by_status`
The old MCP tool has been removed and replaced with the universal function.

**Migration is simple:**
```python
# OLD (removed)
await todo_find_subitems_by_status("list1", {"download": "pending"}, 10)

# NEW (recommended) - just swap parameter order
await todo_find_items_by_status({"download": "pending"}, "list1", 10)
```

**No functionality lost:** The new function provides 100% backwards compatibility through automatic legacy format detection.

---

## ✨ **New Features**

### 🔍 **Multi-Mode Search Engine**
- **Simple status**: Find all items with a specific status
- **Multiple statuses**: OR logic for finding items with any of several statuses
- **Complex conditions**: Advanced item+subitem combinations for sophisticated workflow automation
- **Legacy mode**: Seamless compatibility with existing subitem search patterns

### 📊 **Enhanced Response Data**
- **Intelligent formatting**: Auto-detects search mode and formats responses accordingly
- **Rich statistics**: Status breakdowns, list distributions, and match counts
- **Context awareness**: Automatic hierarchy information and cross-list context

### 🏷️ **Environment Isolation**
Full support for `filter_tags` across all modes for secure multi-environment workflows.

### 📤 **Export Capabilities**
Built-in JSON and CSV export for search results:
```bash
todoit item find-status --status completed --export csv --limit 100
```

---

## 🔧 **Technical Improvements**

### 🗄️ **Database Optimizations**
- **6 new optimized query methods** leveraging existing composite indexes
- **Single-query cross-list searches** eliminate N+1 query patterns
- **Performance gains** especially noticeable with large datasets

### 🧪 **Comprehensive Testing**
- **15+ test methods** covering all search modes and edge cases
- **Integration tests** for MCP, CLI, and core functionality
- **Backwards compatibility validation** ensures no regressions

### 📈 **Scalability Enhancements**
- **Efficient pagination** with proper limit handling
- **Memory optimization** for large result sets
- **Response streaming** for better performance with high-volume searches

---

## 📚 **Documentation Updates**

### Updated Guides
- **MCP_TOOLS.md**: Enhanced with new function examples and comprehensive migration guide
- **CLI_GUIDE.md**: New section for `item find-status` command with real-world examples
- **CHANGELOG.md**: Detailed release notes with usage examples

### Migration Resources
- **Complete migration guide** with before/after examples
- **Best practices** for leveraging new search modes
- **Performance tips** for large-scale deployments

---

## 🎯 **Real-World Use Cases**

### Workflow Automation
```python
# Find items ready for next stage
ready_for_testing = await todo_find_items_by_status({
    "item": {"status": "in_progress"},
    "subitem": {"code": "completed", "review": "completed", "test": "pending"}
})
```

### Cross-Project Monitoring
```bash
# Find all failed items across all projects
todoit item find-status --status failed --export csv
```

### Status Reporting
```python
# Get all active work across projects
active_work = await todo_find_items_by_status(["pending", "in_progress"], limit=50)
```

---

## 🚀 **Getting Started**

### Installation
```bash
pip install --upgrade todoit-mcp==2.14.0
```

### Quick Start
```python
# Try the new universal search
from interfaces.mcp_server import todo_find_items_by_status

# Simple search
pending = await todo_find_items_by_status("pending")

# Multi-status search
active = await todo_find_items_by_status(["pending", "in_progress"])

# Complex workflow search
ready = await todo_find_items_by_status({
    "item": {"status": "in_progress"},
    "subitem": {"build": "completed", "test": "pending"}
})
```

### CLI Examples
```bash
# Cross-list pending search
todoit item find-status --status pending

# Export completed tasks
todoit item find-status --status completed --export json

# Complex workflow query
todoit item find-status --complex '{"subitem": {"generate": "completed", "download": "pending"}}'
```

---

## 🤝 **Community & Support**

- **GitHub Issues**: Report bugs or request features at [claude-code/issues](https://github.com/anthropics/claude-code/issues)
- **Documentation**: Complete guides at [TODOIT MCP Docs](../docs/)
- **Migration Help**: Detailed examples in [CHANGELOG.md](CHANGELOG.md)

---

## 🙏 **Acknowledgments**

This release represents a major leap forward in TODOIT's search capabilities, delivering the flexibility and power that our community has requested. The universal search function streamlines workflows while maintaining full backwards compatibility.

Special thanks to all users who provided feedback on the previous search functionality - your insights directly shaped this release.

---

**Full Changelog**: [v2.13.4...v2.14.0](CHANGELOG.md#2140---2025-09-13)