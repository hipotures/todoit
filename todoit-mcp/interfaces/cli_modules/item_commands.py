"""
Item management commands for TODOIT CLI
Handles add, status, subtasks, tree operations
"""
import click
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .display import (
    _get_status_icon, _get_status_display, _render_tree_view, 
    _display_records, console
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
    if db_path == 'todoit.db':
        return TodoManager()
    return TodoManager(db_path)


@click.group()
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
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
@click.option('--status', is_flag=False, flag_value='_show_help', default=None,
              help='Status: pending, in_progress, completed, failed')
@click.option('--state', '-s', multiple=True, help='State in format key=value')
@click.pass_context
def item_status(ctx, list_key, item_key, status, state):
    """Update item status"""
    
    # Check if --status was provided without value (flag_value will be '_show_help')
    if status == '_show_help':
        console.print("[bold red]❌ Error:[/] Option '--status' requires an argument.")
        console.print("[yellow]Available status options:[/]")
        console.print("  • [green]pending[/] - Task is waiting to be started")
        console.print("  • [blue]in_progress[/] - Task is currently being worked on") 
        console.print("  • [green]completed[/] - Task has been finished")
        console.print("  • [red]failed[/] - Task failed or was cancelled")
        console.print("\n[dim]Example:[/] todoit item status mylist task001 --status pending")
        console.print("\n[dim]For more help:[/] todoit item status --help")
        return
    
    # Check if status option was provided
    if status is None:
        console.print("[bold red]❌ Error:[/] Option '--status' requires an argument.")
        console.print("[yellow]Available status options:[/]")
        console.print("  • [green]pending[/] - Task is waiting to be started")
        console.print("  • [blue]in_progress[/] - Task is currently being worked on") 
        console.print("  • [green]completed[/] - Task has been finished")
        console.print("  • [red]failed[/] - Task failed or was cancelled")
        console.print("\n[dim]Example:[/] todoit item status mylist task001 --status pending")
        console.print("\n[dim]For more help:[/] todoit item status --help")
        return
    
    # Validate status value
    valid_statuses = ['pending', 'in_progress', 'completed', 'failed']
    if status not in valid_statuses:
        console.print(f"[bold red]❌ Error:[/] Invalid status '{status}'.")
        console.print("[yellow]Available status options:[/]")
        console.print("  • [green]pending[/] - Task is waiting to be started")
        console.print("  • [blue]in_progress[/] - Task is currently being worked on") 
        console.print("  • [green]completed[/] - Task has been finished")
        console.print("  • [red]failed[/] - Task failed or was cancelled")
        return
    
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        item = manager.get_next_pending(list_key)
        if not item:
            # Use unified display for empty case
            _display_records([], f"Next Task for list '{list_key}'", {})
            return
        
        # Prepare data for unified display
        data = [{
            "Task": item.content,
            "Key": item.item_key,
            "Position": str(item.position),
            "Status": _get_status_display(item.status.value)
        }]
        
        columns = {
            "Task": {"style": "cyan"},
            "Key": {"style": "magenta"},
            "Position": {"style": "yellow"},
            "Status": {"style": "green"}
        }
        
        _display_records(data, f"⏭️ Next Task for list '{list_key}'", columns)
        
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        if item_key:
            # Show hierarchy for specific item
            hierarchy = manager.get_item_hierarchy(list_key, item_key)
            
            def flatten_hierarchy(item_info, depth=0, data_list=None):
                if data_list is None:
                    data_list = []
                
                item = item_info['item']
                status_icon = _get_status_icon(item['status'])
                
                # Create indentation for hierarchy visualization
                indent = "  " * depth
                if depth == 0:
                    hierarchy_display = f"📋 {item['item_key']}: {item['content']}"
                else:
                    hierarchy_display = f"{indent}└─ {status_icon} {item['item_key']}: {item['content']}"
                
                data_list.append({
                    "Level": str(depth),
                    "Item": item['item_key'], 
                    "Content": item['content'],
                    "Status": status_icon,
                    "Hierarchy": hierarchy_display
                })
                
                for subtask_info in item_info['subtasks']:
                    flatten_hierarchy(subtask_info, depth + 1, data_list)
                
                return data_list
            
            data = flatten_hierarchy(hierarchy)
            columns = {
                "Level": {"style": "dim", "width": 5},
                "Item": {"style": "cyan"},
                "Content": {"style": "white"},
                "Status": {"style": "yellow"},
                "Hierarchy": {"style": "white"}
            }
            
            _display_records(data, f"📋 Item Tree for '{item_key}' in '{list_key}'", columns)
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
                if hasattr(item, 'parent_item_id') and item.parent_item_id:
                    depth = 1  # Simplified depth calculation
                
                indent = "  " * depth
                status_icon = _get_status_icon(item.status.value)
                
                if depth == 0:
                    hierarchy_display = f"{status_icon} {item.content}"
                else:
                    hierarchy_display = f"{indent}└─ {status_icon} {item.content}"
                
                data.append({
                    "Position": str(item.position),
                    "Key": item.item_key,
                    "Status": status_icon,
                    "Task": hierarchy_display
                })
            
            columns = {
                "Position": {"style": "dim", "width": 8},
                "Key": {"style": "cyan"},
                "Status": {"style": "yellow", "width": 6},
                "Task": {"style": "white"}
            }
            
            _display_records(data, f"📋 Tree View for '{todo_list.title}' ({list_key})", columns)
            
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
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
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
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


@item.command('next-smart')
@click.argument('list_key')
@click.option('--start', is_flag=True, help='Start the task')
@click.pass_context
def item_next_smart(ctx, list_key, start):
    """Get next pending item with smart subtask logic"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        item = manager.get_next_pending(list_key, smart_subtasks=True)
        if not item:
            # Use unified display for empty case
            _display_records([], f"Next Smart Task for list '{list_key}'", {})
            return
        
        # Check if this is a subtask
        is_subtask = getattr(item, 'parent_item_id', None) is not None
        task_type = "Subtask" if is_subtask else "Task"
        
        # Prepare data for unified display
        data = [{
            "Type": task_type,
            "Task": item.content,
            "Key": item.item_key,
            "Position": str(item.position),
            "Status": _get_status_display(item.status.value)
        }]
        
        columns = {
            "Type": {"style": "yellow"},
            "Task": {"style": "cyan"},
            "Key": {"style": "magenta"},
            "Position": {"style": "blue"},
            "Status": {"style": "green"}
        }
        
        _display_records(data, f"⏭️ Next Smart Task for list '{list_key}'", columns)
        
        if start and Confirm.ask("Start this task?"):
            manager.update_item_status(list_key, item.item_key, status='in_progress')
            console.print("[green]✅ Task started[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.group('state')
def item_state():
    """Manage completion states for TODO items"""
    pass


@item_state.command('list')
@click.argument('list_key')
@click.argument('item_key')
@click.pass_context
def state_list(ctx, list_key, item_key):
    """Show all completion states for an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        console.print(f"[bold]Completion states for '{item_key}':[/]")
        
        if not item.completion_states:
            console.print("[dim]No completion states set[/]")
            return
        
        for key, value in item.completion_states.items():
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}: {value}")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_state.command('clear')
@click.argument('list_key')
@click.argument('item_key')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def state_clear(ctx, list_key, item_key, force):
    """Clear all completion states from an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        if not item.completion_states:
            console.print("[dim]No completion states to clear[/]")
            return
        
        # Show current states
        console.print(f"[yellow]Current states for '{item_key}':[/]")
        for key, value in item.completion_states.items():
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}")
        
        if not force and not Confirm.ask("Clear all completion states?"):
            return
        
        # Clear all states
        updated_item = manager.clear_item_completion_states(list_key, item_key)
        console.print(f"[green]✅ Cleared all completion states from '{item_key}'[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item_state.command('remove')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('state_keys', nargs=-1, required=True)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def state_remove(ctx, list_key, item_key, state_keys, force):
    """Remove specific completion states from an item"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        if not item.completion_states:
            console.print("[dim]No completion states to remove[/]")
            return
        
        # Check which keys exist
        existing_keys = []
        missing_keys = []
        for key in state_keys:
            if key in item.completion_states:
                existing_keys.append(key)
            else:
                missing_keys.append(key)
        
        if missing_keys:
            console.print(f"[yellow]Warning: Keys not found: {', '.join(missing_keys)}[/]")
        
        if not existing_keys:
            console.print("[red]No valid state keys found to remove[/]")
            return
        
        # Show states to be removed
        console.print(f"[yellow]Removing states from '{item_key}':[/]")
        for key in existing_keys:
            value = item.completion_states[key]
            icon = "✅" if value else "❌"
            console.print(f"  {icon} {key}")
        
        if not force and not Confirm.ask(f"Remove {len(existing_keys)} state(s)?"):
            return
        
        # Remove specific states
        updated_item = manager.clear_item_completion_states(list_key, item_key, existing_keys)
        console.print(f"[green]✅ Removed {len(existing_keys)} completion state(s) from '{item_key}'[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('delete')
@click.argument('list_key')
@click.argument('item_key')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def item_delete(ctx, list_key, item_key, force):
    """Delete an item from a TODO list permanently"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        # Get item details for confirmation
        item = manager.get_item(list_key, item_key)
        if not item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        # Show what will be deleted
        console.print(f"[yellow]About to delete:[/] {item.content}")
        console.print(f"[yellow]From list:[/] {list_key}")
        
        # Confirm deletion unless force flag is used
        if not force and not Confirm.ask("[red]Are you sure you want to delete this item? This cannot be undone"):
            console.print("[yellow]Deletion cancelled[/]")
            return
        
        # Delete the item
        success = manager.delete_item(list_key, item_key)
        if success:
            console.print(f"[green]✅ Item '{item_key}' deleted from list '{list_key}'[/]")
        else:
            console.print(f"[red]❌ Failed to delete item '{item_key}'[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('edit')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('new_content')
@click.pass_context
def item_edit(ctx, list_key, item_key, new_content):
    """Edit the content/description of a TODO item"""
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        # Get current item
        current_item = manager.get_item(list_key, item_key)
        if not current_item:
            console.print(f"[red]Item '{item_key}' not found in list '{list_key}'[/]")
            return
        
        # Show changes
        console.print(f"[yellow]Old content:[/] {current_item.content}")
        console.print(f"[green]New content:[/] {new_content}")
        
        # Update the content
        updated_item = manager.update_item_content(list_key, item_key, new_content)
        console.print(f"[green]✅ Content updated for item '{item_key}' in list '{list_key}'[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@item.command('find')
@click.argument('list_key')
@click.option('--property', 'property_key', required=True, help='Property name to search for')
@click.option('--value', 'property_value', required=True, help='Property value to match')
@click.option('--limit', type=int, help='Maximum number of results (default: all)')
@click.option('--first', is_flag=True, help='Return only first result (limit=1)')
@click.pass_context
def item_find(ctx, list_key, property_key, property_value, limit, first):
    """Find items by property value
    
    Examples:
      todoit item find mylist --property status --value reviewed
      todoit item find mylist --property issue_id --value 123 --first
      todoit item find mylist --property priority --value high --limit 5
    """
    manager = get_manager(ctx.obj['db_path'])
    
    # Check if list is accessible based on FORCE_TAGS (environment isolation)
    if not _check_list_access(manager, list_key):
        console.print(f"[red]List '{list_key}' not found or not accessible[/]")
        console.print("[dim]Check your TODOIT_FORCE_TAGS environment variable if using environment isolation[/]")
        return
    
    try:
        # Determine actual limit
        actual_limit = None
        if first:
            actual_limit = 1
        elif limit:
            actual_limit = limit
        
        # Search for items
        items = manager.find_items_by_property(list_key, property_key, property_value, actual_limit)
        
        if not items:
            # Use unified display for empty result
            _display_records([], f"🔍 Search Results for {property_key}='{property_value}' in '{list_key}'", {})
            return
        
        # Prepare data for unified display
        data = []
        for item in items:
            data.append({
                "Item Key": item.item_key,
                "Content": item.content,
                "Status": _get_status_display(item.status.value),
                "Position": str(item.position),
                "Created": item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "N/A"
            })
        
        # Define column styling
        columns = {
            "Item Key": {"style": "cyan", "width": 15},
            "Content": {"style": "white"},
            "Status": {"style": "yellow", "width": 12},
            "Position": {"style": "blue", "width": 8},
            "Created": {"style": "dim", "width": 16}
        }
        
        # Create title with search info
        title = f"🔍 Found {len(items)} item(s) with {property_key}='{property_value}' in '{list_key}'"
        if actual_limit:
            title += f" (limit: {actual_limit})"
        
        # Use unified display system
        _display_records(data, title, columns)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")