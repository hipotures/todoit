"""
Display utilities for TODOIT CLI
Rich formatting, tables, trees, and status rendering
Supports multiple output formats: table, vertical, json, yaml, xml
"""

import os
import json
import yaml
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import box
import dicttoxml

# Mapping emoji keys to human-readable names for JSON/YAML/XML output
EMOJI_TO_NAME_MAPPING = {
    "🏷️": "tags",
    "📋": "pending_count",
    "🔄": "in_progress_count",
    "❌": "failed_count",
    "✅": "completed_count",
    "⏳": "completion_percentage",
    "📦": "status",
}

console = Console()


def _get_output_format() -> str:
    """Get output format from environment variable"""
    format_value = os.environ.get("TODOIT_OUTPUT_FORMAT", "table").lower()
    valid_formats = ["table", "vertical", "json", "yaml", "xml"]
    return format_value if format_value in valid_formats else "table"


def _format_date(date: datetime) -> str:
    """Standardized date formatting - converts UTC to local time"""
    if date is None:
        return "Never"

    # Assume date from DB is naive UTC, convert to local time
    if date.tzinfo is None:
        utc_date = date.replace(tzinfo=timezone.utc)
        local_date = utc_date.astimezone()
        return local_date.strftime("%Y-%m-%d %H:%M")
    else:
        # Already timezone-aware
        local_date = date.astimezone()
        return local_date.strftime("%Y-%m-%d %H:%M")


def _display_records_vertical(data: List[Dict[str, Any]], title: str = "Records"):
    """Display records in vertical format (key-value pairs)"""
    console.print(f"[bold cyan]{title}[/]")
    console.print()

    for i, record in enumerate(data, 1):
        console.print(f"Record {i}:")

        # Find the maximum key length for alignment
        max_key_len = max(len(str(key)) for key in record.keys()) if record else 0

        for key, value in record.items():
            # Right-align keys for clean look
            console.print(f"  {key:>{max_key_len}}: {value}")

        # Add blank line between records (except last)
        if i < len(data):
            console.print()


def _display_records_table(
    data: List[Dict[str, Any]], title: str, columns: Dict[str, Dict] = None
):
    """Display records in table format"""
    if not data:
        console.print(f"[yellow]No {title.lower()} found[/]")
        return

    table = Table(title=title, box=box.ROUNDED)

    # Use first record to determine columns if not specified
    if not columns:
        columns = {key: {"style": "white"} for key in data[0].keys()}

    # Add columns with optional styling
    for col_name, col_config in columns.items():
        style = col_config.get("style", "white")
        width = col_config.get("width")
        justify = col_config.get("justify", "left")
        table.add_column(col_name, style=style, width=width, justify=justify)

    # Add rows
    for record in data:
        row_data = [str(record.get(col, "")) for col in columns.keys()]
        table.add_row(*row_data)

    console.print(table)


def _serialize_for_output(obj):
    """Convert objects to serializable format for JSON/YAML/XML"""
    if isinstance(obj, datetime):
        return _format_date(obj)
    elif hasattr(obj, "value"):  # Enum objects
        return obj.value
    elif hasattr(obj, "__dict__"):  # Pydantic models
        return obj.__dict__
    else:
        return str(obj)


def _prepare_data_for_serialization(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare data for JSON/YAML/XML serialization with emoji-to-name mapping"""
    serialized_data = []
    for record in data:
        serialized_record = {}
        for key, value in record.items():
            # Replace emoji keys with human-readable names for serialization
            clean_key = EMOJI_TO_NAME_MAPPING.get(key, key)
            serialized_record[clean_key] = _serialize_for_output(value)
        serialized_data.append(serialized_record)
    return serialized_data


def _display_records_json(data: List[Dict[str, Any]], title: str):
    """Display records in JSON format"""
    output = {
        "title": title,
        "count": len(data),
        "data": _prepare_data_for_serialization(data),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def _display_records_yaml(data: List[Dict[str, Any]], title: str):
    """Display records in YAML format"""
    output = {
        "title": title,
        "count": len(data),
        "data": _prepare_data_for_serialization(data),
    }
    print(yaml.dump(output, default_flow_style=False, allow_unicode=True, indent=2))


def _display_records_xml(data: List[Dict[str, Any]], title: str):
    """Display records in XML format"""
    output = {
        "title": title,
        "count": len(data),
        "data": _prepare_data_for_serialization(data),
    }
    xml_data = dicttoxml.dicttoxml(
        output,
        custom_root="todoit_output",
        attr_type=False,
        item_func=lambda x: "record" if x == "data" else x,
    )
    print(xml_data.decode("utf-8"))


def _display_records(
    data: List[Dict[str, Any]], title: str, columns: Dict[str, Dict] = None
):
    """Unified record display - switches between all supported formats"""
    output_format = _get_output_format()

    if output_format == "vertical":
        _display_records_vertical(data, title)
    elif output_format == "json":
        _display_records_json(data, title)
    elif output_format == "yaml":
        _display_records_yaml(data, title)
    elif output_format == "xml":
        _display_records_xml(data, title)
    else:  # default to table
        _display_records_table(data, title, columns)


def _display_lists_tree(lists, manager):
    """Display lists in hierarchical tree view based on relations"""
    from collections import defaultdict

    # Get all list relations
    root_lists = []
    children_by_parent = defaultdict(list)

    # Build relation mapping
    for todo_list in lists:
        has_parent = False
        with manager.db.get_session() as session:
            from core.database import ListRelationDB, TodoListDB

            parent_relations = (
                session.query(ListRelationDB)
                .filter(ListRelationDB.target_list_id == todo_list.id)
                .all()
            )

            if parent_relations:
                for rel in parent_relations:
                    parent_list = (
                        session.query(TodoListDB)
                        .filter(TodoListDB.id == rel.source_list_id)
                        .first()
                    )
                    if parent_list:
                        children_by_parent[parent_list.list_key].append(todo_list)
                        has_parent = True

        if not has_parent:
            root_lists.append(todo_list)

    # Create tree view
    tree = Tree("📋 All TODO Lists (Hierarchical)", guide_style="bold bright_blue")

    def add_list_to_tree(parent_node, todo_list, level=0):
        progress = manager.get_progress(todo_list.list_key)

        # Check if list is archived
        is_archived = hasattr(todo_list, "status") and todo_list.status == "archived"

        # Use different colors for archived lists
        if is_archived:
            list_text = (
                f"[dim cyan]{todo_list.list_key}[/] - [dim white]{todo_list.title}[/] "
            )
        else:
            list_text = f"[cyan]{todo_list.list_key}[/] - [white]{todo_list.title}[/] "


        # Add archived indicator
        if is_archived:
            list_text += "[dim]📦[/] "

        list_text += f"[green]{progress.total}[/]/[blue]{progress.completed}[/] "
        list_text += f"([magenta]{progress.completion_percentage:.1f}%[/])"

        list_text = f"[dim]{todo_list.id}[/] " + list_text

        list_node = parent_node.add(list_text)

        for child_list in children_by_parent.get(todo_list.list_key, []):
            add_list_to_tree(list_node, child_list, level + 1)

    for root_list in sorted(root_lists, key=lambda x: x.list_key):
        add_list_to_tree(tree, root_list)

    console.print(tree)


def _get_status_icon(status_value: str, is_blocked: bool = False) -> str:
    """Get status icon for display (Phase 2: includes blocked status)"""
    if is_blocked and status_value == "pending":
        return "🚫"  # Blocked
    return {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
    }.get(status_value, "❓")


def _get_status_display(status_value: str, is_blocked: bool = False) -> str:
    """Get full status display text (Phase 2: includes blocked status)"""
    if is_blocked and status_value == "pending":
        return "🚫 Blocked"
    return {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
    }.get(status_value, f"❓ {status_value}")


def _get_status_style(status_value: str, is_blocked: bool = False) -> str:
    """Get status style for Rich formatting (Phase 2: includes blocked status)"""
    if is_blocked and status_value == "pending":
        return "red bold"  # Blocked items are red and bold
    return {
        "pending": "yellow",
        "in_progress": "blue",
        "completed": "green",
        "failed": "red",
    }.get(status_value, "white")


def _add_completion_states_to_node(node, completion_states):
    """Add completion states to tree node"""
    if completion_states:
        for state, value in completion_states.items():
            if isinstance(value, bool):
                icon = "✅" if value else "❌"
                node.add(f"{icon} {state}")
            else:
                node.add(f"📝 {state}: {value}")


def _organize_items_by_hierarchy(items: List) -> Dict[str, Any]:
    """Organize items into hierarchical structure"""
    # Create lookup dictionaries
    items_by_id = {item.id: item for item in items}
    items_by_parent = {}
    root_items = []

    # Group items by parent
    for item in items:
        parent_id = getattr(item, "parent_item_id", None)
        if parent_id is None:
            root_items.append(item)
        else:
            if parent_id not in items_by_parent:
                items_by_parent[parent_id] = []
            items_by_parent[parent_id].append(item)

    # Sort each group by position
    root_items.sort(key=lambda x: x.position)
    for parent_id in items_by_parent:
        items_by_parent[parent_id].sort(key=lambda x: x.position)

    return {"roots": root_items, "children": items_by_parent}


def _get_hierarchical_numbering(item, parent_numbers: List[int] = None) -> str:
    """Generate hierarchical numbering like 1, 1.1, 1.2, 2, 2.1, etc."""
    if parent_numbers is None:
        parent_numbers = []

    # For root items, use position directly
    if not parent_numbers:
        return str(item.position)

    # For subitems, append to parent numbering
    return ".".join(map(str, parent_numbers + [item.position]))


def _render_tree_view(
    todo_list, items: List, properties: Dict[str, str], manager=None
) -> Tree:
    """Render list as hierarchical tree view (Phase 2: includes blocked status)"""
    tree_view = Tree(f"📋 {todo_list.title} ({todo_list.list_key})")

    # Organize items by hierarchy
    hierarchy = _organize_items_by_hierarchy(items)

    def add_item_to_tree(item, parent_node, depth=0):
        """Recursively add item and its children to tree"""
        # Phase 2: Check if item is blocked
        is_blocked = False
        if manager and item.status.value == "pending":
            try:
                is_blocked = manager.is_item_blocked(todo_list.list_key, item.item_key)
            except:
                is_blocked = False

        status_icon = _get_status_icon(item.status.value, is_blocked)

        # Calculate progress if item has children
        children = hierarchy["children"].get(item.id, [])
        progress_info = ""
        if children:
            completed = sum(
                1 for child in children if child.status.value == "completed"
            )
            total = len(children)
            progress_info = f" [Progress: {completed}/{total}]"

        # Add blocked info
        blocked_info = " [BLOCKED]" if is_blocked else ""

        # Add item node
        item_text = f"{status_icon} {item.content}{progress_info}{blocked_info}"
        item_node = parent_node.add(item_text)

        # Add completion states
        _add_completion_states_to_node(item_node, item.completion_states)

        # Phase 2: Add dependency info if blocked
        if is_blocked and manager:
            try:
                blockers = manager.get_item_blockers(todo_list.list_key, item.item_key)
                if blockers:
                    deps_node = item_node.add("🔗 Dependencies:")
                    for blocker in blockers[:3]:  # Show first 3 blockers
                        deps_node.add(f"→ Waiting for: {blocker.item_key}")
                    if len(blockers) > 3:
                        deps_node.add(f"→ ... and {len(blockers) - 3} more")
            except:
                pass

        # Recursively add children
        for child in children:
            add_item_to_tree(child, item_node, depth + 1)

    # Add all root items and their subtrees
    for root_item in hierarchy["roots"]:
        add_item_to_tree(root_item, tree_view)

    # Add list properties to tree if any
    if properties:
        props_node = tree_view.add("🔧 Properties")
        for key, value in properties.items():
            display_value = value if len(value) <= 40 else value[:37] + "..."
            props_node.add(f"{key}: {display_value}")

    return tree_view


def _render_table_view(
    todo_list, items: List, properties: Dict[str, str], manager=None
):
    """Render list as hierarchical table view (Phase 2: includes blocked status)"""
    # Organize items by hierarchy first to check what columns are needed
    hierarchy = _organize_items_by_hierarchy(items)

    # Check if we need optional columns
    has_progress = False
    has_dependencies = False
    has_states = False

    for item in items:
        # Check if any item has children (needs progress)
        if hierarchy["children"].get(item.id, []):
            has_progress = True

        # Check if any item has dependencies
        if manager and item.status.value == "pending":
            try:
                is_blocked = manager.is_item_blocked(todo_list.list_key, item.item_key)
                if is_blocked:
                    has_dependencies = True
            except:
                pass

        # Check if any item has completion states
        if item.completion_states:
            has_states = True

    # Prepare data for unified display
    data = []

    def add_item_to_table(item, parent_numbers=None, depth=0, sibling_index=None):
        """Recursively add item and its children to table"""
        if parent_numbers is None:
            parent_numbers = []

        # Generate hierarchical numbering
        # For root items, use position; for subitems, use sibling_index (1-based)
        if depth == 0:
            position_number = item.position
        else:
            position_number = sibling_index if sibling_index is not None else 1
            
        current_numbers = parent_numbers + [position_number]
        hierarchical_num = ".".join(map(str, current_numbers))

        # Create indentation for visual hierarchy
        indent = "  " * depth
        if depth > 0:
            indent += ""  # Remove tree symbols for cleaner look

        # Phase 2: Check if item is blocked
        is_blocked = False
        dependencies_str = ""
        if manager and item.status.value == "pending":
            try:
                is_blocked = manager.is_item_blocked(todo_list.list_key, item.item_key)
                if is_blocked:
                    blockers = manager.get_item_blockers(
                        todo_list.list_key, item.item_key
                    )
                    if blockers:
                        blocker_names = [
                            b.item_key for b in blockers[:2]
                        ]  # Show first 2
                        if len(blockers) > 2:
                            blocker_names.append(f"+{len(blockers) - 2}")
                        dependencies_str = ", ".join(blocker_names)
            except:
                is_blocked = False

        # Get status info
        status_display = _get_status_display(item.status.value, is_blocked)
        status_style = _get_status_style(item.status.value, is_blocked)

        # Calculate progress if item has children
        children = hierarchy["children"].get(item.id, [])
        progress_str = ""
        if children:
            completed = sum(
                1 for child in children if child.status.value == "completed"
            )
            total = len(children)
            percentage = (completed / total * 100) if total > 0 else 0
            progress_str = f"{percentage:.0f}% ({completed}/{total})"

        # Format completion states
        states_str = ""
        if item.completion_states:
            states = []
            for k, v in item.completion_states.items():
                if isinstance(v, bool):
                    icon = "✅" if v else "❌"
                    states.append(f"{icon}{k}")
                else:
                    states.append(f"📝{k}")
            states_str = " ".join(states)

        # Build record for unified display
        # Format key column: use indentation for subitems
        key_indent = "  " * depth
        key_display = f"{key_indent}{item.item_key}"
        
        record = {
            "#": hierarchical_num,
            "Key": key_display,
            "Task": f"{indent}{item.content}",
            "Status": status_display,  # No Rich formatting for vertical format
        }

        # Add optional columns only if they exist
        if has_progress:
            record["Progress"] = progress_str
        if has_dependencies:
            record["Dependencies"] = dependencies_str
        if has_states:
            record["States"] = states_str

        data.append(record)

        # Recursively add children
        for child_index, child in enumerate(children, 1):
            add_item_to_table(child, current_numbers, depth + 1, child_index)

    # Add all root items and their subtrees
    for root_item in hierarchy["roots"]:
        add_item_to_table(root_item)

    # Define column styling for table format
    columns = {
        "#": {"style": "cyan", "width": 8},
        "Key": {"style": "magenta"},
        "Task": {"style": "white"},
        "Status": {"style": "yellow"},
    }

    # Add optional columns with styling
    if has_progress:
        columns["Progress"] = {"style": "blue", "width": 10}
    if has_dependencies:
        columns["Dependencies"] = {"style": "red", "width": 15}
    if has_states:
        columns["States"] = {"style": "green"}

    # Check if we're in JSON mode to handle output differently
    output_format = _get_output_format()
    
    if output_format == "json":
        # For JSON output, combine everything into one JSON object
        combined_output = {
            "list_info": {
                "id": todo_list.id,
                "list_key": todo_list.list_key,
                "title": todo_list.title,
                "created_at": todo_list.created_at.isoformat() if todo_list.created_at else None,
                "metadata": todo_list.metadata
            },
            "items": {
                "title": f"📋 {todo_list.title} (ID: {todo_list.id})",
                "count": len(data),
                "data": _prepare_data_for_serialization(data)
            }
        }
        
        # Add properties if they exist
        if properties:
            prop_data = [{"Key": k, "Value": v} for k, v in properties.items()]
            combined_output["properties"] = {
                "title": "Properties",
                "count": len(prop_data),
                "data": _prepare_data_for_serialization(prop_data)
            }
        
        # Print single JSON
        print(json.dumps(combined_output, indent=2, ensure_ascii=False))
    else:
        # For non-JSON outputs, use the original separate display method
        _display_records(data, f"📋 {todo_list.title} (ID: {todo_list.id})", columns)

        # Properties display
        if properties:
            console.print()
            prop_data = [{"Key": k, "Value": v} for k, v in properties.items()]
            prop_columns = {
                "Key": {"style": "cyan", "width": 20},
                "Value": {"style": "white"},
            }
            _display_records(prop_data, "Properties", prop_columns)


# Live display functions for list_live command


def _create_list_info_panel(
    todo_list, progress, last_update_time, has_changed, no_heartbeat=False
):
    """Create list information panel for live display"""
    from rich.panel import Panel
    from rich.text import Text

    # Status indicator
    status_icon = "🔄" if has_changed else ("💓" if not no_heartbeat else "📊")

    info_text = Text()
    info_text.append(f"{status_icon} ", style="bold green")
    info_text.append(f"List: {todo_list.title}\n", style="bold cyan")
    info_text.append(f"Key: {todo_list.list_key}\n", style="white")
    info_text.append(f"Total: {progress.total} | ", style="white")
    info_text.append(f"Completed: {progress.completed} | ", style="green")
    info_text.append(
        f"Progress: {progress.completion_percentage:.1f}%\n", style="yellow"
    )
    info_text.append(f"Last update: {_format_date(last_update_time)}", style="dim")

    return Panel(info_text, title="📋 List Status", border_style="blue")


def _create_live_items_table(items, has_changed):
    """Create items table for live display"""
    if not items:
        return Table(title="📝 No items in this list")

    table = Table(title=f"📝 Items {'(Updated!)' if has_changed else ''}")
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Key", style="magenta")
    table.add_column("Task", style="white", min_width=20)
    table.add_column("Status", style="yellow", justify="left", width=6)
    table.add_column("Modified", style="dim", width=16)

    for i, item in enumerate(items, 1):
        status_icon = _get_status_icon(item.status.value)
        status_text = status_icon

        # Truncate long content for live view
        content = item.content[:30] + "..." if len(item.content) > 30 else item.content

        table.add_row(
            str(i), item.item_key, content, status_text, _format_date(item.updated_at)
        )

    return table


def _create_changes_panel(changes_history):
    """Create changes history panel"""
    from rich.panel import Panel
    from rich.text import Text

    if not changes_history:
        return Panel("No recent changes", title="📈 Recent Changes", border_style="dim")

    changes_text = Text()
    for i, change in enumerate(changes_history[-5:], 1):  # Last 5 changes
        time_str = _format_date(change.get("timestamp", datetime.now()))
        changes_text.append(f"{i}. ", style="cyan")
        changes_text.append(f"[{time_str}] ", style="dim")
        changes_text.append(
            f"{change.get('description', 'Unknown change')}\n", style="white"
        )

    return Panel(changes_text, title="📈 Recent Changes", border_style="green")
