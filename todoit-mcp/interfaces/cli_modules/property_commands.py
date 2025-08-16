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

    if db_path == "todoit.db":
        return TodoManager()
    return TodoManager(db_path)


# === List property management commands ===


@click.group(name="property")
def list_property_group():
    """List property management"""
    pass


@list_property_group.command("set")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--key", "property_key", required=True, help="Property key")
@click.option("--value", "property_value", required=True, help="Property value")
@click.pass_context
def list_property_set(ctx, list_key, property_key, property_value):
    """Set a property for a list"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        property_obj = manager.set_list_property(list_key, property_key, property_value)
        console.print(
            f"[green]✅ Set property '{property_key}' = '{property_value}' for list '{list_key}'[/]"
        )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command("get")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--key", "property_key", required=True, help="Property key")
@click.pass_context
def list_property_get(ctx, list_key, property_key):
    """Get a property value for a list"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        value = manager.get_list_property(list_key, property_key)
        if value is not None:
            console.print(f"[cyan]{property_key}:[/] {value}")
        else:
            console.print(
                f"[yellow]Property '{property_key}' not found for list '{list_key}'[/]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command("show")
@click.option("--list", "list_key", required=True, help="List key")
@click.pass_context
def list_property_show(ctx, list_key):
    """Show all properties for a list"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        properties = manager.get_list_properties(list_key)
        if properties:
            # Prepare properties data for unified display
            data = [{"Key": k, "Value": v} for k, v in properties.items()]
            columns = {
                "Key": {"style": "cyan", "width": 20},
                "Value": {"style": "white"},
            }

            _display_records(data, f"Properties for list '{list_key}'", columns)
        else:
            # Use unified display for empty message
            _display_records([], f"Properties for list '{list_key}'", {})
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_property_group.command("delete")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--key", "property_key", required=True, help="Property key")
@click.pass_context
def list_property_delete(ctx, list_key, property_key):
    """Delete a property from a list"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        success = manager.delete_list_property(list_key, property_key)
        if success:
            console.print(
                f"[green]✅ Deleted property '{property_key}' from list '{list_key}'[/]"
            )
        else:
            console.print(
                f"[yellow]Property '{property_key}' not found for list '{list_key}'[/]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Item property management commands ===


@click.group(name="property")
def item_property_group():
    """Item property management"""
    pass


@item_property_group.command("set")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (for setting property on subitem)")
@click.option("--key", "property_key", required=True, help="Property key")
@click.option("--value", "property_value", required=True, help="Property value")
@click.pass_context
def item_property_set(ctx, list_key, item_key, subitem_key, property_key, property_value):
    """Set a property for an item or subitem"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        if subitem_key:
            # Setting property on subitem
            property_obj = manager.set_item_property(
                list_key, subitem_key, property_key, property_value, parent_item_key=item_key
            )
            console.print(
                f"[green]✅ Set property '{property_key}' = '{property_value}' for subitem '{subitem_key}' under item '{item_key}' in list '{list_key}'[/]"
            )
        else:
            # Setting property on main item
            property_obj = manager.set_item_property(
                list_key, item_key, property_key, property_value
            )
            console.print(
                f"[green]✅ Set property '{property_key}' = '{property_value}' for item '{item_key}' in list '{list_key}'[/]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command("get")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (for getting property from subitem)")
@click.option("--key", "property_key", required=True, help="Property key")
@click.pass_context
def item_property_get(ctx, list_key, item_key, subitem_key, property_key):
    """Get a property value for an item or subitem"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        if subitem_key:
            # Getting property from subitem
            value = manager.get_item_property(list_key, subitem_key, property_key, parent_item_key=item_key)
            target = f"subitem '{subitem_key}' under item '{item_key}'"
        else:
            # Getting property from main item
            value = manager.get_item_property(list_key, item_key, property_key)
            target = f"item '{item_key}'"
            
        if value is not None:
            console.print(f"[cyan]{property_key}:[/] {value}")
        else:
            console.print(
                f"[yellow]Property '{property_key}' not found for {target} in list '{list_key}'[/]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command("list")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", help="Item key (optional - if not provided, shows all items)")
@click.option("--subitem", "subitem_key", help="Subitem key (for listing properties of specific subitem)")
@click.option(
    "--tree", is_flag=True, help="Display properties in tree format grouped by item"
)
@click.pass_context
def item_property_list(ctx, list_key, item_key, subitem_key, tree):
    """List all properties for an item, subitem, or all items if item_key not provided"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        if subitem_key:
            # Show properties for specific subitem
            if not item_key:
                console.print("[bold red]❌ Error:[/] --item must be specified when using --subitem")
                return
            
            if tree:
                console.print(
                    "[yellow]⚠️  --tree option ignored when showing single subitem properties[/]"
                )

            properties = manager.get_item_properties(list_key, subitem_key, parent_item_key=item_key)
            if properties:
                # Prepare properties data for unified display
                data = [{"Key": k, "Value": v} for k, v in properties.items()]
                columns = {
                    "Key": {"style": "cyan", "width": 20},
                    "Value": {"style": "white"},
                }

                _display_records(
                    data,
                    f"Properties for subitem '{subitem_key}' under item '{item_key}' in list '{list_key}'",
                    columns,
                )
            else:
                # Use unified display for empty message
                _display_records(
                    [], f"Properties for subitem '{subitem_key}' under item '{item_key}' in list '{list_key}'", {}
                )
        elif item_key:
            # Original behavior: show properties for single item
            if tree:
                console.print(
                    "[yellow]⚠️  --tree option ignored when showing single item properties[/]"
                )

            properties = manager.get_item_properties(list_key, item_key)
            if properties:
                # Prepare properties data for unified display
                data = [{"Key": k, "Value": v} for k, v in properties.items()]
                columns = {
                    "Key": {"style": "cyan", "width": 20},
                    "Value": {"style": "white"},
                }

                _display_records(
                    data,
                    f"Properties for item '{item_key}' in list '{list_key}'",
                    columns,
                )
            else:
                # Use unified display for empty message
                _display_records(
                    [], f"Properties for item '{item_key}' in list '{list_key}'", {}
                )
        else:
            # New behavior: show properties for all items in the list
            all_properties = manager.get_all_items_properties(list_key)

            # Check if JSON output is requested - use special grouped format for better usability
            from .display import _get_output_format

            output_format = _get_output_format()

            if output_format == "json":
                # For JSON, group properties by item_key for better API usability
                grouped_data = {}
                for prop in all_properties:
                    item_key = prop["item_key"]
                    if item_key not in grouped_data:
                        grouped_data[item_key] = {}
                    grouped_data[item_key][prop["property_key"]] = prop[
                        "property_value"
                    ]

                # Output JSON directly in the grouped format
                import json

                print(json.dumps(grouped_data, indent=2, ensure_ascii=False))
            elif all_properties:
                if tree:
                    _display_item_properties_tree(all_properties, list_key)
                else:
                    _display_item_properties_table(all_properties, list_key)
            else:
                # Use unified display for empty message
                _display_records([], f"Item Properties for list '{list_key}'", {})
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_property_group.command("delete")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (for deleting property from subitem)")
@click.option("--key", "property_key", required=True, help="Property key")
@click.pass_context
def item_property_delete(ctx, list_key, item_key, subitem_key, property_key):
    """Delete a property from an item or subitem"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        if subitem_key:
            # Deleting property from subitem
            success = manager.delete_item_property(list_key, subitem_key, property_key, parent_item_key=item_key)
            target = f"subitem '{subitem_key}' under item '{item_key}'"
        else:
            # Deleting property from main item
            success = manager.delete_item_property(list_key, item_key, property_key)
            target = f"item '{item_key}'"
            
        if success:
            console.print(
                f"[green]✅ Deleted property '{property_key}' from {target} in list '{list_key}'[/]"
            )
        else:
            console.print(
                f"[yellow]Property '{property_key}' not found for {target} in list '{list_key}'[/]"
            )
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


def _display_item_properties_table(properties_data, list_key):
    """Display item properties in table format using unified display system"""
    # Transform data for unified display
    data = []
    for prop in properties_data:
        # Determine item type based on parent_item_id
        item_type = "📝 Item" if prop.get("parent_item_id") is None else "└─ Subitem"
        
        data.append(
            {
                "Type": item_type,
                "Item Key": prop["item_key"],
                "Property Key": prop["property_key"],
                "Value": prop["property_value"],
            }
        )

    # Define columns for unified display
    columns = {
        "Type": {"style": "blue", "width": 12},
        "Item Key": {"style": "cyan", "width": 18},
        "Property Key": {"style": "magenta", "width": 20},
        "Value": {"style": "white"},
    }

    # Use unified display system
    _display_records(data, f"All Item Properties for list '{list_key}'", columns)


def _display_item_properties_tree(properties_data, list_key):
    """Display item properties in tree format grouped by item hierarchy"""
    from rich.tree import Tree

    tree = Tree(f"📋 All Item Properties for list '{list_key}'")

    # Group properties by item hierarchy
    main_items = {}
    subitems_by_parent = {}
    
    for prop in properties_data:
        item_key = prop["item_key"]
        parent_item_key = prop.get("parent_item_key")
        
        if parent_item_key is None:
            # Main item
            if item_key not in main_items:
                main_items[item_key] = []
            main_items[item_key].append((prop["property_key"], prop["property_value"]))
        else:
            # Subitem - group by parent key
            if parent_item_key not in subitems_by_parent:
                subitems_by_parent[parent_item_key] = {}
            if item_key not in subitems_by_parent[parent_item_key]:
                subitems_by_parent[parent_item_key][item_key] = []
            subitems_by_parent[parent_item_key][item_key].append((prop["property_key"], prop["property_value"]))

    # Build hierarchical tree
    for item_key, properties in main_items.items():
        item_branch = tree.add(f"📝 {item_key}")
        
        # Add properties for main item
        for prop_key, prop_value in properties:
            item_branch.add(f"[cyan]{prop_key}[/]: [white]{prop_value}[/]")
        
        # Add subitems under this main item (if any)
        if item_key in subitems_by_parent:
            for subitem_key, subitem_properties in subitems_by_parent[item_key].items():
                subitem_branch = item_branch.add(f"└─ {subitem_key}")
                for prop_key, prop_value in subitem_properties:
                    subitem_branch.add(f"[cyan]{prop_key}[/]: [white]{prop_value}[/]")
    
    # Add orphaned subitems (subitems whose parents don't have properties)
    orphaned_parents = set(subitems_by_parent.keys()) - set(main_items.keys())
    if orphaned_parents:
        orphans_branch = tree.add("🔗 Items with Subitems (no main item properties)")
        for parent_key in orphaned_parents:
            parent_branch = orphans_branch.add(f"📝 {parent_key}")
            for subitem_key, subitem_properties in subitems_by_parent[parent_key].items():
                subitem_branch = parent_branch.add(f"└─ {subitem_key}")
                for prop_key, prop_value in subitem_properties:
                    subitem_branch.add(f"[cyan]{prop_key}[/]: [white]{prop_value}[/]")

    console.print(tree)
