# TODOIT MCP

**Intelligent Task Management System with MCP Integration**

TODOIT (Todo It) is a comprehensive task management platform that scales from simple lists to complex multi-team projects. Built with intelligent prioritization, hierarchical task breakdown, and cross-list dependency management.

## 🚀 Key Features

### 🧠 **Smart Task Management**
- **Hierarchical Tasks** - Break down complex tasks into subitems with parent-child relationships
- **Cross-List Dependencies** - Coordinate work across different lists and teams
- **Intelligent Next Task Algorithm** - Smart prioritization for optimal workflow
- **Auto-completion Logic** - Parents auto-complete when all subitems are done
- **Circular Dependency Prevention** - Automatic detection and prevention of dependency loops

### 📊 **Advanced Progress Tracking**
- **Comprehensive Statistics** - 12 different metrics including blocked/available counts
- **Real-time Status** - Live blocking detection and workflow optimization
- **Project-wide Progress** - Track progress across multiple related lists

### 🏷️ **Dynamic Tag System**
- **12-Color Visual System** - Dynamic color assignment based on alphabetical sorting
- **Self-Healing Colors** - Automatic color recalculation when tags are deleted
- **Smart Column Layout** - Dynamic width adjustment (3-12 chars) based on tag count
- **Professional Display** - Colored dots (●) with interactive legends

### 🔗 **Integration Capabilities**
- **55 MCP Tools** - Complete API for Claude Code integration with 3 configuration levels
- **Rich CLI Interface** - Icon-based columns (⏳ ✅ 📊 📋) with blocked status indicators (🚫)
- **SQLite Database** - Robust schema with foreign key relationships
- **Import/Export** - Markdown format with checkbox support

## 🏗️ Architecture

```
Claude Code <--MCP--> TodoMCPServer <--API--> TodoManager <--ORM--> SQLite
                            |                         ^                  |
                            |                         |                  |
                       55 MCP Tools           Smart Algorithm      Enhanced Schema
                                                    |                     |
                                               Rich CLI              Dependencies
                                            (📊 status display)        & Relations
```

### Database Schema (9 Tables)
- **todo_lists** - List management with metadata and hierarchical relationships
- **todo_items** - Items with subitem support via `parent_item_id`
- **item_dependencies** - Cross-list task dependencies and blocking logic
- **list_relations** - Project grouping and 1:1 list linking
- **list_properties** - Key-value configuration storage for lists
- **item_properties** - Key-value runtime properties for individual items
- **list_tags** - Global tag definitions with color system
- **list_tag_assignments** - Many-to-many list-to-tag relationships
- **todo_history** - Complete audit trail for all operations

## 📦 Installation

### Requirements
- Python 3.12+
- SQLite (included with Python)

For detailed instructions on how to install `todoit-mcp` for user, developer, or MCP integration, please see the **[Comprehensive Installation Guide](docs/installation.md)**.

### Project Structure
```
todoit-mcp/
├── core/                   # Core Logic
│   ├── manager.py         # TodoManager - main API
│   ├── models.py          # Data models (Pydantic)
│   ├── database.py        # Database layer (SQLAlchemy)
│   └── validators.py      # Business rules
├── interfaces/            # User Interfaces  
│   ├── mcp_server.py     # MCP Server (56 tools)
│   └── cli.py            # Command-line interface
├── migrations/           # Database migrations
├── docs/                 # Documentation & examples
├── pyproject.toml       # Project configuration
└── requirements.txt     # Python dependencies
```

## 🛠️ Tech Stack

- **Python 3.12+** - Modern Python with type hints and async support
- **SQLAlchemy 2.0** - Advanced ORM with foreign key relationships and migrations
- **Pydantic V2** - Data validation with enhanced models and performance
- **FastMCP** - Model Context Protocol server framework for Claude Code
- **Click + Rich** - Beautiful CLI with progress visualization and colored output
- **SQLite** - Production-ready embedded database with WAL mode

## ⚡ Performance & Testing

### Performance Metrics
- **Database**: Optimized SQLite with proper indexing and foreign keys
- **MCP Response Time**: < 50ms for standard operations
- **CLI Rendering**: Rich tables with sub-second display for 1000+ items
- **Memory Usage**: < 50MB typical working set
- **Concurrent Support**: Thread-safe operations with session management

### Quality Assurance
- **428 Tests Passing** - Comprehensive test coverage
- **Unit Tests**: Core business logic with mocked dependencies
- **Integration Tests**: Full database workflows and API testing
- **Edge Cases**: Robustness testing for error conditions
- **End-to-End**: Complete workflow validation from CLI to database

## 🎯 Core Capabilities

### **Basic Task Management**
- `create_list` / `delete_list` - Manage task lists
- `add_item` / `update_item_status` - Basic task operations
- `get_next_pending` - Get next available task
- `get_progress` - Track completion statistics

### **Hierarchical Tasks (Subitems)**
- `add_subitem` - Create parent-child task relationships
- `get_item_hierarchy` - View complete task breakdown
- `auto_complete_parent` - Smart parent completion logic
- `get_next_pending_with_subitems` - Priority-based task selection

### **Cross-List Dependencies**
- `add_item_dependency` - Create dependencies between different lists
- `get_item_blockers` - Identify what's blocking a task
- `is_item_blocked` - Check if task can be started
- `get_dependency_graph` - Visualize project dependencies

### **Smart Integration**
- `get_comprehensive_status` - Complete task and project status
- `can_start_item` - Check availability across all mechanisms
- `get_cross_list_progress` - Multi-list project tracking
- Enhanced progress with blocked/available item counts

### **MCP Integration (44 Tools)**
All functionality available via MCP for Claude Code:
- List management (create, update, delete, relations)
- Item operations (add, update status, move, convert to subitem)  
- Smart algorithms (next task, blocking analysis, progress tracking)
- Import/Export (Markdown format with checkbox support)
- Project coordination (dependency graphs, cross-list progress)

## 💼 Real-World Use Cases

### **Software Development**
- **Multi-team coordination** - Backend depends on frontend, QA depends on dev
- **Feature breakdown** - Epic → Stories → Tasks → Subtasks
- **Release pipelines** - Sequential phases with cross-team dependencies

### **Content Creation**
- **Editorial workflows** - Writing → Editing → Design → Publishing
- **Campaign management** - Research → Content → Graphics → Distribution
- **Documentation projects** - Technical writing with review dependencies

### **Project Management**
- **Complex projects** - Multiple lists with interdependent tasks
- **Resource coordination** - Tasks blocked until prerequisites complete
- **Progress tracking** - Real-time visibility across all project components

### **Personal Productivity**
- **Simple lists** - Basic todo functionality
- **Goal breakdown** - Large goals into manageable subitems
- **Habit tracking** - Sequential task completion with progress metrics

## 🚀 Quick Start

### Basic Usage (After Installation)
```bash
# Create your first project
todoit list create --list "my-project" --title "My First Project"

# Add some tasks
todoit item add --list "my-project" --item "setup" --title "Set up development environment"
todoit item add --list "my-project" --item "feature" --title "Implement main feature"

# Add subitems for better organization
todoit item add --list "my-project" --item "setup" --subitem "install-deps" --title "Install dependencies"
todoit item add --list "my-project" --item "setup" --subitem "config" --title "Configure environment"

# Check what to work on next
todoit item next --list "my-project"

# Mark tasks as completed
todoit item status --list "my-project" --item "setup" --subitem "install-deps" --status completed

# View project progress
todoit list show --list "my-project"
```

### Using with Claude Code (MCP)
After MCP setup, all 56 tools are available directly in Claude Code:

**Example conversation with Claude Code:**
```
You: "Help me plan a new web application project"

Claude: I'll help you create a structured project plan using TODOIT. Let me set up 
some task lists for your web application.

*Uses todo_create_list to create "backend", "frontend", and "deployment" lists*
*Uses todo_add_item to add initial tasks*
*Uses todo_add_subitem to break down complex tasks*
*Uses todo_add_item_dependency to set up proper task ordering*

You: "What should I work on first?"

Claude: *Uses todo_get_next_pending_enhanced to find the optimal next task*
Based on your project dependencies, you should start with "Set up database schema" 
in the backend list, as the frontend components depend on this being completed first.
```

**Available MCP Tools:**
- **Project Management**: Create lists, set up relationships
- **Task Management**: Add/update tasks, hierarchical subitems
- **Properties Management**: Set runtime properties on lists and individual items
- **Smart Workflow**: Next task recommendations, dependency management  
- **Progress Tracking**: Statistics, completion status, project overviews
- **Import/Export**: Markdown integration for documentation

### Advanced Workflows
```bash
# Multi-list project with dependencies
todoit list create --list "backend" --title "Backend Development"
todoit list create --list "frontend" --title "Frontend Development"

todoit item add --list "backend" --item "api" --title "REST API implementation"
todoit item add --list "frontend" --item "ui" --title "User interface"

# Create dependency: frontend depends on backend
todoit dep add "frontend:ui" requires "backend:api" --force

# Smart task selection respects dependencies
todoit item next --list "frontend"  # Will be blocked until backend:api is done
todoit item next --list "backend"   # Will suggest api task
```

## 🔧 Troubleshooting

### Common Issues

#### MCP Integration
- **"Server not responding"**: Ensure Python environment matches Claude Code's environment
- **"Module not found"**: Try absolute path: `/usr/bin/python3 -m interfaces.mcp_server`
- **"Permission denied"**: Check config directory permissions: `~/.config/claude-code/`

#### CLI Issues
- **"Command not found: todoit"**: Install with `pip install -e .` or use `python -m interfaces.cli`
- **"Database locked"**: Close other TODOIT instances, or specify different DB with `--db`
- **"No such table"**: Database migration needed, delete and recreate: `rm ~/.todoit/todoit.db`

#### Tag System
- **"Tags not showing colors"**: Ensure Rich library is updated: `pip install --upgrade rich`
- **"Tag column too wide/narrow"**: Dynamic sizing based on tag count, working as designed
- **"Tags disappeared after deletion"**: Colors recalculate alphabetically (expected behavior)

#### Environment Issues
- **FORCE_TAGS not working**: Environment variables only affect CLI, not MCP tools
- **Tags not auto-applying**: Check `.env` file location and format: `TODOIT_FORCE_TAGS=dev,test`

### Debug Mode
```bash
# Enable verbose output for debugging
export TODOIT_DEBUG=1
todoit --help

# Check database status
python -c "from core.manager import TodoManager; mgr = TodoManager(); print(f'DB: {mgr.db_path}')"

# Test MCP server directly
python -m interfaces.mcp_server
```

### Getting Help
- 📖 **Documentation**: Full guides in [docs/](docs/)
- 🐛 **Issues**: Report bugs on [GitHub](https://github.com/hipotures/todoit/issues)
- 💬 **Discussions**: Ask questions in [GitHub Discussions](https://github.com/hipotures/todoit/discussions)

## 📚 Documentation

Complete documentation available in the [docs/](docs/) directory:

- **[CLI User Guide](docs/CLI_GUIDE.md)** - Comprehensive command-line interface guide
- **[MCP Tools Reference](docs/MCP_TOOLS.md)** - All 56 MCP tools for Claude Code
- **[Architecture](docs/architecture.md)** - System design and patterns
- **[API Reference](docs/api.md)** - TodoManager class documentation
- **[CHANGELOG](CHANGELOG.md)** - Version history and release notes

## 📄 License

This project is released into the public domain under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license.

## 🤝 Contributing

Contributions are welcome! This project uses:
- **Modern Python** development practices
- **Claude Code** for AI-assisted development
- **TODOIT itself** for project management

---

## 🎉 Status: **Production Ready** 

Full-featured task management system with intelligent prioritization, hierarchical tasks, cross-list dependencies, and complete MCP integration for Claude Code.

**Ready for use in simple todo lists through complex multi-team projects!** 🚀