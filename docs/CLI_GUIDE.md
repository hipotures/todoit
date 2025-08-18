# TODOIT CLI User Guide

## Overview

TODOIT provides a comprehensive command-line interface with beautiful visualizations, rich tables, and intelligent workflow management.

The CLI is implemented in `interfaces/cli.py` using the `click` library and offers the following core commands:

- `list`: Manage TODO lists.
- `item`: Manage TODO items.
- `tag`: Global tag management.
- `tags`: Quick tag overview (alias for `tag list`).
- `stats`: View statistics and reports.
- `io`: Import and export data.
- `property`: Manage list properties.
- `dep`: Manage cross-list dependencies.
- `interactive`: Enter interactive mode.

## Installation & Setup

For detailed installation instructions, please see the [**Comprehensive Installation Guide**](installation.md).

### Basic Usage

```bash
# Get help for all commands
todoit --help

# Use a custom database for a specific command
todoit --db /path/to/custom.db list all
```

## Global CLI Features

### Output Formats

TODOIT supports multiple output formats for most commands, controlled by the `TODOIT_OUTPUT_FORMAT` environment variable. This is useful for scripting and integration with other tools.

**Available Formats:**
- `table` (default) - Richly formatted tables with colors and icons.
- `vertical` - Key-value pairs, useful for easy parsing in scripts.
- `json` - JSON output for modern applications and APIs.
- `yaml` - YAML output, often more human-readable than JSON.
- `xml` - XML format for legacy systems.

**Examples:**

**Default `table` format:**
```bash
todoit list all
```

**JSON output:**
You can set the environment variable for a single command or export it for the session.
```bash
TODOIT_OUTPUT_FORMAT=json todoit list all
```
```json
{
  "title": "📋 All TODO Lists",
  "count": 2,
  "data": [
    {
      "ID": "1",
      "Key": "work_tasks",
      "Title": "Work Tasks",
      "Items": "5",
      "Progress": "60.0%"
    }
  ]
}
```

**Persistent format setting:**
```bash
export TODOIT_OUTPUT_FORMAT=json
todoit list all          # This will output JSON
todoit list show project1  # This will also output JSON
```

## Command Structure

```
todoit [OPTIONS] COMMAND [ARGS]...
```

**Note:** You can also use the module form `todoit` if needed for development.

### Global Options
- `--db-path TEXT` - Path to database file (overrides TODOIT_DB_PATH environment variable)
- `--help` - Show help and exit

## Command Categories

### 📋 List Management (`list`)

#### Create Lists
```bash
# Basic list creation
todoit list create --list "my-project" --title "My Project"

# With initial items
todoit list create --list "tasks" --title "Daily Tasks" --items "Task 1" --items "Task 2"

# From folder contents
todoit list create --list "docs" --title "Documentation" --from-folder ./docs --filter-ext .md

# With metadata
todoit list create --list "project" --title "Project" -m '{"priority": "high", "team": "backend"}'
```

#### List Operations
```bash
# Show all lists
todoit list all

# Show specific list with beautiful table
todoit list show --list "my-project"

# Delete list
todoit list delete --list "old-project"
todoit list delete --list "old-project" --force  # Skip confirmation
```


#### Archive Management
```bash
# Archive completed list (requires all tasks to be completed)
todoit list archive --list "completed-project"

# Force archive list with incomplete tasks
todoit list archive --list "incomplete-project" --force

# Unarchive list (restore to active status)
todoit list unarchive --list "archived-project"

# View archived lists only
todoit list all --archived

# View all lists including archived ones
todoit list all --include-archived

# Example workflow with archive validation
todoit list create --list "sprint-1" --title "Sprint 1" --items "Feature A" "Bug fix" "Testing"
todoit item status --list "sprint-1" --item "item_1" --status completed  # Complete some items
todoit list archive --list "sprint-1"  # Will fail - shows incomplete items count
todoit item status --list "sprint-1" --item "item_2" --status completed  # Complete more
todoit item status --list "sprint-1" --item "item_3" --status completed  # Complete all
todoit list archive --list "sprint-1"  # Now succeeds
```

#### Live Monitoring
```bash
# Real-time monitoring of list changes
todoit list live --list "my-project"

# With faster refresh rate
todoit list live --list "my-project" --refresh 1

# Show change history panel
todoit list live --list "my-project" --show-history

# Filter by status
todoit list live --list "my-project" --filter-status pending
todoit list live --list "my-project" --filter-status in_progress

# Disable heartbeat animation (reduces flicker)
todoit list live --list "my-project" --no-heartbeat
```


### 📝 Item Management (`item`)

#### Add Items
```bash
# Add item to list
todoit item add --list "my-project" --item "feature1" --title "Implement feature X"

# Add with metadata
todoit item add --list "my-project" --item "feature2" --title "Write tests" -m '{"priority": "high"}'
```

#### Update Status
```bash
# Update item status
todoit item status --list "my-project" --item "feature1" --status in_progress
todoit item status --list "my-project" --item "feature1" --status completed

# Add completion states
todoit item status --list "my-project" --item "feature1" --status completed -s "quality=excellent"
```

#### Edit Item Content
```bash
# Edit item title/description
todoit item edit --list "my-project" --item "feature1" --title "Updated feature description"
```

#### Delete Items
```bash
# Delete item with confirmation prompt
todoit item delete --list "my-project" --item "feature1"

# Force delete without confirmation
todoit item delete --list "my-project" --item "feature1" --force
```

#### Subitem Operations
```bash
# Add subitem
todoit item add --list "my-project" --item "feature1" --subitem "step1" --title "Backend implementation"

# Show subitems
todoit item list --list "my-project" --item "feature1"

# Move item to become subitem
todoit item move-to-subitem --list "my-project" --item "feature2" --parent "feature1"
todoit item move-to-subitem --list "my-project" --item "feature2" --parent "feature1" --force  # Skip confirmation

# Show hierarchy tree
todoit item tree --list "my-project"
todoit item tree --list "my-project" --item "feature1"  # Specific item tree
```

#### Smart Item Selection
```bash
# Get next pending item
todoit item next --list "my-project"

# Get next with smart subitem logic
todoit item next-smart --list "my-project"
```

#### Search Items by Properties
```bash
# Find all items with specific property value
todoit item find --list "my-project" --property "priority" --value "high"
# Find items by status property 
todoit item find --list "my-project" --property "status" --value "reviewed"
# Find items by issue ID
todoit item find --list "my-project" --property "issue_id" --value "123"

# Limit search results
todoit item find --list "my-project" --property "priority" --value "high" --limit 5
# Get only first match (equivalent to --limit 1)
todoit item find --list "my-project" --property "assignee" --value "john" --first

# Examples of property-based search
todoit item find --list "backend" --property "component" --value "api" --limit 3
todoit item find --list "frontend" --property "framework" --value "react" --first
```

#### Advanced Subitem Search

Find subitems based on sibling status conditions - useful for workflow automation:

```bash
# Find downloads ready to process (where generation is completed)
todoit item find-subitems --list "images" --conditions '{"generate":"completed","download":"pending"}' --limit 5

# Find test items where design and code are done
todoit item find-subitems --list "features" --conditions '{"design":"completed","code":"completed","tests":"pending"}'

# Complex workflow condition matching
todoit item find-subitems --list "ai-generation" --conditions '{"image_gen":"completed","image_dwn":"pending"}' --limit 1
```

This command finds subitems that match status conditions within their sibling groups. All conditions must be satisfied by the sibling group for subitems to be returned.

**Example Subitem Search Output:**
```
🔍 Found 2 matching subitem(s) in 'images' (limit: 5)
╭───────┬──────────────────┬───────┬────────────────────────────┬────┬─────────╮
│ Parent│ Parent Content   │ Subitem│ Content                   │ S… │ Created │
├───────┼──────────────────┼────────┼───────────────────────────┼────┼─────────┤
│ img1  │ Generate image 1 │ downl… │ Download processed image  │ ⏳ │ 2025-0… │
│ img2  │ Generate image 2 │ downl… │ Download processed image  │ ⏳ │ 2025-0… │
╰───────┴──────────────────┴────────┴───────────────────────────┴────┴─────────╯
Conditions: generate=completed, download=pending
```

**Example Property Search Output:**
```
🔍 Found 2 item(s) with priority='high' in 'my-project'
╭────────────────┬──────────────────────────────┬────────────┬──────────┬─────────────────╮
│ Item Key       │ Content                      │ Status     │ Position │ Created         │
├────────────────┼──────────────────────────────┼────────────┼──────────┼─────────────────┤
│ task1          │ Implement authentication     │ pending    │ 1        │ 2025-08-12 10:30 │
│ task5          │ Database optimization        │ in_progress │ 5        │ 2025-08-12 11:15 │
╰────────────────┴──────────────────────────────┴────────────┴──────────┴─────────────────╯
```

**Search Use Cases:**
- Find all tasks assigned to specific team member: `--property "assignee" --value "john"`
- Filter by custom status: `--property "review_status" --value "approved"`  
- Locate tasks by external reference: `--property "jira_ticket" --value "PROJ-123"`
- Find items by category: `--property "category" --value "bug"`
- Search by difficulty level: `--property "complexity" --value "low"`

### 🏷️ Tag Management (`tag` and `tags`)

#### Global Tag Management
```bash
# Quick overview of all tags (shortcut command)
todoit tags

# Create new tags for organization
todoit tag create --name work --color blue
todoit tag create --name urgent --color red
todoit tag create --name client --color green
todoit tag create --name personal --color yellow

# List all available tags (explicit command)
todoit tag list

# Delete unused tags
todoit tag delete --name old-tag --force  # Skip confirmation
```

#### List Tagging
```bash
# Add tags to lists for categorization
todoit list tag add --list project-alpha --tag work
todoit list tag add --list project-alpha --tag client
todoit list tag add --list hotfix-123 --tag urgent

# Remove tags from lists
todoit list tag remove --list project-alpha --tag urgent

# Show all tags for a specific list
todoit list tag show --list project-alpha
```

#### Tag Filtering
```bash
# Filter lists by tags using CLI options
todoit list all --tag work              # Lists tagged with "work"
todoit list all --tag work --tag urgent # Lists with "work" OR "urgent"

# Use environment variable for automatic filtering
export TODOIT_FILTER_TAGS=work,urgent
todoit list all                         # Automatically filtered by work,urgent

# Combine environment and CLI tags (unique union)
export TODOIT_FILTER_TAGS=work,urgent
todoit list all --tag client           # Shows lists with work, urgent, OR client
```

#### Environment Variable Support
```bash
# Create .env file for persistent filtering
echo "TODOIT_FILTER_TAGS=work,urgent,client" > .env

# The CLI will automatically load .env and apply filters
todoit list all    # Filtered by tags from .env

# Override or extend with --tag option
todoit list all --tag personal  # Shows work,urgent,client,personal
```

### 🔒 Environment Isolation with FORCE_TAGS

For complete environment separation (dev/test/prod), use `TODOIT_FORCE_TAGS` instead of `TODOIT_FILTER_TAGS`:

```bash
# Development environment - everything isolated to 'dev' tag
export TODOIT_FORCE_TAGS=dev

# Create new list - automatically gets 'dev' tag
todoit list create --list my-feature --title "My Feature"  # Auto-tagged with 'dev'

# View lists - only shows lists tagged with 'dev'
todoit list all                             # Only 'dev' tagged lists

# Reports - only include 'dev' environment
todoit reports errors                       # Only errors from 'dev' lists
```

```bash
# Test environment - can see dev+test but not prod
export TODOIT_FORCE_TAGS=dev,test

# Create lists - automatically get both tags
todoit list create --list integration --title "Integration Tests"  # Tagged: dev,test

# View all - shows lists with dev OR test tags
todoit list all                             # Shows dev and test lists
```

#### Environment Variables Comparison

| Variable | Purpose | New Lists | Filtering | Priority |
|----------|---------|-----------|-----------|----------|
| `TODOIT_FILTER_TAGS` | **Filtering only** | No auto-tags | Combines with `--tag` | Low |
| `TODOIT_FORCE_TAGS` | **Environment isolation** | Auto-tagged | Overrides `FILTER_TAGS` | High |

#### Best Practices
```bash
# .env for development
echo "TODOIT_FORCE_TAGS=dev" > .env

# .env.test for testing
echo "TODOIT_FORCE_TAGS=dev,test" > .env.test

# .env.prod for production (if needed)
echo "TODOIT_FORCE_TAGS=prod" > .env.prod

# Load different environments
source .env      # Dev mode
source .env.test # Test mode  
```

#### Use Cases
- **FORCE_TAGS**: Complete environment separation, automatic tagging, dev/test/prod isolation
- **FILTER_TAGS**: Simple filtering, temporary views, additional constraints

**Note**: Environment variables only affect CLI commands. MCP tools use explicit parameters only.

### 🔗 Dependency Management (`dep`)

#### Add Dependencies
```bash
# Create dependency between tasks from different lists
todoit dep add --dependent "frontend:ui-component" --required "backend:api-endpoint"
todoit dep add --dependent "frontend:ui-component" --required "backend:api-endpoint" --force  # Skip confirmation

# With custom dependency type
todoit dep add --dependent "task1:item1" --required "task2:item2" --type "related"
```

#### Manage Dependencies
```bash
# Show dependencies for item
todoit dep show --item "frontend:ui-component"

# Remove dependency
todoit dep remove --dependent "frontend:ui-component" --required "backend:api-endpoint" 
todoit dep remove --dependent "frontend:ui-component" --required "backend:api-endpoint" --force  # Skip confirmation

# Show dependency graph
todoit dep graph --project "my-project"
```

### 📊 Statistics & Reports (`stats`)

```bash
# Show progress for list
todoit stats progress --list "my-project"
```

### 📋 Reports & Analytics (`reports`)

Generate comprehensive reports for project management and troubleshooting.

#### Error Reports
```bash
# Show all failed tasks across active lists
todoit reports errors

# Filter by list name patterns (regex)
todoit reports errors --filter "^\d{4}_.*"     # NNNN_* pattern
todoit reports errors --filter ".*project.*"   # Containing "project"
todoit reports errors --filter "^sprint_.*"    # Starting with "sprint_"

# JSON output for automation and scripting
TODOIT_OUTPUT_FORMAT=json todoit reports errors
TODOIT_OUTPUT_FORMAT=json todoit reports errors --filter "^\d{4}_.*"
```

**Example Output:**
```
📊 Failed Tasks Report (filter: ^\d{4}_.*)
┌──────────────┬──────────┬─────────────────┬─────────────┬─────────────────┐
│ List         │ Item     │ Content         │ Updated     │ Properties      │
├──────────────┼──────────┼─────────────────┼─────────────┼─────────────────┤
│ 0001_proj_a  │ task_001 │ Deploy to prod  │ 2025-08-09  │ retry=3, sev=h  │
│ 0023_sprint  │ bug_fix  │ Fix auth issue  │ 2025-08-08  │ assignee=john   │
└──────────────┴──────────┴─────────────────┴─────────────┴─────────────────┘

Total failed tasks: 2 (from 15 active lists)
Filter applied: ^\d{4}_.*
💡 Some tasks have additional properties - use JSON output for full details
```

**Common Filter Patterns:**
- `^\d{4}_.*` - Lists starting with 4 digits + underscore (e.g., 0001_project, 2023_sprint)
- `^(sprint|release)_.*` - Lists starting with "sprint_" or "release_"  
- `.*project.*` - Lists containing "project" anywhere in the name
- `^0023.*` - Lists starting with "0023"
- `^dev_.*` - Development lists

**JSON Output Structure:**
```json
{
  "title": "📊 Failed Tasks Report",
  "count": 2,
  "data": [
    {
      "List": "0001_project_alpha",
      "Item": "deploy_task",
      "Content": "Deploy to production server",
      "Updated": "2025-08-09 14:30",
      "Properties": "retry_count=3, error_type=timeout"
    }
  ]
}
```

### 📄 Import/Export (`io`)

#### Export
```bash
# Export to markdown
todoit io export --list "my-project" --file "/path/to/export.md"
```

#### Import
```bash
# Import from markdown (supports both formats)
todoit io import --file "/path/to/tasks.md"
todoit io import --file "/path/to/tasks.md" --key "imported"

# Supported markdown formats:
# [x] Completed task
# [ ] Pending task  
# - [x] Completed task (NEW: fixed in latest version)
# - [ ] Pending task (NEW: fixed in latest version)
```

### 🔧 Property Management

#### List Properties (`list property`)

**Note:** All property commands support numeric list IDs as well as list keys (e.g., `126` or `"my-project"`).

```bash
# Set list property
todoit list property set "my-project" "priority" "high"
# Or using numeric ID:
todoit list property set 126 "priority" "high"

# Get list property
todoit list property get "my-project" "priority"

# List all list properties
todoit list property show "my-project"

# Delete list property
todoit list property delete "my-project" "old-property"
```

#### Item Properties (`item property`)

**Note:** All property commands support numeric list IDs as well as list keys (e.g., `--list 126` or `--list "my-project"`).

```bash
# Set item property for runtime tracking
todoit item property set --list "my-project" --item "feature1" --key "priority" --value "high"
# Or using numeric ID:
todoit item property set --list 126 --item "feature1" --key "priority" --value "high"
todoit item property set --list "my-project" --item "feature1" --key "estimated_hours" --value "8"
todoit item property set --list "my-project" --item "feature1" --key "assignee" --value "john_doe"

# Set subitem property (NEW!)
todoit item property set --list "my-project" --item "feature1" --subitem "subtask1" --key "difficulty" --value "medium"

# Get item property
todoit item property get --list "my-project" --item "feature1" --key "priority"

# Get subitem property (NEW!)
todoit item property get --list "my-project" --item "feature1" --subitem "subtask1" --key "difficulty"

# List all properties for a specific item
todoit item property list --list "my-project" --item "feature1"

# List all properties for a specific subitem (NEW!)
todoit item property list --list "my-project" --item "feature1" --subitem "subtask1"

# List ALL properties for ALL items in the list (NEW!)
todoit item property list --list "my-project"

# Display properties in tree format grouped by item (NEW!)
todoit item property list --list "my-project" --tree

# Delete item property when no longer needed
todoit item property delete --list "my-project" --item "feature1" --key "assignee"

# Delete subitem property (NEW!)
todoit item property delete --list "my-project" --item "feature1" --subitem "subtask1" --key "difficulty"
```

**Example Output:**

**Table format (default with hierarchy support):**
```
             All Item Properties for list 'my-project'              
╭──────────────┬────────────┬──────────────────────┬─────────────╮
│ Type         │ Item Key   │ Property Key         │ Value       │
├──────────────┼────────────┼──────────────────────┼─────────────┤
│ 📝 Item      │ feature1   │ assignee             │ john        │
│ 📝 Item      │ feature1   │ priority             │ high        │
│ └─ Subitem   │ backend    │ estimated_hours      │ 8           │
│ └─ Subitem   │ backend    │ difficulty           │ medium      │
│ └─ Subitem   │ frontend   │ framework            │ react       │
│ 📝 Item      │ feature2   │ priority             │ low         │
╰──────────────┴────────────┴──────────────────────┴─────────────╯
```

**Tree format (with --tree and hierarchy):**
```
📋 All Item Properties for list 'my-project'
├── 📝 feature1
│   ├── assignee: john
│   ├── priority: high
│   ├── └─ backend
│   │   ├── estimated_hours: 8
│   │   └── difficulty: medium
│   └── └─ frontend
│       └── framework: react
└── 📝 feature2
    └── priority: low
```

**Property Use Cases:**
- **List Properties**: Configuration and metadata (team, project phase, default priority)
- **Item Properties**: Runtime tracking (priority, estimated hours, assignee, progress notes)

### 🎮 Interactive Mode (`interactive`)

```bash
# Enter interactive mode with menu
todoit interactive
```

## Visual Features

### Rich Table Display
- **Status Icons**: ⏳ Pending, 🔄 In Progress, ✅ Completed, ❌ Failed
- **Progress Bars**: Visual completion indicators
- **Dependency Indicators**: 🚫 for blocked items
- **Hierarchy Visualization**: Tree-style subtask display

### List Types & Table Icons

TODOIT supports several list types, each with a corresponding icon in the `list all` table view.

- **S (Sequential)**: Tasks must be completed in their defined order.

The `list all` command provides a rich, at-a-glance view of all your projects using these icons:

- **`ID`**: The numeric ID of the list.
- **`Key`**: The unique string identifier for the list.
- **`Title`**: The human-readable title of the list.
- **`🏷️`**: Tags associated with the list, displayed as colored dots.
- **`🔀`**: The **List Type** (S, P, H, or L).
- **`📋`**: The number of **pending** tasks.
- **`🔄`**: The number of **in-progress** tasks.
- **`❌`**: The number of **failed** tasks.
- **`✅`**: The number of **completed** tasks.
- **`⏳`**: The overall completion **progress percentage**.
- **`📦`**: The list's **status** (A for Active, Z for Archived). This column only appears when viewing archived lists.

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
todoit list create --list "backend" --title "Backend Development"
todoit list create --list "frontend" --title "Frontend Development"  
todoit list create --list "testing" --title "QA Testing"

# Add items with hierarchies
todoit item add --list "backend" --item "api" --title "Implement REST API"
todoit item add --list "backend" --item "api" --subitem "auth" --title "Authentication endpoint"
todoit item add --list "backend" --item "api" --subitem "crud" --title "CRUD operations"

# Create dependencies
todoit dep add --dependent "frontend:components" --required "backend:api" --force
todoit dep add --dependent "testing:integration" --required "backend:api" --force
todoit dep add --dependent "testing:e2e" --required "frontend:components" --force

# Monitor progress
todoit item next-smart --list "backend"  # Get next backend item
todoit stats progress --list "backend"   # Check backend progress
todoit dep graph --project "project"        # Visualize dependencies
```

### Development-Testing Workflow with List Linking
```bash
# Create development list with tasks
todoit list create --list "feature-dev" --title "Feature Development"
todoit item add --list "feature-dev" --item "setup" --title "Setup development environment"
todoit item add --list "feature-dev" --item "implement" --title "Implement core functionality"
todoit item add --list "feature-dev" --item "review" --title "Code review and cleanup"

# Add properties to development list
todoit list property set "feature-dev" "project_id" "proj-123"
todoit list property set "feature-dev" "team" "backend"

# Link to create testing list with 1:1 task mapping
todoit list link --source "feature-dev" --target "feature-test" --title "Feature Testing"

# Both lists now have identical tasks and properties, but testing tasks are all pending
# Development list maintains original task statuses
# Automatic project relationship created between the lists
```

### Daily Workflow
```bash
# Morning routine: check what to work on
todoit item next-smart --list "my-project"

# Start working on item
todoit item status --list "my-project" --item "current-feature" --status in_progress

# Complete item
todoit item status --list "my-project" --item "current-feature" --status completed

# Check overall progress
todoit stats progress --list "my-project"
```

## Tips & Best Practices

### Efficient Task Management
1. **Use hierarchies** for complex tasks - break them into manageable subtasks
2. **Set up dependencies** between related tasks across different lists  
3. **Use smart next item** to let the system guide your workflow
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
1. **Command not found**: Make sure you're in the correct directory and using `todoit`
2. **Database errors**: Check database path and permissions
3. **Interactive prompts hang**: Use `--force` flags for automation
4. **Import fails**: Verify markdown format matches supported patterns

### Getting Help
```bash
# General help
todoit --help

# Command-specific help  
todoit list --help
todoit item add --help
todoit dep add --help
```

### 🔄 Completion State Management (`item state`)

Manage completion states (flags) that are set alongside task status changes.

#### View Current States
```bash
# Show all completion states for an item
todoit item state list --list "my-project" --item "feature1"
```

#### Clear States
```bash
# Clear all completion states from an item
todoit item state clear --list "my-project" --item "feature1"

# Skip confirmation prompt
todoit item state clear --list "my-project" --item "feature1" --force
```

#### Remove Specific States
```bash
# Remove one or more specific completion states
todoit item state remove --list "my-project" --item "feature1" --state-keys "quality"
todoit item state remove --list "my-project" --item "feature1" --state-keys "quality,tested,reviewed"

# Skip confirmation prompt
todoit item state remove --list "my-project" --item "feature1" --state-keys "unwanted_state" --force
```

**Example Workflow:**
```bash
# Accidentally set wrong state during status update
todoit item status --list "project" --item "feature1" --status completed -s wrong_name=true

# Check what states exist
todoit item state list --list "project" --item "feature1"
# Shows: ❌ wrong_name: false

# Remove the problematic state
todoit item state remove --list "project" --item "feature1" --state-keys "wrong_name"

# Set correct status
todoit item status --list "project" --item "feature1" --status completed -s quality=true
```

**Common Use Cases:**
- Fix accidentally created states with wrong names
- Clean up old/unused completion flags
- Resolve table formatting issues caused by long state names
- Prepare items for archival by clearing temporary states

---

*CLI fully tested and production-ready with rich visualizations and comprehensive functionality.*