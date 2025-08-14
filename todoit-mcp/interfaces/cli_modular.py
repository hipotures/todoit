"""
TODOIT CLI
Command Line Interface with Rich for better presentation
Modular design with separate command modules
"""

import click
from typing import Optional
from pathlib import Path
from rich.console import Console

from core.manager import TodoManager

# Import command modules
from .cli.list_commands import list_group
from .cli.item_commands import item
from .cli.property_commands import list_property_group, item_property_group
from .cli.dependency_commands import dep
from .cli.io_stats_commands import stats, io, schema_info, interactive


console = Console()


def get_manager(db_path: Optional[str]) -> TodoManager:
    """Get TodoManager instance"""
    if db_path == "todoit.db":
        # Use default if user didn't specify custom path
        return TodoManager()
    return TodoManager(db_path)


# === Main command group ===


@click.group()
@click.option(
    "--db",
    default="todoit.db",
    help="Path to database file (default: ~/.todoit/todoit.db)",
)
@click.version_option(package_name="todoit-mcp", prog_name="TODOIT")
@click.pass_context
def cli(ctx, db):
    """TODOIT - Intelligent TODO list management system"""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db

    # Show DB location on first use
    if db == "todoit.db":
        default_db = Path.home() / ".todoit" / "todoit.db"
        if not default_db.exists():
            console.print(f"[dim]Using database: {default_db}[/dim]")


# Register command groups from modules
cli.add_command(list_group, name="list")
cli.add_command(item)
cli.add_command(stats)
cli.add_command(io)
cli.add_command(dep)
cli.add_command(schema_info)
cli.add_command(interactive)

# Register property subgroups
list_group.add_command(list_property_group)
item.add_command(item_property_group)


if __name__ == "__main__":
    cli()
