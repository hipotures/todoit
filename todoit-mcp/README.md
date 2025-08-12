# TODOIT MCP

This directory contains the source code for the `todoit-mcp` package, the intelligent task management system with MCP integration for Claude Code.

For installation instructions, please see the [main documentation](../docs/installation.md).

## Technical Details

### Requirements
- Python >= 3.12
- See `pyproject.toml` for dependencies.

### Database
The default database location is `~/.todoit/todoit.db`.

### Output Formats
TODOIT CLI supports multiple output formats for better integration and automation:

- **Table** (default): Human-readable table format
- **JSON**: Machine-readable JSON format for automation
- **YAML**: YAML format for configuration management
- **XML**: XML format for enterprise integration

Set the output format using the environment variable:
```bash
export TODOIT_OUTPUT_FORMAT=json    # JSON format
export TODOIT_OUTPUT_FORMAT=yaml    # YAML format  
export TODOIT_OUTPUT_FORMAT=xml     # XML format
export TODOIT_OUTPUT_FORMAT=table   # Table format (default)
```

Commands supporting unified output formats:
- `item next` / `item next-smart` - Get next tasks
- `item tree` - Display item hierarchies
- `stats progress` - Show progress statistics
- `tag list` - List all tags
- `list tag show` - Show list tags
- `item property list` / `list property list` - Show properties
- `dep show` - Display dependencies
- `schema` - Show system schema
- `dep graph` - Visualize dependency graphs
