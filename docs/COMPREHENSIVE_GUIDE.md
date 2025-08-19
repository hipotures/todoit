# TODOIT MCP - Comprehensive Documentation Guide

**Version**: 2.12.0  
**Last Updated**: August 19, 2025  
**License**: MIT

---

## 📖 Table of Contents

- [Project Overview](#-project-overview)
- [Quick Start](#-quick-start)
- [Architecture Deep Dive](#-architecture-deep-dive)
- [Feature Matrix](#-feature-matrix)
- [Development Guide](#-development-guide)
- [Production Deployment](#-production-deployment)
- [Documentation Index](#-documentation-index)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

**TODOIT MCP** is an intelligent task management system designed for scalability - from simple personal lists to complex multi-team projects. Built with a focus on intelligent prioritization, hierarchical task breakdown, and seamless Claude Code integration.

### 🔑 Key Value Propositions

1. **Intelligence-First**: Smart algorithms determine what to work on next
2. **Hierarchy Support**: Break complex tasks into manageable subtasks
3. **Cross-List Dependencies**: Coordinate work across teams and projects
4. **Claude Code Integration**: 51 MCP tools for programmatic access
5. **Production Ready**: Comprehensive testing, performance optimization, security

### 🏆 Core Differentiators

- **Smart Next Task Algorithm** with 3-phase prioritization logic
- **Automatic Status Synchronization** for hierarchical tasks
- **Dynamic 12-Color Tag System** with self-healing properties
- **Cross-List Blocking Detection** for dependency management
- **Natural Sorting** for intuitive numeric sequence handling

---

## 🚀 Quick Start

### Installation Options

#### Option A: PyPI Installation (Recommended)
```bash
pip install todoit-mcp
```

#### Option B: Development Installation
```bash
git clone https://github.com/hipotures/todoit.git
cd todoit/todoit-mcp
pip install -e .[dev]
```

### Basic Usage

```bash
# Create your first list
todoit list create --list "my-project" --title "My First Project"

# Add tasks
todoit item add --list "my-project" --item "task1" --title "Setup environment"
todoit item add --list "my-project" --item "task2" --title "Implement feature"

# Check progress
todoit list show --list "my-project"

# Get next task to work on
todoit item next --list "my-project"
```

### Claude Code Integration

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "todoit": {
      "command": "python",
      "args": ["-m", "interfaces.mcp_server"],
      "env": {
        "TODOIT_DB_PATH": "/path/to/your/tasks.db",
        "TODOIT_MCP_TOOLS_LEVEL": "standard"
      }
    }
  }
}
```

---

## 🏗️ Architecture Deep Dive

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │◄──►│   MCP Server     │◄──►│  TodoManager    │
│                 │    │  (51 tools)     │    │  (Core Logic)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌──────────────────┐             │
                       │   Rich CLI       │◄────────────┤
                       │  (Interactive)   │             │
                       └──────────────────┘             │
                                                         ▼
                                               ┌─────────────────┐
                                               │  SQLite DB      │
                                               │  (9 tables)     │
                                               └─────────────────┘
```

### 3-Layer Architecture

#### 1. **Interface Layer** (`interfaces/`)
- **CLI**: Rich terminal interface with interactive modes
- **MCP Server**: 51 tools for Claude Code integration
- **Modular Commands**: Organized in `cli_modules/` for maintainability

#### 2. **Core Logic Layer** (`core/`)
- **TodoManager**: Main business logic coordinator (2861 lines)
- **Database**: SQLAlchemy ORM with comprehensive schema (1618 lines)  
- **Models**: Pydantic validation with 17 model classes (655 lines)
- **Specialized Managers**: Modular components for lists, items, properties, etc.

#### 3. **Data Layer** (SQLite)
- **9 Core Tables**: Lists, items, dependencies, properties, tags, relations
- **ACID Compliance**: Full transaction support with rollback
- **Foreign Key Constraints**: Referential integrity enforcement
- **Performance Optimized**: 12+ strategic indexes

### Smart Algorithms

#### Next Task Selection (3-Phase Algorithm)
1. **Phase 1**: Prioritize in-progress parents with pending subtasks
2. **Phase 2**: Cross-list dependency checking to avoid blocked tasks  
3. **Phase 3**: Position-based selection with hierarchy awareness

#### Status Synchronization Rules
```
Parent Status = f(All Subitem Statuses):
- Any subitem failed → Parent failed
- All subitems pending → Parent pending
- All subitems completed → Parent completed  
- Mixed states → Parent in_progress
```

#### Circular Dependency Prevention
- Graph traversal with visited-set tracking
- Depth limits (max 10 levels) for safety
- Real-time validation on dependency creation

---

## 🎛️ Feature Matrix

### Core Features

| Feature | CLI | MCP | API | Status |
|---------|-----|-----|-----|--------|
| List Management | ✅ | ✅ | ✅ | Production |
| Item CRUD | ✅ | ✅ | ✅ | Production |
| Hierarchical Tasks | ✅ | ✅ | ✅ | Production |
| Cross-List Dependencies | ✅ | ✅ | ✅ | Production |
| Smart Next Task | ✅ | ✅ | ✅ | Production |
| Auto Status Sync | ✅ | ✅ | ✅ | Production |
| Property System | ✅ | ✅ | ✅ | Production |
| Tag Management | ✅ | ✅ | ✅ | Production |

### Advanced Features

| Feature | Description | Interfaces | Version |
|---------|-------------|------------|---------|
| Natural Sorting | Intuitive numeric sorting (test_2 before test_10) | All | v2.11.0+ |
| Dynamic Tag Colors | 12-color system with alphabetical assignment | CLI, MCP | v2.0.0+ |
| Environment Isolation | FORCE_TAGS for dev/test/prod separation | CLI | v1.20.0+ |
| Live Monitoring | Real-time list watching with change detection | CLI | v1.15.0+ |
| Bulk Operations | Quick-add multiple items, batch updates | All | v1.10.0+ |
| Import/Export | Markdown format with checkbox support | All | v1.5.0+ |
| Reports & Analytics | Failed task reports with regex filtering | All | v2.0.0+ |

### MCP Integration Levels

| Level | Tools Count | Use Case | Token Savings |
|-------|-------------|----------|---------------|
| **MINIMAL** | 12 | Essential operations, maximum performance | 82% |
| **STANDARD** | 23 | Balanced functionality (default) | 55% |
| **MAX** | 51 | Complete feature set | 0% |

---

## 🛠️ Development Guide

### Prerequisites

- **Python**: 3.12+
- **Database**: SQLite 3.35+ (with foreign key support)
- **Dependencies**: See `pyproject.toml`

### Development Setup

```bash
# Clone and setup
git clone https://github.com/hipotures/todoit.git
cd todoit/todoit-mcp

# Install in development mode
pip install -e .[dev]

# Initialize database (automatic on first run)
python -c "from core.manager import TodoManager; TodoManager()"

# Verify installation
todoit --help
```

### Testing Framework

```bash
# Run all tests (178+ test cases)
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests  
pytest tests/edge_cases/              # Edge case tests
pytest tests/e2e/                     # End-to-end tests

# Run with coverage
pytest --cov=core --cov=interfaces

# Performance benchmarks
python benchmark_performance.py
```

### Code Quality

```bash
# Format code (Black + isort for 88-char lines)
black core/ interfaces/ tests/
isort core/ interfaces/ tests/

# Type checking
mypy core/ --strict

# Run all quality checks
black --check core/ interfaces/ && isort --check-only core/ interfaces/ && mypy core/
```

### Database Development

```bash
# View schema
sqlite3 todoit.db ".schema"

# Run migrations
python -c "from core.database import DatabaseManager; DatabaseManager().run_migrations()"

# Backup database
cp todoit.db todoit.db.backup
```

---

## 🚀 Production Deployment

### Environment Configuration

```bash
# Required environment variables
export TODOIT_DB_PATH=/var/lib/todoit/production.db
export TODOIT_MCP_TOOLS_LEVEL=standard

# Optional: Environment isolation
export TODOIT_FORCE_TAGS=production

# Optional: Output format
export TODOIT_OUTPUT_FORMAT=json
```

### Security Considerations

- **File Path Validation**: All import/export operations validate paths
- **Input Sanitization**: Comprehensive Pydantic validation
- **Database Security**: Parameterized queries, no SQL injection risk
- **Error Handling**: No sensitive information leaked in error messages

### Performance Optimization

- **Database Indexes**: 12+ strategic indexes for common queries
- **Query Optimization**: Bulk operations, lazy loading, covering indexes
- **Memory Management**: Efficient session handling, connection pooling
- **Token Reduction**: 62-67% data reduction in MCP responses

### Monitoring

```bash
# Health check
todoit list all --format json | jq '.success'

# Performance metrics
python benchmark_performance.py

# Database size
du -h /var/lib/todoit/production.db
```

---

## 📚 Documentation Index

### User Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [CLI_GUIDE.md](CLI_GUIDE.md) | Complete CLI usage guide | End users |
| [MCP_TOOLS.md](MCP_TOOLS.md) | All 51 MCP tools documentation | Claude Code users |
| [installation.md](installation.md) | Installation instructions | All users |
| [configuration.md](configuration.md) | Environment variables and options | System administrators |

### Technical Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [api.md](api.md) | TodoManager API reference | Developers |
| [architecture.md](architecture.md) | System design overview | Architects |
| [database.md](database.md) | Database schema and relationships | Database administrators |
| [TESTS.md](TESTS.md) | Testing strategy and coverage | QA Engineers |

### Development Resources

| Document | Purpose | Audience |
|----------|---------|----------|
| [CLAUDE.md](../CLAUDE.md) | Claude Code integration guide | AI developers |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines | Contributors |
| [SECURITY.md](../SECURITY.md) | Security policies and reporting | Security teams |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and changes | All stakeholders |

### Project Management

| Document | Purpose | Audience |
|----------|---------|----------|
| [ROADMAP.md](ROADMAP.md) | Future development plans | Product managers |
| [TODO.md](TODO.md) | Current development tasks | Development team |
| [REF-20250816.md](REF-20250816.md) | Technical reference snapshot | Developers |

---

## 🔧 Troubleshooting

### Common Issues

#### Database Issues
```bash
# Problem: Database locked
# Solution: Check for running processes
ps aux | grep todoit
kill <pid_if_needed>

# Problem: Corrupted database
# Solution: Restore from backup
cp todoit.db.backup todoit.db
```

#### MCP Integration Issues
```bash
# Problem: MCP tools not available in Claude Code
# Solution: Check configuration
cat ~/.config/claude-desktop/config.json

# Problem: Performance issues with MAX tools level
# Solution: Reduce tools level
export TODOIT_MCP_TOOLS_LEVEL=standard
```

#### CLI Issues
```bash
# Problem: Command not found
# Solution: Verify installation
pip show todoit-mcp
which todoit

# Problem: Permissions error
# Solution: Check database permissions
chmod 664 todoit.db
chown $USER todoit.db
```

### Getting Help

1. **Check existing documentation** in the `docs/` directory
2. **Search closed issues** on GitHub for similar problems
3. **Run diagnostic commands**:
   ```bash
   todoit --version
   python -c "from core.manager import TodoManager; print('Database OK')"
   ```
4. **Create detailed bug reports** with:
   - Version information
   - Environment details
   - Steps to reproduce
   - Expected vs actual behavior

### Performance Tuning

#### Database Optimization
```sql
-- Analyze query performance
EXPLAIN QUERY PLAN SELECT * FROM todo_items WHERE status = 'pending';

-- Rebuild indexes
REINDEX;

-- Vacuum database
VACUUM;
```

#### MCP Performance
```bash
# Use minimal tools level for performance
export TODOIT_MCP_TOOLS_LEVEL=minimal

# Monitor token usage
echo "Token usage reduced by 82% with minimal level"
```

---

## 📊 Project Statistics

- **Total Lines of Code**: ~15,000+ (excluding tests)
- **Test Coverage**: 178+ test cases across 4 categories
- **Documentation**: 20+ comprehensive guides
- **MCP Tools**: 51 tools with 3 configuration levels
- **Database Tables**: 9 tables with full referential integrity
- **CLI Commands**: 50+ commands across 8 categories
- **Supported Formats**: 5 output formats (table, JSON, YAML, XML, vertical)

---

## 🤝 Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines
- [SECURITY.md](../SECURITY.md) for security policies
- [ROADMAP.md](ROADMAP.md) for planned features

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

*This comprehensive guide provides a complete overview of the TODOIT MCP system. For specific implementation details, refer to the individual documentation files listed in the [Documentation Index](#-documentation-index).*