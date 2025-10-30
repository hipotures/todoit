# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TODOIT MCP is an intelligent task management system with MCP integration for Claude Code. The system provides MCP tools for programmatic task management, featuring hierarchical tasks, cross-list dependencies, smart workflow algorithms, and dynamic tag system with 12-color visual support.

**Key Architecture**: Clean 3-layer design with `core/` (business logic), `interfaces/` (MCP server + CLI), and SQLite database with comprehensive schema for tasks, dependencies, and relationships.

**Requirements**: Python 3.12+, modern dependency stack (SQLAlchemy 2.0, Pydantic V2, FastMCP, Rich CLI).

## Development Setup

```bash
# Navigate to main codebase
cd todoit-mcp

# Install in development mode with dev dependencies
pip install -e .[dev]

# Initialize database (automatic on first run)
python -c "from core.manager import TodoManager; TodoManager()"

# Build package for distribution
python -m build

# Install package locally for testing
pip install dist/todoit_mcp-*.whl
```

## Essential Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_manager_comprehensive.py

# Run tests with coverage
pytest --cov=core --cov=interfaces

# Run specific test category
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/edge_cases/              # Edge case tests only
pytest tests/e2e/                     # End-to-end tests only

# Run tests matching pattern
pytest -k "test_create_list"
```

### Code Quality
```bash
# Format code (Black + isort configured for 88-char lines)
black core/ interfaces/ tests/
isort core/ interfaces/ tests/

# Type checking with MyPy
mypy core/ --strict

# Run all quality checks
black --check core/ interfaces/ && isort --check core/ interfaces/ && mypy core/
```

### MCP Server
```bash
# Test MCP server manually (for debugging Claude Code integration)
python -m interfaces.mcp_server

# CLI interface (alternative to MCP)
todoit --help
todoit list create "test" --title "Test List"
```

## Recent Major Features (v2.15.0)

### MCP Protocol Annotations
All 51 MCP tools now include proper protocol annotations:
- **29 read-only tools** (`readOnlyHint=True`) - Pure reads, no side effects
- **18 idempotent tools** (`idempotentHint=True`) - Safe to retry
- **12 destructive tools** (`destructiveHint=True`) - Modify/delete data

Annotations managed in `interfaces/mcp_tool_annotations.py` and automatically applied via `conditional_tool` decorator using `ToolAnnotations` from `mcp.types`.

### Pagination Support
Three key tools now support pagination (limit=50, offset=0):
- `todo_list_all()` - Paginate through all lists
- `todo_find_items_by_property()` - Paginate search results
- `todo_find_items_by_status()` - Paginate status queries

Standard pagination format includes metadata: `{limit, offset, total, has_more, next_offset}`

### Actionable Error Messages
Error responses now include suggestions:
```python
{
    "success": False,
    "error": "List 'mylist' not found",
    "error_type": "not_found",
    "suggestions": [
        "Use todo_list_all() to see available lists",
        "Use todo_create_list() to create a new list"
    ]
}
```

Helper function `error_response()` available in `interfaces/mcp_server.py`.

## Architecture Overview

### Core Components
- **`core/manager.py`** (2861 lines) - Main `TodoManager` class containing all business logic
- **`core/database.py`** (1618 lines) - SQLAlchemy ORM layer with 8 tables (lists, items, dependencies, properties, tags, assignments, history)
- **`core/models.py`** (655 lines) - Pydantic models with comprehensive validation (5 enums, 17 model classes)

### Interface Layer
- **`interfaces/mcp_server.py`** (~2200 lines) - MCP tools for Claude Code integration with protocol annotations, pagination, and actionable errors
- **`interfaces/mcp_tool_annotations.py`** (289 lines) - MCP protocol annotations for all 51 tools (readOnlyHint, destructiveHint, idempotentHint)
- **`interfaces/cli.py`** - Rich CLI with modular commands in `cli_modules/`
- **`interfaces/cli_modules/`** - Modular CLI commands (list, item, dependency, property management)

### Database Schema (8 core tables)
- `todo_lists` - List management with hierarchical relationships
- `todo_items` - Items with subtask support via `parent_item_id`
- `item_dependencies` - Cross-list task blocking/requirements
- `list_relations` - Project grouping and list relationships
- `list_properties`/`item_properties` - Key-value runtime configuration
- `list_tags`/`list_tag_assignments` - Dynamic tag system with 12-color visual support
- `todo_history` - Complete audit trail for all operations

### Pydantic Models Architecture
The `core/models.py` file provides comprehensive data validation and type safety:

**Core Enums (5 types)**:
- `ListType` - List ordering strategy (`sequential`)
- `ListStatus` - Active/archived list states
- `ItemStatus` - Task states (`pending`, `in_progress`, `completed`, `failed`)
- `HistoryAction` - Audit trail action types
- `DependencyType` - Cross-list dependency relationships

**Data Models (17 classes)**:
- **Core Models**: `TodoList`, `TodoItem`, `ListProperty`, `ItemProperty`
- **Hierarchy Models**: Subitem support with parent-child validation
- **Dependency Models**: Cross-list blocking relationships with circular detection
- **Tag Models**: Dynamic 12-color tag system with alphabetical ordering
- **History Models**: Complete audit trail with action tracking
- **Response Models**: Consistent API response formats with error handling

**Validation Features**:
- Automatic timestamp generation and timezone handling
- Key format validation (alphanumeric + underscore/dash)
- Business rule enforcement (status transitions, hierarchy constraints)
- Foreign key relationship validation
- Data integrity checks for complex operations

## Key Business Logic Patterns

### Smart Task Selection Algorithm
The `get_next_pending_with_subtasks()` function (lines 881-975) implements a 3-phase algorithm:
1. **Phase 1**: In-progress parents with pending subtasks (highest priority)
2. **Phase 2**: Cross-list dependency checking to avoid blocked tasks
3. **Phase 3**: Position-based selection with hierarchy awareness

### Circular Dependency Prevention
Database layer includes graph traversal algorithms in `_would_create_circular_dependency()` with depth limits and visited tracking to prevent infinite loops.

### List Linking System
`link_list_1to1()` creates complete copies with property synchronization and automatic project relations for collaborative workflows.

## Testing Strategy

### Test Organization
- **`tests/unit/`** - Fast unit tests with mocked dependencies
- **`tests/integration/`** - Full database integration tests
- **`tests/edge_cases/`** - Boundary conditions and robustness testing
- **`tests/e2e/`** - End-to-end workflow validation
- **`conftest.py`** - Shared fixtures with temporary database setup

### Critical Test Areas
- **Complex functions**: `link_list_1to1`, `get_next_pending_with_subtasks` require comprehensive coverage
- **Dependency management**: Circular detection, cross-list blocking logic
- **Data integrity**: SQLite foreign key constraints and cascade operations
- **Tag system**: Dynamic color assignment and self-healing capabilities
- **MCP interface**: All 51 tools have basic coverage but need edge case expansion
- **MCP compliance** (v2.15.0): `tests/unit/test_mcp_compliance.py` - 17 tests verifying protocol annotations for all 51 tools

## Common Development Patterns

### Database Operations
Always use session context managers for automatic cleanup:
```python
def create_list(self, list_data: Dict[str, Any]) -> TodoListDB:
    with self.get_session() as session:
        db_list = TodoListDB(**list_data)
        session.add(db_list)
        session.commit()
        session.refresh(db_list)
        return db_list
```

### Error Handling
Use `ValueError` for business logic violations, specific exceptions for system errors:
```python
# Good pattern used throughout codebase
if not re.search(r'[a-zA-Z]', list_key):
    raise ValueError(f"List key '{list_key}' must contain at least one letter")
```

### Model Conversion
Standard pattern for ORM to Pydantic model conversion:
```python
def _db_to_model(self, db_obj: Any, model_class: type) -> Any:
    obj_dict = {}
    for column in db_obj.__table__.columns:
        value = getattr(db_obj, column.name)
        obj_dict[column.name] = value
    return model_class.model_validate(obj_dict)
```

## Performance Considerations

**Known Issues** (from recent code review):
- N+1 query problems in `get_next_pending_with_subtasks` - consider bulk loading with `selectinload()`
- Missing composite indexes for common query patterns like `(parent_item_id, status)`
- Excessive session creation (174+ individual sessions) - consider transaction scopes

**Database Indexes** already optimized for:
- List lookups: `idx_todo_lists_list_key`
- Item queries: `idx_todo_items_list_id`, `idx_todo_items_status`, `idx_todo_items_position`
- Dependencies: `idx_item_deps_dependent`, `idx_item_deps_required`

## Security Notes

**Current Vulnerabilities** (from security audit):
- File path validation needed in `import_from_markdown()` and `export_to_markdown()`
- MCP interface lacks authentication - all 51 tools are publicly accessible
- Error messages may leak internal details

**Input Validation**: Comprehensive Pydantic validation in place for all models with custom validators for business rules.

## Documentation

Extensive documentation in `docs/` directory:
- `CLI_GUIDE.md` (835 lines) - Complete CLI usage
- `MCP_TOOLS.md` (832 lines) - MCP tools documented
- `api.md` (416 lines) - TodoManager API reference with examples
- `architecture.md` - System design overview
