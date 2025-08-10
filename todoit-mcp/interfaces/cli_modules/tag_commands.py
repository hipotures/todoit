"""
Tag management commands for TODOIT CLI
Handles global tag operations (create, list, delete) and tag aliases
"""
import os
import click
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import box

from .display import _display_records, console

def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager
    if db_path == 'todoit.db':
        return TodoManager()
    return TodoManager(db_path)


def _get_force_tags() -> List[str]:
    """Get forced tags from TODOIT_FORCE_TAGS environment variable
    
    FORCE_TAGS creates environment isolation - all operations are limited
    to lists with these tags, and new lists automatically get these tags.
    Used only in CLI, never in MCP tools.
    """
    env_tags = os.environ.get('TODOIT_FORCE_TAGS', '').split(',')
    return [tag.strip().lower() for tag in env_tags if tag.strip()]


def _get_filter_tags(cli_tags: Optional[List[str]] = None) -> List[str]:
    """Get combined filter tags from environment and CLI parameters
    
    Priority order:
    1. TODOIT_FORCE_TAGS (if set) - overrides everything for environment isolation
    2. TODOIT_FILTER_TAGS + CLI --tag parameters - normal filtering mode
    
    Used only in CLI, never in MCP tools.
    """
    # Check for forced tags first (environment isolation)
    force_tags = _get_force_tags()
    if force_tags:
        # In force mode, CLI tags are added to forced tags
        cli_tags = cli_tags or []
        cli_tags = [tag.strip().lower() for tag in cli_tags]
        return list(set(force_tags + cli_tags))
    
    # Normal filtering mode - combine FILTER_TAGS and CLI tags
    env_tags = os.environ.get('TODOIT_FILTER_TAGS', '').split(',')
    env_tags = [tag.strip().lower() for tag in env_tags if tag.strip()]
    
    # Get tags from CLI parameter
    cli_tags = cli_tags or []
    cli_tags = [tag.strip().lower() for tag in cli_tags]
    
    # Return unique union
    return list(set(env_tags + cli_tags))


# ===== TAG MANAGEMENT GROUP =====

@click.group()
def tag():
    """Global tag management"""
    pass


@tag.command("create")
@click.argument('name')
@click.option('--color', default=None, help='Tag color (auto-assigned if not specified)')
@click.pass_context
def create_tag(ctx, name, color):
    """Create a new tag in the system"""
    try:
        manager = get_manager(ctx.obj['db_path'])
        tag = manager.create_tag(name, color)
        
        console.print(f"✅ Tag '{tag.name}' created successfully with color '{tag.color}'")
        
    except ValueError as e:
        console.print(f"❌ Error: {e}")
        raise click.ClickException(str(e))
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        raise click.ClickException(str(e))


@tag.command("list")
@click.pass_context 
def list_tags(ctx):
    """Show all available tags in the system"""
    try:
        manager = get_manager(ctx.obj['db_path'])
        tags = manager.get_all_tags()
        
        if not tags:
            console.print("📭 No tags found in the system")
            return
        
        # Create table for tags
        table = Table(
            title=f"🏷️ Available Tags ({len(tags)})",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Name", style="bold white")
        table.add_column("Color", style="dim")
        table.add_column("Created", style="dim")
        
        for tag in tags:
            # Format date
            created_date = tag.created_at.strftime('%Y-%m-%d %H:%M') if tag.created_at else 'Unknown'
            
            # Add color indicator with Rich color formatting
            color_indicator = f"[{tag.color}]●[/{tag.color}]"
            
            table.add_row(
                tag.name,
                f"{color_indicator} {tag.color}",
                created_date
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing tags: {e}")
        raise click.ClickException(str(e))


@tag.command("delete")
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete_tag(ctx, name, force):
    """Delete a tag from the system (removes all assignments)"""
    try:
        manager = get_manager(ctx.obj['db_path'])
        
        # Check if tag exists
        tag = manager.get_tag(name)
        if not tag:
            console.print(f"❌ Tag '{name}' not found")
            return
        
        # Confirm deletion unless --force is used
        if not force:
            from rich.prompt import Confirm
            if not Confirm.ask(f"❓ Delete tag '{tag.name}'? This will remove it from all lists"):
                console.print("Operation cancelled")
                return
        
        # Delete the tag
        success = manager.delete_tag(name)
        
        if success:
            console.print(f"✅ Tag '{name}' deleted successfully")
        else:
            console.print(f"❌ Failed to delete tag '{name}'")
            
    except Exception as e:
        console.print(f"❌ Error deleting tag: {e}")
        raise click.ClickException(str(e))


# ===== TAGS ALIAS COMMAND =====

@click.command()
@click.pass_context
def tags(ctx):
    """Show all tags (alias for 'tag list')"""
    # Call the same function as 'tag list'
    ctx.invoke(list_tags)