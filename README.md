# TODOIT MCP

**Advanced Task Management System with Complete Phase 3 Integration**

TODOIT (Todo It) is a comprehensive task management platform that scales from simple lists to complex multi-team projects. Built with intelligent prioritization, hierarchical task breakdown, and cross-list dependency management.

## 🚀 Phase 3 Features (Complete System)

### 🎯 **Three-Phase Architecture**
- **Phase 1: Subtasks** - Hierarchical task breakdown with parent-child relationships
- **Phase 2: Cross-List Dependencies** - Project coordination across different lists/teams
- **Phase 3: Smart Integration** - Intelligent algorithms combining all mechanisms

### 🧠 **Smart Task Management**
- **Intelligent Next Task Algorithm** - 4-tier priority system for optimal workflow
- **Comprehensive Progress Tracking** - 12 different metrics including blocked/available counts
- **Circular Dependency Prevention** - Automatic detection and prevention of dependency cycles
- **Auto-completion Logic** - Parents auto-complete when all subtasks are done

### 🔗 **Integration Capabilities**
- **43 MCP Tools** - Complete API coverage for all functionality
- **Rich CLI Interface** - Beautiful tables with blocked status indicators (🚫)
- **SQLite Database** - Robust schema with foreign key relationships
- **Real-time Status** - Live blocking detection and workflow optimization

## 🏗️ Phase 3 Architecture

```
Claude Code <--MCP--> TodoMCPServer <--API--> TodoManager <--ORM--> SQLite
                            |                         ^                  |
                            |                         |                  |
                       43 MCP Tools           Smart Algorithm      item_dependencies
                                                    |                  table
                                               Rich CLI
                                            (🚫 blocked status)
```

### Database Schema
- **todo_lists** - Basic list management
- **todo_items** - Items with `parent_item_id` for Phase 1 subtasks
- **item_dependencies** - Cross-list dependencies for Phase 2
- **list_relations** - Project grouping and relationships
- **list_properties** - Key-value metadata storage

## 📦 Project Structure

```
todoit-mcp/
├── core/                   # Phase 3 Core Logic
│   ├── manager.py         # TodoManager with smart algorithms
│   ├── models.py          # Enhanced Pydantic models
│   ├── database.py        # Full ORM with dependencies
│   └── validators.py      # Business rules & validation
├── interfaces/            # User Interfaces
│   ├── mcp_server.py     # 43 MCP Tools (all phases)
│   └── cli.py            # Rich CLI with Phase 3 display
├── migrations/           # Database Schema Evolution
│   ├── 001_initial.sql   # Basic schema
│   └── 002_item_dependencies.sql # Phase 2 cross-list deps
├── docs/                 # Complete Documentation
│   ├── SUBTASKS.md       # Architectural plan
│   ├── PHASE3_INTEGRATION.md # Integration guide
│   └── PHASE3_EXAMPLES.md    # Real-world examples
├── pyproject.toml       # Project configuration
└── requirements.txt     # Dependencies
```

## 🛠️ Tech Stack

- **Python 3.12+** - Modern Python with type hints and async
- **SQLAlchemy 2.0** - Advanced ORM with foreign key relationships
- **Pydantic V2** - Data validation with enhanced models
- **FastMCP** - Model Context Protocol server framework
- **Click + Rich** - Beautiful CLI with progress visualization
- **SQLite** - Production-ready embedded database

## 🎯 Phase 3 Capabilities

### **Phase 1: Hierarchical Subtasks**
- `add_subtask` - Create parent-child task relationships
- `get_item_hierarchy` - Recursive task structure retrieval
- `auto_complete_parent` - Smart parent completion logic
- `get_next_pending_with_subtasks` - Priority-based task selection

### **Phase 2: Cross-List Dependencies**
- `add_item_dependency` - Create cross-list task dependencies
- `get_item_blockers` - Identify blocking tasks
- `is_item_blocked` - Real-time blocking status
- `get_dependency_graph` - Visualization data for complex projects

### **Phase 3: Smart Integration**
- `get_comprehensive_status` - Unified status across all mechanisms
- `can_start_item` - Combined Phase 1 + 2 availability checks
- `get_cross_list_progress` - Multi-list project progress tracking
- Enhanced progress stats with 12 different metrics

### **Core MCP Tools (43 Total)**
All functionality accessible via MCP for Claude Code integration:
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

- **[SUBTASKS.md](docs/SUBTASKS.md)** - Complete architectural plan
- **[PHASE3_INTEGRATION.md](docs/PHASE3_INTEGRATION.md)** - Integration guide  
- **[PHASE3_EXAMPLES.md](docs/PHASE3_EXAMPLES.md)** - Practical examples and scenarios

## 📄 License

This project is released into the public domain under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license.

## 🤝 Contributing

Contributions are welcome! This project uses:
- **Task Master** workflow for development coordination
- **Claude Code** for AI-assisted development
- **Phase 3 TODOIT** for project management (self-hosting!)

---

## 🎉 Status: **COMPLETE** 
**Phase 3 Integration Finished** - Full-featured task management system ready for production use

### Implementation Timeline
- ✅ **Phase 1: Subtasks** - Hierarchical task management
- ✅ **Phase 2: Cross-List Dependencies** - Multi-list project coordination  
- ✅ **Phase 3: Smart Integration** - Unified intelligent system

All three phases working together seamlessly! 🚀