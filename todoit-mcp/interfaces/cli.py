
"""
TODOIT CLI
Command Line Interface with Rich for better presentation
"""
import click
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
from rich import box

from core.manager import TodoManager


console = Console()


# === UNIFIED DISPLAY SYSTEM ===

def _get_output_format() -> str:
    """Get output format from environment variable"""
    return os.environ.get('TODOIT_OUTPUT_FORMAT', 'table').lower()


def _format_date(date: datetime) -> str:
    """Standardized date formatting"""
    return date.strftime('%Y-%m-%d %H:%M')


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


def _display_records_table(data: List[Dict[str, Any]], title: str, columns: Dict[str, Dict] = None):
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
        table.add_column(col_name, style=style, width=width)
    
    # Add rows
    for record in data:
        row_data = [str(record.get(col, "")) for col in columns.keys()]
        table.add_row(*row_data)
    
    console.print(table)


def _display_records(data: List[Dict[str, Any]], title: str, columns: Dict[str, Dict] = None):
    """Unified record display - switches between table and vertical format"""
    output_format = _get_output_format()
    
    if output_format == 'vertical':
        _display_records_vertical(data, title)
    else:
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
            parent_relations = session.query(ListRelationDB).filter(
                ListRelationDB.target_list_id == todo_list.id
            ).all()
            
            if parent_relations:
                for rel in parent_relations:
                    parent_list = session.query(TodoListDB).filter(
                        TodoListDB.id == rel.source_list_id
                    ).first()
                    if parent_list:
                        children_by_parent[parent_list.list_key].append(todo_list)
                        has_parent = True
        
        if not has_parent:
            root_lists.append(todo_list)
    
    # Create tree view
    tree = Tree("📋 All TODO Lists (Hierarchical)", guide_style="bold bright_blue")
    
    def add_list_to_tree(parent_node, todo_list, level=0):
        progress = manager.get_progress(todo_list.list_key)
        
        list_text = f"[cyan]{todo_list.list_key}[/] - [white]{todo_list.title}[/] "
        list_text += f"([yellow]{todo_list.list_type.value if hasattr(todo_list.list_type, 'value') else str(todo_list.list_type)}[/]) "
        list_text += f"[green]{progress.total}[/]/[blue]{progress.completed}[/] "
        list_text += f"([magenta]{progress.completion_percentage:.1f}%[/])"
        
        list_text = f"[dim]{todo_list.id}[/] " + list_text
        
        list_node = parent_node.add(list_text)
        
        for child_list in children_by_parent.get(todo_list.list_key, []):
            add_list_to_tree(list_node, child_list, level + 1)
    
    for root_list in sorted(root_lists, key=lambda x: x.id):
        add_list_to_tree(tree, root_list)
    
    console.print(tree)


def _get_status_icon(status_value: str, is_blocked: bool = False) -> str:
    """Get status icon for display (Phase 2: includes blocked status)"""
    if is_blocked and status_value == 'pending':
        return '🚫'  # Blocked
    return {
        'pending': '⏳',
        'in_progress': '🔄',
        'completed': '✅',
        'failed': '❌'
    }.get(status_value, '❓')


def _get_status_display(status_value: str, is_blocked: bool = False) -> str:
    """Get full status display text (Phase 2: includes blocked status)"""
    if is_blocked and status_value == 'pending':
        return '🚫 Blocked'
    return {
        'pending': '⏳ Pending',
        'in_progress': '🔄 In Progress', 
        'completed': '✅ Completed',
        'failed': '❌ Failed'
    }.get(status_value, f'❓ {status_value}')


def _get_status_style(status_value: str, is_blocked: bool = False) -> str:
    """Get status style for Rich formatting (Phase 2: includes blocked status)"""
    if is_blocked and status_value == 'pending':
        return 'red bold'  # Blocked items are red and bold
    return {
        'pending': 'yellow',
        'in_progress': 'blue', 
        'completed': 'green',
        'failed': 'red'
    }.get(status_value, 'white')


def _add_completion_states_to_node(node, completion_states):
    """Add completion states to tree node"""
    if completion_states:
        for state, value in completion_states.items():
            if isinstance(value, bool):
                icon = '✅' if value else '❌'
                node.add(f"{icon} {state}")
            else:
                node.add(f"📝 {state}: {value}")


# _create_properties_table removed - now using unified _display_records system


def _organize_items_by_hierarchy(items: List) -> Dict[str, Any]:
    """Organize items into hierarchical structure"""
    # Create lookup dictionaries
    items_by_id = {item.id: item for item in items}
    items_by_parent = {}
    root_items = []
    
    # Group items by parent
    for item in items:
        parent_id = getattr(item, 'parent_item_id', None)
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
    
    return {
        'roots': root_items,
        'children': items_by_parent
    }


def _get_hierarchical_numbering(item, parent_numbers: List[int] = None) -> str:
    """Generate hierarchical numbering like 1, 1.1, 1.2, 2, 2.1, etc."""
    if parent_numbers is None:
        parent_numbers = []
    
    # For root items, use position directly
    if not parent_numbers:
        return str(item.position)
    
    # For subtasks, append to parent numbering
    return ".".join(map(str, parent_numbers + [item.position]))


def _render_tree_view(todo_list, items: List, properties: Dict[str, str], manager: TodoManager = None) -> Tree:
    """Render list as hierarchical tree view (Phase 2: includes blocked status)"""
    tree_view = Tree(f"📋 {todo_list.title} ({todo_list.list_key})")
    
    # Organize items by hierarchy
    hierarchy = _organize_items_by_hierarchy(items)
    
    def add_item_to_tree(item, parent_node, depth=0):
        """Recursively add item and its children to tree"""
        # Phase 2: Check if item is blocked
        is_blocked = False
        if manager and item.status.value == 'pending':
            try:
                is_blocked = manager.is_item_blocked(todo_list.list_key, item.item_key)
            except:
                is_blocked = False
        
        status_icon = _get_status_icon(item.status.value, is_blocked)
        
        # Calculate progress if item has children
        children = hierarchy['children'].get(item.id, [])
        progress_info = ""
        if children:
            completed = sum(1 for child in children if child.status.value == 'completed')
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
    for root_item in hierarchy['roots']:
        add_item_to_tree(root_item, tree_view)
    
    # Add list properties to tree if any
    if properties:
        props_node = tree_view.add("🔧 Properties")
        for key, value in properties.items():
            display_value = value if len(value) <= 40 else value[:37] + "..."
            props_node.add(f"{key}: {display_value}")
    
    return tree_view


def _render_table_view(todo_list, items: List, properties: Dict[str, str], manager: TodoManager = None):
    """Render list as hierarchical table view (Phase 2: includes blocked status)"""
    # Organize items by hierarchy first to check what columns are needed
    hierarchy = _organize_items_by_hierarchy(items)
    
    # Check if we need optional columns
    has_progress = False
    has_dependencies = False  
    has_states = False
    
    for item in items:
        # Check if any item has children (needs progress)
        if hierarchy['children'].get(item.id, []):
            has_progress = True
            
        # Check if any item has dependencies
        if manager and item.status.value == 'pending':
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
    
    def add_item_to_table(item, parent_numbers=None, depth=0):
        """Recursively add item and its children to table"""
        if parent_numbers is None:
            parent_numbers = []
        
        # Generate hierarchical numbering
        current_numbers = parent_numbers + [item.position]
        hierarchical_num = ".".join(map(str, current_numbers))
        
        # Create indentation for visual hierarchy
        indent = "  " * depth
        if depth > 0:
            indent += "└─ "
        
        # Phase 2: Check if item is blocked
        is_blocked = False
        dependencies_str = ""
        if manager and item.status.value == 'pending':
            try:
                is_blocked = manager.is_item_blocked(todo_list.list_key, item.item_key)
                if is_blocked:
                    blockers = manager.get_item_blockers(todo_list.list_key, item.item_key)
                    if blockers:
                        blocker_names = [b.item_key for b in blockers[:2]]  # Show first 2
                        if len(blockers) > 2:
                            blocker_names.append(f"+{len(blockers) - 2}")
                        dependencies_str = ", ".join(blocker_names)
            except:
                is_blocked = False
        
        # Get status info
        status_display = _get_status_display(item.status.value, is_blocked)
        status_style = _get_status_style(item.status.value, is_blocked)
        
        # Calculate progress if item has children
        children = hierarchy['children'].get(item.id, [])
        progress_str = ""
        if children:
            completed = sum(1 for child in children if child.status.value == 'completed')
            total = len(children)
            percentage = (completed / total * 100) if total > 0 else 0
            progress_str = f"{percentage:.0f}% ({completed}/{total})"
        
        # Format completion states
        states_str = ""
        if item.completion_states:
            states = []
            for k, v in item.completion_states.items():
                if isinstance(v, bool):
                    icon = '✅' if v else '❌'
                    states.append(f"{icon}{k}")
                else:
                    states.append(f"📝{k}")
            states_str = " ".join(states)
        
        # Build record for unified display
        record = {
            "#": hierarchical_num,
            "Key": item.item_key,
            "Task": f"{indent}{item.content}",
            "Status": status_display  # No Rich formatting for vertical format
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
        for child in children:
            add_item_to_table(child, current_numbers, depth + 1)
    
    # Add all root items and their subtrees
    for root_item in hierarchy['roots']:
        add_item_to_table(root_item)
    
    # Define column styling for table format
    columns = {
        "#": {"style": "cyan", "width": 8},
        "Key": {"style": "magenta"},
        "Task": {"style": "white"},
        "Status": {"style": "yellow"}
    }
    
    # Add optional columns with styling
    if has_progress:
        columns["Progress"] = {"style": "blue", "width": 10}
    if has_dependencies:
        columns["Dependencies"] = {"style": "red", "width": 15}
    if has_states:
        columns["States"] = {"style": "green"}
    
    # Use unified display system
    _display_records(data, f"📋 {todo_list.title} (ID: {todo_list.id})", columns)
    
    # Properties display
    if properties:
        console.print()
        prop_data = [{"Key": k, "Value": v} for k, v in properties.items()]
        prop_columns = {"Key": {"style": "cyan", "width": 20}, "Value": {"style": "white"}}
        _display_records(prop_data, "Properties", prop_columns)


def get_manager(db_path: Optional[str]) -> TodoManager:
    """Get TodoManager instance"""
    if db_path == 'todoit.db':
        # Use default if user didn't specify custom path
        return TodoManager()
    return TodoManager(db_path)


# === Main command group ===

@click.group()
@click.option('--db', default='todoit.db', help='Path to database file (default: ~/.todoit/todoit.db)')
@click.version_option(package_name='todoit-mcp', prog_name='TODOIT')
@click.pass_context
def cli(ctx, db):
    """TODOIT - Intelligent TODO list management system"""
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db
    
    # Show DB location on first use
    if db == 'todoit.db':
        from pathlib import Path
        default_db = Path.home() / ".todoit" / "todoit.db"
        if not default_db.exists():
            console.print(f"[dim]Using database: {default_db}[/dim]")


# === List management commands ===

@cli.group(name='list')
def list_group():
    """Manage TODO lists"""
    pass


@list_group.command('create')
@click.argument('list_key')
@click.option('--title', help='List title')
@click.option('--items', '-i', multiple=True, help='Initial items')
@click.option('--from-folder', help='Create tasks from folder contents')
@click.option('--filter-ext', help='Filter files by extension (e.g., .yaml, .py, .md)')
@click.option('--task-prefix', default='Process', help='Task name prefix (default: Process)')
@click.option('--type', 'list_type', default='sequential', 
              type=click.Choice(['sequential', 'parallel', 'hierarchical']))
@click.option('--metadata', '-m', help='Metadata JSON')
@click.pass_context
def list_create(ctx, list_key, title, items, from_folder, filter_ext, task_prefix, list_type, metadata):
    """Create a new TODO list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        # Use list_key as title if not provided
        if not title:
            title = list_key.replace('_', ' ').replace('-', ' ').title()
        
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
                        if not filter_ext.startswith('.'):
                            filter_ext = '.' + filter_ext
                        if not item.lower().endswith(filter_ext.lower()):
                            continue
                    folder_items.append(f"{task_prefix} {item}")
                elif os.path.isdir(item_path) and not filter_ext:
                    # Only include directories if no extension filter
                    folder_items.append(f"Handle folder {item}/")
            
            final_items.extend(folder_items)
            meta["source_folder"] = from_folder
            if filter_ext:
                meta["filter_extension"] = filter_ext
                console.print(f"[dim]Filtered for {filter_ext} files: {len(folder_items)} items[/dim]")
        
        with console.status(f"[bold green]Creating list '{list_key}'..."):
            todo_list = manager.create_list(
                list_key=list_key,
                title=title,
                items=final_items if final_items else None,
                list_type=list_type,
                metadata=meta
            )
        
        # Display created list
        panel = Panel(
            f"[bold cyan]ID:[/] {todo_list.id}\n"
            f"[bold cyan]Key:[/] {todo_list.list_key}\n"
            f"[bold cyan]Title:[/] {todo_list.title}\n"
            f"[bold cyan]Type:[/] {todo_list.list_type}\n"
            f"[bold cyan]Items:[/] {len(final_items)}",
            title="✅ List Created",
            border_style="green"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command('show')
@click.argument('list_key')
@click.option('--tree', is_flag=True, help='Display as tree')
@click.pass_context
def list_show(ctx, list_key, tree):
    """Show list details"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        # Support both ID and key lookup
        todo_list = None
        if list_key.isdigit():
            # If it's a number, try to find by ID first
            list_id = int(list_key)
            with manager.db.get_session() as session:
                from core.database import TodoListDB
                db_list = session.query(TodoListDB).filter(TodoListDB.id == list_id).first()
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
            
            # Show progress
            progress = manager.get_progress(actual_list_key)
            console.print(f"\n[bold]Progress:[/] {progress.completion_percentage:.1f}% "
                         f"({progress.completed}/{progress.total})")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command('all')
@click.option('--limit', type=int, help='Limit number of results')
@click.option('--tree', is_flag=True, help='Show hierarchical view with list relations')
@click.option('--details', is_flag=True, help='Show detailed information including creation date')
@click.pass_context
def list_all(ctx, limit, tree, details):
    """List all TODO lists"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        lists = manager.list_all(limit=limit)
        
        # Sort lists by ID (lowest first) for consistent ordering
        lists = sorted(lists, key=lambda x: x.id)
        
        if tree:
            # Show hierarchical view with relations
            _display_lists_tree(lists, manager)
        else:
            # Prepare data for unified display
            data = []
            
            for todo_list in lists:
                progress = manager.get_progress(todo_list.list_key)
                
                record = {
                    "ID": str(todo_list.id),
                    "Key": todo_list.list_key,
                    "Title": todo_list.title,
                    "Type": str(todo_list.list_type).replace('ListType.', '').lower(),
                    "Items": str(progress.total),
                    "Completed": str(progress.completed),
                    "Progress": f"{progress.completion_percentage:.1f}%"
                }
                
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
                "Type": {"style": "yellow"},
                "Items": {"style": "green"},
                "Completed": {"style": "blue"},
                "Progress": {"style": "magenta"}
            }
            
            if details:
                columns["Created"] = {"style": "green"}
                columns["Updated"] = {"style": "blue"}
            
            # Use unified display system
            _display_records(data, "📋 All TODO Lists", columns)
        console.print(f"\n[bold]Total lists:[/] {len(lists)}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list_group.command('delete')
@click.argument('list_keys', nargs=-1, required=True)
@click.option('--force', is_flag=True, help='Force deletion')
@click.pass_context
def list_delete(ctx, list_keys, force):
    """Delete TODO lists (with dependency validation)
    
    Examples:
    todoit list delete key1
    todoit list delete key1 key2 key3
    todoit list delete key1,key2,key3
    """
    manager = get_manager(ctx.obj['db_path'])
    
    # Handle comma-separated keys
    all_keys = []
    for key_arg in list_keys:
        if ',' in key_arg:
            all_keys.extend([k.strip() for k in key_arg.split(',')])
        else:
            all_keys.append(key_arg)
    
    if not all_keys:
        console.print("[red]No list keys provided[/]")
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
            console.print(f"[cyan]  • {actual_key}[/] - {todo_list.title} ({progress.total} items)")
            
        except Exception as e:
            console.print(f"[red]  ❌ Error checking '{list_key}': {e}[/]")
            failed_keys.append(list_key)
    
    if failed_keys:
        console.print(f"[red]Cannot proceed - {len(failed_keys)} list(s) have errors[/]")
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
                console.print("[yellow]    Hint: Use --force to break dependencies and delete[/]")
        except Exception as e:
            console.print(f"[bold red]  ❌ {actual_key}: {e}[/]")
    
    # Summary
    if deleted_count > 0:
        console.print(f"\n[green]Successfully deleted {deleted_count}/{len(all_keys)} list(s)[/]")
    else:
        console.print(f"\n[red]No lists were deleted[/]")


# === Item management commands ===

@cli.group()
def item():
    """Manage TODO items"""
    pass


@item.command('add')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('content')
@click.option('--metadata', '-m', help='Metadata JSON')
@click.pass_context
def item_add(ctx, list_key, item_key, content, metadata):
    """Add item to TODO list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        meta = json.loads(metadata) if metadata else {}
        item = manager.add_item(
            list_key=list_key,
            item_key=item_key,
            content=content,
            metadata=meta
        )
        console.print(f"[green]✅ Added item '{item_key}' to list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('status')
@click.argument('list_key')
@click.argument('item_key')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'failed']))
@click.option('--state', '-s', multiple=True, help='State in format key=value')
@click.pass_context
def item_status(ctx, list_key, item_key, status, state):
    """Update item status"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        states = {}
        for s in state:
            k, v = s.split('=', 1)
            states[k] = v.lower() in ['true', '1', 'yes']
        
        item = manager.update_item_status(
            list_key=list_key,
            item_key=item_key,
            status=status,
            completion_states=states if states else None
        )
        
        console.print(f"[green]✅ Updated '{item_key}'[/]")
        if states:
            console.print("States:")
            for k, v in states.items():
                icon = '✅' if v else '❌'
                console.print(f"  {icon} {k}")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('next')
@click.argument('list_key')
@click.option('--start', is_flag=True, help='Start the task')
@click.pass_context
def item_next(ctx, list_key, start):
    """Get next pending item"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        item = manager.get_next_pending(list_key)
        if not item:
            console.print(f"[yellow]No pending items in list '{list_key}'[/]")
            return
        
        panel = Panel(
            f"[bold cyan]Task:[/] {item.content}\n"
            f"[bold cyan]Key:[/] {item.item_key}\n"
            f"[bold cyan]Position:[/] {item.position}",
            title="⏭️ Next Task",
            border_style="cyan"
        )
        console.print(panel)
        
        if start and Confirm.ask("Start this task?"):
            manager.update_item_status(list_key, item.item_key, status='in_progress')
            console.print("[green]✅ Task started[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('add-subtask')
@click.argument('list_key')
@click.argument('parent_key')
@click.argument('subtask_key')
@click.argument('content')
@click.option('--metadata', '-m', help='Metadata JSON')
@click.pass_context
def item_add_subtask(ctx, list_key, parent_key, subtask_key, content, metadata):
    """Add subtask to existing task"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        meta = json.loads(metadata) if metadata else {}
        subtask = manager.add_subtask(
            list_key=list_key,
            parent_key=parent_key,
            subtask_key=subtask_key,
            content=content,
            metadata=meta
        )
        console.print(f"[green]✅ Added subtask '{subtask_key}' to '{parent_key}' in list '{list_key}'[/]")
        
        # Show hierarchy for parent
        try:
            hierarchy = manager.get_item_hierarchy(list_key, parent_key)
            console.print(f"\n[dim]Current hierarchy:[/]")
            console.print(f"📋 {parent_key}: {hierarchy['item']['content']}")
            for subtask_info in hierarchy['subtasks']:
                st = subtask_info['item']
                status_icon = _get_status_icon(st['status'])
                console.print(f"  └─ {status_icon} {st['item_key']}: {st['content']}")
        except:
            pass  # Skip hierarchy display if error
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('tree')
@click.argument('list_key')
@click.argument('item_key', required=False)
@click.pass_context
def item_tree(ctx, list_key, item_key):
    """Show hierarchy tree for item or entire list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        if item_key:
            # Show hierarchy for specific item
            hierarchy = manager.get_item_hierarchy(list_key, item_key)
            
            def print_hierarchy(item_info, depth=0):
                item = item_info['item']
                indent = "  " * depth
                status_icon = _get_status_icon(item['status'])
                
                if depth == 0:
                    console.print(f"📋 {item['item_key']}: {item['content']}")
                else:
                    console.print(f"{indent}└─ {status_icon} {item['item_key']}: {item['content']}")
                
                for subtask_info in item_info['subtasks']:
                    print_hierarchy(subtask_info, depth + 1)
            
            print_hierarchy(hierarchy)
        else:
            # Show entire list in tree view
            todo_list = manager.get_list(list_key)
            if not todo_list:
                console.print(f"[red]List '{list_key}' not found[/]")
                return
            
            items = manager.get_list_items(list_key)
            properties = manager.get_list_properties(list_key)
            tree_view = _render_tree_view(todo_list, items, properties)
            console.print(tree_view)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('move-to-subtask')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('new_parent_key')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def item_move_to_subtask(ctx, list_key, item_key, new_parent_key, force):
    """Convert existing task to be a subtask of another task"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        # Show current state
        item = manager.get_item(list_key, item_key)
        parent = manager.get_item(list_key, new_parent_key)
        
        if not item or not parent:
            console.print("[red]Item or parent not found[/]")
            return
        
        console.print(f"[yellow]Moving '{item.item_key}: {item.content}'[/]")
        console.print(f"[yellow]To be subtask of '{parent.item_key}: {parent.content}'[/]")
        
        if not force and not Confirm.ask("Proceed with move?"):
            return
        
        moved_item = manager.move_to_subtask(list_key, item_key, new_parent_key)
        console.print(f"[green]✅ Moved '{item_key}' to be subtask of '{new_parent_key}'[/]")
        
        # Show updated hierarchy
        try:
            hierarchy = manager.get_item_hierarchy(list_key, new_parent_key)
            console.print(f"\n[dim]Updated hierarchy:[/]")
            console.print(f"📋 {new_parent_key}: {hierarchy['item']['content']}")
            for subtask_info in hierarchy['subtasks']:
                st = subtask_info['item']
                status_icon = _get_status_icon(st['status'])
                console.print(f"  └─ {status_icon} {st['item_key']}: {st['content']}")
        except:
            pass
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('subtasks')
@click.argument('list_key')
@click.argument('parent_key')
@click.pass_context
def item_subtasks(ctx, list_key, parent_key):
    """List all subtasks for a parent task"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        subtasks = manager.get_subtasks(list_key, parent_key)
        
        if not subtasks:
            console.print(f"[yellow]No subtasks found for '{parent_key}' in list '{list_key}'[/]")
            return
        
        # Show parent info
        parent = manager.get_item(list_key, parent_key)
        console.print(f"📋 Parent: {parent.item_key} - {parent.content}")
        console.print()
        
        # Prepare subtasks data for unified display
        data = []
        
        for subtask in subtasks:
            status_display = _get_status_display(subtask.status.value)
            
            states_str = ""
            if subtask.completion_states:
                states = []
                for k, v in subtask.completion_states.items():
                    if isinstance(v, bool):
                        icon = '✅' if v else '❌'
                        states.append(f"{icon}{k}")
                    else:
                        states.append(f"📝{k}")
                states_str = " ".join(states)
            
            record = {
                "Key": subtask.item_key,
                "Task": subtask.content,
                "Status": status_display,
                "States": states_str
            }
            data.append(record)
        
        # Define column styling
        columns = {
            "Key": {"style": "magenta"},
            "Task": {"style": "white"},
            "Status": {"style": "yellow"},
            "States": {"style": "blue"}
        }
        
        # Use unified display system
        _display_records(data, f"Subtasks for '{parent_key}'", columns)
        
        # Show completion info
        completed = sum(1 for st in subtasks if st.status.value == 'completed')
        total = len(subtasks)
        percentage = (completed / total * 100) if total > 0 else 0
        console.print(f"\n[bold]Progress:[/] {percentage:.1f}% ({completed}/{total} completed)")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Enhanced next command with smart subtasks ===

@item.command('next-smart')
@click.argument('list_key')
@click.option('--start', is_flag=True, help='Start the task')
@click.pass_context
def item_next_smart(ctx, list_key, start):
    """Get next pending item with smart subtask logic"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        item = manager.get_next_pending(list_key, smart_subtasks=True)
        if not item:
            console.print(f"[yellow]No pending items in list '{list_key}'[/]")
            return
        
        # Check if this is a subtask
        is_subtask = getattr(item, 'parent_item_id', None) is not None
        task_type = "Subtask" if is_subtask else "Task"
        
        panel = Panel(
            f"[bold cyan]Type:[/] {task_type}\n"
            f"[bold cyan]Task:[/] {item.content}\n"
            f"[bold cyan]Key:[/] {item.item_key}\n"
            f"[bold cyan]Position:[/] {item.position}",
            title="⏭️ Next Smart Task",
            border_style="cyan"
        )
        console.print(panel)
        
        if start and Confirm.ask("Start this task?"):
            manager.update_item_status(list_key, item.item_key, status='in_progress')
            console.print("[green]✅ Task started[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Progress and stats commands ===

@cli.group()
def stats():
    """Statistics and reports"""
    pass


@stats.command('progress')
@click.argument('list_key')
@click.option('--detailed', is_flag=True, help='Detailed statistics')
@click.pass_context
def stats_progress(ctx, list_key, detailed):
    """Show list progress"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        progress = manager.get_progress(list_key)
        todo_list = manager.get_list(list_key)
        
        # Progress panel
        panel = Panel(
            f"[bold cyan]List:[/] {todo_list.title}\n"
            f"[bold cyan]Completed:[/] {progress.completed}/{progress.total} "
            f"({progress.completion_percentage:.1f}%)\n"
            f"[bold cyan]In Progress:[/] {progress.in_progress}\n"
            f"[bold cyan]Pending:[/] {progress.pending}\n"
            f"[bold cyan]Failed:[/] {progress.failed}",
            title="📊 Progress Report",
            border_style="blue"
        )
        console.print(panel)
        
        if detailed:
            # Progress bar
            total = progress.total
            if total > 0:
                completed_bar = '█' * int(progress.completed / total * 30)
                in_progress_bar = '▒' * int(progress.in_progress / total * 30)
                pending_bar = '░' * int(progress.pending / total * 30)
                
                console.print(f"\n[green]{completed_bar}[/][yellow]{in_progress_bar}[/][dim]{pending_bar}[/]")
                
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === Import/Export commands ===

@cli.group()
def io():
    """Import/Export operations"""
    pass


@io.command('import')
@click.argument('file_path')
@click.option('--key', help='Base key for imported lists')
@click.pass_context
def io_import(ctx, file_path, key):
    """Import lists from markdown (supports multi-column)"""
    manager = get_manager(ctx.obj['db_path'])
    
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


@io.command('export')
@click.argument('list_key')
@click.argument('file_path')
@click.pass_context
def io_export(ctx, list_key, file_path):
    """Export list to markdown [x] format"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        manager.export_to_markdown(list_key, file_path)
        console.print(f"[green]✅ Exported list '{list_key}' to {file_path}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# === List property management commands ===

@list_group.group(name='property')
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

@item.group(name='property')
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


# === Interactive mode ===

@cli.command()
@click.pass_context
def interactive(ctx):
    """Interactive mode with menu"""
    console.print(Panel.fit(
        "[bold cyan]TODOIT - Interactive Mode[/]\n"
        "Type 'help' to see available commands",
        border_style="cyan"
    ))
    
    manager = get_manager(ctx.obj['db_path'])
    
    while True:
        try:
            command = Prompt.ask("\n[bold cyan]todoit>[/]")
            
            if command.lower() in ['exit', 'quit', 'q']:
                break
            elif command.lower() == 'help':
                console.print("""
[bold]Available commands:[/]\n  lists          - Show all lists\n  show <key>     - Show list details\n  next <key>     - Next task from list\n  complete <key> <item> - Mark task as completed  \n  progress <key> - Show list progress\n  help          - This help\n  exit          - Exit
                """)
            elif command.startswith('lists'):
                lists = manager.list_all()
                for lst in lists:
                    console.print(f"  {lst.list_key} - {lst.title}")
            elif command.startswith('show '):
                key = command.split()[1]
                try:
                    items = manager.get_list_items(key)
                    for item in items:
                        status = '✅' if item.status == 'completed' else '⏳'
                        console.print(f"  {status} {item.content}")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            elif command.startswith('next '):
                key = command.split()[1]
                try:
                    item = manager.get_next_pending(key)
                    if item:
                        console.print(f"[cyan]Next: {item.content}[/]")
                    else:
                        console.print("[yellow]No pending tasks[/]")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            elif command.startswith('progress '):
                key = command.split()[1]
                try:
                    progress = manager.get_progress(key)
                    console.print(f"Progress: {progress.completion_percentage:.1f}% "
                                f"({progress.completed}/{progress.total})")
                except Exception as e:
                    console.print(f"[red]Error: {e}[/]")
            else:
                console.print(f"[red]Unknown command: {command}[/]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
    
    console.print("[yellow]Goodbye! 👋[/]")


# ===== PHASE 2: CROSS-LIST DEPENDENCIES COMMANDS =====

@cli.group()
def dep():
    """Cross-list dependency management (Phase 2)"""
    pass


def _parse_item_reference(ref: str) -> tuple:
    """Parse list:item reference like 'backend:auth_api'"""
    if ':' not in ref:
        raise ValueError(f"Invalid reference format '{ref}'. Expected 'list_key:item_key'")
    parts = ref.split(':', 1)
    return parts[0], parts[1]


@dep.command('add')
@click.argument('dependent_ref')  # list:item that depends 
@click.argument('requires_word')  # literally "requires"
@click.argument('required_ref')   # list:item that is required
@click.option('--type', 'dep_type', default='blocks', help='Dependency type (blocks, requires, related)')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def dep_add(ctx, dependent_ref, requires_word, required_ref, dep_type, force):
    """Add dependency between tasks from different lists
    
    Example: cli dep add frontend:auth_ui requires backend:auth_api
    """
    if requires_word.lower() not in ['requires', 'depends', 'needs']:
        console.print(f"[red]Expected 'requires', 'depends', or 'needs', got '{requires_word}'[/]")
        return
    
    manager = get_manager(ctx.obj['db_path'])
    
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
            dependency_type=dep_type
        )
        
        console.print(f"[green]✅ Dependency added successfully[/]")
        console.print(f"   ID: {dependency.id}, Type: {dependency.dependency_type}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command('remove')
@click.argument('dependent_ref')  # list:item that depends
@click.argument('required_ref')   # list:item that is required  
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def dep_remove(ctx, dependent_ref, required_ref, force):
    """Remove dependency between tasks
    
    Example: cli dep remove frontend:auth_ui backend:auth_api
    """
    manager = get_manager(ctx.obj['db_path'])
    
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
            required_item=req_item
        )
        
        if success:
            console.print(f"[green]✅ Dependency removed successfully[/]")
        else:
            console.print(f"[yellow]No dependency found between these items[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command('show')
@click.argument('item_ref')  # list:item to analyze
@click.pass_context
def dep_show(ctx, item_ref):
    """Show all dependencies for an item
    
    Example: cli dep show frontend:auth_ui
    """
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        # Parse reference
        list_key, item_key = _parse_item_reference(item_ref)
        
        # Get item info
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        console.print(f"[bold cyan]Dependencies for:[/] {list_key}:{item_key}")
        console.print(f"[dim]Content:[/] {item.content}")
        console.print(f"[dim]Status:[/] {_get_status_display(item.status.value)}")
        console.print()
        
        # Check if blocked
        is_blocked = manager.is_item_blocked(list_key, item_key)
        if is_blocked:
            console.print("[red]🚫 This item is BLOCKED[/]")
        else:
            console.print("[green]✅ This item is ready to work on[/]")
        console.print()
        
        # Show what blocks this item
        blockers = manager.get_item_blockers(list_key, item_key)
        if blockers:
            console.print(f"[red]📥 Blocked by ({len(blockers)} items):[/]")
            for blocker in blockers:
                status_icon = _get_status_icon(blocker.status.value)
                console.print(f"  → {status_icon} {blocker.item_key}: {blocker.content}")
        else:
            console.print("[green]📥 Not blocked by any dependencies[/]")
        console.print()
        
        # Show what this item blocks
        blocked_items = manager.get_items_blocked_by(list_key, item_key)
        if blocked_items:
            console.print(f"[yellow]📤 This item blocks ({len(blocked_items)} items):[/]")
            for blocked in blocked_items:
                status_icon = _get_status_icon(blocked.status.value)  
                console.print(f"  → {status_icon} {blocked.item_key}: {blocked.content}")
        else:
            console.print("[dim]📤 This item doesn't block anything[/]")
        
        # Show can start analysis
        can_start_info = manager.can_start_item(list_key, item_key)
        console.print()
        console.print(f"[bold]Can start:[/] {'✅ YES' if can_start_info['can_start'] else '❌ NO'}")
        if not can_start_info['can_start']:
            console.print(f"[dim]Reason:[/] {can_start_info['reason']}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@dep.command('graph')
@click.option('--project', help='Project key to visualize dependencies for')
@click.pass_context 
def dep_graph(ctx, project):
    """Show dependency graph visualization
    
    Example: cli dep graph --project website
    """
    if not project:
        console.print("[red]--project parameter is required[/]")
        return
    
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        # Get cross-list progress with dependencies
        progress_info = manager.get_cross_list_progress(project)
        
        if not progress_info['lists']:
            console.print(f"[yellow]No lists found for project '{project}'[/]")
            return
        
        console.print(f"[bold cyan]📊 Dependency Graph for Project: {project}[/]")
        console.print()
        
        # Show lists overview
        for list_info in progress_info['lists']:
            list_data = list_info['list']
            progress_data = list_info['progress']
            blocked_count = list_info['blocked_items']
            
            console.print(f"📋 [bold]{list_data['title']}[/] ({list_data['list_key']})")
            console.print(f"   Progress: {progress_data['completion_percentage']:.1f}% "
                         f"({progress_data['completed']}/{progress_data['total']})")
            
            if blocked_count > 0:
                console.print(f"   [red]🚫 {blocked_count} blocked items[/]")
            
            console.print()
        
        # Show dependencies
        dependencies = progress_info['dependencies']  
        if dependencies:
            console.print(f"[bold yellow]🔗 Dependencies ({len(dependencies)}):[/]")
            for dep in dependencies:
                # Find items by ID to get their keys
                dep_item = None
                req_item = None
                
                for list_info in progress_info['lists']:
                    for item in list_info['items']:
                        if item['id'] == dep['dependent']:
                            dep_item = item
                        if item['id'] == dep['required']:
                            req_item = item
                
                if dep_item and req_item:
                    # Find list keys
                    dep_list_key = next((l['list']['list_key'] for l in progress_info['lists'] 
                                       if l['list']['id'] == dep_item['list_id']), '?')
                    req_list_key = next((l['list']['list_key'] for l in progress_info['lists']
                                       if l['list']['id'] == req_item['list_id']), '?')
                    
                    req_status = _get_status_icon(req_item['status'])
                    dep_status = _get_status_icon(dep_item['status'])
                    
                    console.print(f"  {req_status} {req_list_key}:{req_item['key']} → "
                                f"{dep_status} {dep_list_key}:{dep_item['key']}")
        else:
            console.print("[dim]No cross-list dependencies found[/]")
        
        # Overall project stats
        console.print()
        console.print(f"[bold]Overall Project Progress:[/] {progress_info['overall_progress']:.1f}%")
        console.print(f"Total: {progress_info['total_completed']}/{progress_info['total_items']} completed")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


# ===== SYSTEM METADATA COMMANDS =====

@cli.command('schema')
@click.pass_context
def schema_info(ctx):
    """Show system schema information (available statuses, types, etc.)"""
    
    # Get schema info from manager (we'll implement this logic directly)
    schema_info = {
        "item_statuses": ["pending", "in_progress", "completed", "failed"],
        "list_types": ["sequential", "parallel"], 
        "relation_types": ["dependency", "parent", "related", "project"],
        "dependency_types": ["blocks", "requires", "related"],
        "history_actions": ["created", "updated", "status_changed", "deleted"]
    }
    
    descriptions = {
        "item_statuses": {
            "pending": "Task is waiting to be started",
            "in_progress": "Task is currently being worked on", 
            "completed": "Task has been finished successfully",
            "failed": "Task could not be completed"
        },
        "list_types": {
            "sequential": "Tasks should be completed in order",
            "parallel": "Tasks can be completed in any order"
        },
        "relation_types": {
            "dependency": "Lists have dependency relationship",
            "parent": "Parent-child relationship between lists", 
            "related": "Lists are loosely related",
            "project": "Lists belong to the same project"
        },
        "dependency_types": {
            "blocks": "This item blocks another from starting",
            "requires": "This item requires another to be completed first",
            "related": "Items are related but not blocking"
        }
    }
    
    console.print(Panel.fit(
        "[bold cyan]TODOIT System Schema Information[/]",
        border_style="cyan"
    ))
    
    # Display each category
    for category, values in schema_info.items():
        console.print(f"\n[bold yellow]{category.replace('_', ' ').title()}:[/]")
        
        for value in values:
            description = descriptions.get(category, {}).get(value, "")
            if description:
                console.print(f"  [cyan]{value}[/] - {description}")
            else:
                console.print(f"  [cyan]{value}[/]")


if __name__ == '__main__':
    cli()
