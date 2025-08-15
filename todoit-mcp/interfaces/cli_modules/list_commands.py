"""
List management commands for TODOIT CLI
Handles create, show, delete, live monitoring operations
"""

import click
import json
import os
import time
import hashlib
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich import box

from .display import (
    _render_tree_view,
    _render_table_view,
    _display_lists_tree,
    _display_records,
    _format_date,
    console,
)
from .tag_commands import _get_filter_tags


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


@click.group(name="list")
def list_group():
    """Manage TODO lists"""
    pass


@list_group.command("create")
@click.argument("list_key")
@click.option("--title", help="List title")
@click.option("--items", "-i", multiple=True, help="Initial items")
@click.option("--from-folder", help="Create items from folder contents")
@click.option("--filter-ext", help="Filter files by extension (e.g., .yaml, .py, .md)")
@click.option(
    "--item-prefix", default="Process", help="Item name prefix (default: Process)"
)
@click.option(
    "--type",
    "list_type",
    default="sequential",
    type=click.Choice(["sequential", "parallel", "hierarchical", "linked"]),
)
@click.option("--metadata", "-m", help="Metadata JSON")
@click.pass_context
def list_create(
    ctx,
    list_key,
    title,
    items,
    from_folder,
    filter_ext,
    item_prefix,
    list_type,
    metadata,
):
    """Create a new TODO list"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Use list_key as title if not provided
        if not title:
            title = list_key.replace("_", " ").replace("-", " ").title()

        meta = json.loads(metadata) if metadata else {}

        # Handle folder option
        final_items = list(items) if items else []
        if from_folder:
            if not os.path.exists(from_folder):
                console.print(f"[red]Folder '{from_folder}' does not exist[/]")
                return

            folder_items = []
            for item in sorted(os.listdir(from_folder)):
                item_path = os.path.join(from_folder, item)

                if os.path.isfile(item_path):
                    # Apply extension filter if specified
                    if filter_ext:
                        if not filter_ext.startswith("."):
                            filter_ext = "." + filter_ext
                        if not item.lower().endswith(filter_ext.lower()):
                            continue
                    folder_items.append(f"{item_prefix} {item}")
                elif os.path.isdir(item_path) and not filter_ext:
                    # Only include directories if no extension filter
                    folder_items.append(f"Handle folder {item}/")

            final_items.extend(folder_items)
            meta["source_folder"] = from_folder
            if filter_ext:
                meta["filter_extension"] = filter_ext
                console.print(
                    f"[dim]Filtered for {filter_ext} files: {len(folder_items)} items[/dim]"
                )

        with console.status(f"[bold green]Creating list '{list_key}'..."):
            todo_list = manager.create_list(
                list_key=list_key,
                title=title,
                items=final_items if final_items else None,
                list_type=list_type,
                metadata=meta,
            )

            # Auto-tag with TODOIT_FORCE_TAGS if set (environment isolation)
            from .tag_commands import _get_force_tags

            force_tags = _get_force_tags()
            if force_tags:
                for tag_name in force_tags:
                    try:
                        manager.add_tag_to_list(list_key, tag_name)
                    except ValueError:
                        # Tag doesn't exist, create it
                        manager.create_tag(tag_name, "blue")
                        manager.add_tag_to_list(list_key, tag_name)
                console.print(f"[dim]Auto-tagged with: {', '.join(force_tags)}[/dim]")

        # Display created list
        panel = Panel(
            f"[bold cyan]ID:[/] {todo_list.id}\n"
            f"[bold cyan]Key:[/] {todo_list.list_key}\n"
            f"[bold cyan]Title:[/] {todo_list.title}\n"
            f"[bold cyan]Type:[/] {todo_list.list_type}\n"
            f"[bold cyan]Items:[/] {len(final_items)}",
            title="✅ List Created",
            border_style="green",
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command("link")
@click.argument("source_key")
@click.argument("target_key")
@click.option("--title", help="Title for the linked list")
@click.pass_context
def list_link(ctx, source_key, target_key, title):
    """Create a linked copy of a list with 1:1 item mapping

    Creates a complete copy of the source list including all items and properties,
    but with all item statuses reset to 'pending'. Establishes a 'project' relation
    between the source and target lists.

    Examples:
        todoit list link 0008_emma 0008_emma-download
        todoit list link project_a project_a-testing --title "Testing Tasks"
    """
    manager = get_manager(ctx.obj["db_path"])

    try:
        result = manager.link_list_1to1(source_key, target_key, title)

        if result.get("success"):
            # Auto-tag target list with TODOIT_FORCE_TAGS if set (same as create command)
            from .tag_commands import _get_force_tags

            force_tags = _get_force_tags()
            if force_tags:
                for tag_name in force_tags:
                    try:
                        manager.add_tag_to_list(target_key, tag_name)
                    except ValueError:
                        # Tag doesn't exist, create it
                        manager.create_tag(tag_name, "blue")
                        manager.add_tag_to_list(target_key, tag_name)
            # Display success message with statistics
            console.print(f"[bold green]✅ Successfully linked list![/]")
            console.print(f"[dim]Source:[/] {result['source_list']}")
            console.print(
                f"[dim]Target:[/] {result['target_list']} (ID: {result['target_list_id']})"
            )
            console.print()

            # Statistics table
            stats_table = Table(
                title="Link Statistics", show_header=True, header_style="bold blue"
            )
            stats_table.add_column("Operation", style="cyan")
            stats_table.add_column("Count", justify="right", style="green")

            stats_table.add_row("Items copied", str(result["items_copied"]))
            stats_table.add_row(
                "List properties copied", str(result["list_properties_copied"])
            )
            stats_table.add_row(
                "Item properties copied", str(result["item_properties_copied"])
            )
            stats_table.add_row(
                "Items set to pending",
                "✅ All" if result["all_items_set_to_pending"] else "❌ None",
            )
            stats_table.add_row(
                "Project relation created",
                "✅ Yes" if result["relation_created"] else "❌ No",
            )

            console.print(stats_table)
            console.print()
            console.print(f"[dim]Relation key:[/] {result['relation_key']}")
            console.print(
                f"[dim]Both lists are now linked in project:[/] {result['relation_key']}"
            )

        else:
            console.print(
                f"[bold red]❌ Link failed:[/] {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        console.print(f"[bold red]❌ Error linking lists:[/] {e}")


@list_group.command("show")
@click.argument("list_key")
@click.option("--tree", is_flag=True, help="Display as tree")
@click.pass_context
def list_show(ctx, list_key, tree):
    """Show list details"""
    manager = get_manager(ctx.obj["db_path"])

    # First resolve list_key if it's an ID
    actual_list_key = list_key
    if list_key.isdigit():
        list_id = int(list_key)
        with manager.db.get_session() as session:
            from core.database import TodoListDB

            db_list = session.query(TodoListDB).filter(TodoListDB.id == list_id).first()
            if db_list:
                actual_list_key = db_list.list_key

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, actual_list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        # Support both ID and key lookup
        todo_list = None
        if list_key.isdigit():
            # If it's a number, try to find by ID first
            list_id = int(list_key)
            with manager.db.get_session() as session:
                from core.database import TodoListDB

                db_list = (
                    session.query(TodoListDB).filter(TodoListDB.id == list_id).first()
                )
                if db_list:
                    todo_list = manager.get_list(db_list.list_key)
        else:
            # Otherwise, use key directly
            todo_list = manager.get_list(list_key)

        if not todo_list:
            console.print(f"[red]List '{list_key}' not found[/]")
            return

        # Use the actual list key from the found list
        actual_list_key = todo_list.list_key
        items = manager.get_list_items(actual_list_key)
        properties = manager.get_list_properties(actual_list_key)

        if tree:
            tree_view = _render_tree_view(todo_list, items, properties, manager)
            console.print(tree_view)
        else:
            _render_table_view(todo_list, items, properties, manager)

            # Show progress only in table/vertical modes
            from .display import _get_output_format

            if _get_output_format() in ["table", "vertical"]:
                progress = manager.get_progress(actual_list_key)
                console.print(
                    f"\n[bold]Progress:[/] {progress.completion_percentage:.1f}% "
                    f"({progress.completed}/{progress.total})"
                )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command("all")
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--tree", is_flag=True, help="Show hierarchical view with list relations")
@click.option(
    "--details", is_flag=True, help="Show detailed information including creation date"
)
@click.option("--archived", is_flag=True, help="Show only archived lists")
@click.option(
    "--include-archived", is_flag=True, help="Include archived lists in results"
)
@click.option(
    "--tag",
    "filter_tags",
    multiple=True,
    help="Filter by tags (can use multiple times)",
)
@click.pass_context
def list_all(ctx, limit, tree, details, archived, include_archived, filter_tags):
    """List all TODO lists"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Get combined filter tags from environment and CLI
        combined_filter_tags = (
            _get_filter_tags(list(filter_tags)) if filter_tags else _get_filter_tags()
        )

        if archived:
            # Show only archived lists
            lists = manager.get_archived_lists(limit=limit)
            # Apply tag filtering to archived lists if tags specified
            if combined_filter_tags:
                tagged_lists = manager.get_lists_by_tags(combined_filter_tags)
                lists = [l for l in lists if l.id in [tl.id for tl in tagged_lists]]
        else:
            # Show active lists with optional tag filtering
            lists = manager.list_all(
                limit=limit,
                include_archived=include_archived,
                filter_tags=combined_filter_tags if combined_filter_tags else None,
            )

        # Sort lists alphabetically by list key for consistent ordering
        lists = sorted(lists, key=lambda x: x.list_key)

        if tree:
            # Show hierarchical view with relations
            _display_lists_tree(lists, manager)
        else:
            # Prepare data for unified display
            data = []

            # Calculate optimal tags column width based on maximum tags per list
            max_tags_per_list = 0
            for todo_list in lists:
                list_tags = manager.get_tags_for_list(todo_list.list_key)
                max_tags_per_list = max(max_tags_per_list, len(list_tags))

            # Dynamic width: minimum 3, each tag needs ~2 chars (● + space), max 12
            tags_column_width = max(3, min(12, max_tags_per_list * 2))

            for todo_list in lists:
                progress = manager.get_progress(todo_list.list_key)

                # Get tags for this list and format as colored dots
                list_tags = manager.get_tags_for_list(todo_list.list_key)
                tags_display = (
                    " ".join([f"[{tag.color}]●[/{tag.color}]" for tag in list_tags])
                    if list_tags
                    else ""
                )

                # Show first letter of type for clarity
                list_type_str = (
                    str(todo_list.list_type).replace("ListType.", "").lower()
                )
                type_short = list_type_str[0].upper()  # S, P, H, L

                # Show short indicator for status
                if hasattr(todo_list, "status") and todo_list.status:
                    status_value = (
                        todo_list.status.value
                        if hasattr(todo_list.status, "value")
                        else str(todo_list.status)
                    )
                else:
                    status_value = "active"
                # Use specific letters: A for active, Z for archived (from Polish "zarchiwizowana")
                status_short = "A" if status_value == "active" else "Z"

                record = {
                    "ID": str(todo_list.id),
                    "Key": todo_list.list_key,
                    "Title": todo_list.title,
                    "🏷️": tags_display,
                    "🔀": type_short,
                    "📋": str(progress.pending),
                    "🔄": str(progress.in_progress),
                    "❌": str(progress.failed),
                    "✅": str(progress.completed),
                    "⏳": f"{progress.completion_percentage:.0f}%",
                }

                # Only show status column when there are mixed statuses
                if include_archived or archived:
                    record["📦"] = status_short

                # Add date columns if details requested
                if details:
                    record["Created"] = _format_date(todo_list.created_at)
                    record["Updated"] = _format_date(todo_list.updated_at)

                data.append(record)

            # Define column styling for table format
            columns = {
                "ID": {"style": "dim", "width": 4},
                "Key": {"style": "cyan"},
                "Title": {"style": "white"},
                "🏷️": {"style": "white", "justify": "left", "width": tags_column_width},
                "🔀": {"style": "yellow", "justify": "center", "width": 3},
                "📋": {"style": "blue", "justify": "right", "width": 3},
                "🔄": {"style": "yellow", "justify": "right", "width": 3},
                "❌": {"style": "red", "justify": "right", "width": 3},
                "✅": {"style": "green", "justify": "right", "width": 3},
                "⏳": {"style": "magenta", "justify": "right"},
            }

            # Only show status column when there are mixed statuses
            if include_archived or archived:
                columns["📦"] = {
                    "style": "bright_blue",
                    "justify": "center",
                    "width": 3,
                }

            if details:
                columns["Created"] = {"style": "green"}
                columns["Updated"] = {"style": "blue"}

            # Use unified display system
            _display_records(data, "📋 All TODO Lists", columns)

        # Show tags legend if any lists have tags
        from .display import _get_output_format

        if _get_output_format() in ["table", "vertical"]:
            all_tags = {}  # Use dict to store unique tags by name
            for todo_list in lists:
                list_tags = manager.get_tags_for_list(todo_list.list_key)
                for tag in list_tags:
                    all_tags[tag.name] = tag  # Store by name as key

            if all_tags:
                console.print("\n[bold]🏷️ Tags Legend:[/]")
                sorted_tags = sorted(all_tags.values(), key=lambda x: x.name)
                legend_parts = []
                for tag in sorted_tags:
                    colored_dot = f"[{tag.color}]●[/{tag.color}]"
                    legend_parts.append(f"{colored_dot} {tag.name}")
                console.print(" ".join(legend_parts))

            console.print(f"\n[bold]Total lists:[/] {len(lists)}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command("delete")
@click.argument("list_keys", nargs=-1, required=True)
@click.option("--force", is_flag=True, help="Force deletion")
@click.pass_context
def list_delete(ctx, list_keys, force):
    """Delete TODO lists (with dependency validation)

    Examples:
    todoit list delete key1
    todoit list delete key1 key2 key3
    todoit list delete key1,key2,key3
    """
    manager = get_manager(ctx.obj["db_path"])

    # Handle comma-separated keys
    all_keys = []
    for key_arg in list_keys:
        if "," in key_arg:
            all_keys.extend([k.strip() for k in key_arg.split(",")])
        else:
            all_keys.append(key_arg)

    if not all_keys:
        console.print("[red]No list keys provided[/]")
        return

    # Check if all lists are accessible based on FORCE_TAGS (environment isolation)
    inaccessible_lists = []
    for list_key in all_keys:
        if not _check_list_access(manager, list_key):
            inaccessible_lists.append(list_key)

    if inaccessible_lists:
        console.print(
            f"[red]Lists not found or not accessible: {', '.join(inaccessible_lists)}[/]"
        )
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    # Show what will be deleted
    console.print(f"[yellow]Will delete {len(all_keys)} list(s):[/]")
    deleted_count = 0
    failed_keys = []

    for list_key in all_keys:
        try:
            # Try to get list by key first, then by ID if it fails
            todo_list = None
            actual_key = list_key

            # If it looks like an ID, try to find by ID first
            if list_key.isdigit():
                list_id = int(list_key)
                all_lists = manager.list_all()
                for l in all_lists:
                    if l.id == list_id:
                        todo_list = l
                        actual_key = l.list_key
                        break
            else:
                # Try as key
                todo_list = manager.get_list(list_key)

            if not todo_list:
                console.print(f"[red]  ❌ List '{list_key}' not found[/]")
                failed_keys.append(list_key)
                continue

            progress = manager.get_progress(actual_key)
            console.print(
                f"[cyan]  • {actual_key}[/] - {todo_list.title} ({progress.total} items)"
            )

        except Exception as e:
            console.print(f"[red]  ❌ Error checking '{list_key}': {e}[/]")
            failed_keys.append(list_key)

    if failed_keys:
        console.print(
            f"[red]Cannot proceed - {len(failed_keys)} list(s) have errors[/]"
        )
        return

    # Confirm deletion
    if not force:
        if len(all_keys) == 1:
            if not Confirm.ask(f"Delete list '{all_keys[0]}'?"):
                return
        else:
            if not Confirm.ask(f"Delete all {len(all_keys)} lists?"):
                return

    # Delete lists - need to resolve IDs to keys again
    key_mapping = {}
    for list_key in all_keys:
        actual_key = list_key
        if list_key.isdigit():
            list_id = int(list_key)
            all_lists = manager.list_all()
            for l in all_lists:
                if l.id == list_id:
                    actual_key = l.list_key
                    break
        key_mapping[list_key] = actual_key

    for list_key in all_keys:
        actual_key = key_mapping[list_key]
        try:
            manager.delete_list(actual_key)
            console.print(f"[green]  ✅ Deleted '{actual_key}'[/]")
            deleted_count += 1
        except ValueError as e:
            console.print(f"[bold red]  ❌ {actual_key}: {e}[/]")
            if not force:
                console.print(
                    "[yellow]    Hint: Use --force to break dependencies and delete[/]"
                )
        except Exception as e:
            console.print(f"[bold red]  ❌ {actual_key}: {e}[/]")

    # Summary
    if deleted_count > 0:
        console.print(
            f"\n[green]Successfully deleted {deleted_count}/{len(all_keys)} list(s)[/]"
        )
    else:
        console.print(f"\n[red]No lists were deleted[/]")


@list_group.command("live")
@click.argument("list_key")
@click.option(
    "--refresh",
    "-r",
    default=2,
    type=float,
    help="Refresh interval in seconds (default: 2)",
)
@click.option("--show-history", "-h", is_flag=True, help="Show recent changes history")
@click.option(
    "--filter-status",
    "-f",
    help="Filter items by status (pending, in_progress, completed, failed)",
)
@click.option(
    "--no-heartbeat", is_flag=True, help="Disable heartbeat animation (reduces flicker)"
)
@click.pass_context
def list_live(ctx, list_key, refresh, show_history, filter_status, no_heartbeat):
    """Live monitoring of TODO list changes

    Shows real-time updates of list status, item changes, and progress.
    Use Ctrl+C to exit.

    Examples:
    todoit list live my-project
    todoit list live my-project --refresh 1 --show-history
    todoit list live my-project --filter-status pending
    """
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    # Verify list exists
    todo_list = manager.get_list(list_key)
    if not todo_list:
        console.print(f"[red]❌ List '{list_key}' not found[/]")
        return

    # State tracking for change detection
    last_hash = None
    last_update_time = datetime.now()
    changes_history = []
    last_display = None  # Cache for display content

    def get_list_hash(items_data):
        """Generate hash of list state for change detection"""
        state_str = json.dumps(items_data, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()

    def generate_display():
        """Generate the live display layout"""
        nonlocal last_hash, last_update_time, changes_history, last_display

        try:
            # Get current list data
            todo_list = manager.get_list(list_key)
            if not todo_list:
                return Panel("[red]❌ List not found[/]", title="Error")

            items = manager.get_list_items(list_key, status=filter_status)
            progress = manager.get_progress(list_key)

            # Create items data for change detection
            items_data = []
            for item in items:
                items_data.append(
                    {
                        "id": item.item_key,
                        "content": item.content,
                        "status": item.status,
                        "position": item.position,
                        "updated_at": str(item.updated_at),
                    }
                )

            # Check for changes
            current_hash = get_list_hash(items_data)
            has_changed = last_hash is not None and current_hash != last_hash

            # If nothing changed and we have cached display, check if we need heartbeat
            if not has_changed and last_display is not None and no_heartbeat:
                # No changes and no heartbeat wanted - return cached display
                return last_display

            if has_changed:
                last_update_time = datetime.now()
                if len(changes_history) >= 10:  # Keep only last 10 changes
                    changes_history.pop(0)
                changes_history.append(
                    {
                        "timestamp": last_update_time,
                        "type": "update",
                        "message": "List updated",
                    }
                )

            last_hash = current_hash

            # Create layout
            layout = Layout()

            # Top section - List info and progress
            list_info = _create_list_info_panel(
                todo_list, progress, last_update_time, has_changed, no_heartbeat
            )

            # Main section - Items table
            items_table = _create_live_items_table(items, has_changed)

            # Split layout
            if show_history and changes_history:
                layout.split(
                    Layout(list_info, name="info", size=8),
                    Layout(items_table, name="items", ratio=2),
                    Layout(
                        _create_changes_panel(changes_history), name="history", size=8
                    ),
                )
            else:
                layout.split(
                    Layout(list_info, name="info", size=8),
                    Layout(items_table, name="items"),
                )

            # Cache the display
            last_display = layout
            return layout

        except Exception as e:
            return Panel(f"[red]❌ Error: {e}[/]", title="Error")

    # Start live monitoring
    try:
        with Live(
            generate_display(),
            refresh_per_second=2,
            console=console,
            auto_refresh=False,
        ) as live:  # Disable auto refresh, we'll control it
            console.print(
                f"[green]🔴 Live monitoring started for '[cyan]{list_key}[/]'[/]"
            )
            console.print(f"[dim]Refresh rate: {refresh}s | Press Ctrl+C to exit[/]")
            console.print()

            while True:
                time.sleep(refresh)
                old_hash = last_hash
                old_time = datetime.now()
                new_display = generate_display()

                # Determine if we should update display
                content_changed = old_hash != last_hash or old_hash is None
                heartbeat_tick = (
                    not no_heartbeat
                    and int(old_time.timestamp()) % 2
                    != int(datetime.now().timestamp()) % 2
                )

                # Only update if something actually changed, first run, or heartbeat tick
                if content_changed or heartbeat_tick:
                    live.update(new_display)
                    live.refresh()

    except KeyboardInterrupt:
        console.print("\n[yellow]📡 Live monitoring stopped[/]")
    except Exception as e:
        console.print(f"\n[red]❌ Error during live monitoring: {e}[/]")


def _create_list_info_panel(
    todo_list, progress, last_update_time, has_changed, no_heartbeat=False
):
    """Create the list information panel"""
    # Status indicator with heartbeat
    current_time = datetime.now()
    seconds_since_update = (current_time - last_update_time).total_seconds()

    if has_changed:
        status_color = "green"
        status_icon = "🔄"
        status_text = "UPDATED"
    else:
        status_color = "blue"
        status_text = "MONITORING"

        if no_heartbeat:
            status_icon = "📋"  # Static icon
        else:
            # Show heartbeat every few seconds to indicate system is alive
            heartbeat = "💓" if int(current_time.timestamp()) % 4 < 2 else "📋"
            status_icon = heartbeat

    # Progress bar
    if progress.total > 0:
        completed_percentage = int((progress.completed / progress.total) * 100)
        progress_bar = "█" * (completed_percentage // 5) + "░" * (
            20 - (completed_percentage // 5)
        )
        progress_text = f"[{status_color}]{progress_bar}[/] {progress.completed}/{progress.total} ({completed_percentage}%)"
    else:
        progress_text = "[dim]No items[/]"

    info_content = f"""[bold cyan]{todo_list.title}[/]
[dim]Key:[/] {todo_list.list_key}
[dim]Last update:[/] {_format_date(last_update_time)}

{status_icon} [bold]Progress:[/] {progress_text}

[dim]Items:[/] [green]✅ {progress.completed}[/] | [yellow]🔄 {progress.in_progress}[/] | [blue]⏳ {progress.pending}[/] | [red]❌ {progress.failed}[/]"""

    title = f"📋 List Monitor | {status_icon} {status_text}"
    return Panel(info_content, title=title, border_style=status_color)


def _create_live_items_table(items, has_changed):
    """Create the items table with live updates"""
    table = Table(
        title="📝 Items" + (" 🔄 UPDATED" if has_changed else ""), box=box.ROUNDED
    )

    table.add_column("Key", style="cyan")
    table.add_column("Content", style="white", min_width=30)
    table.add_column("Status", justify="center", width=6)
    table.add_column("Updated", style="dim", width=16)

    if not items:
        table.add_row("", "[dim]No items found[/]", "", "")
        return table

    # Sort items by position
    sorted_items = sorted(items, key=lambda x: x.position)

    for item in sorted_items:
        # Status formatting
        status_map = {
            "pending": "[blue]⏳[/]",
            "in_progress": "[yellow]🔄[/]",
            "completed": "[green]✅[/]",
            "failed": "[red]❌[/]",
        }
        status_display = status_map.get(item.status, f"[white]{item.status}[/]")

        # Highlight recently changed items
        content_style = "bold white" if has_changed else "white"

        table.add_row(
            item.item_key,
            Text(
                item.content[:50] + "..." if len(item.content) > 50 else item.content,
                style=content_style,
            ),
            status_display,
            _format_date(item.updated_at),
        )

    return table


def _create_changes_panel(changes_history):
    """Create the changes history panel"""
    if not changes_history:
        return Panel("[dim]No recent changes[/]", title="📊 Recent Changes")

    changes_text = []
    for change in changes_history[-5:]:  # Show last 5 changes
        timestamp = change["timestamp"].strftime("%H:%M:%S")
        changes_text.append(f"[dim]{timestamp}[/] {change['message']}")

    content = "\n".join(changes_text) if changes_text else "[dim]No recent changes[/]"
    return Panel(content, title="📊 Recent Changes", border_style="yellow")


@list_group.command("archive")
@click.argument("list_key")
@click.option(
    "--force", is_flag=True, help="Force archiving even with incomplete items"
)
@click.pass_context
def list_archive(ctx, list_key, force):
    """Archive a TODO list (hide from normal view)

    By default, only lists with all items completed can be archived.
    Use --force to archive lists with incomplete items.
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
        archived_list = manager.archive_list(list_key, force=force)
        console.print(f"✅ List '[cyan]{list_key}[/]' has been archived")
        console.print(f"   Title: [white]{archived_list.title}[/]")
        console.print(f"   Status: [yellow]{archived_list.status}[/]")
        console.print()
        console.print(
            "💡 Use [cyan]todoit list all --include-archived[/] to see archived lists"
        )
        console.print("💡 Use [cyan]todoit list unarchive {list_key}[/] to restore it")
    except ValueError as e:
        console.print(f"[red]❌ Error: {e}[/]")
        if "incomplete items" in str(e).lower() and not force:
            console.print(
                f"[yellow]💡 Use [cyan]todoit list archive {list_key} --force[/] to archive anyway[/]"
            )


@list_group.command("unarchive")
@click.argument("list_key")
@click.pass_context
def list_unarchive(ctx, list_key):
    """Unarchive a TODO list (restore to normal view)"""
    manager = get_manager(ctx.obj["db_path"])

    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print(
            "[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]"
        )
        return

    try:
        restored_list = manager.unarchive_list(list_key)
        console.print(f"✅ List '[cyan]{list_key}[/]' has been restored")
        console.print(f"   Title: [white]{restored_list.title}[/]")
        console.print(f"   Status: [green]{restored_list.status}[/]")
        console.print()
        console.print(
            "💡 The list is now visible in normal [cyan]todoit list all[/] view"
        )
    except ValueError as e:
        console.print(f"[red]❌ Error: {e}[/]")


@list_group.command("rename")
@click.argument("current_key")
@click.option("--key", "new_key", help="New list key")
@click.option("--title", "new_title", help="New list title")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def list_rename(ctx, current_key, new_key, new_title, yes):
    """Rename list key and/or title"""
    try:
        # Validate that at least one parameter is provided
        if not new_key and not new_title:
            console.print("❌ Error: At least one of --key or --title must be provided")
            raise click.ClickException("Missing required options")
        
        manager = get_manager(ctx.obj["db_path"])
        
        # Check access if FORCE_TAGS is enabled
        if not _check_list_access(manager, current_key):
            console.print(
                f"❌ Access denied to list '{current_key}' based on FORCE_TAGS filter"
            )
            raise click.ClickException("Access denied")
        
        # Get current list to show what will change
        current_list = manager.get_list(current_key)
        if not current_list:
            console.print(f"❌ List '{current_key}' does not exist")
            raise click.ClickException("List not found")
        
        # Show changes that will be made
        changes_table = Table(title="Changes to be made", box=box.ROUNDED)
        changes_table.add_column("Field", style="cyan")
        changes_table.add_column("Current", style="white")
        changes_table.add_column("New", style="green")
        
        if new_key:
            changes_table.add_row("Key", current_list.list_key, new_key)
        if new_title:
            changes_table.add_row("Title", current_list.title, new_title)
        
        console.print(changes_table)
        
        # Confirmation
        if not yes:
            if not Confirm.ask("Continue with rename?", default=False):
                console.print("❌ Rename cancelled")
                return
        
        # Perform rename
        renamed_list = manager.rename_list(
            current_key=current_key,
            new_key=new_key,
            new_title=new_title
        )
        
        # Show success result
        result_table = Table(title="✅ List renamed successfully!", box=box.ROUNDED)
        result_table.add_column("Field", style="cyan")
        result_table.add_column("Value", style="white")
        
        result_table.add_row("Key", renamed_list.list_key)
        result_table.add_row("Title", renamed_list.title)
        result_table.add_row("Type", renamed_list.list_type)
        result_table.add_row("Status", renamed_list.status)
        result_table.add_row("Updated", _format_date(renamed_list.updated_at))
        
        console.print(result_table)
        
    except ValueError as e:
        console.print(f"❌ Error: {e}")
        raise click.ClickException(str(e))
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        raise click.ClickException(str(e))


# ===== LIST TAG MANAGEMENT =====


@list_group.group()
def tag():
    """Tag management for lists"""
    pass


@tag.command("add")
@click.argument("list_key")
@click.argument("tag_name")
@click.pass_context
def add_tag_to_list(ctx, list_key, tag_name):
    """Add tag to a list"""
    try:
        manager = get_manager(ctx.obj["db_path"])
        assignment = manager.add_tag_to_list(list_key, tag_name)

        console.print(
            f"✅ Added tag '[cyan]{tag_name}[/]' to list '[white]{list_key}[/]'"
        )

    except ValueError as e:
        console.print(f"❌ Error: {e}")
        raise click.ClickException(str(e))
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        raise click.ClickException(str(e))


@tag.command("remove")
@click.argument("list_key")
@click.argument("tag_name")
@click.pass_context
def remove_tag_from_list(ctx, list_key, tag_name):
    """Remove tag from a list"""
    try:
        manager = get_manager(ctx.obj["db_path"])
        success = manager.remove_tag_from_list(list_key, tag_name)

        if success:
            console.print(
                f"✅ Removed tag '[cyan]{tag_name}[/]' from list '[white]{list_key}[/]'"
            )
        else:
            console.print(
                f"❌ Tag '[cyan]{tag_name}[/]' was not assigned to list '[white]{list_key}[/]'"
            )

    except Exception as e:
        console.print(f"❌ Error removing tag: {e}")
        raise click.ClickException(str(e))


@tag.command("show")
@click.argument("list_key")
@click.pass_context
def show_list_tags(ctx, list_key):
    """Show all tags assigned to a list"""
    try:
        manager = get_manager(ctx.obj["db_path"])

        # Verify list exists
        list_obj = manager.get_list(list_key)
        if not list_obj:
            console.print(f"❌ List '{list_key}' not found")
            return

        # Get tags for list
        tags = manager.get_tags_for_list(list_key)

        if not tags:
            # Use unified display for empty case
            _display_records([], f"Tags for List: {list_obj.title}", {})
            return

        # Prepare data for unified display
        data = []
        for tag in tags:
            # For unified display, use simple color representation
            color_display = f"● {tag.color}"

            data.append({"Tag Name": tag.name, "Color": color_display, "Assigned": "✓"})

        columns = {
            "Tag Name": {"style": "bold white"},
            "Color": {"style": "dim"},
            "Assigned": {"style": "dim"},
        }

        _display_records(data, f"🏷️ Tags for List: {list_obj.title}", columns)

    except Exception as e:
        console.print(f"❌ Error showing tags: {e}")
        raise click.ClickException(str(e))
