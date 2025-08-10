# Changelog

All notable changes to TODOIT MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.15.1] - 2025-08-10

### Fixed
- **🐛 Critical Fix: List deletion with tags** - Fixed FOREIGN KEY constraint error when deleting lists with tags
  - **Issue**: `todoit list delete` command failed with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`
  - **Root Cause**: Missing cleanup of `ListTagAssignmentDB` records before list deletion
  - **Solution**: Added proper tag assignment cleanup in `delete_list()` method
  - **Impact**: All lists with tags can now be deleted successfully via CLI and MCP tools

### Added
- **🧪 Comprehensive Test Coverage**: New unit tests for list deletion scenarios with tags
  - `tests/unit/test_delete_list_with_tags.py` - 5 test cases covering all tag deletion scenarios
  - Tests single tag, multiple tags, complex data combinations, and CLI reproduction scenarios
  - Ensures future regression prevention for tag-related list operations

### Technical Details
- **File Modified**: `core/manager.py:193` - Added `ListTagAssignmentDB` cleanup
- **Test Coverage**: 393 tests passing (5 new tests added)
- **Backward Compatibility**: No breaking changes, existing functionality preserved

## [1.15.0] - 2025-08-10

### Added
- **🎛️ MCP Tools Level Configuration System**: New 3-level system to optimize token usage and performance
  - **MINIMAL** (10 tools): Essential operations only, 82% token savings
  - **STANDARD** (23 tools): Balanced functionality, 58% token savings (new default)
  - **MAX** (55 tools): Complete feature set (previous behavior)
- **Environment Variable Configuration**: `TODOIT_MCP_TOOLS_LEVEL` controls available tools
- **Conditional Tool Registration**: New `@conditional_tool` decorator for dynamic tool loading
- **Security Benefits**: MINIMAL and STANDARD levels exclude destructive operations (`delete_list`, `delete_item`)
- **Comprehensive Documentation**: Updated MCP_TOOLS.md with detailed level breakdowns and performance metrics

### Changed
- **Default MCP Level**: Changed from MAX (55 tools) to STANDARD (23 tools) for better performance
- **MCP Server Architecture**: Reorganized tools by level categories for better maintainability
- **Test Coverage**: Added comprehensive unit tests for all tool levels

### Fixed
- **List Linking CLI**: Fixed issue where linked lists weren't visible due to tag filtering
- **Test Environment Isolation**: Fixed integration tests failing due to FORCE_TAGS conflicts
- **MCP Tools Count Test**: Updated to work with new conditional tool system

### Technical Details
- **Token Context Reduction**: 58-82% reduction in MCP context tokens depending on level
- **Performance Impact**: ~500-1000 tokens (MINIMAL) vs 3000+ tokens (MAX)
- **Backward Compatibility**: Existing configurations work unchanged (defaults to STANDARD)
- **Tool Categories**: Organized into Basic Operations, Advanced, Subtasks, Dependencies, Smart Algorithms, Tags, Reports

### Migration Guide
- **No action required**: Existing setups automatically get STANDARD level (23 tools)
- **For maximum features**: Set `TODOIT_MCP_TOOLS_LEVEL=MAX` (previous behavior)
- **For minimal setup**: Set `TODOIT_MCP_TOOLS_LEVEL=MINIMAL` (10 essential tools)

## [1.14.3] - 2025-08-09

### Added
- Complete comprehensive environment isolation with FORCE_TAGS across all CLI commands

### Fixed
- FORCE_TAGS environment isolation for all list and item commands
- Unit tests for flag_value status command solution

## [1.14.2] - 2025-08-09

### Fixed  
- FORCE_TAGS environment isolation for all item commands
- Add FORCE_TAGS environment isolation to all list commands

## [1.14.1] - Previous releases

### Features
- 55 comprehensive MCP tools for Claude Code integration
- Smart task selection algorithms with subtask prioritization  
- Cross-list dependency management
- Hierarchical task organization with subtasks
- List linking with 1:1 task mapping
- Archive management with completion validation
- Tag-based organization and filtering
- Comprehensive progress tracking and analytics
- Import/export functionality (Markdown support)
- Advanced properties system for lists and items
- Real-time monitoring and live updates
- Comprehensive error reporting and analytics

[1.15.0]: https://github.com/todoit/todoit-mcp/compare/v1.14.3...v1.15.0
[1.14.3]: https://github.com/todoit/todoit-mcp/compare/v1.14.2...v1.14.3
[1.14.2]: https://github.com/todoit/todoit-mcp/compare/v1.14.1...v1.14.2