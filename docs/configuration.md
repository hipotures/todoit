# Configuration

This document lists the available environment variables and command-line options for customizing TODOIT.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TODOIT_DB_PATH` | Path to the SQLite database file. Required if not specified via `--db-path`. Used by both CLI and MCP. | None (required) |
| `TODOIT_FORCE_TAGS` | Comma-separated list of tags for environment isolation. Limits operations to lists with these tags. | None (optional) |
| `TODOIT_OUTPUT_FORMAT` | Controls CLI output format. Supported values: `table`, `vertical`, `json`, `yaml`, `xml`. | `table` |

## CLI Options

Top-level command-line options available for all commands:

| Option | Description | Default |
|--------|-------------|---------|
| `--db-path PATH` | Path to database file used by the CLI. Overrides `TODOIT_DB_PATH`. | None (required) |
| `--version` | Show the application version and exit. | — |
| `--help` | Show help message and exit. | — |

Each subcommand provides additional options; run `todoit <command> --help` for details.