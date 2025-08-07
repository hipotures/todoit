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
from .cli_modules.list_commands import list_group
from .cli_modules.item_commands import item
from .cli_modules.property_commands import list_property_group, item_property_group
from .cli_modules.dependency_commands import dep
from .cli_modules.io_stats_commands import stats, io, schema_info, interactive


console = Console()


def get_manager(db_path: Optional[str]) -> TodoManager:
    """Get TodoManager instance"""
    # Detect if running from source vs installed package
    try:
        import pkg_resources
        pkg_resources.get_distribution('todoit-mcp')
        is_production = True
    except:
        is_production = False
    
    # Development mode: use dev database
    if not is_production:
        dev_db = Path.home() / ".todoit" / "todoit_dev.db"
        return TodoManager(str(dev_db))
    
    # Production mode: use normal database
    if db_path == 'todoit.db':
        return TodoManager()
    return TodoManager(db_path)


# === Main command group ===

@click.group(invoke_without_command=True)
@click.option('--db', default='todoit.db', help='Path to database file (default: ~/.todoit/todoit.db)')
@click.version_option(package_name='todoit-mcp', prog_name='TODOIT')
@click.pass_context
def cli(ctx, db):
    """TODOIT - Intelligent TODO list management system"""
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db
    
    # Always check if in development mode and show warning
    try:
        import pkg_resources
        pkg_resources.get_distribution('todoit-mcp')
        is_production = True
    except:
        is_production = False
    
    if not is_production:
        dev_db = Path.home() / ".todoit" / "todoit_dev.db"
        console.print(f"[yellow]🔧 DEV MODE - Using database: {dev_db}[/yellow]")
    
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
    
    # Show DB location on first use for production
    elif db == 'todoit.db' and is_production:
        default_db = Path.home() / ".todoit" / "todoit.db"
        if not default_db.exists():
            console.print(f"[dim]Using database: {default_db}[/dim]")


# Register command groups from modules
cli.add_command(list_group, name='list')
cli.add_command(item)
cli.add_command(stats)
cli.add_command(io)
cli.add_command(dep)
cli.add_command(schema_info)
cli.add_command(interactive)

# Register property subgroups
list_group.add_command(list_property_group)
item.add_command(item_property_group)


if __name__ == '__main__':
    cli()