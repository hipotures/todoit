"""
Item management commands for TODOIT CLI
Handles add, status, edit, delete, list, tree operations with smart item/subitem detection
"""

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .display import (
    _display_records,
    _get_status_display,
    _get_status_icon,
    _get_output_format,
    _render_tree_view,
    console,
)
from .tag_commands import _get_filter_tags


def _get_status_for_output(status_value: str) -> str:
    """Get status display based on output format - raw for JSON/YAML/XML, emoji for table"""
    output_format = _get_output_format()
    if output_format in ["json", "yaml", "xml"]:
        return status_value  # Raw status for structured formats
    else:
        return _get_status_display(status_value)  # Emoji for table/vertical


def _check_list_access(manager, list_key):
    """Check if list is accessible based on FORCE_TAGS (environment isolation)"""
    filter_tags = _get_filter_tags()
    if not filter_tags:
        return True  # No filtering, all lists accessible

    # Get lists with required tags
    try:
        tagged_lists = manager.get_lists_by_tags(filter_tags)
        allowed_list_keys = {l.list_key for l in tagged_lists}
        return list_key in allowed_list_keys
    except Exception:
        return False


def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager

    if db_path == "todoit.db":
        return TodoManager()
    return TodoManager(db_path)


@click.group()
def item():
    """Manage TODO items and subitems"""
    pass


@item.command("add")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if adding subitem)")
@click.option("--title", required=True, help="Item or subitem title/description")
@click.option("--metadata", "-m", help="Metadata JSON")
@click.pass_context
def item_add(ctx, list_key, item_key, subitem_key, title, metadata):
    """Add item or subitem to TODO list

    Examples:
      # Add regular item
      todoit item add --list "project" --item "feature1" --title "Implement login"

      # Add subitem
      todoit item add --list "project" --item "feature1" --subitem "step1" --title "Design UI"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        meta = json.loads(metadata) if metadata else {}

        if subitem_key:
            # Adding a subitem - item_key is the parent
            subitem = manager.add_subitem(
                list_key=list_key,
                parent_key=item_key,
                subitem_key=subitem_key,
                content=title,  # Map title to content field
                metadata=meta,
            )
            console.print(
                f"[green]✅ Added subitem '{subitem_key}' to item '{item_key}' in list '{list_key}'[/]"
            )

            # Show hierarchy for parent
            try:
                hierarchy = manager.get_item_hierarchy(list_key, item_key)
                console.print(f"\n[dim]Current hierarchy:[/]")
                console.print(f"📋 {item_key}: {hierarchy['item']['content']}")
                for subitem_info in hierarchy["subitems"]:
                    st = subitem_info["item"]
                    status_icon = _get_status_icon(st["status"])
                    console.print(
                        f"  └─ {status_icon} {st['item_key']}: {st['content']}"
                    )
            except:
                pass  # Skip hierarchy display if error
        else:
            # Adding a regular item
            item = manager.add_item(
                list_key=list_key,
                item_key=item_key,
                content=title,  # Map title to content field
                metadata=meta,
            )
            console.print(f"[green]✅ Added item '{item_key}' to list '{list_key}'[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("status")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if updating subitem)")
@click.option(
    "--status",
    required=True,
    type=click.Choice(["pending", "in_progress", "completed", "failed"]),
    help="Status: pending, in_progress, completed, failed",
)
@click.option("--state", "-s", multiple=True, help="State in format key=value")
@click.pass_context
def item_status(ctx, list_key, item_key, subitem_key, status, state):
    """Update item or subitem status

    Examples:
      # Update item status
      todoit item status --list "project" --item "feature1" --status completed

      # Update subitem status
      todoit item status --list "project" --item "feature1" --subitem "step1" --status completed
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        states = {}
        for s in state:
            k, v = s.split("=", 1)
            states[k] = v.lower() in ["true", "1", "yes"]

        # Use new simplified syntax - no more target_key/parent_key translation
        if subitem_key:
            target_type = "subitem"
            item = manager.update_item_status(
                list_key=list_key,
                item_key=subitem_key,  # The subitem to update
                parent_item_key=item_key,  # Parent item key
                status=status,
                completion_states=states if states else None,
            )
        else:
            target_type = "item"
            item = manager.update_item_status(
                list_key=list_key,
                item_key=item_key,
                status=status,
                completion_states=states if states else None,
            )

        display_key = subitem_key if subitem_key else item_key
        console.print(
            f"[green]✅ Updated {target_type} '{display_key}' status to {status}[/]"
        )
        if states:
            console.print("States:")
            for k, v in states.items():
                icon = "✅" if v else "❌"
                console.print(f"  {icon} {k}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("edit")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if editing subitem)")
@click.option("--title", required=True, help="New title/description")
@click.pass_context
def item_edit(ctx, list_key, item_key, subitem_key, title):
    """Edit item or subitem title/description

    Examples:
      # Edit item
      todoit item edit --list "project" --item "feature1" --title "Updated feature description"

      # Edit subitem
      todoit item edit --list "project" --item "feature1" --subitem "step1" --title "Updated step"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine target key and parent - if subitem is specified, edit the subitem
        if subitem_key:
            target_key = subitem_key
            target_type = "subitem"
            parent_key = item_key
        else:
            target_key = item_key
            target_type = "item"
            parent_key = None

        # Get current item/subitem
        current_item = manager.get_item(list_key, target_key, parent_key)
        if not current_item:
            console.print(
                f"[red]{target_type.capitalize()} '{target_key}' not found in list '{list_key}'[/]"
            )
            return

        # Show changes
        console.print(f"[yellow]Old title:[/] {current_item.content}")
        console.print(f"[green]New title:[/] {title}")

        # Update the content
        updated_item = manager.update_item_content(
            list_key, target_key, title, parent_key
        )
        console.print(
            f"[green]✅ Title updated for {target_type} '{target_key}' in list '{list_key}'[/]"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("delete")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if deleting subitem)")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def item_delete(ctx, list_key, item_key, subitem_key, force):
    """Delete item or subitem permanently

    Examples:
      # Delete item
      todoit item delete --list "project" --item "feature1" --force

      # Delete subitem
      todoit item delete --list "project" --item "feature1" --subitem "step1" --force
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine target key and parent - if subitem is specified, delete the subitem
        if subitem_key:
            target_key = subitem_key
            target_type = "subitem"
            parent_key = item_key
        else:
            target_key = item_key
            target_type = "item"
            parent_key = None

        # Get item details for confirmation
        item = manager.get_item(list_key, target_key, parent_key)
        if not item:
            console.print(
                f"[red]{target_type.capitalize()} '{target_key}' not found in list '{list_key}'[/]"
            )
            return

        # Show what will be deleted
        console.print(f"[yellow]About to delete {target_type}:[/] {item.content}")
        console.print(f"[yellow]From list:[/] {list_key}")

        # Confirm deletion unless force flag is used
        if not force and not Confirm.ask(
            f"[red]Are you sure you want to delete this {target_type}? This cannot be undone"
        ):
            console.print("[yellow]Deletion cancelled[/]")
            return

        # Delete the item/subitem
        success = manager.delete_item(list_key, target_key, parent_key)
        if success:
            console.print(
                f"[green]✅ {target_type.capitalize()} '{target_key}' deleted from list '{list_key}'[/]"
            )
        else:
            console.print(f"[red]❌ Failed to delete {target_type} '{target_key}'[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("list")
@click.option("--list", "list_key", required=True, help="List key")
@click.option(
    "--item", "item_key", help="Item key (if listing subitems of specific item)"
)
@click.pass_context
def item_list(ctx, list_key, item_key):
    """List items in a list, or subitems of a specific item

    Examples:
      # List all items in a list
      todoit item list --list "project"

      # List subitems of specific item
      todoit item list --list "project" --item "feature1"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        if item_key:
            # List subitems of specific item
            subitems = manager.get_subitems(list_key, item_key)

            if not subitems:
                console.print(
                    f"[yellow]No subitems found for item '{item_key}' in list '{list_key}'[/]"
                )
                return

            # Show parent info
            parent = manager.get_item(list_key, item_key)
            console.print(f"📋 Parent: {parent.item_key} - {parent.content}")
            console.print()

            # Prepare subitems data for unified display
            data = []
            for subitem in subitems:
                status_display = _get_status_for_output(subitem.status.value)

                states_str = ""
                if subitem.completion_states:
                    states = []
                    for k, v in subitem.completion_states.items():
                        if isinstance(v, bool):
                            icon = "✅" if v else "❌"
                            states.append(f"{icon}{k}")
                        else:
                            states.append(f"📝{k}")
                    states_str = " ".join(states)

                record = {
                    "Key": subitem.item_key,
                    "Title": subitem.content,
                    "Status": status_display,
                    "States": states_str,
                }
                data.append(record)

            # Define column styling
            columns = {
                "Key": {"style": "magenta"},
                "Title": {"style": "white"},
                "Status": {"style": "yellow"},
                "States": {"style": "blue"},
            }

            # Use unified display system
            _display_records(data, f"Subitems for '{item_key}'", columns)

            # Show completion info only for visual formats (not JSON/YAML/XML)
            output_format = _get_output_format()
            if output_format not in ["json", "yaml", "xml"]:
                completed = sum(1 for st in subitems if st.status.value == "completed")
                total = len(subitems)
                percentage = (completed / total * 100) if total > 0 else 0
                console.print(
                    f"\n[bold]Progress:[/] {percentage:.1f}% ({completed}/{total} completed)"
                )
        else:
            # List all items in the list
            items = manager.get_list_items(list_key)
            if not items:
                _display_records([], f"Items in list '{list_key}'", {})
                return

            # Prepare items data for unified display
            data = []
            for item in items:
                data.append(
                    {
                        "Position": str(item.position),
                        "Key": item.item_key,
                        "Title": item.content,
                        "Status": _get_status_for_output(item.status.value),
                    }
                )

            columns = {
                "Position": {"style": "dim", "width": 8},
                "Key": {"style": "cyan"},
                "Title": {"style": "white"},
                "Status": {"style": "yellow"},
            }

            _display_records(data, f"Items in list '{list_key}'", columns)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("next")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--start", is_flag=True, help="Start the item")
@click.pass_context
def item_next(ctx, list_key, start):
    """Get next pending item

    Example:
      todoit item next --list "project" --start
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        item = manager.get_next_pending(list_key)
        if not item:
            # Use unified display for empty case
            _display_records([], f"Next Item for list '{list_key}'", {})
            return

        # Prepare data for unified display
        data = [
            {
                "Item": item.content,
                "Key": item.item_key,
                "Position": str(item.position),
                "Status": _get_status_for_output(item.status.value),
            }
        ]

        columns = {
            "Item": {"style": "cyan"},
            "Key": {"style": "magenta"},
            "Position": {"style": "yellow"},
            "Status": {"style": "green"},
        }

        _display_records(data, f"⏭️ Next Item for list '{list_key}'", columns)

        if start and Confirm.ask("Start this item?"):
            manager.update_item_status(list_key, item.item_key, status="in_progress")
            console.print("[green]✅ Item started[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("next-smart")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--start", is_flag=True, help="Start the item")
@click.pass_context
def item_next_smart(ctx, list_key, start):
    """Get next pending item with smart subitem logic

    Example:
      todoit item next-smart --list "project" --start
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        item = manager.get_next_pending(list_key, smart_subtasks=True)
        if not item:
            # Use unified display for empty case
            _display_records([], f"Next Smart Item for list '{list_key}'", {})
            return

        # Check if this is a subitem
        is_subitem = getattr(item, "parent_item_id", None) is not None
        item_type = "Subitem" if is_subitem else "Item"

        # Prepare data for unified display
        data = [
            {
                "Type": item_type,
                "Item": item.content,
                "Key": item.item_key,
                "Position": str(item.position),
                "Status": _get_status_for_output(item.status.value),
            }
        ]

        columns = {
            "Type": {"style": "yellow"},
            "Item": {"style": "cyan"},
            "Key": {"style": "magenta"},
            "Position": {"style": "blue"},
            "Status": {"style": "green"},
        }

        _display_records(data, f"⏭️ Next Smart Item for list '{list_key}'", columns)

        if start and Confirm.ask("Start this item?"):
            manager.update_item_status(list_key, item.item_key, status="in_progress")
            console.print("[green]✅ Item started[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("tree")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", help="Item key (show hierarchy for specific item)")
@click.pass_context
def item_tree(ctx, list_key, item_key):
    """Show hierarchy tree for item or entire list

    Examples:
      # Show tree for entire list
      todoit item tree --list "project"

      # Show tree for specific item
      todoit item tree --list "project" --item "feature1"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        if item_key:
            # Show hierarchy for specific item
            hierarchy = manager.get_item_hierarchy(list_key, item_key)

            def flatten_hierarchy(item_info, depth=0, data_list=None):
                if data_list is None:
                    data_list = []

                item = item_info["item"]
                status_icon = _get_status_icon(item["status"])

                # Create indentation for hierarchy visualization
                indent = "  " * depth
                if depth == 0:
                    hierarchy_display = f"📋 {item['item_key']}: {item['content']}"
                else:
                    hierarchy_display = f"{indent}└─ {status_icon} {item['item_key']}: {item['content']}"

                data_list.append(
                    {
                        "Level": str(depth),
                        "Item": item["item_key"],
                        "Content": item["content"],
                        "Status": status_icon,
                        "Hierarchy": hierarchy_display,
                    }
                )

                for subitem_info in item_info.get("subitems", []):
                    flatten_hierarchy(subitem_info, depth + 1, data_list)

                return data_list

            data = flatten_hierarchy(hierarchy)
            columns = {
                "Level": {"style": "dim", "width": 5},
                "Item": {"style": "cyan"},
                "Content": {"style": "white"},
                "Status": {"style": "yellow"},
                "Hierarchy": {"style": "white"},
            }

            _display_records(
                data, f"📋 Item Tree for '{item_key}' in '{list_key}'", columns
            )
        else:
            # Show entire list in tree view
            todo_list = manager.get_list(list_key)
            if not todo_list:
                console.print(f"[red]List '{list_key}' not found[/]")
                return

            items = manager.get_list_items(list_key)
            if not items:
                _display_records([], f"📋 Tree View for '{list_key}'", {})
                return

            # Convert items to hierarchical flat structure for unified display
            data = []
            for item in items:
                # Calculate indentation based on parent relationship
                depth = 0
                if hasattr(item, "parent_item_id") and item.parent_item_id:
                    depth = 1  # Simplified depth calculation

                indent = "  " * depth
                status_icon = _get_status_icon(item.status.value)

                if depth == 0:
                    hierarchy_display = f"{status_icon} {item.content}"
                else:
                    hierarchy_display = f"{indent}└─ {status_icon} {item.content}"

                data.append(
                    {
                        "Position": str(item.position),
                        "Key": item.item_key,
                        "Status": status_icon,
                        "Item": hierarchy_display,
                    }
                )

            columns = {
                "Position": {"style": "dim", "width": 8},
                "Key": {"style": "cyan"},
                "Status": {"style": "yellow", "width": 6},
                "Item": {"style": "white"},
            }

            _display_records(
                data, f"📋 Tree View for '{todo_list.title}' ({list_key})", columns
            )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("move-to-subitem")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key to move")
@click.option("--parent", "new_parent_key", required=True, help="New parent item key")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def item_move_to_subitem(ctx, list_key, item_key, new_parent_key, force):
    """Convert existing item to be a subitem of another item

    Example:
      todoit item move-to-subitem --list "project" --item "feature2" --parent "feature1" --force
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Show current state
        item = manager.get_item(list_key, item_key)
        parent = manager.get_item(list_key, new_parent_key)

        if not item or not parent:
            console.print("[red]Item or parent not found[/]")
            return

        console.print(f"[yellow]Moving '{item.item_key}: {item.content}'[/]")
        console.print(
            f"[yellow]To be subitem of '{parent.item_key}: {parent.content}'[/]"
        )

        if not force and not Confirm.ask("Proceed with move?"):
            return

        moved_item = manager.move_to_subitem(list_key, item_key, new_parent_key)
        console.print(
            f"[green]✅ Moved '{item_key}' to be subitem of '{new_parent_key}'[/]"
        )

        # Show updated hierarchy
        try:
            hierarchy = manager.get_item_hierarchy(list_key, new_parent_key)
            console.print(f"\n[dim]Updated hierarchy:[/]")
            console.print(f"📋 {new_parent_key}: {hierarchy['item']['content']}")
            for subitem_info in hierarchy.get("subitems", []):
                st = subitem_info["item"]
                status_icon = _get_status_icon(st["status"])
                console.print(f"  └─ {status_icon} {st['item_key']}: {st['content']}")
        except:
            pass

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("find")
@click.option(
    "--list",
    "list_key",
    required=False,
    help="List key (optional, if not provided searches all lists)",
)
@click.option(
    "--property", "property_key", required=True, help="Property name to search for"
)
@click.option(
    "--value", "property_value", required=True, help="Property value to match"
)
@click.option("--limit", type=int, help="Maximum number of results (default: all)")
@click.option("--first", is_flag=True, help="Return only first result (limit=1)")
@click.pass_context
def item_find(ctx, list_key, property_key, property_value, limit, first):
    """Find items by property value

    Examples:
      todoit item find --list "mylist" --property "status" --value "reviewed"
      todoit item find --list "mylist" --property "issue_id" --value "123" --first
      todoit item find --list "mylist" --property "priority" --value "high" --limit 5
      todoit item find --property "priority" --value "high"  # Search all lists
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if list_key and not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine actual limit
        actual_limit = None
        if first:
            actual_limit = 1
        elif limit:
            actual_limit = limit

        # Search for items
        items = manager.find_items_by_property(
            list_key, property_key, property_value, actual_limit
        )

        if not items:
            # Use unified display for empty result
            search_scope = list_key if list_key else "all lists"
            _display_records(
                [],
                f"🔍 Search Results for {property_key}='{property_value}' in '{search_scope}'",
                {},
            )
            return

        # Prepare data for unified display
        data = []
        for item in items:
            # Add hierarchy context when searching across multiple lists
            item_data = {
                "Item Key": item.item_key,
                "Content": item.content,
                "Status": _get_status_for_output(item.status.value),
                "Position": str(item.position),
                "Created": (
                    item.created_at.strftime("%Y-%m-%d %H:%M")
                    if item.created_at
                    else "N/A"
                ),
            }
            
            # Add List column when searching all lists (not specific list)
            if list_key is None and hasattr(item, 'list_key') and item.list_key:
                item_data["List"] = item.list_key
            
            # Add Parent column for subitems
            if hasattr(item, 'parent_item_key') and item.parent_item_key:
                item_data["Parent"] = item.parent_item_key
            
            data.append(item_data)

        # Define column styling - dynamically based on available columns
        columns = {
            "Item Key": {"style": "cyan", "width": 15},
            "Content": {"style": "white"},
            "Status": {"style": "yellow", "width": 12},
            "Position": {"style": "blue", "width": 8},
            "Created": {"style": "dim", "width": 16},
        }
        
        # Add styling for new columns if they exist in data
        if data and "List" in data[0]:
            columns["List"] = {"style": "magenta", "width": 20}
        if data and "Parent" in data[0]:
            columns["Parent"] = {"style": "green", "width": 15}

        # Create title with search info
        search_scope = list_key if list_key else "all lists"
        title = f"🔍 Found {len(items)} item(s) with {property_key}='{property_value}' in '{search_scope}'"
        if actual_limit:
            title += f" (limit: {actual_limit})"

        # Use unified display system
        _display_records(data, title, columns)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("find-subitems")
@click.option("--list", "list_key", required=True, help="List key")
@click.option(
    "--conditions",
    required=True,
    help="JSON dictionary of {subitem_key: expected_status} conditions",
)
@click.option("--limit", type=int, default=10, help="Maximum number of results")
@click.pass_context
def item_find_subitems(ctx, list_key, conditions, limit):
    """Find subitems based on sibling status conditions

    This command finds subitems that match status conditions within their
    sibling groups. All conditions must be satisfied by the sibling group
    for subitems to be returned.

    Examples:
      # Find downloads ready to process (where generation is completed)
      todoit item find-subitems --list "images" --conditions '{"generate":"completed","download":"pending"}' --limit 5

      # Find test items where design and code are done
      todoit item find-subitems --list "features" --conditions '{"design":"completed","code":"completed","tests":"pending"}'
    """
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Parse JSON conditions
        try:
            conditions_dict = json.loads(conditions)
        except json.JSONDecodeError as e:
            console.print(f"[bold red]❌ Invalid JSON in conditions:[/] {e}")
            return

        if not isinstance(conditions_dict, dict):
            console.print("[bold red]❌ Conditions must be a JSON dictionary[/]")
            return

        if not conditions_dict:
            console.print("[bold red]❌ Conditions dictionary cannot be empty[/]")
            return

        # Find subitems
        matches = manager.find_items_by_status(conditions_dict, list_key, limit)

        if not matches:
            # Use unified display for empty result
            _display_records(
                [],
                f"🔍 Subitem Search Results in '{list_key}'",
                {},
            )
            console.print(
                f"[dim]No subitems found matching conditions: {conditions_dict}[/]"
            )
            return

        # Prepare data for unified display - flatten results
        data = []
        for match in matches:
            parent = match["parent"]
            matching_subitems = match["matching_subitems"]

            for subitem in matching_subitems:
                # Handle both object and dict formats for compatibility
                parent_key = (
                    parent.item_key
                    if hasattr(parent, "item_key")
                    else parent["item_key"]
                )
                parent_content = (
                    parent.content if hasattr(parent, "content") else parent["content"]
                )
                subitem_key = (
                    subitem.item_key
                    if hasattr(subitem, "item_key")
                    else subitem["item_key"]
                )
                subitem_content = (
                    subitem.content
                    if hasattr(subitem, "content")
                    else subitem["content"]
                )
                subitem_status = (
                    subitem.status.value
                    if hasattr(subitem, "status") and hasattr(subitem.status, "value")
                    else subitem["status"]
                )
                subitem_created = (
                    subitem.created_at
                    if hasattr(subitem, "created_at")
                    else subitem.get("created_at")
                )

                data.append(
                    {
                        "Parent": parent_key,
                        "Parent Content": (
                            parent_content[:30] + "..."
                            if len(parent_content) > 30
                            else parent_content
                        ),
                        "Subitem": subitem_key,
                        "Content": (
                            subitem_content[:40] + "..."
                            if len(subitem_content) > 40
                            else subitem_content
                        ),
                        "Status": _get_status_for_output(subitem_status),
                        "Created": (
                            subitem_created.strftime("%Y-%m-%d %H:%M")
                            if subitem_created and hasattr(subitem_created, "strftime")
                            else (
                                subitem_created
                                if isinstance(subitem_created, str)
                                else "N/A"
                            )
                        ),
                    }
                )

        # Define column styling
        columns = {
            "Parent": {"style": "cyan", "width": 15},
            "Parent Content": {"style": "dim", "width": 25},
            "Subitem": {"style": "yellow", "width": 15},
            "Content": {"style": "white", "width": 35},
            "Status": {"style": "green", "width": 12},
            "Created": {"style": "dim", "width": 16},
        }

        # Create title with search info
        title = f"🔍 Found {len(data)} matching subitem(s) in '{list_key}'"
        if limit and len(matches) >= limit:
            title += f" (limit: {limit})"

        # Use unified display system
        _display_records(data, title, columns)

        # Show search conditions
        conditions_str = ", ".join([f"{k}={v}" for k, v in conditions_dict.items()])
        console.print(f"[dim]Conditions: {conditions_str}[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.group("state")
def item_state():
    """Manage completion states for TODO items"""
    pass


@item_state.command("list")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if checking subitem)")
@click.pass_context
def state_list(ctx, list_key, item_key, subitem_key):
    """Show all completion states for an item or subitem

    Examples:
      # Show states for item
      todoit item state list --list "project" --item "feature1"

      # Show states for subitem
      todoit item state list --list "project" --item "feature1" --subitem "step1"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine target key and parent - if subitem is specified, check the subitem
        if subitem_key:
            target_key = subitem_key
            target_type = "subitem"
            parent_key = item_key
        else:
            target_key = item_key
            target_type = "item"
            parent_key = None

        item = manager.get_item(list_key, target_key, parent_key)
        if not item:
            console.print(
                f"[red]{target_type.capitalize()} '{target_key}' not found in list '{list_key}'[/]"
            )
            return

        console.print(f"[bold]Completion states for {target_type} '{target_key}':[/]")

        if not item.completion_states:
            console.print("[dim]No completion states set[/]")
            return

        for key, value in item.completion_states.items():
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}: {value}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_state.command("clear")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if clearing subitem)")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def state_clear(ctx, list_key, item_key, subitem_key, force):
    """Clear all completion states from an item or subitem

    Examples:
      # Clear states for item
      todoit item state clear --list "project" --item "feature1" --force

      # Clear states for subitem
      todoit item state clear --list "project" --item "feature1" --subitem "step1" --force
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine target key and parent - if subitem is specified, clear the subitem
        if subitem_key:
            target_key = subitem_key
            target_type = "subitem"
            parent_key = item_key
        else:
            target_key = item_key
            target_type = "item"
            parent_key = None

        item = manager.get_item(list_key, target_key, parent_key)
        if not item:
            console.print(
                f"[red]{target_type.capitalize()} '{target_key}' not found in list '{list_key}'[/]"
            )
            return

        if not item.completion_states:
            console.print("[dim]No completion states to clear[/]")
            return

        # Show current states
        console.print(f"[yellow]Current states for {target_type} '{target_key}':[/]")
        for key, value in item.completion_states.items():
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}")

        if not force and not Confirm.ask("Clear all completion states?"):
            return

        # Clear all states
        updated_item = manager.clear_item_completion_states(
            list_key, target_key, parent_item_key=parent_key
        )
        console.print(
            f"[green]✅ Cleared all completion states from {target_type} '{target_key}'[/]"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_state.command("remove")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Item key")
@click.option("--subitem", "subitem_key", help="Subitem key (if removing from subitem)")
@click.option(
    "--state-keys", required=True, help="Comma-separated state keys to remove"
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def state_remove(ctx, list_key, item_key, subitem_key, state_keys, force):
    """Remove specific completion states from an item or subitem

    Examples:
      # Remove states from item
      todoit item state remove --list "project" --item "feature1" --state-keys "quality,tested" --force

      # Remove states from subitem
      todoit item state remove --list "project" --item "feature1" --subitem "step1" --state-keys "reviewed" --force
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Parse state keys
        state_key_list = [key.strip() for key in state_keys.split(",")]

        # Determine target key and parent - if subitem is specified, remove from the subitem
        if subitem_key:
            target_key = subitem_key
            target_type = "subitem"
            parent_key = item_key
        else:
            target_key = item_key
            target_type = "item"
            parent_key = None

        item = manager.get_item(list_key, target_key, parent_key)
        if not item:
            console.print(
                f"[red]{target_type.capitalize()} '{target_key}' not found in list '{list_key}'[/]"
            )
            return

        if not item.completion_states:
            console.print("[dim]No completion states to remove[/]")
            return

        # Check which keys exist
        existing_keys = []
        missing_keys = []
        for key in state_key_list:
            if key in item.completion_states:
                existing_keys.append(key)
            else:
                missing_keys.append(key)

        if missing_keys:
            console.print(
                f"[yellow]Warning: Keys not found: {', '.join(missing_keys)}[/]"
            )

        if not existing_keys:
            console.print("[red]No valid state keys found to remove[/]")
            return

        # Show states to be removed
        console.print(f"[yellow]Removing states from {target_type} '{target_key}':[/]")
        for key in existing_keys:
            value = item.completion_states[key]
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}")

        if not force and not Confirm.ask(f"Remove {len(existing_keys)} state(s)?"):
            return

        # Remove specific states
        updated_item = manager.clear_item_completion_states(
            list_key, target_key, parent_item_key=parent_key, state_keys=existing_keys
        )
        console.print(
            f"[green]✅ Removed {len(existing_keys)} completion state(s) from {target_type} '{target_key}'[/]"
        )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("rename")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--item", "item_key", required=True, help="Current item key")
@click.option("--new-key", help="New item key (optional)")
@click.option("--new-title", help="New item title/content (optional)")
@click.option(
    "--parent", "parent_item_key", help="Parent item key (if renaming subitem)"
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def item_rename(ctx, list_key, item_key, new_key, new_title, parent_item_key, force):
    """Rename an item's key and/or title

    At least one of --new-key or --new-title must be provided.

    Examples:
      # Change item key only
      todoit item rename --list "project" --item "task1" --new-key "feature1"

      # Change item title only
      todoit item rename --list "project" --item "task1" --new-title "Implement user authentication"

      # Change both key and title
      todoit item rename --list "project" --item "task1" --new-key "auth" --new-title "User Authentication Feature"

      # Rename a subitem
      todoit item rename --list "project" --item "subtask1" --parent "maintask" --new-key "test_auth" --new-title "Test authentication system"
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    # Validate inputs
    if not new_key and not new_title:
        console.print(
            "[red]At least one of --new-key or --new-title must be provided[/]"
        )
        return

    try:
        # Get current item to show what will be changed
        current_item = manager.get_item(list_key, item_key, parent_item_key)
        if not current_item:
            item_type = "subitem" if parent_item_key else "item"
            console.print(
                f"[red]{item_type.capitalize()} '{item_key}' not found in list '{list_key}'[/]"
            )
            return

        # Show current state and planned changes
        item_type = "subitem" if parent_item_key else "item"
        console.print(f"[yellow]Current {item_type}:[/]")
        console.print(f"  Key: {current_item.item_key}")
        console.print(f"  Title: {current_item.content}")
        if parent_item_key:
            console.print(f"  Parent: {parent_item_key}")

        console.print(f"\n[yellow]Planned changes:[/]")
        if new_key:
            console.print(f"  Key: {current_item.item_key} → {new_key}")
        if new_title:
            console.print(f"  Title: {current_item.content} → {new_title}")

        if not force and not Confirm.ask("Proceed with rename?"):
            return

        # Perform the rename
        updated_item = manager.rename_item(
            list_key=list_key,
            item_key=item_key,
            new_key=new_key,
            new_content=new_title,  # Map new_title to new_content for internal API
            parent_item_key=parent_item_key,
        )

        console.print(f"[green]✅ Successfully renamed {item_type}[/]")

        # Show final state
        console.print(f"\n[green]Updated {item_type}:[/]")
        console.print(f"  Key: {updated_item.item_key}")
        console.print(f"  Title: {updated_item.content}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command("find-status")
@click.option(
    "--status",
    "statuses",
    multiple=True,
    required=True,
    help="Status to search for (can be specified multiple times for OR logic)",
)
@click.option(
    "--list", "list_key", help="List key to limit search scope (optional, default: all lists)"
)
@click.option("--limit", type=int, default=20, help="Maximum number of results")
@click.option(
    "--complex",
    "complex_conditions",
    help="JSON string with complex conditions: {'item': {'status': 'pending'}, 'subitem': {'download': 'pending'}}",
)
@click.option("--no-subitems", is_flag=True, help="Exclude subitems from results")
@click.option("--group-by-list", is_flag=True, help="Group results by list")
@click.option("--export", type=click.Choice(["json", "csv"]), help="Export results to format")
@click.pass_context
def item_find_status(
    ctx, statuses, list_key, limit, complex_conditions, no_subitems, group_by_list, export
):
    """Find items by status with multiple search modes.

    This command supports three search modes:
    1. Simple status search: --status pending
    2. Multiple statuses (OR): --status pending --status in_progress
    3. Complex conditions: --complex '{"item": {"status": "in_progress"}, "subitem": {"download": "pending"}}'

    Examples:
      # Find all pending items
      todoit item find-status --status pending

      # Find pending OR in_progress items in specific list
      todoit item find-status --status pending --status in_progress --list myproject

      # Complex search: in_progress items with pending download subitem
      todoit item find-status --complex '{"item": {"status": "in_progress"}, "subitem": {"download": "pending"}}'

      # Export to JSON
      todoit item find-status --status completed --export json

      # Exclude subitems, group by list
      todoit item find-status --status pending --no-subitems --group-by-list
    """
    import json
    from datetime import datetime

    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if list_key and not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Determine search conditions
        if complex_conditions:
            # Parse complex JSON conditions
            try:
                conditions = json.loads(complex_conditions)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON in --complex: {e}[/]")
                return
        else:
            # Simple status search
            if len(statuses) == 1:
                conditions = statuses[0]
            else:
                conditions = list(statuses)

        # Execute search
        results = manager.find_items_by_status(conditions, list_key, limit)

        if not results:
            search_scope = list_key if list_key else "all lists"
            console.print(f"[yellow]No items found matching criteria in '{search_scope}'[/]")
            return

        # Process results based on type
        if isinstance(results, list) and results and hasattr(results[0], 'item_key'):
            # Simple items list
            items_data = []
            for item in results:
                item_data = {
                    "Item Key": item.item_key,
                    "Title": item.content,
                    "Status": _get_status_for_output(item.status.value),
                    "Position": str(item.position),
                }

                # Add list context for cross-list searches
                if not list_key and hasattr(item, 'list_id'):
                    item_list = manager.db.get_list_by_id(item.list_id)
                    if item_list:
                        item_data["List"] = item_list.list_key

                # Add parent context for subitems (unless excluded)
                if not no_subitems and hasattr(item, 'parent_item_id') and item.parent_item_id:
                    parent = manager.db.get_item_by_id(item.parent_item_id)
                    if parent:
                        item_data["Parent"] = parent.item_key
                elif no_subitems and hasattr(item, 'parent_item_id') and item.parent_item_id:
                    # Skip subitems if no_subitems flag is set
                    continue

                items_data.append(item_data)

            # Handle export
            if export:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"items_by_status_{timestamp}.{export}"

                if export == "json":
                    with open(filename, 'w') as f:
                        json.dump(items_data, f, indent=2)
                elif export == "csv":
                    import csv
                    if items_data:
                        with open(filename, 'w', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=items_data[0].keys())
                            writer.writeheader()
                            writer.writerows(items_data)

                console.print(f"[green]✅ Results exported to {filename}[/]")
                return

            # Display results
            search_scope = list_key if list_key else "all lists"
            if isinstance(conditions, str):
                title = f"🔍 Found {len(items_data)} item(s) with status '{conditions}' in '{search_scope}'"
            elif isinstance(conditions, list):
                status_list = "', '".join(conditions)
                title = f"🔍 Found {len(items_data)} item(s) with status '{status_list}' in '{search_scope}'"
            else:
                title = f"🔍 Found {len(items_data)} item(s) matching complex conditions in '{search_scope}'"

            # Column styling
            columns = {
                "Item Key": {"style": "cyan", "width": 20},
                "Title": {"style": "white"},
                "Status": {"style": "yellow", "width": 12},
                "Position": {"style": "blue", "width": 8},
            }

            # Add conditional columns
            if items_data and "List" in items_data[0]:
                columns["List"] = {"style": "magenta", "width": 20}
            if items_data and "Parent" in items_data[0]:
                columns["Parent"] = {"style": "green", "width": 15}

            _display_records(items_data, title, columns)

        else:
            # Complex matches (parent-subitem format)
            matches_data = []
            for match in results:
                parent_data = {
                    "Parent Key": match["parent"].item_key,
                    "Parent Title": match["parent"].content,
                    "Parent Status": _get_status_for_output(match["parent"].status.value),
                    "Matching Subitems": ", ".join([s.item_key for s in match["matching_subitems"]]),
                    "Subitem Count": str(len(match["matching_subitems"])),
                }

                # Add list context
                if not list_key and hasattr(match["parent"], 'list_id'):
                    parent_list = manager.db.get_list_by_id(match["parent"].list_id)
                    if parent_list:
                        parent_data["List"] = parent_list.list_key

                matches_data.append(parent_data)

            # Display complex matches
            search_scope = list_key if list_key else "all lists"
            title = f"🔍 Found {len(matches_data)} parent item(s) with matching subitems in '{search_scope}'"

            columns = {
                "Parent Key": {"style": "cyan", "width": 20},
                "Parent Title": {"style": "white"},
                "Parent Status": {"style": "yellow", "width": 12},
                "Matching Subitems": {"style": "green"},
                "Subitem Count": {"style": "blue", "width": 12},
            }

            if matches_data and "List" in matches_data[0]:
                columns["List"] = {"style": "magenta", "width": 20}

            _display_records(matches_data, title, columns)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")
