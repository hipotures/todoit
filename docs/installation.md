# Installation Guide

This guide provides comprehensive instructions for installing TODOIT MCP for various use cases.

## Requirements

- **Python 3.12+**
- **SQLite** (which is included with Python)

---

## 1. Standard User Installation (Recommended)

This is the recommended method for most users who want to use the `todoit` CLI or integrate it with Claude Code.

### Option A: Install from PyPI

This is the easiest method, once the package is available on the Python Package Index (PyPI).

```bash
pip install todoit-mcp

# Verify the installation
todoit --help
```

### Option B: Install from GitHub

Install the latest version directly from the GitHub repository.

```bash
pip install git+https://github.com/hipotures/todoit.git

# Verify the installation
todoit --help
```

---

## 2. Developer Setup

This method is for developers who want to contribute to the project or modify the source code.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hipotures/todoit.git
    cd todoit/todoit-mcp
    ```

2.  **Install in editable mode:**
    This command installs the project in a way that your changes to the source code are immediately reflected when you run the `todoit` command.

    ```bash
    # Install with core dependencies
    pip install -e .

    # Or, to include development and testing dependencies
    pip install -e .[dev]
    ```

3.  **Run tests (optional but recommended):**
    ```bash
    pytest
    ```

4.  **Initialize the database:**
    The database is created automatically on the first run. You can also initialize it manually:
    ```bash
    export TODOIT_DB_PATH=/tmp/test.db && python -c "from core.manager import TodoManager; TodoManager()"
    ```

---

## 3. MCP Integration with Claude Code

To use TODOIT's tools within Claude Code, you need to tell Claude Code how to start the MCP server.

### Step 1: Install TODOIT MCP
First, ensure `todoit-mcp` is installed using one of the methods described above.

### Step 2: Locate the Claude Code Configuration Directory

-   **macOS/Linux**: `~/.config/claude-code/`
-   **Windows**: `%APPDATA%\claude-code\`

If this directory doesn't exist, create it:
```bash
# For macOS/Linux
mkdir -p ~/.config/claude-code/
```

### Step 3: Create or Edit the MCP Configuration File

Create or edit the file `mcp.json` inside the configuration directory and add the following server configuration:

```json
{
  "servers": {
    "todoit": {
      "command": "python",
      "args": ["-m", "interfaces.mcp_server"],
      "env": {}
    }
  }
}
```

### Step 4: Restart Claude Code
For the changes to take effect, you must restart Claude Code.

### Step 5: Verify the Integration
Once restarted, you should have access to all `todo_*` tools within Claude Code.

### Advanced MCP Configuration

You can customize the MCP server startup, for example, by specifying a different Python executable or setting environment variables like the database path.

```json
{
  "servers": {
    "todoit": {
      "command": "/path/to/your/virtualenv/bin/python",
      "args": ["-m", "interfaces.mcp_server"],
      "env": {
        "TODOIT_DB_PATH": "/custom/path/to/your_project.db"
      },
      "timeout": 30
    }
  }
}
```

---

## 4. Advanced Installation: Building from Source

This method is for advanced users who want to build the package from source and install it manually.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/hipotures/todoit.git
    cd todoit/todoit-mcp
    ```

2.  **Install build dependencies:**
    ```bash
    pip install build
    ```

3.  **Build the package:**
    This command will create a `dist` directory containing the build artifacts (a `.whl` file and a `.tar.gz` file).
    ```bash
    python -m build
    ```

4.  **Install from the built wheel:**
    Replace the version number with the one that was just built.
    ```bash
    pip install dist/todoit_mcp-*.whl
    ```
