# TODOIT MCP

This directory contains the source code for the `todoit-mcp` package, the intelligent task management system with MCP integration for Claude Code.

For installation instructions, please see the [main documentation](../docs/installation.md).

## Technical Details

### Requirements
- Python >= 3.12
- See `pyproject.toml` for dependencies.

### Database
Database location must be specified via `--db-path` parameter or `TODOIT_DB_PATH` environment variable.

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

### Subitem Key Flexibility

Starting from version 1.25.3, TODOIT supports **duplicate subitem keys** across different parent tasks. This enables standardized workflows where multiple items can share common subitem patterns:

```bash
# Example: Multiple scenes with identical subitem workflow
todoit item add --list scene_list --item scene_0019 --subitem image_gen --title "Generate image for scene 19"
todoit item add --list scene_list --item scene_0019 --subitem image_dwn --title "Download generated image"

todoit item add --list scene_list --item scene_0020 --subitem image_gen --title "Generate image for scene 20"  # Same key!
todoit item add --list scene_list --item scene_0020 --subitem image_dwn --title "Download generated image"     # Same key!
```

This improvement allows:
- **Standardized Workflows**: Common subitem patterns across different parent tasks
- **Generic MCP Searches**: Use `todo_find_subitems_by_status` with generic keys like `{"image_gen":"completed","image_dwn":"pending"}`
- **Simplified Naming**: No need for unique prefixes like `scene_0019_image_gen`
