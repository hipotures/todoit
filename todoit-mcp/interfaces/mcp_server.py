"""
TODOIT MCP Server
MCP (Model Context Protocol) interface for TodoManager
"""
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

from core.manager import TodoManager

# Initialize FastMCP server
mcp = FastMCP("todoit-mcp")

# Global manager instance
manager = None

def init_manager(db_path: Optional[str] = None):
    """Initialize the TodoManager instance"""
    global manager
    if manager is None:
        manager = TodoManager(db_path)
    return manager

# === ETAP 1: 10 kluczowych funkcji ===

@mcp.tool()
async def todo_create_list(list_key: str, title: str, items: Optional[List[str]] = None, list_type: str = "sequential", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new TODO list with optional initial items.
    
    Args:
        list_key: Unique identifier for the list (required)
        title: Display title for the list (required) 
        items: Optional list of initial todo items to add
        list_type: List organization type, defaults to "sequential"
        metadata: Optional dictionary of custom metadata for the list
        
    Returns:
        Dictionary with success status and created list details
    """
    try:
        mgr = init_manager()
        if metadata is None:
            metadata = {}
        todo_list = mgr.create_list(
            list_key=list_key,
            title=title,
            items=items,
            list_type=list_type,
            metadata=metadata
        )
        return {
            "success": True,
            "list": todo_list.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_list(key: str) -> Dict[str, Any]:
    """Get TODO list by key or ID.
    
    Args:
        key: List key or ID to retrieve (required)
        
    Returns:
        Dictionary with success status and list details if found
    """
    try:
        mgr = init_manager()
        todo_list = mgr.get_list(key)
        if todo_list:
            return {
                "success": True,
                "list": todo_list.to_dict()
            }
        else:
            return {
                "success": False,
                "error": f"List '{key}' not found"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_delete_list(key: str) -> Dict[str, Any]:
    """Delete TODO list with dependency validation.
    
    Args:
        key: List key or ID to delete (required)
        
    Returns:
        Dictionary with success status and deletion confirmation
    """
    try:
        mgr = init_manager()
        success = mgr.delete_list(key)
        return {
            "success": success,
            "message": f"List '{key}' deleted successfully" if success else "List not found"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_list_all(limit: Optional[int] = None) -> Dict[str, Any]:
    """List all TODO lists in the database.
    
    Args:
        limit: Optional maximum number of lists to return
        
    Returns:
        Dictionary with success status, list of all todo lists, and count
    """
    try:
        mgr = init_manager()
        lists = mgr.list_all(limit=limit)
        return {
            "success": True,
            "lists": [todo_list.to_dict() for todo_list in lists],
            "count": len(lists)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_add_item(list_key: str, item_key: str, content: str, position: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add item to TODO list.
    
    Args:
        list_key: Key of the list to add item to (required)
        item_key: Unique key for the new item (required)
        content: Text content of the todo item (required)
        position: Optional position to insert item at
        metadata: Optional dictionary of custom metadata for the item
        
    Returns:
        Dictionary with success status and created item details
    """
    try:
        mgr = init_manager()
        if metadata is None:
            metadata = {}
        item = mgr.add_item(
            list_key=list_key,
            item_key=item_key,
            content=content,
            position=position,
            metadata=metadata
        )
        return {
            "success": True,
            "item": item.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_update_item_status(list_key: str, item_key: str, status: Optional[str] = None, completion_states: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update item status with multi-state support.
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to update (required)
        status: New status to set (pending, in_progress, completed, etc.)
        completion_states: Optional dictionary of completion state details
        
    Returns:
        Dictionary with success status and updated item details
    """
    try:
        mgr = init_manager()
        item = mgr.update_item_status(
            list_key=list_key,
            item_key=item_key,
            status=status,
            completion_states=completion_states
        )
        return {
            "success": True,
            "item": item.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_next_pending(list_key: str, respect_dependencies: bool = True) -> Dict[str, Any]:
    """Get next pending item to work on from a list.
    
    Args:
        list_key: Key of the list to get next item from (required)
        respect_dependencies: Whether to consider item dependencies when selecting next item
        
    Returns:
        Dictionary with success status and next available item or null if none
    """
    try:
        mgr = init_manager()
        item = mgr.get_next_pending(
            list_key=list_key,
            respect_dependencies=respect_dependencies
        )
        if item:
            return {
                "success": True,
                "item": item.to_dict()
            }
        else:
            return {
                "success": True,
                "item": None,
                "message": "No pending items available"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_progress(list_key: str) -> Dict[str, Any]:
    """Get progress statistics for a todo list.
    
    Args:
        list_key: Key of the list to get progress for (required)
        
    Returns:
        Dictionary with success status and progress statistics (total, completed, percentage)
    """
    try:
        mgr = init_manager()
        progress = mgr.get_progress(list_key)
        return {
            "success": True,
            "progress": progress.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_import_from_markdown(file_path: str, base_key: Optional[str] = None) -> Dict[str, Any]:
    """Import todo lists from markdown file with multi-column support.
    
    Args:
        file_path: Path to the markdown file to import (required)
        base_key: Optional base key prefix for imported lists
        
    Returns:
        Dictionary with success status, imported lists, count, and confirmation message
    """
    try:
        mgr = init_manager()
        lists = mgr.import_from_markdown(
            file_path=file_path,
            base_key=base_key
        )
        return {
            "success": True,
            "lists": [todo_list.to_dict() for todo_list in lists],
            "count": len(lists),
            "message": f"Imported {len(lists)} list(s) from {file_path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_export_to_markdown(list_key: str, file_path: str) -> Dict[str, Any]:
    """Export todo list to markdown format with [x] checkboxes.
    
    Args:
        list_key: Key of the list to export (required)
        file_path: Path where to save the markdown file (required)
        
    Returns:
        Dictionary with success status and export confirmation message
    """
    try:
        mgr = init_manager()
        mgr.export_to_markdown(
            list_key=list_key,
            file_path=file_path
        )
        return {
            "success": True,
            "message": f"List '{list_key}' exported to {file_path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# === Funkcje pomocnicze ===

@mcp.tool()
async def todo_get_item(list_key: str, item_key: str) -> Dict[str, Any]:
    """Get specific todo item from a list.
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to retrieve (required)
        
    Returns:
        Dictionary with success status and item details if found
    """
    try:
        mgr = init_manager()
        item = mgr.get_item(
            list_key=list_key,
            item_key=item_key
        )
        if item:
            return {
                "success": True,
                "item": item.to_dict()
            }
        else:
            return {
                "success": False,
                "error": f"Item '{item_key}' not found in list '{list_key}'"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_list_items(list_key: str, status: Optional[str] = None) -> Dict[str, Any]:
    """Get all items from a todo list with optional status filtering.
    
    Args:
        list_key: Key of the list to get items from (required)
        status: Optional status filter (pending, completed, in_progress, etc.)
        
    Returns:
        Dictionary with success status, list of items, and count
    """
    try:
        mgr = init_manager()
        items = mgr.get_list_items(
            list_key=list_key,
            status=status
        )
        return {
            "success": True,
            "items": [item.to_dict() for item in items],
            "count": len(items)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_create_list_relation(source_list_id: int, target_list_id: int, relation_type: str, relation_key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a relationship between two todo lists.
    
    Args:
        source_list_id: ID of the source list (required)
        target_list_id: ID of the target list (required)
        relation_type: Type of relationship (e.g., 'project', 'dependency') (required)
        relation_key: Optional key to group related lists
        metadata: Optional dictionary of custom metadata for the relation
        
    Returns:
        Dictionary with success status and created relation details
    """
    try:
        mgr = init_manager()
        if metadata is None:
            metadata = {}
        relation = mgr.create_list_relation(
            source_list_id=source_list_id,
            target_list_id=target_list_id,
            relation_type=relation_type,
            relation_key=relation_key,
            metadata=metadata
        )
        return {
            "success": True,
            "relation": relation.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_lists_by_relation(relation_type: str, relation_key: str) -> Dict[str, Any]:
    """Get todo lists filtered by relation type and key.
    
    Args:
        relation_type: Type of relationship to filter by (required)
        relation_key: Specific key to match within the relation type (required)
        
    Returns:
        Dictionary with success status, list of matching todo lists, and count
    """
    try:
        mgr = init_manager()
        lists = mgr.get_lists_by_relation(
            relation_type=relation_type,
            relation_key=relation_key
        )
        return {
            "success": True,
            "lists": [todo_list.to_dict() for todo_list in lists],
            "count": len(lists)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_get_item_history(list_key: str, item_key: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """Get complete change history for a specific todo item.
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to get history for (required)
        limit: Optional maximum number of history entries to return
        
    Returns:
        Dictionary with success status, history entries, and count
    """
    try:
        mgr = init_manager()
        history = mgr.get_item_history(
            list_key=list_key,
            item_key=item_key,
            limit=limit
        )
        return {
            "success": True,
            "history": [entry.to_dict() for entry in history],
            "count": len(history)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# === Convenient wrapper tools ===

@mcp.tool()
async def todo_quick_add(list_key: str, items: List[str]) -> Dict[str, Any]:
    """Quick add multiple todo items to a list at once.
    
    Args:
        list_key: Key of the list to add items to (required)
        items: List of item contents to add (required)
        
    Returns:
        Dictionary with success status, created items, and count
    """
    try:
        mgr = init_manager()
        created_items = []
        for i, content in enumerate(items):
            item_key = f"quick_item_{i+1}_{len(content)}"  # Simple unique key
            item = mgr.add_item(
                list_key=list_key,
                item_key=item_key,
                content=content
            )
            created_items.append(item.to_dict())
        
        return {
            "success": True,
            "items": created_items,
            "count": len(created_items)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_mark_completed(list_key: str, item_key: str) -> Dict[str, Any]:
    """Mark a todo item as completed (convenience shortcut).
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to mark as completed (required)
        
    Returns:
        Dictionary with success status, updated item details, and confirmation message
    """
    try:
        mgr = init_manager()
        item = mgr.update_item_status(
            list_key=list_key,
            item_key=item_key,
            status="completed"
        )
        return {
            "success": True,
            "item": item.to_dict(),
            "message": f"Item '{item_key}' marked as completed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_start_item(list_key: str, item_key: str) -> Dict[str, Any]:
    """Start working on a todo item (convenience shortcut).
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to start working on (required)
        
    Returns:
        Dictionary with success status, updated item details, and confirmation message
    """
    try:
        mgr = init_manager()
        item = mgr.update_item_status(
            list_key=list_key,
            item_key=item_key,
            status="in_progress"
        )
        return {
            "success": True,
            "item": item.to_dict(),
            "message": f"Started working on '{item_key}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def todo_project_overview(project_key: str) -> Dict[str, Any]:
    """Get comprehensive overview of a project with multiple todo lists.
    
    Args:
        project_key: Key of the project to get overview for (required)
        
    Returns:
        Dictionary with success status and detailed project overview including:
        - All lists in the project
        - Progress statistics for each list
        - Overall project progress and totals
    """
    try:
        mgr = init_manager()
        
        # Get lists by project relation
        lists = mgr.get_lists_by_relation("project", project_key)
        
        overview = {
            "project_key": project_key,
            "lists": [],
            "total_items": 0,
            "total_completed": 0,
            "overall_progress": 0.0
        }
        
        total_items = 0
        total_completed = 0
        
        for todo_list in lists:
            progress = mgr.get_progress(todo_list.list_key)
            
            list_info = {
                "list": todo_list.to_dict(),
                "progress": progress.to_dict()
            }
            
            overview["lists"].append(list_info)
            total_items += progress.total
            total_completed += progress.completed
        
        if total_items > 0:
            overview["overall_progress"] = (total_completed / total_items) * 100
        
        overview["total_items"] = total_items
        overview["total_completed"] = total_completed
        
        return {
            "success": True,
            "overview": overview
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize the manager for standalone testing
    init_manager()
    # Run the MCP server
    try:
        mcp.run()
    except KeyboardInterrupt:
        sys.exit(0)