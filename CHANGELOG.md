# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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