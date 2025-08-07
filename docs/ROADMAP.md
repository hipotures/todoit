# TODOIT Development Roadmap

## Current Version: 1.7.0

### Recently Completed ✅

#### Version 1.5.0 - CLI Modularization
- **Major CLI Refactoring**: Split monolithic `cli.py` (2043 lines → 64 lines)
- **Modular Architecture**: Created 6 specialized modules:
  - `display.py`: Rich formatting and display functions (507 lines)
  - `list_commands.py`: List management operations (564 lines)
  - `item_commands.py`: Item CRUD and status operations (404 lines)
  - `property_commands.py`: Property management (180 lines)
  - `dependency_commands.py`: Cross-list dependency handling (262 lines)
  - `io_stats_commands.py`: Import/export and statistics (234 lines)
- **Package Configuration**: Fixed setuptools package discovery
- **Documentation**: Added installation guide for dev vs production

#### Version 1.5.1 - Output Formats
- **Multiple Output Formats**: Added JSON, YAML, XML support via `TODOIT_OUTPUT_FORMAT` env var
- **Smart Serialization**: Automatic datetime and enum conversion
- **Comprehensive Testing**: 20+ test cases for all output formats
- **New Dependencies**: Added `dicttoxml>=1.7.0` for XML support

#### Version 1.7.0 - Icon-based UI
- **Text-to-Icon Replacement**: Replaced text labels with intuitive icons in CLI tables
- **Column Icons**: Added ✅ (completed), ⏳ (progress/pending), 📋 (list info), 🔀 (list type)
- **Improved Column Alignment**: Right-aligned numeric columns, centered single characters
- **Compact Display**: Removed verbose text descriptions, kept only essential icons
- **Documentation Updates**: Added icon explanations and list type documentation
- **Space Optimization**: Better column width management for cleaner tables

### Planned Features 🚧

#### Version 1.8.0 - Enhanced Export/Import
- **Structured Export**: Export with full hierarchy and dependencies preserved
- **Import Validation**: Schema validation for imported data
- **Backup/Restore**: Complete database backup and restore functionality
- **Migration Tools**: Import from other TODO applications (Todoist, Trello, etc.)

#### Version 1.9.0 - Advanced Scheduling
- **Due Dates**: Add due date support to tasks
- **Recurring Tasks**: Support for recurring task patterns
- **Calendar Integration**: iCal export and import
- **Reminders**: Basic notification system

#### Version 2.0.0 - Collaboration Features
- **Shared Lists**: Multi-user list sharing
- **Assignment**: Task assignment to team members  
- **Comments**: Task comments and notes
- **Audit Trail**: Enhanced history tracking with user attribution

#### Version 2.1.0 - Web Interface
- **REST API**: Full REST API for all operations
- **Web Dashboard**: Modern web interface
- **Real-time Updates**: WebSocket-based live updates
- **Mobile Responsive**: Mobile-friendly design

### Technical Debt & Improvements 🔧

#### High Priority
- **Performance**: Database query optimization for large datasets
- **Memory Usage**: Optimize memory usage for large lists
- **Error Handling**: Improve error messages and recovery
- **Documentation**: Complete API documentation

#### Medium Priority  
- **Internationalization**: Multi-language support
- **Themes**: Customizable Rich themes
- **Plugins**: Plugin architecture for extensions
- **Configuration**: Advanced configuration management
- **Bash/Zsh Completion**: Auto-completion for list keys and commands (requires proper testing environment)

#### Low Priority
- **AI Integration**: Smart task suggestions and automation
- **Analytics**: Task completion analytics and insights
- **Integrations**: GitHub, Slack, email integrations
- **Mobile App**: Native mobile applications

### Environment Variables 📝

Current supported environment variables:
- `TODOIT_OUTPUT_FORMAT`: Controls output format
  - Values: `table` (default), `vertical`, `json`, `yaml`, `xml`
  - Example: `TODOIT_OUTPUT_FORMAT=json todoit list all`

### Testing Coverage 📊

- **Unit Tests**: Core functionality and edge cases
- **Integration Tests**: CLI commands and database operations  
- **E2E Tests**: Complete workflow testing
- **Output Format Tests**: All serialization formats
- **Edge Case Tests**: Limits, unicode, error conditions

### Performance Benchmarks 🚀

Target performance metrics:
- **List Operations**: < 100ms for lists with 1000+ items
- **Search**: < 50ms full-text search across all lists
- **Export**: < 500ms for complete database export
- **Startup**: < 200ms CLI startup time

### Breaking Changes Policy 💔

- **Major Versions** (x.0.0): May include breaking changes
- **Minor Versions** (x.y.0): Backward compatible feature additions
- **Patch Versions** (x.y.z): Bug fixes and small improvements

### Contributing Guidelines 🤝

1. **Feature Requests**: Create GitHub issues with detailed requirements
2. **Bug Reports**: Include reproduction steps and environment details
3. **Pull Requests**: Follow existing code style and include tests
4. **Documentation**: Update relevant docs for any changes

---

**Note**: This roadmap is subject to change based on user feedback and project priorities. Features may be moved between versions or modified based on technical constraints.