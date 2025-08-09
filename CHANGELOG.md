# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.14.1] - 2025-08-09

### Enhanced
- **📋 Improved CLI Error Handling**: Better user experience for `item status` command
  - Enhanced error messages when `--status` argument is missing
  - Display available status options with descriptions (pending, in_progress, completed, failed)
  - Added helpful examples and reference to help command
  - Improved help text for better discoverability

### Fixed  
- **CLI UX**: Status command now shows available options instead of generic error message

## [1.14.0] - 2025-08-09

### Added
- **🔒 Environment Isolation with TODOIT_FORCE_TAGS**: Complete environment separation for dev/test/prod workflows
  - New `TODOIT_FORCE_TAGS` environment variable for automatic tagging and filtering
  - Auto-tagging: New lists automatically receive tags from `TODOIT_FORCE_TAGS`
  - Environment isolation: All operations limited to lists with forced tags
  - Priority system: `FORCE_TAGS` overrides `FILTER_TAGS` for complete control

### Enhanced
- **CLI Tag Filtering**: Redesigned tag filtering with priority-based logic
  - `_get_force_tags()` helper function for environment tag extraction
  - `_get_filter_tags()` enhanced with FORCE_TAGS priority handling
  - Auto-tagging in `list create` command when FORCE_TAGS is set
- **Command Integration**: All filtering commands now respect FORCE_TAGS
  - `todoit list all` - Environment-aware list display
  - `todoit reports errors` - Filtered error reports by environment
  - Interactive mode lists - Environment-scoped list display

### Environment Features
- **Automatic Tag Creation**: Missing tags from FORCE_TAGS are auto-created
- **Complete Isolation**: Environment tags enforce strict separation between dev/test/prod
- **Flexible Configuration**: Support for multiple tags (e.g., `dev,test`) for shared access
- **Dotenv Integration**: Works seamlessly with `.env` files for persistent environments

### Technical
- 14 comprehensive unit tests covering all FORCE_TAGS scenarios
- Enhanced documentation with environment setup examples and best practices
- Backward compatibility: Empty FORCE_TAGS maintains existing FILTER_TAGS behavior
- CLI-only feature: MCP tools unaffected, maintaining explicit parameter control

### Use Cases
- **Development Isolation**: `export TODOIT_FORCE_TAGS=dev` - only see and create dev lists
- **Testing Environment**: `export TODOIT_FORCE_TAGS=dev,test` - access dev+test lists
- **Production Safety**: `export TODOIT_FORCE_TAGS=prod` - complete prod isolation
- **Team Workflows**: Different `.env` files for different team members/roles

## [1.13.1] - 2025-08-09

### Added
- **🔄 Completion State Management**: CLI tools for managing item completion states
  - `todoit item state list` - View all completion states for an item
  - `todoit item state clear` - Clear all completion states from item
  - `todoit item state remove` - Remove specific completion states by key
  - Fixes table formatting issues caused by long state names
  - Full confirmation prompts and `--force` flag support

### Enhanced
- **Core Manager**: New `clear_item_completion_states()` method with selective key removal
- **History Tracking**: Added `STATES_CLEARED` action type for audit trail
- **Error Handling**: Comprehensive validation for state management operations

### Technical
- Added `HistoryAction.STATES_CLEARED` enum value for proper history recording
- 13 comprehensive unit tests covering all state management scenarios
- Rich CLI formatting with visual state indicators (✅/❌)

## [1.13.0] - 2025-08-09

### Added
- **🏷️ Complete Tag System for Lists**: Comprehensive tagging functionality for organizing and categorizing TODO lists
  - Global tag management: Create, list, delete tags with color support
  - List tagging: Add/remove tags from lists, view tags per list
  - Advanced filtering: Filter lists by tags in both CLI and MCP interfaces
  - Environment variable support: `TODOIT_FILTER_TAGS` for automatic CLI filtering with `.env` file support
  - Union logic: CLI `--tag` and environment variables combine for flexible filtering

### CLI Enhancements
- **New Commands**: 
  - `todoit tag` group: `create`, `list`, `delete` for global tag management
  - `todoit tags` alias: Quick overview shortcut (alias for `tag list`)
  - `todoit list tag` subgroup: `add`, `remove`, `show` for list-specific tagging
  - `todoit list all --tag` option: Filter lists by tags with multiple tag support
- **Environment Integration**: Automatic `.env` loading with `python-dotenv` dependency
- **Smart Filtering**: Tags from environment and CLI combine as unique union

### MCP Interface Expansion (46→55 tools)
- **New MCP Tools**:
  - `todo_create_tag`: Create new tags with color customization
  - `todo_add_list_tag`: Add tags to lists (auto-creates tags if needed)
  - `todo_remove_list_tag`: Remove tags from lists
  - `todo_get_lists_by_tag`: Filter lists by tags with comprehensive metadata
- **Enhanced Existing Tools**:
  - `todo_list_all`: Added `filter_tags` parameter with tag information in responses
  - `todo_report_errors`: Added `tag_filter` parameter for targeted error reporting

### Database & Architecture
- **New Tables**: `list_tags`, `list_tag_assignments` with proper indexing and foreign keys
- **Pydantic Models**: `ListTag`, `ListTagCreate`, `ListTagAssignment` with validation
- **Manager Methods**: Complete tag CRUD operations and filtering logic
- **Tag Normalization**: Consistent lowercase handling across all interfaces

### Security & Isolation
- **Environment Isolation**: MCP tools ignore environment variables for security
- **Explicit Parameters**: MCP uses only explicit parameters, CLI respects environment
- **Input Validation**: Comprehensive tag name validation with reserved word protection

### Testing & Quality
- **Comprehensive Test Coverage**: 21+ new tests covering unit, integration, and edge cases
- **CLI Integration Tests**: Environment variable handling and tag filtering validation
- **MCP Integration Tests**: Full workflow testing for all new tools
- **Backward Compatibility**: All existing functionality preserved, new parameters optional

### Documentation
- **MCP_TOOLS.md**: Updated with 4 new tools and enhanced existing tool descriptions
- **CLI_GUIDE.md**: Complete tag management section with examples and best practices
- **API Documentation**: Full coverage of tag system architecture and usage patterns

### Technical Details
- **Dependencies**: Added `python-dotenv>=1.0.0` for `.env` support
- **Performance**: Optimized queries with proper database indexing
- **Consistency**: Unified tag handling between CLI and MCP with clear separation

## [1.12.0] - 2025-08-09

### Added
- **Reports & Analytics System**: New comprehensive reporting functionality for project management
  - CLI `reports errors` command shows all failed tasks across active lists with full context
  - MCP `todo_report_errors` tool provides programmatic access to failed task data
  - Regex filtering support for list patterns (e.g., `^\d{4}_.*` for NNNN_*, `.*project.*` for containing "project")
  - Always includes task properties, list context, and metadata for troubleshooting
  - Automatic exclusion of archived lists from reports (active lists only)

### Enhanced
- **CLI Interface**: New `reports` command group with analytics capabilities
- **Core Manager**: Added `get_all_failed_items()` method with regex filtering and comprehensive data aggregation
- **MCP Integration**: Enhanced API with 46th tool providing structured JSON responses with metadata
- **Documentation**: Updated CLI_GUIDE.md and MCP_TOOLS.md with comprehensive examples and usage patterns

### Technical
- Added comprehensive test suite for reports functionality (15 new unit tests)
- Tests cover CLI display, MCP responses, regex filtering, and edge cases
- Enhanced error handling for invalid regex patterns with user-friendly messages
- Full support for all output formats (table, JSON, YAML, XML) in CLI reports
- Proper datetime serialization in MCP responses for JSON compatibility

## [1.11.0] - 2025-08-09

### Added
- **Enhanced Failed Status Display**: Always-visible failed task column in `list all` views
  - CLI `list all` now shows separate status columns: 📋 (pending), 🔄 (in_progress), ❌ (failed), ✅ (completed)
  - MCP `todo_list_all` tool enhanced with comprehensive progress statistics including failed counts
  - Failed column (❌) always visible even when no tasks are failed (shows "0")
  - Better project management visibility with detailed status breakdown

### Enhanced
- **CLI List Display**: Improved table layout with dedicated status columns for better task overview
- **MCP Integration**: Enhanced `todo_list_all` response includes full progress statistics with failed task tracking
- **Documentation**: Updated CLI_GUIDE.md with column descriptions and example table layout
- **Documentation**: Enhanced MCP_TOOLS.md with progress statistics example and JSON response format

### Technical
- Added comprehensive test suite for enhanced list display (6 new unit tests)
- Tests cover both CLI column display and MCP progress statistics enhancement
- Enhanced column styling with proper color coding and width management
- Backward compatible: existing API structure maintained with additive enhancements
- All output formats (table, JSON, YAML, XML) support new status breakdown

## [1.10.0] - 2025-08-08

### Added
- **Archive Validation System**: Lists can only be archived when all tasks are completed
  - New `force` parameter in `archive_list()` core manager method
  - CLI `--force` flag for `list archive` command to bypass validation
  - MCP `force: bool = False` parameter for `todo_archive_list` tool
  - Comprehensive error messages showing incomplete task counts
  - Automatic completion validation with detailed feedback

### Enhanced
- **Archive Safety**: Prevents accidental archiving of incomplete projects
- **User Experience**: Clear error messages with guidance on using `--force`
- **Documentation**: Updated MCP_TOOLS.md and CLI_GUIDE.md with new archive validation examples
- **Error Handling**: Informative messages showing "Incomplete: X/Y tasks. Use force=True to archive anyway."

### Technical
- Added comprehensive test suite for archive validation (19 new tests)
- Unit tests in `test_archive_validation.py` covering all validation scenarios
- Integration tests in `test_mcp_archive.py` for MCP interface validation
- Enhanced CLI tests in `test_archive_cli.py` with force flag coverage
- Backward compatible: `force` parameter defaults to `False`

## [1.9.1] - 2025-08-08

### Added
- **Comprehensive Test Suite for Archiving**: Complete test coverage for list archiving functionality
  - Unit tests for archiving business logic with proper mocking
  - 13 CLI integration tests covering all archiving scenarios
  - End-to-end workflow testing from archive to unarchive
  - Error handling validation for edge cases

### Enhanced  
- **Test Coverage**: Enhanced unit test suite with archiving functionality tests
- **Quality Assurance**: All archiving features now fully tested and validated

### Fixed
- **Unit Test Dependencies**: Fixed mock database method calls in archiving unit tests
- **Test Reliability**: Improved test stability and mock object configuration

### Technical
- Added `test_archive_cli.py` with 13 comprehensive CLI integration tests
- Enhanced `test_manager_unit.py` with 8 new archiving unit tests
- All tests passing with 100% archiving feature coverage
- Validated archiving workflow from CLI commands to database operations

## [1.9.0] - 2025-08-08

### Added
- **List Archiving**: Complete archiving system for lists
  - Archive lists to hide them from normal view without deletion
  - New CLI commands: `list archive <key>` and `list unarchive <key>`
  - New MCP tools: `todo_archive_list` and `todo_unarchive_list`
  - List status system with `ListStatus` enum (active, archived)
- **Enhanced List Display**: 
  - New status column 📦 showing A (active) or Z (archived)
  - Archive indicators in tree view with dimmed colors
  - Filter options: `--archived` (only archived) and `--include-archived` (all lists)
- **Database Migration**: Added status column with proper indexing
- **MCP Integration**: Extended `todo_list_all` with `include_archived` parameter

### Enhanced
- **List Management**: Lists now have persistent status (active by default)
- **UI Improvements**: Visual distinction between active and archived lists
- **Filtering System**: Smart filtering hides archived lists by default

### Technical
- Added `ListStatus` enum to models
- Database schema update with migration 003_add_list_status.sql
- 50 MCP tools total (added 2 new archiving tools)
- Comprehensive error handling and validation

## [1.8.2] - 2025-08-07

### Improved
- **MCP Documentation**: Enhanced `todo_update_item_status` documentation with complete status descriptions
- **Status Clarity**: Replaced "etc." with explicit list of all valid status values and their meanings

## [1.8.1] - 2025-08-07

### Fixed
- **CLI Validation**: Added 'linked' to allowed list types in CLI create command
- **List Type Support**: Fixed validation error when using linked list type

## [1.8.0] - 2025-08-07

### Added
- **List Linking (1:1 Relationships)**: New `list link` CLI command for creating linked lists
- **MCP Tool `todo_link_list_1to1`**: Programmatic list linking with comprehensive statistics
- **Automatic Synchronization**: New tasks added to parent lists automatically sync to linked children
- **Advanced List Management**: Support for multiple child lists with 1:1 relationships
- **Property Preservation**: Automatic copying of list and item properties during linking
- **Comprehensive Testing**: 37 new test cases (15 unit + 13 integration + 9 CLI tests)

### Enhanced
- **CLI Documentation**: Updated with list linking examples and workflows
- **MCP Tools**: Now 48 total tools available (was 47)
- **API Documentation**: Added `link_list_1to1` method documentation

### Implementation Details
- New helper methods: `_get_1to1_child_lists()` and `_sync_add_to_children()`
- Enhanced `add_item()` method with automatic synchronization to linked lists
- Rich CLI output with detailed linking statistics
- Error handling that doesn't interrupt main operations

## [1.7.1] - 2025-08-07

### Added
- Comprehensive API documentation with detailed method references
- Source code links and usage examples for all TodoManager methods
- Configuration documentation (`docs/configuration.md`)
- Icon explanations in CLI documentation (⏳ ✅ 📊 📋)

### Changed
- Enhanced API documentation from basic overview to detailed reference
- Updated CLI documentation with visual feature explanations
- Improved documentation structure and organization

### Removed
- Deprecated `docs/cli.md` file

## [1.7.0] - 2025-08-07

### Added
- Icon-based column headers in CLI tables for better visual representation
- Multiple output formats (JSON, XML, CSV, YAML) support
- Development/production environment detection
- Live monitoring capabilities
- Timezone handling improvements

### Changed
- Replaced text column labels with icons (⏳ Pending, ✅ Completed, 📊 Progress, 📋 List Type)
- Consolidated documentation to single `docs/` directory
- Improved CLI table styling and color coding
- Enhanced progress visualization

### Fixed
- Updated requirements.txt with dicttoxml dependency
- Replaced deprecated pkg_resources with importlib.metadata
- CLI modularization and test imports

## [1.6.0] - 2025-08-06

### Added
- Item deletion and content editing functionality
- System schema info tool (`todo_get_schema_info`)
- Quick add item key sequential numbering

### Changed
- Modular CLI structure for better maintainability
- Code cleanup and test consolidation
- Quick add item key schema from `quick_item_` to `item_`

### Fixed
- MCP parameter conflict in error handler
- Test imports after CLI modularization

### Removed
- Task Master AI integration files
- Obsolete configuration files

## [1.5.0] - 2025-08-05

### Added
- Cross-list dependencies system
- Subtask hierarchy support
- Smart task prioritization algorithms
- Comprehensive progress tracking with blocked/available counts
- 45 MCP tools for Claude Code integration

### Changed
- Enhanced database schema with foreign key relationships
- Improved task workflow management
- Better dependency resolution

### Fixed
- Database consistency and integrity
- Task blocking logic
- Progress calculation accuracy

## [1.4.0] - 2025-08-04

### Added
- Rich CLI interface with status indicators
- SQLite database backend
- Import/export functionality with Markdown support
- Project-wide progress tracking

### Changed
- Complete rewrite of core architecture
- Enhanced data models and relationships
- Improved error handling and validation

## [1.3.0] - 2025-08-03

### Added
- Initial MCP server implementation
- Basic todo list and item management
- CLI interface foundation
- Database migrations system

### Changed
- Project structure and organization
- Configuration management

## [1.2.0] - 2025-08-02

### Added
- Core TodoManager class
- Basic CRUD operations
- Initial documentation

## [1.1.0] - 2025-08-01

### Added
- Project initialization
- Basic models and database setup
- Initial CLI structure

## [1.0.0] - 2025-07-31

### Added
- Initial project setup
- Basic todo functionality
- Foundation for MCP integration