#!/usr/bin/env python3
"""
Example script showing bash completion for todoit list keys
Usage: 
1. Run script: python completion_example.py
2. Enable completion: eval "$(_COMPLETION_EXAMPLE_COMPLETE=bash_source python completion_example.py)"
3. Test: python completion_example.py show 00<TAB>
"""

import click
from core.manager import TodoManager


def complete_list_keys(ctx, param, incomplete):
    """Complete list keys - called when user presses TAB"""
    try:
        # Get database path from context (or use default)
        db_path = ctx.obj.get('db_path', 'todoit.db') if ctx.obj else 'todoit.db'
        
        # Create manager and get all lists
        manager = TodoManager(db_path)
        lists = manager.list_all()
        
        # Return keys that start with what user typed
        matching_keys = [l.list_key for l in lists if l.list_key.startswith(incomplete)]
        
        return matching_keys
        
    except Exception:
        # If anything fails, return empty list
        return []


@click.group()
@click.option('--db', default='todoit.db', help='Database path')
@click.pass_context
def cli(ctx, db):
    """Example CLI with bash completion"""
    ctx.ensure_object(dict)
    ctx.obj['db_path'] = db


@cli.command()
@click.argument('list_key', shell_complete=complete_list_keys)
def show(list_key):
    """Show a todo list with completion support"""
    try:
        manager = TodoManager()
        todo_list = manager.get_list(list_key)
        
        if not todo_list:
            click.echo(f"List '{list_key}' not found")
            return
            
        click.echo(f"Found list: {todo_list.title}")
        items = manager.get_list_items(list_key)
        click.echo(f"Items: {len(items)}")
        
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.command()
def list():
    """List all available lists"""
    try:
        manager = TodoManager()
        lists = manager.list_all()
        
        click.echo("Available lists:")
        for todo_list in lists:
            click.echo(f"  {todo_list.list_key} - {todo_list.title}")
            
    except Exception as e:
        click.echo(f"Error: {e}")


if __name__ == '__main__':
    # Click 8.x+ automatically handles completion environment variables
    cli()