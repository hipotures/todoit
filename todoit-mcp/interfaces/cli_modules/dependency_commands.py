"""
Dependency management commands for TODOIT CLI
Handles cross-list dependencies and graph visualization
"""

import click
from rich.console import Console
from rich.prompt import Confirm

from .display import _display_records, _get_status_display, _get_status_icon, console


def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager

    if db_path == "todoit.db":
        return TodoManager()
    return TodoManager(db_path)


def _parse_item_reference(ref: str) -> tuple:
    """Parse list:item reference like 'backend:auth_api'"""
    if ":" not in ref:
        raise ValueError(
            f"Invalid reference format '{ref}'. Expected 'list_key:item_key'"
        )
    parts = ref.split(":", 1)
    return parts[0], parts[1]


@click.group()
def dep():
    """Cross-list dependency management"""
    pass


@dep.command("add")
@click.option(
    "--dependent",
    "dependent_ref",
    required=True,
    help="Dependent item reference (list:item)",
)
@click.option(
    "--required",
    "required_ref",
    required=True,
    help="Required item reference (list:item)",
)
@click.option(
    "--type",
    "dep_type",
    default="blocks",
    help="Dependency type (blocks, requires, related)",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def dep_add(ctx, dependent_ref, required_ref, dep_type, force):
    """Add dependency between items from different lists

    Example: todoit dep add --dependent "frontend:auth_ui" --required "backend:auth_api"
    """

    manager = get_manager(ctx.obj["db_path"])

    try:
        # Parse references
        dep_list, dep_item = _parse_item_reference(dependent_ref)
        req_list, req_item = _parse_item_reference(required_ref)

        # Show what we're about to do
        console.print(f"[yellow]Adding dependency:[/]")
        console.print(f"  {dep_list}:{dep_item} → {req_list}:{req_item}")
        console.print(f"  Type: {dep_type}")

        if not force and not Confirm.ask("Proceed?"):
            return

        # Add dependency
        dependency = manager.add_item_dependency(
            dependent_list=dep_list,
            dependent_item=dep_item,
            required_list=req_list,
            required_item=req_item,
            dependency_type=dep_type,
        )

        console.print(f"[green]✅ Dependency added successfully[/]")
        console.print(f"   ID: {dependency.id}, Type: {dependency.dependency_type}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command("remove")
@click.option(
    "--dependent",
    "dependent_ref",
    required=True,
    help="Dependent item reference (list:item)",
)
@click.option(
    "--required",
    "required_ref",
    required=True,
    help="Required item reference (list:item)",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def dep_remove(ctx, dependent_ref, required_ref, force):
    """Remove dependency between items

    Example: todoit dep remove --dependent "frontend:auth_ui" --required "backend:auth_api"
    """
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Parse references
        dep_list, dep_item = _parse_item_reference(dependent_ref)
        req_list, req_item = _parse_item_reference(required_ref)

        # Show what we're about to do
        console.print(f"[yellow]Removing dependency:[/]")
        console.print(f"  {dep_list}:{dep_item} → {req_list}:{req_item}")

        if not force and not Confirm.ask("Proceed?"):
            return

        # Remove dependency
        success = manager.remove_item_dependency(
            dependent_list=dep_list,
            dependent_item=dep_item,
            required_list=req_list,
            required_item=req_item,
        )

        if success:
            console.print(f"[green]✅ Dependency removed successfully[/]")
        else:
            console.print(f"[yellow]No dependency found between these items[/]")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command("show")
@click.option(
    "--item", "item_ref", required=True, help="Item reference to analyze (list:item)"
)
@click.pass_context
def dep_show(ctx, item_ref):
    """Show all dependencies for an item

    Example: todoit dep show --item "frontend:auth_ui"
    """
    manager = get_manager(ctx.obj["db_path"])

    try:
        # Parse reference
        list_key, item_key = _parse_item_reference(item_ref)

        # Get item info
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return

        # Get dependency information
        is_blocked = manager.is_item_blocked(list_key, item_key)
        blockers = manager.get_item_blockers(list_key, item_key)
        blocked_items = manager.get_items_blocked_by(list_key, item_key)
        can_start_info = manager.can_start_item(list_key, item_key)

        # Prepare data for unified display
        data = []

        # Item info
        data.append(
            {
                "Property": "Item Reference",
                "Value": f"{list_key}:{item_key}",
                "Details": "",
            }
        )

        data.append({"Property": "Content", "Value": item.content, "Details": ""})

        data.append(
            {
                "Property": "Status",
                "Value": _get_status_display(item.status.value),
                "Details": "",
            }
        )

        data.append(
            {
                "Property": "Blocked Status",
                "Value": "🚫 BLOCKED" if is_blocked else "✅ Ready to work",
                "Details": "",
            }
        )

        data.append(
            {
                "Property": "Can Start",
                "Value": "✅ YES" if can_start_info["can_start"] else "❌ NO",
                "Details": (
                    can_start_info.get("reason", "")
                    if not can_start_info["can_start"]
                    else ""
                ),
            }
        )

        # Add blocked by information
        if blockers:
            for i, blocker in enumerate(blockers):
                status_icon = _get_status_icon(blocker.status.value)
                prop_name = "Blocked By" if i == 0 else ""
                data.append(
                    {
                        "Property": prop_name,
                        "Value": f"{status_icon} {blocker.item_key}",
                        "Details": blocker.content,
                    }
                )
        else:
            data.append(
                {
                    "Property": "Blocked By",
                    "Value": "None",
                    "Details": "Not blocked by any dependencies",
                }
            )

        # Add blocks information
        if blocked_items:
            for i, blocked in enumerate(blocked_items):
                status_icon = _get_status_icon(blocked.status.value)
                prop_name = "Blocks" if i == 0 else ""
                data.append(
                    {
                        "Property": prop_name,
                        "Value": f"{status_icon} {blocked.item_key}",
                        "Details": blocked.content,
                    }
                )
        else:
            data.append(
                {
                    "Property": "Blocks",
                    "Value": "None",
                    "Details": "This item doesn't block anything",
                }
            )

        # Define column styling
        columns = {
            "Property": {"style": "cyan", "width": 15},
            "Value": {"style": "white", "width": 25},
            "Details": {"style": "dim"},
        }

        # Use unified display system
        _display_records(data, f"🔗 Dependencies for {list_key}:{item_key}", columns)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command("graph")
@click.option("--project", help="Project key to visualize dependencies for")
@click.pass_context
def dep_graph(ctx, project):
    """Show dependency graph visualization

    Example: cli dep graph --project website
    """
    if not project:
        console.print("[red]--project parameter is required[/]")
        return

    manager = get_manager(ctx.obj["db_path"])

    try:
        # Get cross-list progress with dependencies
        progress_info = manager.get_cross_list_progress(project)

        if not progress_info["lists"]:
            _display_records([], f"📊 Dependency Graph for Project: {project}", {})
            return

        # Prepare data for unified display
        data = []

        # Add project summary
        data.append(
            {
                "Type": "Project",
                "Name": project,
                "Details": f"Overall Progress: {progress_info['overall_progress']:.1f}%",
                "Status": f"{progress_info['total_completed']}/{progress_info['total_items']} completed",
            }
        )

        # Add separator
        data.append({"Type": "", "Name": "--- Lists ---", "Details": "", "Status": ""})

        # Show lists overview
        for list_info in progress_info["lists"]:
            list_data = list_info["list"]
            progress_data = list_info["progress"]
            blocked_count = list_info["blocked_items"]

            details = f"Progress: {progress_data['completion_percentage']:.1f}% ({progress_data['completed']}/{progress_data['total']})"
            if blocked_count > 0:
                details += f", 🚫 {blocked_count} blocked"

            data.append(
                {
                    "Type": "List",
                    "Name": f"📋 {list_data['title']} ({list_data['list_key']})",
                    "Details": details,
                    "Status": "Active",
                }
            )

        # Show dependencies
        dependencies = progress_info["dependencies"]
        if dependencies:
            # Add separator
            data.append(
                {
                    "Type": "",
                    "Name": "--- Dependencies ---",
                    "Details": "",
                    "Status": "",
                }
            )

            for dep in dependencies:
                # Find items by ID to get their keys
                dep_item = None
                req_item = None

                for list_info in progress_info["lists"]:
                    for item in list_info["items"]:
                        if item["id"] == dep["dependent"]:
                            dep_item = item
                        if item["id"] == dep["required"]:
                            req_item = item

                if dep_item and req_item:
                    # Find list keys
                    dep_list_key = next(
                        (
                            l["list"]["list_key"]
                            for l in progress_info["lists"]
                            if l["list"]["id"] == dep_item["list_id"]
                        ),
                        "?",
                    )
                    req_list_key = next(
                        (
                            l["list"]["list_key"]
                            for l in progress_info["lists"]
                            if l["list"]["id"] == req_item["list_id"]
                        ),
                        "?",
                    )

                    req_status = _get_status_icon(req_item["status"])
                    dep_status = _get_status_icon(dep_item["status"])

                    data.append(
                        {
                            "Type": "Dependency",
                            "Name": f"{req_status} {req_list_key}:{req_item['key']} → {dep_status} {dep_list_key}:{dep_item['key']}",
                            "Details": f"Required: {req_item.get('content', '')[:30]}{'...' if len(req_item.get('content', '')) > 30 else ''}",
                            "Status": f"Dep: {dep_item.get('content', '')[:30]}{'...' if len(dep_item.get('content', '')) > 30 else ''}",
                        }
                    )
        else:
            # Add separator
            data.append(
                {
                    "Type": "",
                    "Name": "--- Dependencies ---",
                    "Details": "",
                    "Status": "",
                }
            )

            data.append(
                {
                    "Type": "Dependency",
                    "Name": "No cross-list dependencies found",
                    "Details": "",
                    "Status": "",
                }
            )

        # Define column styling
        columns = {
            "Type": {"style": "yellow", "width": 12},
            "Name": {"style": "cyan"},
            "Details": {"style": "white"},
            "Status": {"style": "green"},
        }

        # Use unified display system
        _display_records(data, f"📊 Dependency Graph for Project: {project}", columns)

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")
