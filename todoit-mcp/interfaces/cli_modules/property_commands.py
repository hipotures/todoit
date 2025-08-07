"""
Property management commands for TODOIT CLI
Handles list and item property operations
"""
import click
from rich.console import Console

from .display import _display_records, console

def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager
    if db_path == 'todoit.db':
        return TodoManager()
    return TodoManager(db_path)


# === List property management commands ===

@click.group(name='property')
def list_property_group():
    """List property management"""
    pass


@list_property_group.command('set')
@click.argument('list_key')
@click.argument('property_key')
@click.argument('property_value')
@click.pass_context
def list_property_set(ctx, list_key, property_key, property_value):
    """Set a property for a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        property_obj = manager.set_list_property(list_key, property_key, property_value)
        console.print(f"[green]✅ Set property '{property_key}' = '{property_value}' for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command('get')
@click.argument('list_key')
@click.argument('property_key')
@click.pass_context
def list_property_get(ctx, list_key, property_key):
    """Get a property value for a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        value = manager.get_list_property(list_key, property_key)
        if value is not None:
            console.print(f"[cyan]{property_key}:[/] {value}")
        else:
            console.print(f"[yellow]Property '{property_key}' not found for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command('list')
@click.argument('list_key')
@click.pass_context
def list_property_list(ctx, list_key):
    """List all properties for a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        properties = manager.get_list_properties(list_key)
        if properties:
            # Prepare properties data for unified display
            data = [{"Key": k, "Value": v} for k, v in properties.items()]
            columns = {"Key": {"style": "cyan", "width": 20}, "Value": {"style": "white"}}
            
            _display_records(data, f"Properties for list '{list_key}'", columns)
        else:
            console.print(f"[yellow]No properties found for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command('delete')
@click.argument('list_key')
@click.argument('property_key')
@click.pass_context
def list_property_delete(ctx, list_key, property_key):
    """Delete a property from a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        success = manager.delete_list_property(list_key, property_key)
        if success:
            console.print(f"[green]✅ Deleted property '{property_key}' from list '{list_key}'[/]")
        else:
            console.print(f"[yellow]Property '{property_key}' not found for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Item property management commands ===

@click.group(name='property')
def item_property_group():
    """Item property management"""
    pass


@item_property_group.command('set')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('property_key')
@click.argument('property_value')
@click.pass_context
def item_property_set(ctx, list_key, item_key, property_key, property_value):
    """Set a property for an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        property_obj = manager.set_item_property(list_key, item_key, property_key, property_value)
        console.print(f"[green]✅ Set property '{property_key}' = '{property_value}' for item '{item_key}' in list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command('get')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('property_key')
@click.pass_context
def item_property_get(ctx, list_key, item_key, property_key):
    """Get a property value for an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        value = manager.get_item_property(list_key, item_key, property_key)
        if value is not None:
            console.print(f"[cyan]{property_key}:[/] {value}")
        else:
            console.print(f"[yellow]Property '{property_key}' not found for item '{item_key}' in list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command('list')
@click.argument('list_key')
@click.argument('item_key')
@click.pass_context
def item_property_list(ctx, list_key, item_key):
    """List all properties for an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        properties = manager.get_item_properties(list_key, item_key)
        if properties:
            # Prepare properties data for unified display
            data = [{"Key": k, "Value": v} for k, v in properties.items()]
            columns = {"Key": {"style": "cyan", "width": 20}, "Value": {"style": "white"}}
            
            _display_records(data, f"Properties for item '{item_key}' in list '{list_key}'", columns)
        else:
            console.print(f"[yellow]No properties found for item '{item_key}' in list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command('delete')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('property_key')
@click.pass_context
def item_property_delete(ctx, list_key, item_key, property_key):
    """Delete a property from an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        success = manager.delete_item_property(list_key, item_key, property_key)
        if success:
            console.print(f"[green]✅ Deleted property '{property_key}' from item '{item_key}' in list '{list_key}'[/]")
        else:
            console.print(f"[yellow]Property '{property_key}' not found for item '{item_key}' in list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")