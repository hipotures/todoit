"""
Report and analytics commands for TODOIT CLI
Generate various reports for project management and troubleshooting
"""

import click
import re
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from .display import _display_records, _format_date, console


def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager

    if db_path == "todoit.db":
        return TodoManager()
    return TodoManager(db_path)


@click.group(name="reports")
def report_group():
    """Generate reports and analytics for project management"""
    pass


@report_group.command("errors")
@click.option(
    "--filter",
    "list_filter",
    help='Regex pattern to filter lists (e.g. "^\\d{4}_.*" for NNNN_*, ".*project.*" for containing "project")',
)
@click.pass_context
def report_errors(ctx, list_filter):
    """Show all failed tasks from active lists with full details

    This command provides a centralized view of all tasks with 'failed' status
    across all active (non-archived) lists. Includes task content, properties,
    and context information to help with troubleshooting and project management.

    Examples:
    \b
        todoit reports errors                           # All failed tasks
        todoit reports errors --filter "^\\d{4}_.*"     # Only NNNN_* lists
        todoit reports errors --filter ".*sprint.*"     # Lists containing "sprint"
        TODOIT_OUTPUT_FORMAT=json todoit reports errors # JSON output for scripts
    """
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Validate regex pattern if provided
        if list_filter:
            try:
                re.compile(list_filter)
            except re.error as e:
                console.print(f"[red]❌ Invalid regex pattern: {e}[/]")
                console.print(f"[yellow]💡 Example patterns:[/]")
                console.print(
                    f"[dim]  ^\\d{{4}}_.*     - Lists starting with 4 digits + underscore[/]"
                )
                console.print(f"[dim]  .*project.*    - Lists containing 'project'[/]")
                console.print(
                    f"[dim]  ^(sprint|release)_.* - Lists starting with 'sprint_' or 'release_'[/]"
                )
                return

        # Apply FORCE_TAGS filtering for environment isolation
        from .tag_commands import _get_force_tags

        force_tags = _get_force_tags()

        # Get all failed items with filtering
        failed_items = manager.get_all_failed_items(
            list_filter=list_filter, tag_filter=force_tags if force_tags else None
        )

        if not failed_items:
            if list_filter:
                console.print(
                    f"[yellow]No failed tasks found in active lists matching pattern: {list_filter}[/]"
                )
            else:
                console.print(f"[green]✅ No failed tasks found in active lists[/]")
            return

        # Prepare data for display
        data = []
        for item_info in failed_items:
            # Format properties as compact string
            if item_info.get("properties"):
                props_str = ", ".join(
                    [f"{k}={v}" for k, v in item_info["properties"].items()]
                )
                props_display = (
                    props_str[:30] + "..." if len(props_str) > 30 else props_str
                )
            else:
                props_display = "-"

            # Truncate content for table display
            content = item_info["content"]
            content_display = content[:35] + "..." if len(content) > 35 else content

            record = {
                "List": item_info["list_key"],
                "Item": item_info["item_key"],
                "Content": content_display,
                "Updated": _format_date(item_info["updated_at"]),
                "Properties": props_display,
            }
            data.append(record)

        # Define column styling
        columns = {
            "List": {"style": "cyan"},
            "Item": {"style": "yellow"},
            "Content": {"style": "white"},
            "Updated": {"style": "green"},
            "Properties": {"style": "magenta"},
        }

        # Display the report
        title = "📊 Failed Tasks Report"
        if list_filter:
            title += f" (filter: {list_filter})"

        _display_records(data, title, columns)

        # Summary information (only for table/vertical formats)
        from .display import _get_output_format

        if _get_output_format() in ["table", "vertical"]:
            # Count unique lists
            unique_lists = len(set(item["list_key"] for item in failed_items))

            console.print(f"\n[bold]Total failed tasks:[/] {len(failed_items)}")
            console.print(f"[bold]From active lists:[/] {unique_lists}")

            if list_filter:
                console.print(f"[dim]Filter applied:[/] {list_filter}")

            # Show hint about properties if they exist
            has_properties = any(item.get("properties") for item in failed_items)
            if has_properties:
                console.print(
                    f"[dim]💡 Some tasks have additional properties - use JSON output for full details[/]"
                )

    except Exception as e:
        console.print(f"[bold red]❌ Error generating report:[/] {e}")
