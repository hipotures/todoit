# TODOIT CLI User Guide

## Overview

TODOIT provides a comprehensive command-line interface with beautiful visualizations, rich tables, and intelligent workflow management.

The CLI is implemented in `interfaces/cli.py` using the `click` library and offers the following core commands:

- `list`: Manage TODO lists.
- `item`: Manage TODO items.
- `stats`: View statistics and reports.
- `io`: Import and export data.
- `property`: Manage list properties.
- `dep`: Manage cross-list dependencies.
- `interactive`: Enter interactive mode.

## Installation & Setup

```bash
# Navigate to project directory
cd todoit-mcp

# Basic usage
python -m interfaces.cli --help

# With custom database
python -m interfaces.cli --db /path/to/custom.db <command>
```

## Command Structure

```
python -m interfaces.cli [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `--db TEXT` - Path to database file (default: ~/.todoit/todoit.db)
- `--help` - Show help and exit

## Command Categories

### 📋 List Management (`list`)

#### Create Lists
```bash
# Basic list creation
python -m interfaces.cli list create "my-project" --title "My Project"

# With initial items
python -m interfaces.cli list create "tasks" --title "Daily Tasks" --items "Task 1" --items "Task 2"

# From folder contents
python -m interfaces.cli list create "docs" --title "Documentation" --from-folder ./docs --filter-ext .md

# With metadata
python -m interfaces.cli list create "project" --title "Project" -m '{"priority": "high", "team": "backend"}'
```

#### List Operations
```bash
# Show all lists
python -m interfaces.cli list all

# Show specific list with beautiful table
python -m interfaces.cli list show "my-project"

# Delete list
python -m interfaces.cli list delete "old-project"
python -m interfaces.cli list delete "old-project" --force  # Skip confirmation
```

#### Live Monitoring
```bash
# Real-time monitoring of list changes
python -m interfaces.cli list live "my-project"

# With faster refresh rate
python -m interfaces.cli list live "my-project" --refresh 1

# Show change history panel
python -m interfaces.cli list live "my-project" --show-history

# Filter by status
python -m interfaces.cli list live "my-project" --filter-status pending
python -m interfaces.cli list live "my-project" --filter-status in_progress

# Disable heartbeat animation (reduces flicker)
python -m interfaces.cli list live "my-project" --no-heartbeat
```

#### Link Lists (1:1 Relationships)
```bash
# Create a linked copy of a list with 1:1 task mapping
python -m interfaces.cli list link "source-list" "target-list"

# Link with custom title for the target list
python -m interfaces.cli list link "api-dev" "api-test" --title "API Testing Tasks"

# Example workflow: Create development and testing lists
python -m interfaces.cli list create "frontend-dev" --title "Frontend Development"
python -m interfaces.cli item add "frontend-dev" "component1" "Build user dashboard"
python -m interfaces.cli item add "frontend-dev" "component2" "Implement authentication"
python -m interfaces.cli list link "frontend-dev" "frontend-test" --title "Frontend Testing"
```

**What the link command does:**
- Creates a new target list (fails if target already exists)
- Copies all tasks from source to target with 1:1 mapping
- Resets all target task statuses to "pending" 
- Copies all list properties from source to target
- Copies all item properties from source to target
- Creates automatic project relationship between lists
- Displays comprehensive statistics of the linking operation

### 📝 Item Management (`item`)

#### Add Items
```bash
# Add item to list
python -m interfaces.cli item add "my-project" "task1" "Implement feature X"

# Add with metadata
python -m interfaces.cli item add "my-project" "task2" "Write tests" -m '{"priority": "high"}'
```

#### Update Status
```bash
# Update item status
python -m interfaces.cli item status "my-project" "task1" --status in_progress
python -m interfaces.cli item status "my-project" "task1" --status completed

# Add completion states
python -m interfaces.cli item status "my-project" "task1" --status completed -s "quality=excellent"
```

#### Edit Item Content
```bash
# Edit item description/content
python -m interfaces.cli item edit "my-project" "task1" "Updated task description"
```

#### Delete Items
```bash
# Delete item with confirmation prompt
python -m interfaces.cli item delete "my-project" "task1"

# Force delete without confirmation
python -m interfaces.cli item delete "my-project" "task1" --force
```

#### Subtask Operations
```bash
# Add subtask
python -m interfaces.cli item add-subtask "my-project" "task1" "subtask1" "Backend implementation"

# Show subtasks
python -m interfaces.cli item subtasks "my-project" "task1"

# Move task to become subtask
python -m interfaces.cli item move-to-subtask "my-project" "task2" "task1"
python -m interfaces.cli item move-to-subtask "my-project" "task2" "task1" --force  # Skip confirmation

# Show hierarchy tree
python -m interfaces.cli item tree "my-project"
python -m interfaces.cli item tree "my-project" "task1"  # Specific item tree
```

#### Smart Task Selection
```bash
# Get next pending task
python -m interfaces.cli item next "my-project"

# Get next with smart subtask logic
python -m interfaces.cli item next-smart "my-project"
```

### 🔗 Dependency Management (`dep`)

#### Add Dependencies
```bash
# Create dependency between tasks from different lists
python -m interfaces.cli dep add "frontend:ui-component" requires "backend:api-endpoint"
python -m interfaces.cli dep add "frontend:ui-component" requires "backend:api-endpoint" --force  # Skip confirmation

# With custom dependency type
python -m interfaces.cli dep add "task1:item1" requires "task2:item2" --type "related"
```

#### Manage Dependencies
```bash
# Show dependencies for item
python -m interfaces.cli dep show "frontend:ui-component"

# Remove dependency
python -m interfaces.cli dep remove "frontend:ui-component" "backend:api-endpoint" 
python -m interfaces.cli dep remove "frontend:ui-component" "backend:api-endpoint" --force  # Skip confirmation

# Show dependency graph
python -m interfaces.cli dep graph "my-project"
```

### 📊 Statistics & Reports (`stats`)

```bash
# Show progress for list
python -m interfaces.cli stats progress "my-project"
```

### 📄 Import/Export (`io`)

#### Export
```bash
# Export to markdown
python -m interfaces.cli io export "my-project" "/path/to/export.md"
```

#### Import
```bash
# Import from markdown (supports both formats)
python -m interfaces.cli io import "/path/to/tasks.md"
python -m interfaces.cli io import "/path/to/tasks.md" --key "imported"

# Supported markdown formats:
# [x] Completed task
# [ ] Pending task  
# - [x] Completed task (NEW: fixed in latest version)
# - [ ] Pending task (NEW: fixed in latest version)
```

### 🔧 Property Management

#### List Properties (`list property`)
```bash
# Set list property
python -m interfaces.cli list property set "my-project" "priority" "high"

# Get list property
python -m interfaces.cli list property get "my-project" "priority"

# List all list properties
python -m interfaces.cli list property list "my-project"

# Delete list property
python -m interfaces.cli list property delete "my-project" "old-property"
```

#### Item Properties (`item property`)
```bash
# Set item property for runtime tracking
python -m interfaces.cli item property set "my-project" "task1" "priority" "high"
python -m interfaces.cli item property set "my-project" "task1" "estimated_hours" "8"
python -m interfaces.cli item property set "my-project" "task1" "assignee" "john_doe"

# Get item property
python -m interfaces.cli item property get "my-project" "task1" "priority"

# List all properties for an item
python -m interfaces.cli item property list "my-project" "task1"

# Delete item property when no longer needed
python -m interfaces.cli item property delete "my-project" "task1" "assignee"
```

**Property Use Cases:**
- **List Properties**: Configuration and metadata (team, project phase, default priority)
- **Item Properties**: Runtime tracking (priority, estimated hours, assignee, progress notes)

### 🎮 Interactive Mode (`interactive`)

```bash
# Enter interactive mode with menu
python -m interfaces.cli interactive
```

## Visual Features

### Rich Table Display
- **Status Icons**: ⏳ Pending, 🔄 In Progress, ✅ Completed, ❌ Failed
- **Progress Bars**: Visual completion indicators
- **Dependency Indicators**: 🚫 for blocked items
- **Hierarchy Visualization**: Tree-style subtask display

### Column Icons
- **⏳** - Pending items (total tasks - completed tasks)
- **✅** - Completed items count
- **📊** - Progress percentage
- **📋** - List type: S (Sequential), P (Parallel), H (Hierarchical)

### List Types
- **S** - Sequential: Tasks must be completed in order
- **P** - Parallel: Tasks can be completed in any order
- **H** - Hierarchical: Tasks have parent-child relationships

### Color Coding
- **Green**: Success messages and completed items
- **Yellow**: Warning messages and in-progress items  
- **Red**: Error messages and failed items
- **Blue**: Information and pending items

### Live Monitoring Display
- **Real-time Updates**: Automatically refreshes list status and changes
- **Change Detection**: Visual indicators when items are modified 🔄
- **Progress Visualization**: Live progress bars and completion statistics
- **Status Filtering**: Focus on specific item statuses (pending, in-progress, etc.)
- **Change History**: Recent modification timestamps and activity log
- **Interactive Layout**: Three-panel view with list info, items table, and history

#### Live Monitoring Features:
- 📋 **List Monitor Panel**: Shows list title, progress bar, and statistics
- 📝 **Items Table**: Real-time item status with color coding
- 📊 **Change History Panel**: Recent activity log (optional with `--show-history`)
- 🔄 **Update Indicators**: Visual highlights when changes are detected
- ⏱️ **Configurable Refresh**: Adjust update frequency with `--refresh` option

## Advanced Workflows

### Complex Project Setup
```bash
# Create related lists
python -m interfaces.cli list create "backend" --title "Backend Development"
python -m interfaces.cli list create "frontend" --title "Frontend Development"  
python -m interfaces.cli list create "testing" --title "QA Testing"

# Add tasks with hierarchies
python -m interfaces.cli item add "backend" "api" "Implement REST API"
python -m interfaces.cli item add-subtask "backend" "api" "auth" "Authentication endpoint"
python -m interfaces.cli item add-subtask "backend" "api" "crud" "CRUD operations"

# Create dependencies
python -m interfaces.cli dep add "frontend:components" requires "backend:api" --force
python -m interfaces.cli dep add "testing:integration" requires "backend:api" --force
python -m interfaces.cli dep add "testing:e2e" requires "frontend:components" --force

# Monitor progress
python -m interfaces.cli item next-smart "backend"  # Get next backend task
python -m interfaces.cli stats progress "backend"   # Check backend progress
python -m interfaces.cli dep graph "project"        # Visualize dependencies
```

### Development-Testing Workflow with List Linking
```bash
# Create development list with tasks
python -m interfaces.cli list create "feature-dev" --title "Feature Development"
python -m interfaces.cli item add "feature-dev" "setup" "Setup development environment"
python -m interfaces.cli item add "feature-dev" "implement" "Implement core functionality"
python -m interfaces.cli item add "feature-dev" "review" "Code review and cleanup"

# Add properties to development list
python -m interfaces.cli list property set "feature-dev" "project_id" "proj-123"
python -m interfaces.cli list property set "feature-dev" "team" "backend"

# Link to create testing list with 1:1 task mapping
python -m interfaces.cli list link "feature-dev" "feature-test" --title "Feature Testing"

# Both lists now have identical tasks and properties, but testing tasks are all pending
# Development list maintains original task statuses
# Automatic project relationship created between the lists
```

### Daily Workflow
```bash
# Morning routine: check what to work on
python -m interfaces.cli item next-smart "my-project"

# Start working on task
python -m interfaces.cli item status "my-project" "current-task" --status in_progress

# Complete task
python -m interfaces.cli item status "my-project" "current-task" --status completed

# Check overall progress
python -m interfaces.cli stats progress "my-project"
```

## Tips & Best Practices

### Efficient Task Management
1. **Use hierarchies** for complex tasks - break them into manageable subtasks
2. **Set up dependencies** between related tasks across different lists  
3. **Use smart next task** to let the system guide your workflow
4. **Regular progress checks** to stay on track

### CLI Productivity
1. **Use --force flags** for automation and scripting
2. **Leverage tab completion** (if available in your shell)
3. **Create aliases** for frequently used commands
4. **Use metadata** to add context and searchability

### Error Prevention
- Always use `--force` flag when scripting to avoid hanging on prompts
- Check dependencies before creating complex setups
- Use `list show` to verify list contents before operations
- Export important lists before major changes

## Troubleshooting

### Common Issues
1. **Command not found**: Make sure you're in the correct directory and using `python -m interfaces.cli`
2. **Database errors**: Check database path and permissions
3. **Interactive prompts hang**: Use `--force` flags for automation
4. **Import fails**: Verify markdown format matches supported patterns

### Getting Help
```bash
# General help
python -m interfaces.cli --help

# Command-specific help  
python -m interfaces.cli list --help
python -m interfaces.cli item add --help
python -m interfaces.cli dep add --help
```

---

*CLI fully tested and production-ready with rich visualizations and comprehensive functionality.*