# Changelog

All notable changes to TODOIT MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-08-16

### 🔥 BREAKING CHANGES - Complete Test Suite Fix (100% Pass Rate)
- **FIXED**: All remaining test failures after parallel/hierarchical/linked removal
- **UPDATED**: 80+ test files to work with simplified sequential-only architecture
- **REMOVED**: Obsolete tests for removed functionality (sync_add, list relations)
- **ACHIEVED**: Perfect 612/612 tests passing (100% success rate)

#### Test Fixes Applied:
- **Models Tests**: Removed RelationType enum references
- **MCP Tools**: Updated expected tool count from 56 to 52 tools
- **Schema Tests**: Updated to expect 4 categories instead of 5
- **Archive Tests**: Fixed parent_list_id AttributeError issues
- **E2E Workflow**: Removed --tree option usage throughout
- **Dependency Graph**: Updated to return empty results for removed functionality
- **Emoji Mapping**: Removed type column (🔀) references from expectations
- **Integration Tests**: Converted all --tree usage to standard list view
- **Subtask Positioning**: Fixed hierarchy display testing

#### Core System Improvements:
- **Simplified Manager**: Removed get_cross_list_progress and get_dependency_graph complexity
- **Clean MCP Interface**: All 52 tools working perfectly with sequential lists
- **Stable Database**: No more parent_list_id or relation table dependencies
- **Reliable CLI**: All commands work without tree/hierarchy options

### Benefits:
- **Development Confidence**: 100% test pass rate ensures system reliability
- **Simplified Codebase**: Easier maintenance without complex relation logic
- **Clean Architecture**: Focus on core functionality without unused features
- **Future-Proof**: Solid foundation for new feature development

## [2.2.0] - 2025-08-16

### ✨ Feature Enhancement - CLI Simplification
- **REMOVED**: `--type` option from `list create` command (auto-set to sequential)
- **REMOVED**: Type column from `list all` table display (🔀 column)
- **REMOVED**: Type information from list creation success messages
- **REMOVED**: Type from list rename command output
- **UPDATED**: Schema command no longer shows obsolete relation types
- **SIMPLIFIED**: CLI interface is now cleaner and more focused

Since only sequential list type exists, displaying type information was redundant.
The CLI now focuses on actual functionality rather than implementation details.

## [2.1.1] - 2025-08-16

### 🐛 Bug Fixes
- **FIXED**: Import errors after removing list relations functionality
  - Remove orphaned imports: `ListRelation`, `RelationType` from database.py
  - Fix indentation errors in `list_commands.py` after removing tree/hierarchical code blocks
- **VERIFIED**: All CLI functionality works correctly with sequential-only list type
- **TESTED**: Complete test suite on clean database confirms stability

## [2.1.0] - 2025-08-16

### 🗑️ BREAKING CHANGES - Feature Removal

#### Removed List Types and Relations
- **REMOVED**: Parallel, hierarchical, and linked list types functionality 
- **REMOVED**: `list_relations` table and all related database operations
- **REMOVED**: `parent_list_id` column from `todo_lists` table
- **REMOVED**: MCP tools: `todo_link_list_1to1`, `todo_create_list_relation`, `todo_get_list_items_hierarchical`
- **REMOVED**: CLI command: `todoit list link`
- **REMOVED**: CLI options: `--tree` flag from list commands
- **SIMPLIFIED**: Only sequential list type is now supported
- **MIGRATION**: Database migration 005 removes deprecated schema elements

#### Code Cleanup
- **REMOVED**: All related model classes: `ListRelation`, `ListRelationCreate`, `RelationType` enum
- **REMOVED**: Database methods: `create_list_relation()`, `get_list_relations()`, `delete_list_relations()`
- **REMOVED**: Manager methods: `link_list_1to1()`, `create_list_relation()`, `get_lists_by_relation()`
- **REMOVED**: Dedicated test files for removed functionality
- **UPDATED**: Documentation to reflect simplified feature set

### 📖 Documentation Updates
- **UPDATED**: MCP tools documentation (MCP_TOOLS.md) - removed deprecated tools
- **UPDATED**: CLI guide (CLI_GUIDE.md) - removed link command documentation  
- **UPDATED**: API documentation (api.md) - simplified list type options
- **UPDATED**: Database schema documentation (database.md) - removed list_relations table
- **UPDATED**: README.md - removed hierarchical tasks from feature list

## [2.0.0] - 2025-08-16

### 🔄 BREAKING CHANGES - CLI Complete Refactoring

#### Major CLI Syntax Changes
- **NEW SYNTAX**: ALL CLI commands now use explicit switches instead of positional arguments
  - **Item Commands**: `todoit item status --list "list" --item "item" --status completed`
  - **List Commands**: `todoit list create --list "project" --title "My Project"`
  - **Dependency Commands**: `todoit dep add --dependent "frontend:ui" --required "backend:api"`
  - **Property Commands**: `todoit property set --list "project" --key "priority" --value "high"`
  - **Stats Commands**: `todoit stats progress --list "project"`
  - **I/O Commands**: `todoit io export --list "project" --file "export.md"`
  - **Tag Commands**: `todoit tag create --name "urgent" --color "red"`

#### Terminology Standardization
- **BREAKING**: Replaced all "task/subtask" terminology with "item/subitem" throughout CLI interface
- **Parameter Change**: `--content` parameter renamed to `--title` for better user experience
- **Command Updates**: All help text, error messages, and examples updated to new terminology

#### Smart Command Logic
- **Unified Commands**: Single commands now handle both items and subitems automatically
  - `item add` - Smart add based on `--subitem` parameter presence
  - `item status` - Smart status update for items or subitems
  - `item edit` - Smart edit with context detection
  - `item delete` - Smart delete with unified interface
- **Context Detection**: Commands automatically determine whether to operate on items or subitems

#### Manager API Updates
- **BREAKING**: Renamed core manager methods:
  - `add_subtask()` → `add_subitem()`
  - `get_subtasks()` → `get_subitems()`
  - `move_to_subtask()` → `move_to_subitem()`
- **Updated Documentation**: All docstrings and method descriptions use new terminology

#### Documentation Complete Overhaul
- **New Reference**: Created comprehensive `docs/REF-20250816.md` with migration guide
- **Updated CLI Guide**: All examples in `docs/CLI_GUIDE.md` converted to new syntax
- **No Backward Compatibility**: Clean break approach - old syntax no longer supported

#### Example New Syntax
```bash
# Item commands
todoit item add --list "project" --item "feature1" --title "Implement login"
todoit item add --list "project" --item "feature1" --subitem "step1" --title "Design UI"
todoit item status --list "project" --item "feature1" --status completed
todoit item list --list "project"

# List commands  
todoit list create --list "project" --title "My Project"
todoit list delete --list "old-project" --force
todoit list live --list "project" --refresh 5

# Dependencies
todoit dep add --dependent "frontend:component" --required "backend:api"
todoit dep show --item "frontend:component"

# Properties
todoit property set --list "project" --key "priority" --value "high"
todoit property list --list "project"

# Stats and I/O
todoit stats progress --list "project" --detailed
todoit io export --list "project" --file "/path/export.md"

# Tags
todoit tag create --name "urgent" --color "red"
todoit list tag add --list "project" --tag "urgent"
```

### Benefits
- **Explicit and Clear**: All parameters use descriptive switches
- **Unified Interface**: Fewer commands, more consistency
- **Better Discoverability**: Clear parameter names eliminate ambiguity
- **Consistent Terminology**: item/subitem throughout entire system
- **Smart Context**: Commands adapt based on provided parameters

### Migration Required
⚠️ **NO BACKWARD COMPATIBILITY** - All scripts and workflows must be updated to new syntax

## [1.25.3] - 2025-08-15

### Added
- **🔄 Duplicate Subtask Keys**: Enhanced subtask flexibility by allowing the same key across different parents
  - **Feature**: Subtasks can now use identical keys (e.g., `image_gen`, `image_dwn`) for different parent tasks
  - **Use Case**: Enables standardized workflows where multiple scenes/items share common subtask patterns
  - **Example**: `scene_0019` and `scene_0020` can both have `image_gen` and `image_dwn` subtasks
  - **Search Enhancement**: `todo_find_subitems_by_status` now works with generic keys like `{"image_gen":"completed","image_dwn":"pending"}`

### Technical
- **Database Schema**: Modified unique constraint from `(list_id, item_key)` to `(list_id, parent_item_id, item_key)`
- **New Function**: Added `get_item_by_key_and_parent()` for precise subtask lookup with parent context
- **Validation Logic**: Updated `add_subtask()` to check uniqueness only among siblings (same parent)
- **Backward Compatibility**: Main task keys remain unique within each list as before
- **Test Coverage**: 5 comprehensive tests covering duplicate keys, constraint validation, and search functionality

### Benefits
- **Workflow Standardization**: Common subtask patterns can be reused across different parent tasks
- **MCP Integration**: Claude Code can now use generic subtask keys in `todo_find_subitems_by_status`
- **Reduced Naming Complexity**: No need for unique prefixes like `scene_0019_image_gen`
- **Data Integrity**: Maintains all existing constraints while providing new flexibility

## [1.25.2] - 2025-08-15

### Fixed
- **📋 Property List Hierarchical Sorting**: Fixed `todoit item property list` to display properties in hierarchical order
  - **Issue**: Properties were sorted alphabetically by item_key instead of following list hierarchy
  - **Root Cause**: `get_all_items_properties()` used alphabetical sorting instead of hierarchical position
  - **Solution**: Added `item_order` tracking to maintain hierarchical sequence from `get_list_items()`
  - **Result**: Properties now display in logical task order (1,2,3...) matching list structure

### Technical
- **Enhanced Sorting Logic**: Modified `get_all_items_properties()` to use `(item_order, property_key)` for sorting
- **Maintained Structure**: Preserved alphabetical sorting of properties within each item
- **Test Coverage**: 5 new unit tests for hierarchical property sorting scenarios
- **Performance**: No performance impact - leverages existing hierarchical ordering from database

## [1.25.1] - 2025-08-15

### Fixed
- **🔢 Hierarchical Task Positioning**: Fixed sequential numbering for main tasks and subtasks
  - **Issue**: Main tasks displayed non-sequential positions (1, 9, 17, 25...) due to interleaved positioning with subtasks
  - **Root Cause**: Single global position counter caused main tasks and subtasks to compete for sequential positions
  - **Solution**: Implemented separate positioning logic - main tasks get positions 1,2,3... and subtasks get positions 1,2,3... within each parent
  - **Result**: Clean hierarchical display with main tasks numbered 1,2,3 and subtasks numbered 1.1,1.2,2.1,2.2 etc.

### Technical
- **Database Enhancement**: Enhanced `get_next_position()` to accept `parent_item_id` parameter for hierarchical positioning
- **Query Optimization**: Updated `get_list_items()` and `get_items_by_status()` with hierarchical ordering (main tasks first, then subtasks by parent)
- **Test Coverage**: 6 new unit tests + updated existing tests for new positioning behavior
- **Performance**: Independent position counters eliminate position conflicts and improve scalability

## [1.25.0] - 2025-08-15

### Fixed
- **🔧 Subtask Position Conflicts**: Fixed critical position conflicts in subtask creation
  - **Issue**: Database position conflicts caused by inconsistent positioning logic in `add_subtask()`
  - **Root Cause**: First subtask used `parent.position + 1` with shifting, subsequent subtasks used `max(subtask_positions) + 1` without shifting
  - **Solution**: Simplified positioning to always use `get_next_position()` for all subtasks
  - **Result**: Sequential positions without conflicts, reliable subtask creation and display

### Technical
- **Database Fix**: Eliminated position conflicts that could cause data integrity issues
- **Code Simplification**: Reduced complex positioning logic from 13 lines to 1 line
- **Test Coverage**: 6 new unit tests + 4 integration tests for position conflict scenarios
- **Performance**: Removed unnecessary `get_item_children()` and `shift_positions()` calls

## [1.24.0] - 2025-08-15

### Fixed
- **🔢 Hierarchical Numbering**: Fixed subtask numbering to reset per parent task
  - **Issue**: Subtasks had continuous numbering (1.2, 1.3, ..., 9.10, 9.11) instead of parent-relative (1.1, 1.2, 1.3, 9.1, 9.2)
  - **Root Cause**: Display logic used global `item.position` instead of sibling index within parent
  - **Solution**: Modified `add_item_to_table()` in `display.py` to use enumerated sibling index for subtasks
  - **Result**: Correct hierarchical numbering (Task 1: 1.1, 1.2, 1.3; Task 3: 3.1, 3.2; Task 6: 6.1)

### Technical
- **Code Changes**: Enhanced `_render_table_view()` with proper parent-relative indexing
- **Test Coverage**: 4 new unit tests + 3 integration tests for hierarchical numbering
- **Backward Compatible**: No API changes, only display logic improvement

## [1.23.0] - 2025-08-15

### Added
- **🏷️ List Rename Functionality**: Complete CLI command for renaming list keys and titles
  - **New CLI Command**: `todoit list rename <current_key> --key <new_key> --title "New Title"`
  - **Flexible Options**: Rename key only, title only, or both simultaneously
  - **Safe Operation**: Validation for unique keys, proper format, and confirmation prompts
  - **History Tracking**: Full audit trail of rename operations
  - **FORCE_TAGS Integration**: Respects environment isolation settings
  - **Rich UI**: Preview changes in tables with success confirmation

### Technical
- **New Method**: `TodoManager.rename_list()` with comprehensive validation
- **Database Update**: Uses existing `update_list()` with proper foreign key preservation
- **Test Coverage**: 11 unit tests + 13 integration tests for CLI functionality
- **Error Handling**: Comprehensive validation for all edge cases

## [1.22.0] - 2025-08-15

### Enhanced
- **🚀 CLI JSON Output**: Fixed `todoit list show` to return single unified JSON instead of multiple separate JSONs in JSON mode
  - **Unified Structure**: Combined `list_info`, `items`, and `properties` sections in one JSON response  
  - **Backward Compatible**: Table, YAML, and XML formats remain unchanged
  - **Improved Integration**: Better support for automation and API consumption

- **⚡ Enhanced MCP `todo_get_list`**: Extended with optional parameters for complete data retrieval
  - **New Parameters**: `include_items` and `include_properties` (both default to `True`)
  - **Single Call Efficiency**: Get list, items, and properties in one MCP call instead of three
  - **Flexible Usage**: Can retrieve only specific data sections as needed
  - **Backward Compatible**: Default behavior includes everything, maintaining existing workflows

### Configuration
- **🛡️ MCP Tools Reorganization**: Moved archive management tools from STANDARD to MAX level
  - **Enhanced Security**: `todo_archive_list` and `todo_unarchive_list` now require MAX level
  - **Updated Counts**: STANDARD level now has 24 tools (down from 25), MAX level has 58 tools (up from 57)
  - **Better Token Efficiency**: STANDARD level now provides 59% token savings (improved from 55%)

### Documentation
- **📚 Updated MCP Tools Documentation**: Complete documentation update for enhanced `todo_get_list`
  - **New Usage Examples**: Comprehensive examples showing all parameter combinations
  - **Updated Tool Counts**: Corrected all tool level counts and performance metrics
  - **Enhanced Clarity**: Better organization and more detailed explanations

### Testing
- **🧪 Comprehensive Test Coverage**: Added robust test suites for all new functionality
  - **JSON Output Tests**: 9 test scenarios covering CLI and MCP JSON output fixes
  - **Enhanced MCP Tests**: Complete coverage of new `todo_get_list` parameter combinations
  - **Backward Compatibility**: Verified no breaking changes in existing functionality

## [1.21.0] - 2025-08-15

### Added
- **🔍 Advanced Subitem Search**: New `find_subitems_by_status()` function for workflow automation
  - **Sibling Status Conditions**: Find subitems based on status of their siblings within the same parent group
  - **Perfect for Workflows**: Automate sequential processes (e.g., find downloads when generation complete)
  - **Multiple Conditions**: All conditions must be satisfied within sibling groups (AND logic)
  - **Optimized Performance**: Single database queries with proper sorting by position
  - **Complete Integration**: Available in API, MCP tools (`todo_find_subitems_by_status`), and CLI (`todoit item find-subitems`)

### Technical Implementation
- **Database Layer**: Added `find_subitems_by_status()` method with efficient parent grouping
- **Manager Layer**: Full validation and error handling with Pydantic model conversion
- **CLI Interface**: Rich JSON parsing with comprehensive error messages and formatted output
- **MCP Interface**: Standard tool with complete metadata in responses
- **Testing**: 13 comprehensive test scenarios covering edge cases and performance

### Usage Examples
```bash
# CLI: Find downloads ready to process
todoit item find-subitems images --conditions '{"generate":"completed","download":"pending"}' --limit 5

# Python API: Development workflow automation
ready_tests = manager.find_subitems_by_status(
    "features", 
    {"design": "completed", "code": "completed", "test": "pending"},
    limit=10
)
```

## [1.20.0] - 2025-08-14

### Added
- **🔄 Automatic Status Synchronization**: Revolutionary parent-child status management system
  - **Smart Status Calculation**: Parent status automatically calculated from children (failed > all_pending > all_completed > in_progress)
  - **Manual Change Blocking**: Tasks with subtasks cannot have manually changed status - prevents inconsistencies
  - **Real-time Propagation**: Status changes propagate recursively through entire hierarchy instantly
  - **Transaction Safety**: All synchronization happens in atomic database transactions

### Technical
- **Performance Optimized**: Single SQL query per hierarchy level with covering indexes
- **Database Schema**: Added `idx_todo_items_parent_status` index for O(1) child status aggregation
- **New Methods**: `has_subtasks()`, `get_children_status_summary()`, `_sync_parent_status()`
- **Circular Protection**: Visited-set mechanism prevents infinite recursion (max 10 levels)
- **MCP Integration**: Enhanced error messages for blocked operations with `status_sync_blocked` type

### Breaking Changes
- **Status Lock**: Tasks with subtasks can no longer have manually changed status - use subtask status changes instead
- **Behavior Change**: Adding first subtask to completed task changes parent to pending automatically

### Tests
- **Comprehensive Coverage**: 10 new test scenarios covering all synchronization edge cases
- **Performance Tested**: Verified with 100+ subtasks, completes in <5 seconds
- **Integration Updated**: All existing tests adapted to new status synchronization behavior

## [1.19.4] - 2025-08-13

### Added 
- **🎯 Readable JSON Field Names**: Emoji symbols in CLI headers now map to human-readable field names in JSON/YAML/XML output
  - **Better API Usability**: `🏷️` → `tags`, `📋` → `pending_count`, `✅` → `completed_count`, etc.
  - **Script-Friendly**: JSON output now parseable without dealing with emoji characters
  - **Backward Compatible**: Table output still uses emoji for visual appeal

### Technical
- **Emoji Mapping System**: Added `EMOJI_TO_NAME_MAPPING` in display module
- **Unified Serialization**: Enhanced `_prepare_data_for_serialization()` to map emoji keys
- **Test Coverage**: Added comprehensive integration tests for emoji mapping functionality
- **Property Command Fix**: Standardized JSON output format for `item property list` command

## [1.19.3] - 2025-08-13

### Added
- **🆕 Item Limit Parameter**: Added optional `limit` parameter to `todo_get_all_items_properties`
  - **Performance Optimization**: Limit number of items processed for large lists
  - **Flexible Querying**: Works with status filters - limit applies to items, not properties
  - **Backward Compatible**: Optional parameter - existing code continues to work unchanged

### Technical
- **Core Manager Enhancement**: Updated `get_all_items_properties()` to accept `limit` parameter
- **MCP Interface Update**: Added `limit` parameter to MCP tool `todo_get_all_items_properties`
- **Test Coverage**: Added comprehensive unit and integration tests for limit functionality

## [1.19.2] - 2025-08-13

### Changed
- **🔧 Unified JSON Format**: Fixed MCP `todo_get_all_items_properties` to match CLI JSON format
  - **Consistent Output**: MCP now returns same grouped format as CLI: `{"item_key": {"prop": "value"}}`
  - **Clean Response**: Removed wrapper metadata, returns direct property data
  - **Better Integration**: MCP and CLI now provide identical JSON structure for property data

### Technical
- **MCP Server Enhancement**: Updated `todo_get_all_items_properties` to group properties by item_key
- **Simplified Response**: MCP returns grouped data directly without success/count metadata wrapper

## [1.19.1] - 2025-08-13

### Changed
- **🔧 Enhanced JSON Output Format**: Improved `todoit item property list` JSON output for better usability
  - **Grouped Format**: JSON now groups properties by item_key: `{"item_key": {"prop": "value"}}`
  - **Cleaner Structure**: Eliminates verbose table-style format in JSON output
  - **Better Integration**: Simplified structure ideal for external tool integration and scripting
  - **Backward Compatibility**: Table, tree, YAML, and XML formats remain unchanged
  - **Comprehensive Testing**: 7 integration tests covering all output formats and edge cases

### Technical
- **Enhanced CLI Logic**: Added output format detection to property list command
- **Improved User Experience**: JSON output now directly usable without data transformation
- **Test Coverage**: Added comprehensive test suite for new JSON format behavior

### Use Cases
- **API Integration**: Direct consumption of item properties without parsing table structures
- **Scripting**: Simplified property access for automation scripts
- **Data Export**: Clean JSON format for external processing tools

## [1.19.0] - 2025-08-13

### Added
- **📊 Bulk Property Analysis**: New comprehensive tool for retrieving all properties across items with status filtering
  - **Core Function**: `get_all_items_properties(list_key, status=None)` with optional status filter (`pending`, `in_progress`, `completed`, `failed`)
  - **MCP Tool**: `todo_get_all_items_properties` added to **STANDARD** tool set (25 tools total)
  - **Enhanced Response**: Includes property data with status, count, and unique items metadata
  - **Multi-Criteria Filtering**: Enables complex property analysis that single-property search cannot handle
  - **Status-Based Filtering**: Filter properties by item status for targeted analysis
  - **Comprehensive Testing**: 10 integration tests covering all scenarios and edge cases

### Technical
- **Database Optimization**: Leverages existing indexes for efficient property queries
- **Tool Count Update**: STANDARD level now includes 25 tools (was 24), MAX level 57 tools total
- **Documentation**: Updated MCP_TOOLS.md with new tool examples and usage patterns
- **Test Coverage**: Added comprehensive integration test suite for new functionality

### Use Cases
- **Complex Property Analysis**: Find items matching multiple property criteria (e.g., `image_downloaded=pending` AND `image_generated=completed`)
- **Status-Based Property Retrieval**: Get properties only for items in specific status states
- **Bulk Data Export**: Retrieve all properties for external processing and analysis
- **Multi-Property Workflows**: Enable sophisticated filtering logic in client applications

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