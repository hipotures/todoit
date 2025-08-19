# TODOIT MCP - Developer Onboarding Guide

**Welcome to TODOIT MCP Development!** 🎉

This guide will get you from zero to productive contributor in under 30 minutes.

---

## 🎯 Quick Start Checklist

- [ ] **Environment Setup** (5 minutes)
- [ ] **Code Exploration** (10 minutes) 
- [ ] **First Contribution** (15 minutes)
- [ ] **Testing & Quality** (10 minutes)

---

## 🛠️ Environment Setup (5 minutes)

### Prerequisites Check
```bash
# Verify Python version (3.12+ required)
python --version  # Should show Python 3.12+

# Clone the repository
git clone https://github.com/hipotures/todoit.git
cd todoit/todoit-mcp
```

### Development Installation
```bash
# Install in development mode with all dev dependencies
pip install -e .[dev]

# Verify installation works
todoit --version  # Should show current version

# Initialize test database
python -c "from core.manager import TodoManager; TodoManager('/tmp/test_dev.db')"
```

### IDE Setup (Recommended: VS Code)
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension ms-python.mypy-type-checker

# Open project
code .
```

---

## 🗂️ Code Exploration (10 minutes)

### Project Structure Deep Dive

```
todoit-mcp/
├── core/                    # 🧠 Business Logic (Clean Architecture)
│   ├── manager.py          # Main TodoManager class (2861 lines)
│   ├── database.py         # SQLAlchemy ORM layer (1618 lines)
│   ├── models.py           # Pydantic validation models (655 lines)
│   └── manager_*.py        # Specialized manager modules
├── interfaces/             # 🎨 User Interfaces
│   ├── cli.py             # Main CLI entry point
│   ├── cli_modules/       # Modular CLI commands
│   └── mcp_server.py      # MCP server (51 tools, 2105 lines)
├── tests/                 # 🧪 Test Suite (178+ tests)
│   ├── unit/              # Fast unit tests
│   ├── integration/       # Database integration tests
│   ├── edge_cases/        # Boundary condition tests
│   └── e2e/               # End-to-end workflow tests
├── migrations/            # 📊 Database migrations
└── docs/                  # 📚 Documentation
```

### Core Concepts

#### 1. **TodoManager** - The Heart of the System
```python
# Located in: core/manager.py
# Purpose: Central coordinator for all business logic
# Size: 2861 lines - the largest single file

from core.manager import TodoManager
manager = TodoManager()  # Auto-creates database if needed
```

#### 2. **Database Layer** - SQLAlchemy ORM
```python
# Located in: core/database.py  
# 9 Tables with full referential integrity
# Foreign key constraints enforced
# 12+ strategic indexes for performance

# Key tables:
# - todo_lists: List management
# - todo_items: Items with hierarchy support
# - item_dependencies: Cross-list blocking
# - list_properties/item_properties: Key-value storage
```

#### 3. **MCP Integration** - Claude Code Interface
```python
# Located in: interfaces/mcp_server.py
# 51 tools across 3 configuration levels
# MINIMAL (12) / STANDARD (23) / MAX (51)

# Environment variable controls tool availability:
export TODOIT_MCP_TOOLS_LEVEL=standard
```

### Quick Code Tour

```bash
# 1. Explore the main manager
head -50 core/manager.py

# 2. Look at database models
grep -n "class.*DB" core/database.py

# 3. Check Pydantic models
grep -n "class.*:" core/models.py

# 4. Browse CLI commands
ls interfaces/cli_modules/

# 5. See MCP tools structure
grep -n "@server.tool" interfaces/mcp_server.py | head -10
```

---

## 🚀 First Contribution (15 minutes)

### 1. Find Something to Work On

```bash
# Check open issues (easiest first contributions)
grep -r "TODO" core/ interfaces/
grep -r "FIXME" core/ interfaces/  
grep -r "XXX" core/ interfaces/

# Or check the TODO.md file
cat ../docs/TODO.md
```

### 2. Understanding the Development Workflow

#### Branch Strategy
```bash
# Create feature branch
git checkout -b feature/your-improvement
git checkout -b fix/bug-description
git checkout -b docs/documentation-update
```

#### Code Style (Enforced)
```bash
# Format code (Black + isort for 88-char lines)
black core/ interfaces/ tests/
isort core/ interfaces/ tests/

# Type checking (strict mode)
mypy core/ --strict

# All three must pass before commit
black --check core/ interfaces/ && \
isort --check-only core/ interfaces/ && \
mypy core/
```

### 3. Example: Add a New CLI Command

Let's add a simple "version" subcommand to an existing CLI module:

```python
# File: interfaces/cli_modules/info_commands.py (create if doesn't exist)

import click
from ..cli import pass_manager

@click.group(name="info")
def info_group():
    """Information and system details"""
    pass

@info_group.command("version")
def version_command():
    """Show detailed version information"""
    click.echo("TODOIT MCP Version 2.12.0")
    click.echo("Python API Version: 1.0")
    click.echo("MCP Tools: 51")
    click.echo("Database Schema Version: 5")

# Register in main CLI (interfaces/cli.py)
# Add: cli.add_command(info_commands.info_group)
```

### 4. Example: Add MCP Tool

```python
# Add to interfaces/mcp_server.py

@server.tool()
async def todo_system_info() -> dict:
    """Get system information and statistics
    
    Returns comprehensive system information including:
    - Database statistics
    - Performance metrics  
    - Configuration details
    """
    try:
        manager = get_manager()
        
        # Get basic stats
        with manager.get_session() as session:
            list_count = session.query(TodoListDB).count()
            item_count = session.query(TodoItemDB).count()
            
        return {
            "success": True,
            "system_info": {
                "version": "2.12.0",
                "database": {
                    "lists": list_count,
                    "items": item_count,
                    "tables": 9
                },
                "mcp_tools": 51
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## 🧪 Testing & Quality (10 minutes)

### Test Categories Understanding

```bash
# 1. Unit Tests - Fast, isolated
pytest tests/unit/ -v
# Focus: Individual functions, mocked dependencies

# 2. Integration Tests - Real database  
pytest tests/integration/ -v
# Focus: Database operations, component interaction

# 3. Edge Cases - Boundary conditions
pytest tests/edge_cases/ -v  
# Focus: Error handling, limits, robustness

# 4. End-to-End - Full workflows
pytest tests/e2e/ -v
# Focus: Complete user scenarios
```

### Writing Your First Test

```python
# File: tests/unit/test_your_feature.py

import pytest
from core.manager import TodoManager

class TestYourFeature:
    def test_basic_functionality(self, temp_db_path):
        """Test basic functionality works as expected"""
        manager = TodoManager(temp_db_path)
        
        # Test your feature
        result = manager.your_new_method()
        
        # Assertions
        assert result is not None
        assert result.success == True
        
    def test_error_handling(self, temp_db_path):
        """Test error conditions are handled properly"""
        manager = TodoManager(temp_db_path)
        
        # Test error case
        with pytest.raises(ValueError, match="Expected error message"):
            manager.your_method_with_invalid_input("bad_input")
```

### Quality Checklist Before Commit

```bash
# 1. Format code
black core/ interfaces/ tests/
isort core/ interfaces/ tests/

# 2. Type checking
mypy core/ --strict

# 3. Run relevant tests
pytest tests/unit/test_your_feature.py -v

# 4. Run related integration tests
pytest tests/integration/ -k "your_feature" -v

# 5. Check test coverage
pytest --cov=core --cov=interfaces tests/your_test_file.py
```

---

## 🎓 Advanced Topics

### Understanding the Smart Algorithm

The core of TODOIT is the intelligent task selection algorithm:

```python
# core/manager.py - get_next_pending_with_subtasks()
# 3-Phase Algorithm:
# Phase 1: In-progress parents with pending subtasks (highest priority)
# Phase 2: Cross-list dependency checking (avoid blocked tasks)  
# Phase 3: Position-based selection with hierarchy awareness
```

### Database Performance Patterns

```python
# Good: Use sessions properly
with self.get_session() as session:
    items = session.query(TodoItemDB).filter(...).all()
    # Session automatically closed

# Good: Use covering indexes
session.query(TodoItemDB).filter(
    TodoItemDB.status == 'pending',
    TodoItemDB.list_id == list_id
).first()  # Uses idx_todo_items_status
```

### MCP Tool Patterns

```python
# Standard MCP tool structure:
@server.tool()
async def todo_action_name(param1: str, param2: Optional[int] = None) -> dict:
    """Clear docstring describing what this tool does
    
    Args:
        param1: Description of required parameter
        param2: Description of optional parameter
        
    Returns:
        Dictionary with success status and data
    """
    try:
        manager = get_manager()
        result = manager.some_operation(param1, param2)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## 🤝 Getting Help

### Internal Resources
1. **CLAUDE.md** - Claude Code specific guidance  
2. **docs/architecture.md** - System design deep dive
3. **docs/api.md** - TodoManager API reference
4. **tests/** - Comprehensive examples of how everything works

### Communication Channels
1. **GitHub Issues** - Bug reports and feature requests
2. **GitHub Discussions** - Questions and general discussion
3. **Code Reviews** - Learning opportunity in PRs

### Common Gotchas for New Developers

1. **Database Sessions**: Always use context managers
2. **Status Synchronization**: Items with subitems can't have manual status changes
3. **Circular Dependencies**: System prevents them, but understand the logic
4. **MCP Tools Levels**: Test with different levels (MINIMAL/STANDARD/MAX)
5. **Natural Sorting**: Numbers sort intuitively (`test_2` before `test_10`)

---

## 🎉 You're Ready!

Congratulations! You now have:

- ✅ **Development environment** set up and tested
- ✅ **Codebase understanding** of key components  
- ✅ **First contribution** ready to make
- ✅ **Testing knowledge** to ensure quality
- ✅ **Advanced concepts** for deeper contributions

### Next Steps

1. **Pick your first issue** from GitHub or TODO.md
2. **Create a feature branch** and start coding
3. **Write tests** for your changes
4. **Submit a pull request** for review
5. **Iterate** based on feedback

**Welcome to the team!** 🚀

---

*For specific technical details, always refer to the comprehensive documentation in the `docs/` directory.*