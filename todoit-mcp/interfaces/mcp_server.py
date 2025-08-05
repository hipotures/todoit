"""
TODOIT MCP Server
MCP (Model Context Protocol) interface for TodoManager
"""
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
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


def mcp_error_handler(func: Callable) -> Callable:
    """Decorator to handle MCP tool errors consistently."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            # Initialize manager and inject it into the function namespace
            mgr = init_manager()
            # Call the function with manager available in local scope
            return await func(*args, mgr=mgr, **kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e), "error_type": "validation"}
        except Exception as e:
            return {"success": False, "error": str(e), "error_type": "internal"}
    return wrapper

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

# === List Properties Functions ===

@mcp.tool()
@mcp_error_handler
async def todo_set_list_property(list_key: str, property_key: str, property_value: str, mgr=None) -> Dict[str, Any]:
    """Set a property for a list (create or update).
    
    Args:
        list_key: Key of the list to set property for (required)
        property_key: Name of the property (required)
        property_value: Value to set (required)
        
    Returns:
        Dictionary with success status and property details
    """
    property_obj = mgr.set_list_property(list_key, property_key, property_value)
    return {
        "success": True,
        "property": property_obj.to_dict()
    }

@mcp.tool()
@mcp_error_handler
async def todo_get_list_property(list_key: str, property_key: str, mgr=None) -> Dict[str, Any]:
    """Get a property value for a list.
    
    Args:
        list_key: Key of the list to get property from (required)
        property_key: Name of the property (required)
        
    Returns:
        Dictionary with success status and property value
    """
    value = mgr.get_list_property(list_key, property_key)
    if value is not None:
        return {
            "success": True,
            "property_key": property_key,
            "property_value": value
        }
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for list '{list_key}'"
        }

@mcp.tool()
@mcp_error_handler
async def todo_get_list_properties(list_key: str, mgr=None) -> Dict[str, Any]:
    """Get all properties for a list.
    
    Args:
        list_key: Key of the list to get properties from (required)
        
    Returns:
        Dictionary with success status and all properties as key-value pairs
    """
    properties = mgr.get_list_properties(list_key)
    return {
        "success": True,
        "list_key": list_key,
        "properties": properties,
        "count": len(properties)
    }

@mcp.tool()
@mcp_error_handler
async def todo_delete_list_property(list_key: str, property_key: str, mgr=None) -> Dict[str, Any]:
    """Delete a property from a list.
    
    Args:
        list_key: Key of the list to delete property from (required)
        property_key: Name of the property to delete (required)
        
    Returns:
        Dictionary with success status and confirmation message
    """
    success = mgr.delete_list_property(list_key, property_key)
    if success:
        return {
            "success": True,
            "message": f"Property '{property_key}' deleted from list '{list_key}'"
        }
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for list '{list_key}'"
        }


# ===== SUBTASK MANAGEMENT MCP TOOLS (Phase 1) =====

@mcp.tool()
@mcp_error_handler
async def todo_add_subtask(list_key: str, parent_key: str, subtask_key: str, content: str, metadata: Optional[Dict[str, Any]] = None, mgr=None) -> Dict[str, Any]:
    """Add a subtask to an existing task.
    
    Args:
        list_key: Key of the list containing the parent task (required)
        parent_key: Key of the parent task (required)
        subtask_key: Unique key for the new subtask (required)
        content: Content/description of the subtask (required)
        metadata: Optional metadata for the subtask
        
    Returns:
        Dictionary with success status and created subtask details
    """
    subtask = mgr.add_subtask(list_key, parent_key, subtask_key, content, metadata)
    return {
        "success": True,
        "subtask": subtask.to_dict(),
        "message": f"Subtask '{subtask_key}' added to '{parent_key}' in list '{list_key}'"
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_subtasks(list_key: str, parent_key: str, mgr=None) -> Dict[str, Any]:
    """Get all subtasks for a parent task.
    
    Args:
        list_key: Key of the list containing the parent task (required)
        parent_key: Key of the parent task (required)
        
    Returns:
        Dictionary with success status, subtasks list, and count
    """
    subtasks = mgr.get_subtasks(list_key, parent_key)
    return {
        "success": True,
        "subtasks": [subtask.to_dict() for subtask in subtasks],
        "count": len(subtasks),
        "parent_key": parent_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_item_hierarchy(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Get full hierarchy for an item (item + all subtasks recursively).
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to get hierarchy for (required)
        
    Returns:
        Dictionary with success status and hierarchical structure
    """
    hierarchy = mgr.get_item_hierarchy(list_key, item_key)
    return {
        "success": True,
        "hierarchy": hierarchy,
        "list_key": list_key,
        "root_item_key": item_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_move_to_subtask(list_key: str, item_key: str, new_parent_key: str, mgr=None) -> Dict[str, Any]:
    """Convert an existing task to be a subtask of another task.
    
    Args:
        list_key: Key of the list containing both items (required)
        item_key: Key of the item to move (required)
        new_parent_key: Key of the new parent task (required)
        
    Returns:
        Dictionary with success status and updated item details
    """
    moved_item = mgr.move_to_subtask(list_key, item_key, new_parent_key)
    return {
        "success": True,
        "moved_item": moved_item.to_dict(),
        "message": f"Item '{item_key}' moved to be subtask of '{new_parent_key}'"
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_next_pending_smart(list_key: str, mgr=None) -> Dict[str, Any]:
    """Get next pending item using smart subtask logic (subtasks before parents).
    
    Args:
        list_key: Key of the list to get next item from (required)
        
    Returns:
        Dictionary with success status and next available item or null if none
    """
    item = mgr.get_next_pending_with_subtasks(list_key)
    if item:
        return {
            "success": True,
            "next_item": item.to_dict(),
            "is_subtask": item.parent_item_id is not None,
            "message": f"Next smart task: {item.item_key}"
        }
    else:
        return {
            "success": True,
            "next_item": None,
            "message": f"No pending items in list '{list_key}'"
        }


@mcp.tool()
@mcp_error_handler
async def todo_can_complete_item(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Check if an item can be completed (no pending subtasks).
    
    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to check (required)
        
    Returns:
        Dictionary with completion check results
    """
    result = mgr.can_complete_item(list_key, item_key)
    return {
        "success": True,
        "can_complete": result["can_complete"],
        "details": result,
        "item_key": item_key
    }


# Enhanced existing tools to support hierarchy

@mcp.tool()
@mcp_error_handler  
async def todo_get_list_items_hierarchical(list_key: str, status: Optional[str] = None, mgr=None) -> Dict[str, Any]:
    """Get all items from a list with hierarchical organization.
    
    Args:
        list_key: Key of the list to get items from (required)
        status: Optional status filter (pending, completed, in_progress, etc.)
        
    Returns:
        Dictionary with success status, hierarchically organized items, and count
    """
    items = mgr.get_list_items(list_key, status)
    
    # Organize items hierarchically
    items_by_id = {item.id: item for item in items}
    root_items = []
    children_map = {}
    
    for item in items:
        if item.parent_item_id is None:
            root_items.append(item)
        else:
            if item.parent_item_id not in children_map:
                children_map[item.parent_item_id] = []
            children_map[item.parent_item_id].append(item)
    
    def build_hierarchy(item):
        item_dict = item.to_dict()
        children = children_map.get(item.id, [])
        if children:
            item_dict["subtasks"] = [build_hierarchy(child) for child in sorted(children, key=lambda x: x.position)]
        else:
            item_dict["subtasks"] = []
        return item_dict
    
    hierarchical_items = [build_hierarchy(item) for item in sorted(root_items, key=lambda x: x.position)]
    
    return {
        "success": True,
        "items": hierarchical_items,
        "total_count": len(items),
        "root_count": len(root_items),
        "status_filter": status,
        "list_key": list_key
    }


# ===== PHASE 2: CROSS-LIST DEPENDENCIES MCP TOOLS =====

@mcp.tool()
@mcp_error_handler
async def todo_add_item_dependency(dependent_list: str, dependent_item: str, 
                                  required_list: str, required_item: str,
                                  dependency_type: str = "blocks",
                                  metadata: Optional[Dict[str, Any]] = None, mgr=None) -> Dict[str, Any]:
    """Add dependency between tasks from different lists.
    
    Args:
        dependent_list: Key of list containing item that depends on another
        dependent_item: Key of item that depends on another  
        required_list: Key of list containing item that is required
        required_item: Key of item that is required
        dependency_type: Type of dependency (blocks, requires, related)
        metadata: Optional metadata for the dependency
        
    Returns:
        Dictionary with success status and dependency details
    """
    dependency = mgr.add_item_dependency(
        dependent_list=dependent_list,
        dependent_item=dependent_item,
        required_list=required_list,
        required_item=required_item,
        dependency_type=dependency_type,
        metadata=metadata
    )
    return {
        "success": True,
        "dependency": dependency.to_dict(),
        "message": f"Dependency added: {dependent_list}:{dependent_item} → {required_list}:{required_item}"
    }


@mcp.tool()
@mcp_error_handler
async def todo_remove_item_dependency(dependent_list: str, dependent_item: str,
                                     required_list: str, required_item: str, mgr=None) -> Dict[str, Any]:
    """Remove dependency between tasks from different lists.
    
    Args:
        dependent_list: Key of list containing dependent item
        dependent_item: Key of dependent item
        required_list: Key of list containing required item  
        required_item: Key of required item
        
    Returns:
        Dictionary with success status and confirmation
    """
    success = mgr.remove_item_dependency(
        dependent_list=dependent_list,
        dependent_item=dependent_item,
        required_list=required_list,
        required_item=required_item
    )
    return {
        "success": success,
        "message": f"Dependency {'removed' if success else 'not found'}: {dependent_list}:{dependent_item} → {required_list}:{required_item}"
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_item_blockers(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Get all items that block this item (uncompleted required items).
    
    Args:
        list_key: Key of list containing the item
        item_key: Key of item to check for blockers
        
    Returns:
        Dictionary with success status, blockers list, and blocking status
    """
    blockers = mgr.get_item_blockers(list_key, item_key)
    is_blocked = len(blockers) > 0
    
    return {
        "success": True,
        "blockers": [blocker.to_dict() for blocker in blockers],
        "is_blocked": is_blocked,
        "blocker_count": len(blockers),
        "list_key": list_key,
        "item_key": item_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_items_blocked_by(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Get all items blocked by this item.
    
    Args:
        list_key: Key of list containing the item
        item_key: Key of item to check what it blocks
        
    Returns:
        Dictionary with success status and list of blocked items
    """
    blocked_items = mgr.get_items_blocked_by(list_key, item_key)
    
    return {
        "success": True,
        "blocked_items": [item.to_dict() for item in blocked_items],
        "blocked_count": len(blocked_items),
        "list_key": list_key,
        "item_key": item_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_is_item_blocked(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Check if item is blocked by uncompleted cross-list dependencies.
    
    Args:
        list_key: Key of list containing the item
        item_key: Key of item to check
        
    Returns:
        Dictionary with success status and blocking information
    """
    is_blocked = mgr.is_item_blocked(list_key, item_key)
    
    result = {
        "success": True,
        "is_blocked": is_blocked,
        "list_key": list_key,
        "item_key": item_key
    }
    
    if is_blocked:
        blockers = mgr.get_item_blockers(list_key, item_key)
        result["blockers"] = [{"key": b.item_key, "content": b.content} for b in blockers]
    
    return result


@mcp.tool()
@mcp_error_handler
async def todo_can_start_item(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Check if item can be started (combines Phase 1 + Phase 2 logic).
    
    Args:
        list_key: Key of list containing the item
        item_key: Key of item to check
        
    Returns:
        Dictionary with detailed analysis of whether item can be started
    """
    analysis = mgr.can_start_item(list_key, item_key)
    
    return {
        "success": True,
        "analysis": analysis,
        "list_key": list_key,
        "item_key": item_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_cross_list_progress(project_key: str, mgr=None) -> Dict[str, Any]:
    """Get progress for all lists in a project with dependency information.
    
    Args:
        project_key: Key of project to analyze
        
    Returns:
        Dictionary with comprehensive project progress and dependency info
    """
    progress_info = mgr.get_cross_list_progress(project_key)
    
    return {
        "success": True,
        "project_progress": progress_info
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_dependency_graph(project_key: str, mgr=None) -> Dict[str, Any]:
    """Get dependency graph for visualization.
    
    Args:
        project_key: Key of project to get dependency graph for
        
    Returns:
        Dictionary with dependency graph data for visualization
    """
    graph_data = mgr.get_dependency_graph(project_key)
    
    return {
        "success": True,
        "graph": graph_data,
        "project_key": project_key
    }


@mcp.tool()
@mcp_error_handler
async def todo_get_next_pending_enhanced(list_key: str, respect_dependencies: bool = True,
                                        smart_subtasks: bool = False, mgr=None) -> Dict[str, Any]:
    """Get next pending item with enhanced Phase 2 logic (blocks + subtasks).
    
    Args:
        list_key: Key of list to get next item from
        respect_dependencies: Whether to consider cross-list dependencies
        smart_subtasks: Whether to use smart subtask prioritization
        
    Returns:
        Dictionary with next available item or null if none
    """
    item = mgr.get_next_pending(
        list_key=list_key,
        respect_dependencies=respect_dependencies,
        smart_subtasks=smart_subtasks
    )
    
    if item:
        # Get additional context
        is_blocked = mgr.is_item_blocked(list_key, item.item_key) if respect_dependencies else False
        is_subtask = getattr(item, 'parent_item_id', None) is not None
        
        return {
            "success": True,
            "next_item": item.to_dict(),
            "is_blocked": is_blocked,
            "is_subtask": is_subtask,
            "context": {
                "smart_subtasks_used": smart_subtasks,
                "dependencies_considered": respect_dependencies
            }
        }
    else:
        return {
            "success": True,
            "next_item": None,
            "message": f"No available items in list '{list_key}'"
        }


@mcp.tool()
@mcp_error_handler  
async def todo_get_comprehensive_status(list_key: str, mgr=None) -> Dict[str, Any]:
    """Get comprehensive Phase 3 status: hierarchies, dependencies, progress, and next task.
    
    Combines all Phase 1 (subtasks), Phase 2 (cross-list deps), and Phase 3 (smart algorithm) features.
    
    Args:
        list_key: Key of list to analyze
        
    Returns:
        Dictionary with comprehensive status including:
        - Enhanced progress stats (blocked, available, hierarchy info)
        - Next recommended task using Phase 3 smart algorithm  
        - List of blocked items with blocking reasons
        - Hierarchical item structure
        - Cross-list dependency summary
    """
    # Get enhanced progress stats (Phase 3)
    progress = mgr.get_progress(list_key)
    
    # Get next task using Phase 3 smart algorithm
    next_task = mgr.get_next_pending_with_subtasks(list_key)
    
    # Get hierarchical items structure
    items = mgr.get_list_items_hierarchical(list_key)
    
    # Get all items and their blocking status
    all_items = mgr.get_list_items(list_key)
    blocked_items = []
    available_items = []
    
    for item in all_items:
        if item.status == 'pending':
            can_start_info = mgr.can_start_item(list_key, item.item_key)
            if can_start_info['can_start']:
                available_items.append({
                    'key': item.item_key,
                    'content': item.content,
                    'position': item.position
                })
            else:
                blocked_items.append({
                    'key': item.item_key, 
                    'content': item.content,
                    'reason': can_start_info['reason'],
                    'blocked_by_dependencies': can_start_info['blocked_by_dependencies'],
                    'blocked_by_subtasks': can_start_info['blocked_by_subtasks'],
                    'blockers': can_start_info['blockers'],
                    'pending_subtasks': can_start_info['pending_subtasks']
                })
    
    # Get cross-list dependencies summary
    db_list = mgr.db.get_list_by_key(list_key)
    dependencies = mgr.db.get_all_dependencies_for_list(db_list.id) if db_list else []
    
    dependency_summary = {
        'total_dependencies': len(dependencies),
        'as_dependent': 0,  # How many items in this list depend on others
        'as_required': 0    # How many items in this list block others
    }
    
    for dep in dependencies:
        # Check if the dependent item is in this list
        dependent_item = mgr.db.get_item_by_id(dep.dependent_item_id)
        if dependent_item and dependent_item.list_id == db_list.id:
            dependency_summary['as_dependent'] += 1
        
        # Check if the required item is in this list  
        required_item = mgr.db.get_item_by_id(dep.required_item_id)
        if required_item and required_item.list_id == db_list.id:
            dependency_summary['as_required'] += 1
    
    return {
        "success": True,
        "list_key": list_key,
        "progress": progress.to_dict(),
        "next_task": next_task.to_dict() if next_task else None,
        "blocked_items": blocked_items,
        "available_items": available_items,
        "items_hierarchical": items,
        "dependency_summary": dependency_summary,
        "recommendations": {
            "action": "start_next" if next_task else "all_completed" if progress.total > 0 and progress.completed == progress.total else "add_items",
            "next_task_key": next_task.item_key if next_task else None,
            "blocked_count": len(blocked_items),
            "available_count": len(available_items)
        }
    }


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