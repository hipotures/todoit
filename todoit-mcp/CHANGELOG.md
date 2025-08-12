# Changelog

All notable changes to TODOIT MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.18.1] - 2025-08-12

### Changed
- **🔧 API Simplification**: Removed redundant `todo_find_item_by_property` MCP tool
  - **Unified Interface**: Use `todo_find_items_by_property` with `limit=1` for single results
  - **Better Design**: One function with optional parameters > multiple functions
  - **Cleaner API**: Reduced from 57 to 56 total MCP tools
  - **Updated Examples**: Documentation shows `limit=1` usage instead of separate function
  - **Backward Compatibility**: All functionality preserved with cleaner interface

### Technical
- **Code Reduction**: Removed ~126 lines of redundant code
- **Test Updates**: Integrated tests now use unified approach
- **Documentation**: Updated MCP_TOOLS.md with simplified examples

## [1.18.0] - 2025-08-12

### Added
- **🔍 Property-Based Item Search**: New comprehensive search functionality for finding items by custom properties
  - **Database Layer**: `find_items_by_property()` function with optimized SQL JOIN queries and optional LIMIT support
  - **Core Manager**: `find_items_by_property()` business logic function
  - **CLI Command**: `todoit item find` with options: `--property`, `--value`, `--limit`, `--first`
  - **MCP Tools**: `todo_find_items_by_property` for external integration
  - **Standard MCP Integration**: Added `todo_find_items_by_property` to basic MCP tool set (~20 essential tools)
  - **Performance Optimization**: Added composite database index `idx_item_properties_key_value` for fast property searches
  - **JSON Output Support**: Full support for `TODOIT_OUTPUT_FORMAT` environment variable (JSON/YAML/XML)
  - **Comprehensive Testing**: 29 unit and integration tests covering all search scenarios and edge cases

### Performance
- **Database Indexing**: Added optimized composite index on `item_properties(property_key, property_value)` for efficient search queries
- **Query Optimization**: SQL JOIN implementation with position-based ordering and configurable result limits

## [1.17.0] - 2025-08-12

### Added
- **🚀 Complete JSON Output Support**: All CLI commands now support unified output formats
  - **New Format Support**: Added JSON, YAML, XML output formats to all remaining commands
  - **Commands Updated**: `item tree`, `dep show`, `schema`, `dep graph` now support `TODOIT_OUTPUT_FORMAT`
  - **Unified Display System**: Migrated all commands to consistent display system for better format support
  - **Rich Documentation**: Added comprehensive output format documentation to README.md

### Fixed
- **🔧 Advanced Command JSON Output**: Enhanced JSON support for complex display commands
  - **Item Tree**: `todoit item tree` - Hierarchical task display with proper JSON serialization
  - **Dependency Show**: `todoit dep show` - Structured dependency analysis in all formats
  - **System Schema**: `todoit schema` - System information with categorized output
  - **Dependency Graph**: `todoit dep graph` - Project dependency visualization
  - **Enhanced Testing**: Added 41 comprehensive integration tests for all new JSON output features
  - **Backward Compatible**: All existing table format behavior preserved

### Changed
- **📋 Display System Improvements**: Enhanced unified display architecture
  - **Consistent Structure**: All commands now use standardized data formatting
  - **Format Detection**: Automatic format switching based on `TODOIT_OUTPUT_FORMAT` environment variable
  - **Error Handling**: Improved error handling for malformed references and edge cases

## [1.16.6] - 2025-08-12

### Fixed
- **🔧 JSON Output Support for Property Commands**: Fixed `TODOIT_OUTPUT_FORMAT=json` support for property list commands
  - **List Properties**: `todoit list property list` now properly supports JSON, YAML, XML output formats
  - **Item Properties**: `todoit item property list` (both single item and all items) now supports all output formats
  - **Unified Display**: Migrated property commands to use unified display system for consistent formatting
  - **Comprehensive Testing**: Added 7 integration tests covering all property command scenarios and output formats
  - **Backward Compatible**: Table format (default) remains unchanged and fully functional

## [1.16.4] - 2025-08-10

### Changed
- **🎨 Improved Tag Colors**: Updated tag color palette for better visual comfort
  - **Dimmed Primary Colors**: Changed first 5 colors to `dim red`, `dim green`, `dim blue`, `dim yellow`, `dim white` for subtler appearance
  - **Balanced Final Colors**: Changed last 2 colors from `bright_green`, `bright_red` to standard `green`, `red`
  - **Enhanced Readability**: More consistent and less aggressive color scheme across all tag displays

## [1.16.3] - 2025-08-10

### Added
- **📄 List Items Pagination**: Added `limit` parameter to `todo_get_list_items` MCP tool for pagination support
  - **Enhanced Response**: Added `more_available` and `total_count` fields for pagination metadata
  - **Hierarchical Support**: Limit works with both flat and hierarchical task structures
  - **Status Filtering**: Limit parameter works in combination with status filtering
  - **Comprehensive Testing**: 17 unit tests covering all edge cases and scenarios

## [1.16.0] - 2025-08-10

### Added
- **🏷️ 12-Color Tag System**: Complete visual tag system with automatic color assignment
  - **12 Distinct Colors**: `red`, `green`, `blue`, `yellow`, `orange`, `purple`, `cyan`, `magenta`, `pink`, `grey`, `bright_green`, `bright_red`
  - **Automatic Color Assignment**: New tags automatically receive next available color in sequence (index-based)
  - **Tag Limit Enforcement**: System prevents creation of more than 12 tags to maintain visual clarity
  - **Error Messaging**: Clear error message when attempting to create 13th tag: "Maximum number of tags reached (12). Cannot create more tags with distinct colors."

### Changed
- **🎨 Enhanced CLI Display**: Added tags column (🏷️) to `list all` commands showing colored dots
  - **Tags Legend**: Automatic legend displays below tables showing all used tags with colors
  - **Visual Recognition**: Tags appear as colored dots (●) for immediate identification
  - **Consistent Ordering**: Tags displayed alphabetically for predictable organization
- **🔧 Improved Tag Creation**: Default tag creation now uses automatic color assignment instead of always defaulting to blue
  - **CLI**: `todoit tag create <name>` automatically assigns next available color
  - **MCP**: `todo_create_tag` with no color parameter uses automatic assignment
  - **Override**: Explicit color specification still available and overrides auto-assignment

### Fixed
- **🐛 Rich Color Display**: Fixed colored tag dots not displaying correctly in CLI
  - **Issue**: Tags showed as plain text "● blue" instead of colored dots
  - **Solution**: Removed special case handling for blue color, added underscore support to color validation regex
  - **Result**: All 12 colors now display properly with Rich formatting
- **✅ Test Compatibility**: Updated integration tests to handle new table format with tags column
  - **Issue**: Archive CLI tests failing due to changed table structure after adding 🏷️ column
  - **Solution**: Modified test assertions to handle multi-line table entries and truncated names
  - **Coverage**: All archive workflow tests now pass with new display format

### Technical Details
- **Model Validation**: Updated `ListTag` color field regex to accept underscores for `bright_green`/`bright_red`
- **Automatic Color Logic**: Implemented index-based color assignment in `_get_next_available_color()` method
- **Display System**: Added tag retrieval and formatting logic to list display components
- **Database**: No schema changes required - existing tag system extended with color management
- **Performance**: O(1) color assignment based on tag count, efficient legend generation

### Developer Impact
- **11 New Unit Tests**: Comprehensive test suite for tag color system including edge cases
- **Documentation Updated**: MCP_TOOLS.md includes new tag system documentation with examples
- **Backward Compatibility**: Existing tags retain their colors, no migration needed
- **API Consistency**: All MCP tools include color information in tag responses

### User Benefits
- **Visual Clarity**: Easy tag identification with 12 distinct, visually optimized colors
- **Zero Configuration**: Automatic color management requires no user intervention  
- **Predictable Workflow**: Consistent color assignment and display across all interfaces
- **Professional Appearance**: Clean, organized tag display with legend support

## [1.15.2] - 2025-08-10

### Changed
- **📋 Improved List Sorting**: Changed default list sorting from ID to alphabetical by list key
  - **CLI Tables**: All `todoit list all` commands now show lists sorted alphabetically by list key
  - **MCP Tools**: `todo_list_all` and related MCP tools return lists in alphabetical order by key
  - **Tree View**: Hierarchical list displays also use alphabetical sorting
  - **Consistency**: Both CLI and MCP interfaces now use the same predictable sorting order

### Technical Details
- **Database Layer**: Modified `get_all_lists()` and `get_lists_by_tags()` to use `ORDER BY list_key ASC`
- **CLI Layer**: Updated sorting logic from `key=lambda x: x.id` to `key=lambda x: x.list_key`
- **Display Layer**: Tree views and all list displays now consistently use alphabetical sorting
- **Backward Compatibility**: No breaking changes, only improved user experience

### User Impact
- **Before**: Lists displayed in creation order (ID-based): `zebra`, `alpha`, `beta` (IDs: 1, 2, 3)
- **After**: Lists displayed alphabetically: `alpha`, `beta`, `zebra` (more intuitive ordering)
- **Benefit**: Easier to find lists in large projects with many lists

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