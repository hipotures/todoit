"""
Dependency management commands for TODOIT CLI
Handles cross-list dependencies and graph visualization
"""
import click
from rich.console import Console
from rich.prompt import Confirm

from .display import _get_status_icon, _get_status_display, console

def get_manager(db_path):
    """Get TodoManager instance - imported from main cli.py"""
    from core.manager import TodoManager
    if db_path == 'todoit.db':
        return TodoManager()
    return TodoManager(db_path)


def _parse_item_reference(ref: str) -> tuple:
    """Parse list:item reference like 'backend:auth_api'"""
    if ':' not in ref:
        raise ValueError(f"Invalid reference format '{ref}'. Expected 'list_key:item_key'")
    parts = ref.split(':', 1)
    return parts[0], parts[1]


@click.group()
def dep():
    """Cross-list dependency management (Phase 2)"""
    pass


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