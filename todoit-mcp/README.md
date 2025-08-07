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