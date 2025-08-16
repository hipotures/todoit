"""
I/O, Stats and Schema commands for TODOIT CLI
Handles import/export, progress stats, and system information
"""

import click
from rich.console import Console
from rich.panel import Panel

from .display import _display_records

from .display import console


def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager

    if db_path == "todoit.db":
        return TodoManager()
    return TodoManager(db_path)


# === Progress and stats commands ===


@click.group()
def stats():
    """Statistics and reports"""
    pass


@stats.command("progress")
@click.option("--list", "list_key", required=True, help="List key")
@click.option("--detailed", is_flag=True, help="Detailed statistics")
@click.pass_context
def stats_progress(ctx, list_key, detailed):
    """Show list progress"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        progress = manager.get_progress(list_key)
        todo_list = manager.get_list(list_key)

        # Prepare data for unified display
        data = [
            {
                "List": todo_list.title,
                "Total": str(progress.total),
                "Completed": str(progress.completed),
                "Completion %": f"{progress.completion_percentage:.1f}%",
                "In Progress": str(progress.in_progress),
                "Pending": str(progress.pending),
                "Failed": str(progress.failed),
            }
        ]

        columns = {
            "List": {"style": "cyan"},
            "Total": {"style": "white"},
            "Completed": {"style": "green"},
            "Completion %": {"style": "yellow"},
            "In Progress": {"style": "blue"},
            "Pending": {"style": "dim"},
            "Failed": {"style": "red"},
        }

        _display_records(data, f"📊 Progress Report for '{list_key}'", columns)

        if detailed:
            # Progress bar - for detailed mode, still show as console output (not part of unified display)
            total = progress.total
            if total > 0:
                completed_bar = "█" * int(progress.completed / total * 30)
                in_progress_bar = "▒" * int(progress.in_progress / total * 30)
                pending_bar = "░" * int(progress.pending / total * 30)

                console.print(
                    f"\n[green]{completed_bar}[/][yellow]{in_progress_bar}[/][dim]{pending_bar}[/]"
                )

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Import/Export commands ===


@click.group()
def io():
    """Import/Export operations"""
    pass


@io.command("import")
@click.option("--file", "file_path", required=True, help="File path to import from")
@click.option("--key", help="Base key for imported lists")
@click.pass_context
def io_import(ctx, file_path, key):
    """Import lists from markdown (supports multi-column)"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        with console.status(f"[bold green]Importing from {file_path}..."):
            lists = manager.import_from_markdown(file_path, base_key=key)

        if len(lists) == 1:
            console.print(f"[green]✅ Imported 1 list: '{lists[0].list_key}'[/]")
        else:
            console.print(f"[green]✅ Imported {len(lists)} related lists:[/]")
            for i, lst in enumerate(lists):
                relation = " → depends on previous" if i > 0 else ""
                console.print(f"  • {lst.list_key}{relation}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@io.command("export")
@click.option("--list", "list_key", required=True, help="List key to export")
@click.option("--file", "file_path", required=True, help="File path to export to")
@click.pass_context
def io_export(ctx, list_key, file_path):
    """Export list to markdown [x] format"""
    manager = get_manager(ctx.obj["db_path"])

    try:
        manager.export_to_markdown(list_key, file_path)
        console.print(f"[green]✅ Exported list '{list_key}' to {file_path}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === System schema command ===


@click.command("schema")
@click.pass_context
def schema_info(ctx):
    """Show system schema information (available statuses, types, etc.)"""

    # Get schema info from manager (we'll implement this logic directly)
    schema_info = {
        "item_statuses": ["pending", "in_progress", "completed", "failed"],
        "list_types": ["sequential", "parallel"],
        "relation_types": ["dependency", "parent", "related", "project"],
        "dependency_types": ["blocks", "requires", "related"],
        "history_actions": ["created", "updated", "status_changed", "deleted"],
    }

    descriptions = {
        "item_statuses": {
            "pending": "Task is waiting to be started",
            "in_progress": "Task is currently being worked on",
            "completed": "Task has been finished successfully",
            "failed": "Task could not be completed",
        },
        "list_types": {
            "sequential": "Tasks should be completed in order",
            "parallel": "Tasks can be completed in any order",
        },
        "relation_types": {
            "dependency": "Lists have dependency relationship",
            "parent": "Parent-child relationship between lists",
            "related": "Lists are loosely related",
            "project": "Lists belong to the same project",
        },
        "dependency_types": {
            "blocks": "This item blocks another from starting",
            "requires": "This item requires another to be completed first",
            "related": "Items are related but not blocking",
        },
    }

    # Prepare data for unified display
    data = []

    # Display each category
    for category, values in schema_info.items():
        category_name = category.replace("_", " ").title()

        for i, value in enumerate(values):
            description = descriptions.get(category, {}).get(value, "")

            # Use category name only for first item in each category
            category_display = category_name if i == 0 else ""

            data.append(
                {
                    "Category": category_display,
                    "Value": value,
                    "Description": description,
                }
            )

    # Define column styling
    columns = {
        "Category": {"style": "yellow", "width": 18},
        "Value": {"style": "cyan", "width": 15},
        "Description": {"style": "white"},
    }

    # Use unified display system
    _display_records(data, "📋 TODOIT System Schema Information", columns)


# === Interactive mode ===


@click.command()
@click.pass_context
def interactive(ctx):
    """Interactive mode with menu"""
    from rich.prompt import Prompt

    console.print(
        Panel.fit(
            "[bold cyan]TODOIT - Interactive Mode[/]\n"
            "Type 'help' to see available commands",
            border_style="cyan",
        )
    )

    manager = get_manager(ctx.obj["db_path"])

    while True:
        try:
            command = Prompt.ask("\n[bold cyan]todoit>[/]")

            if command.lower() in ["exit", "quit", "q"]:
                break
            elif command.lower() == "help":
                console.print(
                    """
[bold]Available commands:[/]
  lists          - Show all lists
  show <key>     - Show list details
  next <key>     - Next item from list
  complete <key> <item> - Mark item as completed  
  progress <key> - Show list progress
  help          - This help
  exit          - Exit
                """
                )
            elif command.startswith("lists"):
                # Apply FORCE_TAGS filtering for environment isolation
                from .tag_commands import _get_force_tags

                force_tags = _get_force_tags()

                lists = manager.list_all(filter_tags=force_tags if force_tags else None)
                for lst in lists:
                    console.print(f"  {lst.list_key} - {lst.title}")
            elif command.startswith("show "):
                key = command.split(" ", 1)[1]
                try:
                    todo_list = manager.get_list(key)
                    items = manager.get_list_items(key)
                    console.print(f"\n[bold]{todo_list.title}[/] ({len(items)} items)")
                    for item in items[:5]:  # Show first 5
                        console.print(f"  • {item.item_key}: {item.content}")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            elif command.startswith("next "):
                key = command.split(" ", 1)[1]
                try:
                    item = manager.get_next_pending(key)
                    if item:
                        console.print(
                            f"[cyan]Next: {item.item_key} - {item.content}[/]"
                        )
                    else:
                        console.print("[yellow]No pending items[/]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            else:
                console.print(
                    "[yellow]Unknown command. Type 'help' for available commands.[/]"
                )

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

    console.print("[yellow]Goodbye! 👋[/]")
