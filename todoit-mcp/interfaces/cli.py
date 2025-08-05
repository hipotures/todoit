"""
TODOIT CLI
Command Line Interface with Rich for better presentation
"""
import click
import json
import os
from typing import Optional, List
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


def get_manager(db_path: Optional[str]) -> TodoManager:
    """Get TodoManager instance"""
    if db_path == 'todoit.db':
        # Use default if user didn't specify custom path
        return TodoManager()
    return TodoManager(db_path)


# === Main command group ===

@click.group()
@click.option('--db', default='todoit.db', help='Path to database file (default: ~/.todoit/todoit.db)')
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

@cli.group()
def list():
    """Manage TODO lists"""
    pass


@list.command('create')
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


@list.command('show')
@click.argument('list_key')
@click.option('--tree', is_flag=True, help='Display as tree')
@click.pass_context
def list_show(ctx, list_key, tree):
    """Show list details"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        todo_list = manager.get_list(list_key)
        if not todo_list:
            console.print(f"[red]List '{list_key}' not found[/]")
            return
        
        items = manager.get_list_items(list_key)
        
        if tree:
            # Tree view
            tree_view = Tree(f"📋 {todo_list.title} ({todo_list.list_key})")
            
            for item in items:
                status_icon = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(item.status.value, '❓')
                
                node = tree_view.add(f"{status_icon} {item.content}")
                
                # Add completion states if they exist
                if item.completion_states:
                    for state, value in item.completion_states.items():
                        if isinstance(value, bool):
                            icon = '✅' if value else '❌'
                            node.add(f"{icon} {state}")
                        else:
                            node.add(f"📝 {state}: {value}")
            
            # Add list properties to tree if any
            properties = manager.get_list_properties(list_key)
            if properties:
                props_node = tree_view.add("🔧 Properties")
                for key, value in properties.items():
                    display_value = value if len(value) <= 40 else value[:37] + "..."
                    props_node.add(f"{key}: {display_value}")
            
            console.print(tree_view)
        else:
            # Table view
            table = Table(title=f"📋 {todo_list.title} (ID: {todo_list.id})", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Key", style="magenta")
            table.add_column("Task", style="white")
            table.add_column("Status", style="yellow")
            table.add_column("States", style="blue")
            
            for item in items:
                status_icon = {
                    'pending': '⏳ Pending',
                    'in_progress': '🔄 In Progress', 
                    'completed': '✅ Completed',
                    'failed': '❌ Failed'
                }.get(item.status.value, f'❓ {item.status.value}')
                
                status_style = {
                    'pending': 'yellow',
                    'in_progress': 'blue', 
                    'completed': 'green',
                    'failed': 'red'
                }.get(item.status.value, 'white')
                
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
                
                table.add_row(
                    str(item.position),
                    item.item_key,
                    item.content,
                    f"[{status_style}]{status_icon}[/]",
                    states_str
                )
            
            console.print(table)
            
            # Show list properties if any
            properties = manager.get_list_properties(list_key)
            if properties:
                prop_table = Table(title="Properties", box=box.SIMPLE)
                prop_table.add_column("Key", style="cyan", width=20)
                prop_table.add_column("Value", style="white")
                
                for key, value in properties.items():
                    # Truncate long values for display
                    display_value = value if len(value) <= 60 else value[:57] + "..."
                    prop_table.add_row(key, display_value)
                
                console.print()
                console.print(prop_table)
            
            # Show progress
            progress = manager.get_progress(list_key)
            console.print(f"\n[bold]Progress:[/] {progress.completion_percentage:.1f}% "
                         f"({progress.completed}/{progress.total})")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list.command('all')
@click.option('--limit', type=int, help='Limit number of results')
@click.pass_context
def list_all(ctx, limit):
    """List all TODO lists"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        lists = manager.list_all(limit=limit)
        
        table = Table(title="📋 All TODO Lists", box=box.ROUNDED)
        table.add_column("ID", style="dim", width=4)
        table.add_column("Key", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Type", style="yellow")
        table.add_column("Items", style="green")
        table.add_column("Completed", style="blue")
        table.add_column("Progress", style="magenta")
        
        for todo_list in lists:
            progress = manager.get_progress(todo_list.list_key)
            table.add_row(
                str(todo_list.id),
                todo_list.list_key,
                todo_list.title,
                todo_list.list_type,
                str(progress.total),
                str(progress.completed),
                f"{progress.completion_percentage:.1f}%"
            )
        
        console.print(table)
        console.print(f"\n[bold]Total lists:[/] {len(lists)}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@list.command('delete')
@click.argument('list_key')
@click.option('--force', is_flag=True, help='Force deletion')
@click.pass_context
def list_delete(ctx, list_key, force):
    """Delete TODO list (with dependency validation)"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        todo_list = manager.get_list(list_key)
        if not todo_list:
            console.print(f"[red]List '{list_key}' not found[/]")
            return
        
        if not force and not Confirm.ask(f"Delete list '{list_key}'?"):
            return
        
        manager.delete_list(list_key)
        console.print(f"[green]✅ Deleted list '{list_key}'[/]")
        
    except ValueError as e:
        console.print(f"[bold red]❌ {e}[/]")
        console.print("[yellow]Hint: Delete dependent lists first[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


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


# === Property management commands ===

@cli.group()
def property():
    """List property management"""
    pass


@property.command('set')
@click.argument('list_key')
@click.argument('property_key')
@click.argument('property_value')
@click.pass_context
def property_set(ctx, list_key, property_key, property_value):
    """Set a property for a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        property_obj = manager.set_list_property(list_key, property_key, property_value)
        console.print(f"[green]✅ Set property '{property_key}' = '{property_value}' for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@property.command('get')
@click.argument('list_key')
@click.argument('property_key')
@click.pass_context
def property_get(ctx, list_key, property_key):
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


@property.command('list')
@click.argument('list_key')
@click.pass_context
def property_list(ctx, list_key):
    """List all properties for a list"""
    manager = get_manager(ctx.obj['db_path'])
    
    try:
        properties = manager.get_list_properties(list_key)
        if properties:
            prop_table = Table(title=f"Properties for list '{list_key}'", box=box.SIMPLE)
            prop_table.add_column("Key", style="cyan", width=20)
            prop_table.add_column("Value", style="white")
            
            for key, value in properties.items():
                prop_table.add_row(key, value)
            
            console.print(prop_table)
        else:
            console.print(f"[yellow]No properties found for list '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/] {e}")


@property.command('delete')
@click.argument('list_key')
@click.argument('property_key')
@click.pass_context
def property_delete(ctx, list_key, property_key):
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
[bold]Available commands:[/]
  lists          - Show all lists
  show <key>     - Show list details
  next <key>     - Next task from list
  complete <key> <item> - Mark task as completed  
  progress <key> - Show list progress
  help          - This help
  exit          - Exit
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


if __name__ == '__main__':
    cli()