# Architecture

TODOIT MCP is designed with a clean, modular architecture that separates concerns into three main layers, enabling maintainable and scalable task management functionality.

## Overview

The system follows a **3-layer architecture** with clear separation of responsibilities:
- **Core Layer**: Business logic and data management
- **Interfaces Layer**: User-facing interfaces (CLI + MCP)
- **Database Layer**: Persistent storage with SQLite + SQLAlchemy

## 1. Core Layer

The core layer contains all business logic and data management components:

### `core/manager.py` (2861 lines)
The heart of the system - implements the `TodoManager` class which serves as the main programmatic API.

**Key Responsibilities:**
- List and item CRUD operations
- Hierarchical task management (parent/subitem relationships)
- Cross-list dependency management
- Smart task selection algorithms
- Tag system with dynamic color assignment
- Property management for runtime configuration
- Import/export functionality
- Automatic status synchronization for hierarchical tasks

**Major Algorithms:**
- `get_next_pending_with_subtasks()` - 3-phase smart task selection
- `find_subitems_by_status()` - Complex workflow automation queries
- Circular dependency detection for cross-list dependencies

### `core/database.py` (1618 lines)
SQLAlchemy ORM layer providing database abstraction and schema management.

**Database Schema (8 core tables):**
- `todo_lists` - List management with hierarchical relationships
- `todo_items` - Items with subtask support via `parent_item_id`
- `item_dependencies` - Cross-list task blocking/requirements
- `list_properties`/`item_properties` - Key-value runtime configuration
- `list_tags`/`list_tag_assignments` - Dynamic tag system with 12-color visual support
- `todo_history` - Complete audit trail for all operations

**Features:**
- Foreign key constraints with CASCADE operations
- Optimized indexes for common query patterns
- Session management with context managers
- Migration system for schema evolution

### `core/models.py` (655 lines)
Pydantic models providing comprehensive data validation and type safety.

**Model Categories:**
- **5 Enums**: Item status types, list types, list status types, dependency types, history actions
- **17 Pydantic Models**: Core data structures with validation
- **Business Rules**: Automatic validation of relationships and constraints

## 2. Interfaces Layer

User-facing interfaces providing multiple ways to interact with the system:

### `interfaces/mcp_server.py` (2105 lines)
Model Context Protocol server providing **MCP tools** for Claude Code integration.

**Tool Categories:**
- **Basic Operations** (19 tools): Core CRUD functionality
- **Advanced Operations** (16 tools): Complex workflows and properties  
- **Subitem Operations** (5 tools): Hierarchical task management
- **Dependency Operations** (6 tools): Cross-list coordination
- **Smart Algorithms** (5 tools): Intelligent task selection

**Features:**
- 3-level configuration system (MINIMAL/STANDARD/MAX)
- Data optimization for reduced token usage
- Comprehensive error handling
- Natural sorting for predictable ordering

### `interfaces/cli.py` + `cli_modules/`
Rich command-line interface built with `click` and `rich` libraries.

**Modular Commands:**
- `cli_modules/list_commands.py` - List management
- `cli_modules/item_commands.py` - Item operations
- `cli_modules/tag_commands.py` - Tag system
- `cli_modules/property_commands.py` - Property management
- `cli_modules/dependency_commands.py` - Cross-list dependencies
- `cli_modules/report_commands.py` - Analytics and reports

**Visual Features:**
- Rich tables with status icons and progress bars
- Live monitoring with real-time updates
- Multiple output formats (table, JSON, YAML, XML)
- Color-coded status indicators

## 3. Database Layer

### SQLite + SQLAlchemy Stack
- **SQLite**: Lightweight, file-based database perfect for local task management
- **SQLAlchemy 2.0**: Modern ORM with async support and improved type safety
- **Migration System**: Versioned schema changes in `migrations/` directory

### Schema Design Principles
- **Referential Integrity**: Foreign keys with CASCADE constraints
- **Performance**: Strategic indexes for common query patterns
- **Flexibility**: JSON metadata fields for extensibility
- **Audit Trail**: Complete history tracking for all operations

## Data Flow

```
CLI/MCP Interface → TodoManager → Database Layer → SQLite
                ←               ←                ←
```

1. **Interface Layer** receives user requests (CLI commands or MCP tool calls)
2. **TodoManager** validates inputs and applies business logic
3. **Database Layer** persists changes with transaction safety
4. **Responses** flow back through the same layers with formatted output

## Key Design Patterns

### Repository Pattern
- `TodoManager` acts as a repository for all data operations
- Encapsulates database access behind clean APIs
- Provides consistent error handling across interfaces

### Command Pattern
- CLI commands are modularized for maintainability
- MCP tools provide fine-grained programmatic access
- Each operation is atomic and transactional

### Observer Pattern
- Automatic status synchronization for hierarchical tasks
- History tracking for audit trails
- Tag color recalculation on system changes

## Performance Optimizations

### Database Level
- **Covering Indexes**: `idx_todo_items_parent_status` for hierarchy queries
- **Bulk Operations**: `quick_add` for multiple items
- **Lazy Loading**: Dependencies loaded on-demand
- **Connection Pooling**: Efficient SQLite connection management

### Interface Level
- **Data Reduction**: 50-67% smaller responses from MCP tools
- **Natural Sorting**: Intuitive ordering without performance penalty
- **Caching**: Progress statistics cached for repeated queries

## Security Considerations

### Current Vulnerabilities
- File path validation needed for import/export operations
- MCP interface lacks authentication (all 51 tools publicly accessible)
- Error messages may leak internal details

### Implemented Protections
- Comprehensive Pydantic validation for all inputs
- SQL injection protection via SQLAlchemy ORM
- Business rule enforcement at the model level
- Circular dependency detection to prevent infinite loops

## Testing Strategy

The architecture supports comprehensive testing at multiple levels:

- **Unit Tests**: Core business logic in isolation
- **Integration Tests**: Database operations and cross-component interactions
- **End-to-End Tests**: Complete workflows through CLI and MCP interfaces
- **Edge Case Tests**: Boundary conditions and error scenarios

**Test Coverage**: 136/136 tests passing (100%) across all architectural layers.

---

This architecture provides a solid foundation for intelligent task management while maintaining flexibility for future enhancements and integrations.
