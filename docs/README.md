# TODOIT MCP Documentation

Welcome to the official documentation for TODOIT MCP, an intelligent TODO list management system with hierarchical tasks, cross-list dependencies, and complete Claude Code integration.

## 📚 Table of Contents

### Core Documentation
- **[Architecture](architecture.md)** - System architecture and design patterns
- **[Database Schema](database.md)** - Complete database structure and relationships  
- **[Installation & Setup](installation.md)** - Get started quickly

### User Guides  
- **[CLI User Guide](CLI_GUIDE.md)** - Comprehensive command-line interface guide
- **[MCP Tools](MCP_TOOLS.md)** - All 45 MCP tools for Claude Code integration
- **[Programmatic API](api.md)** - TodoManager class reference

### Advanced Topics
- **[Testing Documentation](TESTS.md)** - Complete test suite overview
- **[Refactoring Analysis](REFAKTORING.md)** - DDD+CQRS refactoring lessons learned

### Legacy Documentation
- **[PRD](prd.md)** - Original product requirements document
- **[Design Notes](todo-mcp-design.md)** - Historical design decisions

## 🚀 Quick Start

### Using with Claude Code (MCP)
All 45 MCP tools are automatically available - no additional setup required!

### Command Line Interface
```bash
# Create project and add hierarchical tasks
python -m interfaces.cli list create "project" --title "My Project"
python -m interfaces.cli item add "project" "feature" "Implement feature"  
python -m interfaces.cli item add-subtask "project" "feature" "backend" "Backend work"

# Add cross-list dependencies
python -m interfaces.cli dep add "frontend:ui" requires "backend:api" --force

# Get smart next task
python -m interfaces.cli item next-smart "project"
```

## 🎯 Key Features

- **44 MCP Tools** - Complete Claude Code integration
- **Hierarchical Tasks** - Subtasks with parent-child relationships  
- **Cross-List Dependencies** - Coordinate work across multiple lists
- **Smart Algorithms** - Intelligent next task selection
- **Rich CLI** - Beautiful tables with status indicators
- **Import/Export** - Markdown format with checkbox support (- [ ] format now supported!)

## 📊 System Status

✅ **Production Ready**
- 136/136 tests passing (100%)
- All 45 MCP tools tested and verified
- CLI fully functional with --force flags
- Markdown import/export working with all formats
- Complete documentation coverage

---

*Documentation last updated: August 6, 2025*
