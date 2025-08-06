# TODOIT MCP

**Intelligent Task Management System with MCP Integration**

TODOIT (Todo It) is a comprehensive task management platform that scales from simple lists to complex multi-team projects. Built with intelligent prioritization, hierarchical task breakdown, and cross-list dependency management.

## 🚀 Key Features

### 🧠 **Smart Task Management**
- **Hierarchical Tasks** - Break down complex tasks into subtasks with parent-child relationships
- **Cross-List Dependencies** - Coordinate work across different lists and teams
- **Intelligent Next Task Algorithm** - Smart prioritization for optimal workflow
- **Auto-completion Logic** - Parents auto-complete when all subtasks are done
- **Circular Dependency Prevention** - Automatic detection and prevention of dependency loops

### 📊 **Advanced Progress Tracking**
- **Comprehensive Statistics** - 12 different metrics including blocked/available counts
- **Real-time Status** - Live blocking detection and workflow optimization
- **Project-wide Progress** - Track progress across multiple related lists

### 🔗 **Integration Capabilities**
- **40 MCP Tools** - Complete API for Claude Code integration
- **Rich CLI Interface** - Beautiful tables with blocked status indicators (🚫)
- **SQLite Database** - Robust schema with foreign key relationships
- **Import/Export** - Markdown format with checkbox support

## 🏗️ Architecture

```
Claude Code <--MCP--> TodoMCPServer <--API--> TodoManager <--ORM--> SQLite
                            |                         ^                  |
                            |                         |                  |
                       40 MCP Tools           Smart Algorithm      Enhanced Schema
                                                    |                     |
                                               Rich CLI              Dependencies
                                            (📊 status display)        & Relations
```

### Database Schema
- **todo_lists** - List management with metadata
- **todo_items** - Items with hierarchical relationships (`parent_item_id`)
- **item_dependencies** - Cross-list task dependencies
- **list_relations** - Project grouping and relationships  
- **list_properties** - Key-value configuration storage

## 📦 Installation

### Requirements
- Python 3.12+
- SQLite (included with Python)

### Setup
```bash
# Clone repository
git clone <repository-url>
cd todoit-mcp

# Install dependencies
pip install -r requirements.txt

# Initialize database (automatic on first run)
python -c "from core.manager import TodoManager; TodoManager()"
```

### Project Structure
```
todoit-mcp/
├── core/                   # Core Logic
│   ├── manager.py         # TodoManager - main API
│   ├── models.py          # Data models (Pydantic)
│   ├── database.py        # Database layer (SQLAlchemy)
│   └── validators.py      # Business rules
├── interfaces/            # User Interfaces  
│   ├── mcp_server.py     # MCP Server (43 tools)
│   └── cli.py            # Command-line interface
├── migrations/           # Database migrations
├── docs/                 # Documentation & examples
├── pyproject.toml       # Project configuration
└── requirements.txt     # Python dependencies
```

## 🛠️ Tech Stack

- **Python 3.12+** - Modern Python with type hints and async
- **SQLAlchemy 2.0** - Advanced ORM with foreign key relationships
- **Pydantic V2** - Data validation with enhanced models
- **FastMCP** - Model Context Protocol server framework
- **Click + Rich** - Beautiful CLI with progress visualization
- **SQLite** - Production-ready embedded database

## 🎯 Core Capabilities

### **Basic Task Management**
- `create_list` / `delete_list` - Manage task lists
- `add_item` / `update_item_status` - Basic task operations
- `get_next_pending` - Get next available task
- `get_progress` - Track completion statistics

### **Hierarchical Tasks (Subtasks)**
- `add_subtask` - Create parent-child task relationships
- `get_item_hierarchy` - View complete task breakdown
- `auto_complete_parent` - Smart parent completion logic
- `get_next_pending_with_subtasks` - Priority-based task selection

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

### **MCP Integration (40 Tools)**
All functionality available via MCP for Claude Code:
- List management (create, update, delete, relations)
- Item operations (add, update status, move, convert to subtask)  
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
- **Goal breakdown** - Large goals into manageable subtasks
- **Habit tracking** - Sequential task completion with progress metrics

## 🚀 Quick Start

### Using with Claude Code (MCP)
```bash
# The system is ready for MCP integration
# Use any of the 43 available tools directly in Claude Code
```

### Command Line Interface
```bash
# Create lists and add hierarchical tasks
python -m interfaces.cli list create "project" "My Project"
python -m interfaces.cli item add "project" "feature" "Implement feature"
python -m interfaces.cli item add-subtask "project" "feature" "backend" "Backend implementation"

# Add cross-list dependencies
python -m interfaces.cli dep add "frontend:ui" requires "backend:api"

# Get smart next task
python -m interfaces.cli item next "project" --smart
```

## 📚 Documentation

Complete documentation available in the [docs/](docs/) directory:

- **[CLI User Guide](docs/CLI_GUIDE.md)** - Comprehensive command-line interface guide
- **[MCP Tools Reference](docs/MCP_TOOLS.md)** - All 40 MCP tools for Claude Code
- **[Architecture](docs/architecture.md)** - System design and patterns
- **[API Reference](docs/api.md)** - TodoManager class documentation

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