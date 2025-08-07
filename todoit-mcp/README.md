# TODOIT MCP

Universal TODO list management system with MCP integration for Claude Code.

## Installation

### Local Development
For development and testing in current directory:
```bash
pip install -e .
```

### Production Installation
For installation in other systems/environments:

1. **Build wheel package:**
```bash
python -m build
```

2. **Install from wheel:**
```bash
pip install dist/todoit_mcp-1.4.4-py3-none-any.whl
```

### Usage
After installation, use the CLI:
```bash
todoit --help
```

## Requirements
- Python >= 3.12
- See `pyproject.toml` for dependencies

## Database
Default database location: `~/.todoit/todoit.db`

## Output Formats

TODOIT supports multiple output formats controlled by the `TODOIT_OUTPUT_FORMAT` environment variable:

### Available Formats
- `table` (default) - Rich formatted tables
- `vertical` - Key-value pairs  
- `json` - JSON format
- `yaml` - YAML format
- `xml` - XML format

### Examples

**Default table format:**
```bash
todoit list all
```

**JSON output:**
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

**YAML output:**
```bash
TODOIT_OUTPUT_FORMAT=yaml todoit list show work_tasks
```
```yaml
title: 📋 Work Tasks (ID: 1)
count: 5
data:
  - Key: task_1
    Task: Complete project proposal
    Status: ⏳ Pending
```

**XML output:**
```bash
TODOIT_OUTPUT_FORMAT=xml todoit item list work_tasks
```
```xml
<todoit_output>
  <title>📋 Work Tasks Items</title>
  <count>5</count>
  <data>
    <record>
      <Key>task_1</Key>
      <Task>Complete project proposal</Task>
      <Status>⏳ Pending</Status>
    </record>
  </data>
</todoit_output>
```

**Persistent format setting:**
```bash
export TODOIT_OUTPUT_FORMAT=json
todoit list all  # Will output JSON
todoit list show project1  # Will also output JSON
```

## List Types

TODOIT supports three types of task organization:

- **📋 S** (Sequential) - Tasks must be completed in order, one after another
- **📋 P** (Parallel) - Tasks can be worked on simultaneously  
- **📋 H** (Hierarchical) - Tasks organized in parent-child relationships with subtasks

### Column Icons
- **⏳** - Number of pending items (total - completed)
- **✅** - Number of completed items
- **📊** - Progress percentage
- **📋** - List type (S/P/H)