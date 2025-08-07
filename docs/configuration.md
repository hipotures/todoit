# Configuration

This document lists the available environment variables and command-line options for customizing TODOIT.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TODOIT_DB_PATH` | Path to the SQLite database file. Overrides the default location used by TODOIT. | `~/.todoit/todoit.db` |
| `TODOIT_OUTPUT_FORMAT` | Controls CLI output format. Supported values: `table`, `vertical`, `json`, `yaml`, `xml`. | `table` |

## CLI Options

Top-level command-line options available for all commands:

| Option | Description | Default |
|--------|-------------|---------|
| `--db PATH` | Path to database file used by the CLI. | `~/.todoit/todoit.db` |
| `--version` | Show the application version and exit. | — |
| `--help` | Show help message and exit. | — |

Each subcommand provides additional options; run `todoit <command> --help` for details.