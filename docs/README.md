# TODOIT MCP Documentation

Welcome to the official documentation for TODOIT MCP, an intelligent TODO list management system with hierarchical tasks, cross-list dependencies, and complete Claude Code integration.

## 📚 Table of Contents

### Core Documentation
- **[Architecture](architecture.md)** - System architecture and design patterns
- **[Database Schema](database.md)** - Complete database structure and relationships  
- **[Installation & Setup](installation.md)** - Get started quickly

### User Guides
- **[CLI User Guide](CLI_GUIDE.md)** - Command reference for list, item, stats, io, property, dep, and interactive commands
- **[MCP Tools](MCP_TOOLS.md)** - All 55 MCP tools for Claude Code integration
- **[Programmatic API](api.md)** - TodoManager class reference

### Advanced Topics
- **[Testing Documentation](TESTS.md)** - Complete test suite overview
- **[Refactoring Analysis](REFAKTORING.md)** - DDD+CQRS refactoring lessons learned

### Legacy Documentation
- **[PRD](prd.md)** - Original product requirements document
- **[Design Notes](todo-mcp-design.md)** - Historical design decisions

## 🚀 Quick Start

### Using with Claude Code (MCP)
All 55 MCP tools are automatically available - no additional setup required!

### Command Line Interface
```bash
# Create project and add hierarchical tasks
todoit list create --list "project" --title "My Project"
todoit item add --list "project" --item "feature" --title "Implement feature"  
todoit item add --list "project" --item "feature" --subitem "backend" --title "Backend work"

# Add cross-list dependencies
todoit dep add --dependent "frontend:ui" --required "backend:api" --force

# Get smart next task
todoit item next-smart --list "project"
```

## 🎯 Key Features

- **55 MCP Tools** - Complete Claude Code integration
- **Hierarchical Tasks** - Subitems with parent-child relationships  
- **Cross-List Dependencies** - Coordinate work across multiple lists
- **Smart Algorithms** - Intelligent next task selection
- **Rich CLI** - Beautiful tables with status indicators
- **Import/Export** - Markdown format with checkbox support (- [ ] format now supported!)

## 📊 System Status

✅ **Production Ready**
- 136/136 tests passing (100%)
- All 55 MCP tools tested and verified
- CLI fully functional with --force flags
- Markdown import/export working with all formats
- Complete documentation coverage

---
