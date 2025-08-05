# TODOIT MCP

**Universal TODO list management system with MCP integration for Claude Code**

TODOIT (Todo It) is a professional TODO list management system optimized for automation and AI integration, built with Python and SQLite.

## 🚀 Features

- **Programmatic API** - Core business logic with TodoManager class
- **MCP Integration** - Native support for Claude Code via Model Context Protocol
- **Rich CLI** - Beautiful command-line interface with tables and progress bars
- **SQLite Database** - Lightweight embedded database with full relational structure
- **Multi-state Completion** - Track complex tasks with multiple completion states
- **Hierarchical Lists** - Support for nested tasks and list relationships
- **Import/Export** - Markdown format support with multi-column parsing

## 🏗️ Architecture

```
Claude Code <--MCP--> TodoMCPServer <--API--> TodoManager <--ORM--> SQLite
                                                    ^
                                                    |
                                               Rich CLI
```

## 📦 Project Structure

```
todoit-mcp/
├── core/                   # Programmatic API (core logic)
│   ├── manager.py         # TodoManager - main business logic
│   ├── models.py          # Data models (Pydantic)
│   ├── database.py        # Database access layer
│   └── validators.py      # Business rules
├── interfaces/            # Access interfaces
│   ├── mcp_server.py     # MCP Server
│   └── cli.py            # Rich CLI
├── migrations/           # Database migrations
├── pyproject.toml       # Project configuration
└── requirements.txt     # Dependencies
```

## 🛠️ Tech Stack

- **Python 3.12+** - Modern Python with type hints
- **SQLAlchemy 2.0** - ORM with async support
- **Pydantic** - Data validation and models
- **MCP SDK** - Model Context Protocol integration
- **Click + Rich** - Beautiful CLI interface
- **SQLite** - Lightweight embedded database

## 📋 Core Functions (Stage 1)

1. **create_list** - Create TODO lists (empty, with N items, from directory)
2. **get_list** - Retrieve list by ID or key
3. **delete_list** - Remove list with dependency validation
4. **list_all** - List all TODO lists
5. **add_item** - Add task to list
6. **update_item_status** - Change task status with multi-state support
7. **get_next_pending** - Get next available task
8. **get_progress** - Calculate completion statistics
9. **import_from_markdown** - Import from `[x]` format
10. **export_to_markdown** - Export to `[x]` format

## 🎯 Use Cases

- **Development Projects** - Track coding tasks with multi-state completion
- **Deployment Pipelines** - Sequential task execution with dependencies  
- **Content Creation** - Hierarchical task organization
- **Team Collaboration** - Shared task lists with metadata

## 📄 License

This project is released into the public domain under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license.

## 🤝 Contributing

Contributions are welcome! This project uses:
- **Task Master** for project management
- **Claude Code** for AI-assisted development
- **GitHub Actions** for CI/CD (planned)

---

**Status:** 🚧 In Development - Stage 1 (Project Scaffolding) Complete