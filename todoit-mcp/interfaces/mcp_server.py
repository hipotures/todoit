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
        if db_path is None:
            # Let TodoManager handle TODOIT_DB_PATH environment variable
            manager = TodoManager()
        else:
            manager = TodoManager(db_path)
    return manager


def mcp_error_handler(func: Callable) -> Callable:
    """Decorator to handle MCP tool errors consistently."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            # Initialize manager and inject it into the function namespace
            mgr = init_manager()
            # Remove mgr from kwargs to avoid conflicts
            kwargs.pop("mgr", None)
            # Call the function with manager available in local scope
            return await func(*args, mgr=mgr, **kwargs)
        except ValueError as e:
            return {"success": False, "error": str(e), "error_type": "validation"}
        except Exception as e:
            return {"success": False, "error": str(e), "error_type": "internal"}

    return wrapper


def map_item_content_to_title(item_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Map content field to title in item dictionary for consistent API."""
    if "content" in item_dict:
        item_dict["title"] = item_dict.pop("content")
    return item_dict


def clean_item_data(item_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove unnecessary fields from item data for MCP output."""
    # Essential fields only
    essential_fields = {
        "item_key": item_dict.get("item_key"),
        "content": item_dict.get("content"),
        "title": item_dict.get("title"),
        "status": item_dict.get("status"),
        "position": item_dict.get("position"),
    }
    
    # Add parent info only if it's a subtask
    if item_dict.get("parent_item_id"):
        essential_fields["is_subtask"] = True
    
    # Remove None values
    return {k: v for k, v in essential_fields.items() if v is not None}


def clean_to_dict_result(obj_dict: Dict[str, Any], object_type: str = "item") -> Dict[str, Any]:
    """Remove timestamps and unnecessary fields from .to_dict() results."""
    if object_type == "item":
        return clean_item_data(obj_dict)
    elif object_type == "list":
        # Keep only essential list fields
        essential_fields = {
            "list_key": obj_dict.get("list_key"),
            "title": obj_dict.get("title"),
            "description": obj_dict.get("description"),
            "list_type": obj_dict.get("list_type"),
        }
        return {k: v for k, v in essential_fields.items() if v is not None}
    elif object_type == "property":
        # Keep only essential property fields
        essential_fields = {
            "property_key": obj_dict.get("property_key"),
            "property_value": obj_dict.get("property_value"),
        }
        return {k: v for k, v in essential_fields.items() if v is not None}
    elif object_type == "tag":
        # Keep only essential tag fields
        essential_fields = {
            "name": obj_dict.get("name"),
            "color": obj_dict.get("color"),
        }
        return {k: v for k, v in essential_fields.items() if v is not None}
    elif object_type == "assignment":
        # Tag assignments don't need any specific data - just remove timestamps
        clean_dict = obj_dict.copy()
        for timestamp_field in ["assigned_at", "created_at", "updated_at"]:
            clean_dict.pop(timestamp_field, None)
        return clean_dict
    else:
        # For other objects (progress, dependencies, etc.) keep as-is but remove common timestamp fields
        clean_dict = obj_dict.copy()
        for timestamp_field in ["created_at", "updated_at", "started_at", "completed_at"]:
            clean_dict.pop(timestamp_field, None)
        return clean_dict


# === MCP TOOLS LEVEL CONFIGURATION ===
import os

# Get MCP tools level from environment variable (default: standard)
MCP_TOOLS_LEVEL = os.getenv("TODOIT_MCP_TOOLS_LEVEL", "standard").lower()

# Define tool sets for each level
TOOLS_MINIMAL = [
    # Core list operations (3)
    "todo_create_list",
    "todo_get_list",
    "todo_list_all",
    # Core item operations (4)
    "todo_add_item",
    "todo_update_item_status",
    "todo_get_list_items",
    "todo_get_item",
    # Essential workflow (2)
    "todo_get_next_pending",
    "todo_get_progress",
]

TOOLS_STANDARD = TOOLS_MINIMAL + [
    # Convenience operations (1)
    "todo_quick_add",
    # Basic properties (6)
    "todo_set_list_property",
    "todo_get_list_property",
    "todo_set_item_property",
    "todo_get_item_property",
    "todo_find_items_by_property",
    "todo_find_subitems_by_status",
    "todo_get_all_items_properties",
    # Basic tagging (2)
    "todo_create_tag",
    "todo_add_list_tag",
    # Rename operations (2)
    "todo_rename_item",
    "todo_rename_list",
]

# MAX level includes all tools (defined by registration, not exclusion)
TOOLS_MAX = "all"  # Special value meaning all registered tools


def should_register_tool(tool_name: str) -> bool:
    """Check if tool should be registered based on current MCP_TOOLS_LEVEL"""
    if MCP_TOOLS_LEVEL == "max":
        return True
    elif MCP_TOOLS_LEVEL == "standard":
        return tool_name in TOOLS_STANDARD
    elif MCP_TOOLS_LEVEL == "minimal":
        return tool_name in TOOLS_MINIMAL
    else:
        # Default to standard for unknown levels
        return tool_name in TOOLS_STANDARD


def conditional_tool(func: Callable) -> Callable:
    """Decorator to conditionally register MCP tool based on level configuration"""
    tool_name = func.__name__

    if should_register_tool(tool_name):
        # Register the tool normally
        return mcp.tool()(func)
    else:
        # Return the function undecorated (not registered with MCP)
        return func


# ═══════════════════════════════════════════════════════════════════════════════
# ███ MCP TOOLS IMPLEMENTATION - ORGANIZED BY LEVEL
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# ████ MINIMAL LEVEL TOOLS (9 tools) - Core functionality only
# ═══════════════════════════════════════════════════════════════════════════════
# Essential list operations: create, get, list_all
# Essential item operations: add, update_status, get_list_items, get_item
# Essential workflow: get_next_pending, get_progress, update_item_content


@conditional_tool
async def todo_create_list(
    list_key: str,
    title: str,
    items: Optional[List[str]] = None,
    list_type: str = "sequential",
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new TODO list with optional initial items.

    Args:
        list_key: Unique identifier for the list (required)
        title: Display title for the list (required)
        items: Optional list of initial todo items to add
        list_type: List organization type, defaults to "sequential"
        metadata: Optional dictionary of custom metadata for the list
        tags: Optional list of tag names to assign to the list (tags must already exist)

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
            metadata=metadata,
            tags=tags,
        )
        return {"success": True, "list": clean_to_dict_result(todo_list.to_dict(), "list")}
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
@mcp_error_handler
async def todo_get_list(
    list_key: str, 
    include_items: bool = True, 
    include_properties: bool = True,
    mgr=None
) -> Dict[str, Any]:
    """Get TODO list by key or ID with optional items and properties.

    Args:
        list_key: List key or ID to retrieve (required)
        include_items: Whether to include list items (default: True)
        include_properties: Whether to include list properties (default: True)

    Returns:
        Dictionary with success status, list details, and optionally items and properties
    """
    todo_list = mgr.get_list(list_key)
    if not todo_list:
        return {"success": False, "error": f"List '{list_key}' not found"}

    # Base response with list info
    response = {
        "success": True,
        "list": clean_to_dict_result(todo_list.to_dict(), "list")
    }

    # Add items if requested
    if include_items:
        items = mgr.get_list_items(todo_list.list_key)
        items_data = []
        for item in items:
            item_dict = {
                "item_key": item.item_key,
                "content": item.content,
                "status": item.status.value,
                "position": item.position,
                "parent_item_id": item.parent_item_id,
            }
            items_data.append(clean_item_data(item_dict))
        
        response["items"] = {
            "count": len(items_data),
            "data": items_data
        }

    # Add properties if requested
    if include_properties:
        properties = mgr.get_list_properties(todo_list.list_key)
        prop_data = [{"key": k, "value": v} for k, v in properties.items()] if properties else []
        response["properties"] = {
            "count": len(prop_data),
            "data": prop_data
        }

    return response


@conditional_tool
async def todo_delete_list(list_key: str) -> Dict[str, Any]:
    """Delete TODO list with dependency validation.

    Args:
        list_key: List key or ID to delete (required)

    Returns:
        Dictionary with success status and deletion confirmation
    """
    try:
        mgr = init_manager()
        success = mgr.delete_list(list_key)
        return {
            "success": success,
            "message": (
                f"List '{list_key}' deleted successfully" if success else "List not found"
            ),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
async def todo_archive_list(list_key: str, force: bool = False) -> Dict[str, Any]:
    """Archive a TODO list (hide from normal view).

    Args:
        list_key: Key of the list to archive (required)
        force: If True, force archiving even with incomplete tasks (default: False)

    Returns:
        Dictionary with success status and archived list details
    """
    try:
        mgr = init_manager()
        archived_list = mgr.archive_list(list_key, force=force)
        return {
            "success": True,
            "list": {
                "id": archived_list.id,
                "list_key": archived_list.list_key,
                "title": archived_list.title,
                "status": archived_list.status,
            },
            "message": f"List '{list_key}' archived successfully",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
async def todo_unarchive_list(list_key: str) -> Dict[str, Any]:
    """Unarchive a TODO list (restore to normal view).

    Args:
        list_key: Key of the list to unarchive (required)

    Returns:
        Dictionary with success status and unarchived list details
    """
    try:
        mgr = init_manager()
        unarchived_list = mgr.unarchive_list(list_key)
        return {
            "success": True,
            "list": {
                "id": unarchived_list.id,
                "list_key": unarchived_list.list_key,
                "title": unarchived_list.title,
                "status": unarchived_list.status,
            },
            "message": f"List '{list_key}' unarchived successfully",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}




@conditional_tool
@mcp_error_handler
async def todo_list_all(
    limit: Optional[int] = None,
    include_archived: bool = False,
    filter_tags: Optional[List[str]] = None,
    mgr=None,
) -> Dict[str, Any]:
    """List all TODO lists in the database with optional tag filtering.

    Args:
        limit: Optional maximum number of lists to return
        include_archived: Whether to include archived lists (default: False)
        filter_tags: Optional list of tag names to filter by (lists with ANY of these tags)

    Returns:
        Dictionary with success status, list of all todo lists with progress statistics, tags, and count
    """
    lists = mgr.list_all(
        limit=limit, include_archived=include_archived, filter_tags=filter_tags
    )

    # Enhance each list with progress statistics and tag information
    enhanced_lists = []
    for todo_list in lists:
        list_data = clean_to_dict_result(todo_list.to_dict(), "list")

        # Add progress statistics
        progress = mgr.get_progress(todo_list.list_key)
        list_data["progress"] = progress.to_dict()

        # Add tags information
        tags = mgr.get_tags_for_list(todo_list.list_key)
        list_data["tags"] = [clean_to_dict_result(tag.to_dict(), "tag") for tag in tags]

        enhanced_lists.append(list_data)

    response = {"success": True, "lists": enhanced_lists, "count": len(lists)}

    # Add filtering metadata if tags were used
    if filter_tags:
        response["filter_applied"] = {
            "tag_filter": filter_tags,
            "message": f"Filtered by tags: {', '.join(filter_tags)}",
        }

    return response


@conditional_tool
async def todo_add_item(
    list_key: str,
    item_key: str,
    title: str,
    position: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    subitem_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Add item or subitem to TODO list (unified smart command).

    Args:
        list_key: Key of the list to add item to (required)
        item_key: Unique key for the new item, or parent key if adding subitem (required)
        title: Text title of the todo item/subitem (required)
        position: Optional position to insert item at
        metadata: Optional dictionary of custom metadata for the item/subitem
        subitem_key: Optional subitem key. If provided, adds subitem to item_key as parent

    Returns:
        Dictionary with success status and created item/subitem details

    Examples:
        # Add item:
        await todo_add_item("project", "task1", "Main task")
        
        # Add subitem:
        await todo_add_item("project", "task1", "Sub work", subitem_key="subtask1")
    """
    try:
        mgr = init_manager()
        if metadata is None:
            metadata = {}
            
        if subitem_key is not None:
            # Add subitem: item_key becomes parent_key, subitem_key is the new subitem
            subitem = mgr.add_subitem(
                list_key=list_key,
                parent_key=item_key,
                subitem_key=subitem_key,
                content=title,  # Map title to content internally
                metadata=metadata,
            )
            return {
                "success": True, 
                "subitem": map_item_content_to_title(clean_to_dict_result(subitem.to_dict(), "item")),
                "message": f"Subitem '{subitem_key}' added to '{item_key}' in list '{list_key}'"
            }
        else:
            # Add regular item
            item = mgr.add_item(
                list_key=list_key,
                item_key=item_key,
                content=title,  # Map title to content internally
                position=position,
                metadata=metadata,
            )
            return {"success": True, "item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item"))}
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
async def todo_update_item_status(
    list_key: str,
    item_key: str,
    subitem_key: Optional[str] = None,
    status: Optional[str] = None,
    completion_states: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update item or subitem status with multi-state support.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to update, or parent item key if updating subitem (required)
        subitem_key: Optional subitem key. If provided, updates the subitem within the parent item.
        status: New status to set. Valid values:
                - 'pending': Task is waiting to be started
                - 'in_progress': Task is currently being worked on
                - 'completed': Task has been finished successfully
                - 'failed': Task could not be completed
        completion_states: Optional dictionary of completion state details for multi-state tracking

    Returns:
        Dictionary with success status and updated item details

    Examples:
        # Update item status
        await todo_update_item_status("project", "feature1", status="completed")
        
        # Update subitem status
        await todo_update_item_status("project", "feature1", subitem_key="step1", status="completed")
        
        # Update with completion states
        await todo_update_item_status("project", "feature1", status="in_progress", 
                                      completion_states={"coded": True, "tested": False})

    Note:
        Tasks with subtasks cannot have their status manually changed.
        Their status is automatically synchronized based on subtask statuses.
    """
    try:
        mgr = init_manager()
        
        item = mgr.update_item_status(
            list_key=list_key,
            item_key=item_key,
            subitem_key=subitem_key,
            status=status,
            completion_states=completion_states,
        )
        target_name = subitem_key if subitem_key else item_key
        target_type = "Subitem" if subitem_key else "Item"
        return {
            "success": True,
            "item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")),
            "message": f"{target_type} '{target_name}' status updated successfully",
        }
    except ValueError as e:
        error_msg = str(e)
        if "has subtasks" in error_msg:
            return {
                "success": False,
                "error": error_msg,
                "error_type": "status_sync_blocked",
                "message": "Tasks with subtasks have their status automatically managed. Change subtask statuses instead.",
            }
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
async def todo_get_next_pending(
    list_key: str, respect_dependencies: bool = True
) -> Dict[str, Any]:
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
            list_key=list_key, respect_dependencies=respect_dependencies
        )
        if item:
            return {"success": True, "item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item"))}
        else:
            return {
                "success": True,
                "item": None,
                "message": "No pending items available",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
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
        return {"success": True, "progress": progress.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
@mcp_error_handler
async def todo_report_errors(
    list_filter: Optional[str] = None, tag_filter: Optional[List[str]] = None, mgr=None
) -> Dict[str, Any]:
    """Generate report of all failed tasks across active lists with full context.

    Args:
        list_filter: Optional regex pattern to filter lists by list_key (e.g. "^\\d{4}_.*" for NNNN_*)
        tag_filter: Optional list of tag names to filter lists by

    Returns:
        Dictionary with success status, failed tasks data, and filtering metadata
    """
    # Get all active lists for metadata (with tag filtering if specified)
    all_active_lists = mgr.list_all(include_archived=False, filter_tags=tag_filter)

    # Get failed items with optional filtering
    failed_items = mgr.get_all_failed_items(
        list_filter=list_filter, tag_filter=tag_filter
    )

    # Count lists that matched the filter (if applied)
    lists_matched = len(all_active_lists)
    if list_filter:
        import re

        try:
            pattern = re.compile(list_filter)
            filtered_lists = [l for l in all_active_lists if pattern.match(l.list_key)]
            lists_matched = len(filtered_lists)
        except re.error:
            lists_matched = 0

    # Clean up failed items data - remove timestamps and unnecessary fields
    cleaned_failed_items = []
    for item in failed_items:
        clean_item = {
            "item_key": item.get("item_key"),
            "content": item.get("content"), 
            "status": item.get("status"),
            "position": item.get("position"),
        }
        if item.get("parent_item_id"):
            clean_item["is_subtask"] = True
        cleaned_failed_items.append({k: v for k, v in clean_item.items() if v is not None})

    metadata = {
        "lists_scanned": len(all_active_lists),
        "lists_matched": lists_matched,
        "unique_lists_with_failures": len(
            set(item["list_key"] for item in failed_items)
        ),
    }

    # Add filter metadata
    if list_filter:
        metadata["list_filter_applied"] = list_filter
    if tag_filter:
        metadata["tag_filter_applied"] = tag_filter
        metadata["message"] = f"Filtered by tags: {', '.join(tag_filter)}"

    return {
        "success": True,
        "failed_tasks": cleaned_failed_items,
        "count": len(failed_items),
        "metadata": metadata,
    }


@conditional_tool
async def todo_import_from_markdown(
    file_path: str, base_key: Optional[str] = None
) -> Dict[str, Any]:
    """Import todo lists from markdown file with multi-column support.

    Args:
        file_path: Path to the markdown file to import (required)
        base_key: Optional base key prefix for imported lists

    Returns:
        Dictionary with success status, imported lists, count, and confirmation message
    """
    try:
        mgr = init_manager()
        lists = mgr.import_from_markdown(file_path=file_path, base_key=base_key)
        return {
            "success": True,
            "lists": [clean_to_dict_result(todo_list.to_dict(), "list") for todo_list in lists],
            "count": len(lists),
            "message": f"Imported {len(lists)} list(s) from {file_path}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
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
        mgr.export_to_markdown(list_key=list_key, file_path=file_path)
        return {
            "success": True,
            "message": f"List '{list_key}' exported to {file_path}",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# === Funkcje pomocnicze ===


@conditional_tool
async def todo_get_item(
    list_key: str, 
    item_key: str, 
    subitem_key: Optional[str] = None
) -> Dict[str, Any]:
    """Get specific todo item or its subitems from a list (unified smart command).

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to retrieve (required)
        subitem_key: Optional subitem key. If provided, returns specific subitem.
                     If "all", returns all subitems of the parent item.

    Returns:
        Dictionary with success status and item/subitem(s) details if found

    Examples:
        # Get item:
        await todo_get_item("project", "task1")
        
        # Get specific subitem:
        await todo_get_item("project", "task1", subitem_key="subtask1")
        
        # Get all subitems:
        await todo_get_item("project", "task1", subitem_key="all")
    """
    try:
        mgr = init_manager()
        
        if subitem_key is not None:
            if subitem_key == "all":
                # Get all subitems of the parent item
                subitems = mgr.get_subitems(list_key=list_key, parent_key=item_key)
                return {
                    "success": True,
                    "subitems": [map_item_content_to_title(clean_to_dict_result(subitem.to_dict(), "item")) for subitem in subitems],
                    "count": len(subitems),
                    "parent_key": item_key,
                }
            else:
                # Get specific subitem by key
                subitem = mgr.get_item(list_key=list_key, item_key=subitem_key, parent_item_key=item_key)
                if subitem:
                    return {"success": True, "subitem": map_item_content_to_title(clean_to_dict_result(subitem.to_dict(), "item"))}
                else:
                    return {
                        "success": False,
                        "error": f"Subitem '{subitem_key}' not found under parent '{item_key}' in list '{list_key}'",
                    }
        else:
            # Get regular item
            item = mgr.get_item(list_key=list_key, item_key=item_key)
            if item:
                return {"success": True, "item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item"))}
            else:
                return {
                    "success": False,
                    "error": f"Item '{item_key}' not found in list '{list_key}'",
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


@conditional_tool
async def todo_get_list_items(
    list_key: str, status: Optional[str] = None, limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get all items from a todo list with optional status filtering and limit.

    Args:
        list_key: Key of the list to get items from (required)
        status: Optional status filter (pending, completed, in_progress, etc.)
        limit: Optional maximum number of items to return

    Returns:
        Dictionary with success status, list of items, count, and whether more items exist
    """
    try:
        mgr = init_manager()

        # First, check if the list exists
        if not mgr.get_list(list_key):
            return {"success": False, "error": f"List '{list_key}' not found"}

        items = mgr.get_list_items(list_key=list_key, status=status, limit=limit)

        # Get the total count of items matching the filter, regardless of the limit
        total_count = len(mgr.get_list_items(list_key=list_key, status=status))

        # Determine if more items are available
        more_available = total_count > len(items)

        # Add list_key to each item's dict
        items_with_list_key = []
        for item in items:
            item_dict = map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item"))
            item_dict["list_key"] = list_key
            items_with_list_key.append(item_dict)

        return {
            "success": True,
            "items": items_with_list_key,
            "count": len(items),
            "more_available": more_available,
            "total_count": total_count,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}




@conditional_tool
@mcp_error_handler
async def todo_get_item_history(
    list_key: str, item_key: str, limit: Optional[int] = None, mgr=None
) -> Dict[str, Any]:
    """Get complete change history for a specific todo item.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to get history for (required)
        limit: Optional maximum number of history entries to return

    Returns:
        Dictionary with success status, history entries, and count
    """
    history = mgr.get_item_history(
        list_key=list_key, item_key=item_key, limit=limit
    )
    return {
        "success": True,
        "history": [entry.to_dict() for entry in history],
        "count": len(history),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ████ STANDARD LEVEL TOOLS (+13 tools) - Useful extensions
# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: quick_add, mark_completed, start_item
# Basic subtasks: add_subitem, get_subitems
# Archive management: archive_list, unarchive_list
# Basic properties: set/get list & item properties
# Basic tagging: create_tag, add_list_tag


@conditional_tool
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
            item_key = f"item_{i+1:04d}"  # Simple sequential numbering
            item = mgr.add_item(list_key=list_key, item_key=item_key, content=content)
            created_items.append(map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")))

        return {"success": True, "items": created_items, "count": len(created_items)}
    except Exception as e:
        return {"success": False, "error": str(e)}






@conditional_tool
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

        # Since list relations were removed, return empty lists
        lists = []

        overview = {
            "project_key": project_key,
            "lists": [],
            "total_items": 0,
            "total_completed": 0,
            "overall_progress": 0.0,
        }

        total_items = 0
        total_completed = 0

        for todo_list in lists:
            progress = mgr.get_progress(todo_list.list_key)

            list_info = {"list": clean_to_dict_result(todo_list.to_dict(), "list"), "progress": progress.to_dict()}

            overview["lists"].append(list_info)
            total_items += progress.total
            total_completed += progress.completed

        if total_items > 0:
            overview["overall_progress"] = (total_completed / total_items) * 100

        overview["total_items"] = total_items
        overview["total_completed"] = total_completed

        return {"success": True, "overview": overview}
    except Exception as e:
        return {"success": False, "error": str(e)}


# === List Properties Functions ===


@conditional_tool
@mcp_error_handler
async def todo_set_list_property(
    list_key: str, property_key: str, property_value: str, mgr=None
) -> Dict[str, Any]:
    """Set a property for a list (create or update).

    Args:
        list_key: Key of the list to set property for (required)
        property_key: Name of the property (required)
        property_value: Value to set (required)

    Returns:
        Dictionary with success status and property details
    """
    property_obj = mgr.set_list_property(list_key, property_key, property_value)
    return {"success": True, "property": clean_to_dict_result(property_obj.to_dict(), "property")}


@conditional_tool
@mcp_error_handler
async def todo_get_list_property(
    list_key: str, property_key: str, mgr=None
) -> Dict[str, Any]:
    """Get a property value for a list.

    Args:
        list_key: Key of the list to get property from (required)
        property_key: Name of the property (required)

    Returns:
        Dictionary with success status and property value
    """
    value = mgr.get_list_property(list_key, property_key)
    if value is not None:
        return {"success": True, "property_key": property_key, "property_value": value}
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for list '{list_key}'",
        }


@conditional_tool
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
        "count": len(properties),
    }


@conditional_tool
@mcp_error_handler
async def todo_delete_list_property(
    list_key: str, property_key: str, mgr=None
) -> Dict[str, Any]:
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
            "message": f"Property '{property_key}' deleted from list '{list_key}'",
        }
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for list '{list_key}'",
        }


# ===== ITEM PROPERTIES MCP TOOLS =====


@conditional_tool
@mcp_error_handler
async def todo_set_item_property(
    list_key: str, item_key: str, property_key: str, property_value: str, 
    parent_item_key: str = None, mgr=None
) -> Dict[str, Any]:
    """Set a property for an item or subitem (create or update).

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to set property for (required)
        property_key: Name of the property (required)
        property_value: Value to set (required)
        parent_item_key: Key of parent item (optional, for subitems)

    Returns:
        Dictionary with success status and property details
    """
    property_obj = mgr.set_item_property(
        list_key, item_key, property_key, property_value, parent_item_key
    )
    
    target = f"subitem '{item_key}' under item '{parent_item_key}'" if parent_item_key else f"item '{item_key}'"
    return {
        "success": True,
        "property": clean_to_dict_result(property_obj.to_dict(), "property"),
        "message": f"Property '{property_key}' set for {target} in list '{list_key}'",
    }


@conditional_tool
@mcp_error_handler
async def todo_get_item_property(
    list_key: str, item_key: str, property_key: str, parent_item_key: str = None, mgr=None
) -> Dict[str, Any]:
    """Get a property value for an item or subitem.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to get property from (required)
        property_key: Name of the property (required)
        parent_item_key: Key of parent item (optional, for subitems)

    Returns:
        Dictionary with success status and property value
    """
    value = mgr.get_item_property(list_key, item_key, property_key, parent_item_key)
    target = f"subitem '{item_key}' under item '{parent_item_key}'" if parent_item_key else f"item '{item_key}'"
    
    if value is not None:
        return {
            "success": True,
            "property_key": property_key,
            "property_value": value,
            "list_key": list_key,
            "item_key": item_key,
            "parent_item_key": parent_item_key,
        }
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for {target} in list '{list_key}'",
        }


@conditional_tool
@mcp_error_handler
async def todo_get_item_properties(
    list_key: str, item_key: str, parent_item_key: str = None, mgr=None
) -> Dict[str, Any]:
    """Get all properties for an item or subitem.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to get properties from (required)
        parent_item_key: Key of parent item (optional, for subitems)

    Returns:
        Dictionary with success status, properties, and count
    """
    properties = mgr.get_item_properties(list_key, item_key, parent_item_key)
    return {
        "success": True,
        "list_key": list_key,
        "item_key": item_key,
        "parent_item_key": parent_item_key,
        "properties": properties,
        "count": len(properties),
    }


@conditional_tool
@mcp_error_handler
async def todo_get_all_items_properties(
    list_key: str, status: Optional[str] = None, limit: Optional[int] = None, mgr=None
) -> Dict[str, Any]:
    """Get all properties for all items in a list, optionally filtered by status.

    Args:
        list_key: Key of the list to get item properties from (required)
        status: Optional status filter ('pending', 'in_progress', 'completed', 'failed').
               If not provided, returns properties for all items regardless of status.
        limit: Optional maximum number of items to return properties for

    Returns:
        Dictionary with success status, properties grouped by item_key, and metadata
    """
    properties = mgr.get_all_items_properties(list_key, status, limit)

    # Group properties by item_key with hierarchy support
    grouped_data = {}
    for prop in properties:
        item_key = prop["item_key"]
        parent_item_key = prop.get("parent_item_key")
        
        # Skip placeholder entries (like CLI JSON does)
        if prop["property_key"] == "—":
            continue
            
        if parent_item_key:
            # This is a subitem
            if parent_item_key not in grouped_data:
                grouped_data[parent_item_key] = {"properties": {}, "subitems": {}}
            if item_key not in grouped_data[parent_item_key]["subitems"]:
                grouped_data[parent_item_key]["subitems"][item_key] = {}
            grouped_data[parent_item_key]["subitems"][item_key][prop["property_key"]] = prop["property_value"]
        else:
            # This is a main item
            if item_key not in grouped_data:
                grouped_data[item_key] = {"properties": {}, "subitems": {}}
            grouped_data[item_key]["properties"][prop["property_key"]] = prop["property_value"]

    return {"success": True, "properties": grouped_data, "count": len(grouped_data)}


@conditional_tool
@mcp_error_handler
async def todo_delete_item_property(
    list_key: str, item_key: str, property_key: str, parent_item_key: str = None, mgr=None
) -> Dict[str, Any]:
    """Delete a property from an item or subitem.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to delete property from (required)
        property_key: Name of the property to delete (required)
        parent_item_key: Key of parent item (optional, for subitems)

    Returns:
        Dictionary with success status and confirmation message
    """
    success = mgr.delete_item_property(list_key, item_key, property_key, parent_item_key)
    target = f"subitem '{item_key}' under item '{parent_item_key}'" if parent_item_key else f"item '{item_key}'"
    
    if success:
        return {
            "success": True,
            "message": f"Property '{property_key}' deleted from {target} in list '{list_key}'",
        }
    else:
        return {
            "success": False,
            "error": f"Property '{property_key}' not found for {target} in list '{list_key}'",
        }


@conditional_tool
@mcp_error_handler
async def todo_find_items_by_property(
    list_key: str,
    property_key: str,
    property_value: str,
    limit: Optional[int] = None,
    mgr=None,
) -> Dict[str, Any]:
    """Find items by property value with optional limit.

    Args:
        list_key: Key of the list to search in (required)
        property_key: Name of the property to match (required)
        property_value: Value of the property to match (required)
        limit: Maximum number of results to return (optional, None = all)

    Returns:
        Dictionary with success status, found items, and count
    """
    items = mgr.find_items_by_property(list_key, property_key, property_value, limit)

    # Convert items to dictionaries
    items_data = []
    for item in items:
        item_dict = {
            "item_key": item.item_key,
            "content": item.content,
            "status": item.status.value,
            "position": item.position,
            "parent_item_id": item.parent_item_id,
        }
        item_dict = clean_item_data(item_dict)

        items_data.append(item_dict)

    return {
        "success": True,
        "items": items_data,
        "count": len(items_data),
        "list_key": list_key,
        "search_criteria": {
            "property_key": property_key,
            "property_value": property_value,
            "limit": limit,
        },
    }


@conditional_tool
@mcp_error_handler
async def todo_find_subitems_by_status(
    list_key: str,
    conditions: Dict[str, str],
    limit: int = 10,
    mgr=None,
) -> Dict[str, Any]:
    """Find grouped parent-subitem matches based on sibling status conditions.

    Args:
        list_key: Key of the list to search in (required)
        conditions: Dictionary of {subitem_key: expected_status} (required)
        limit: Maximum number of parent matches to return (default: 10)

    Returns:
        Dictionary with success status, grouped matches, and search details

    Example:
        # Find downloads ready to process (where generation is completed)
        {
            "list_key": "images",
            "conditions": {"generate": "completed", "download": "pending"},
            "limit": 5
        }
        
        # Returns:
        {
            "success": true,
            "matches": [
                {
                    "parent": {...},
                    "matching_subitems": [...]
                }
            ],
            "matches_count": 1
        }
    """
    matches = mgr.find_subitems_by_status(list_key, conditions, limit)

    def _convert_item_to_dict(item):
        """Helper to convert TodoItem to dictionary"""
        item_dict = {
            "item_key": item.item_key,
            "content": item.content,
            "status": item.status.value,
            "position": item.position,
            "parent_item_id": item.parent_item_id,
        }
        return clean_item_data(item_dict)

    # Convert matches to dictionaries
    matches_data = []
    for match in matches:
        parent_dict = _convert_item_to_dict(match["parent"])
        matching_subitems_data = [
            _convert_item_to_dict(subitem) 
            for subitem in match["matching_subitems"]
        ]
        
        matches_data.append({
            "parent": parent_dict,
            "matching_subitems": matching_subitems_data
        })

    return {
        "success": True,
        "matches": matches_data,
        "matches_count": len(matches_data),
        "list_key": list_key,
        "search_criteria": {
            "conditions": conditions,
            "limit": limit,
        },
    }


# ===== SUBTASK MANAGEMENT MCP TOOLS (Phase 1) =====





@conditional_tool
@mcp_error_handler
async def todo_get_item_hierarchy(
    list_key: str, item_key: str, mgr=None
) -> Dict[str, Any]:
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
        "root_item_key": item_key,
    }


@conditional_tool
@mcp_error_handler
async def todo_move_to_subitem(
    list_key: str, item_key: str, new_parent_key: str, mgr=None
) -> Dict[str, Any]:
    """Convert an existing task to be a subtask of another task.

    Args:
        list_key: Key of the list containing both items (required)
        item_key: Key of the item to move (required)
        new_parent_key: Key of the new parent task (required)

    Returns:
        Dictionary with success status and updated item details
    """
    moved_item = mgr.move_to_subitem(list_key, item_key, new_parent_key)
    return {
        "success": True,
        "moved_item": map_item_content_to_title(clean_to_dict_result(moved_item.to_dict(), "item")),
        "message": f"Item '{item_key}' moved to be subtask of '{new_parent_key}'",
    }


@conditional_tool
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
            "next_item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")),
            "is_subtask": item.parent_item_id is not None,
            "message": f"Next smart task: {item.item_key}",
        }
    else:
        return {
            "success": True,
            "next_item": None,
            "message": f"No pending items in list '{list_key}'",
        }


@conditional_tool
@mcp_error_handler
async def todo_can_complete_item(
    list_key: str, item_key: str, mgr=None
) -> Dict[str, Any]:
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
        "item_key": item_key,
    }




# ═══════════════════════════════════════════════════════════════════════════════
# ████ MAX LEVEL TOOLS (+32 tools) - Advanced & specialized functionality
# ═══════════════════════════════════════════════════════════════════════════════
# Cross-list dependencies, advanced subtask ops, smart algorithms,
# import/export, relations, comprehensive analytics, destructive operations

# ===== CROSS-LIST DEPENDENCIES =====


@conditional_tool
@mcp_error_handler
async def todo_add_item_dependency(
    dependent_list: str,
    dependent_item: str,
    required_list: str,
    required_item: str,
    dependency_type: str = "blocks",
    metadata: Optional[Dict[str, Any]] = None,
    mgr=None,
) -> Dict[str, Any]:
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
        metadata=metadata,
    )
    return {
        "success": True,
        "dependency": dependency.to_dict(),
        "message": f"Dependency added: {dependent_list}:{dependent_item} → {required_list}:{required_item}",
    }


@conditional_tool
@mcp_error_handler
async def todo_remove_item_dependency(
    dependent_list: str,
    dependent_item: str,
    required_list: str,
    required_item: str,
    mgr=None,
) -> Dict[str, Any]:
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
        required_item=required_item,
    )
    return {
        "success": success,
        "message": f"Dependency {'removed' if success else 'not found'}: {dependent_list}:{dependent_item} → {required_list}:{required_item}",
    }


@conditional_tool
@mcp_error_handler
async def todo_get_item_blockers(
    list_key: str, item_key: str, mgr=None
) -> Dict[str, Any]:
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
        "item_key": item_key,
    }


@conditional_tool
@mcp_error_handler
async def todo_get_items_blocked_by(
    list_key: str, item_key: str, mgr=None
) -> Dict[str, Any]:
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
        "blocked_items": [map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")) for item in blocked_items],
        "blocked_count": len(blocked_items),
        "list_key": list_key,
        "item_key": item_key,
    }


@conditional_tool
@mcp_error_handler
async def todo_is_item_blocked(
    list_key: str, item_key: str, mgr=None
) -> Dict[str, Any]:
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
        "item_key": item_key,
    }

    if is_blocked:
        blockers = mgr.get_item_blockers(list_key, item_key)
        result["blockers"] = [
            {"key": b.item_key, "content": b.content} for b in blockers
        ]

    return result


@conditional_tool
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
        "item_key": item_key,
    }


@conditional_tool
@mcp_error_handler
async def todo_get_cross_list_progress(project_key: str, mgr=None) -> Dict[str, Any]:
    """Get progress for all lists in a project with dependency information.

    Args:
        project_key: Key of project to analyze

    Returns:
        Dictionary with comprehensive project progress and dependency info
    """
    progress_info = mgr.get_cross_list_progress(project_key)

    return {"success": True, "project_progress": progress_info}


@conditional_tool
@mcp_error_handler
async def todo_get_dependency_graph(project_key: str, mgr=None) -> Dict[str, Any]:
    """Get dependency graph for visualization.

    Args:
        project_key: Key of project to get dependency graph for

    Returns:
        Dictionary with dependency graph data for visualization
    """
    graph_data = mgr.get_dependency_graph(project_key)

    return {"success": True, "graph": graph_data, "project_key": project_key}


@conditional_tool
@mcp_error_handler
async def todo_get_next_pending_enhanced(
    list_key: str,
    respect_dependencies: bool = True,
    smart_subtasks: bool = False,
    mgr=None,
) -> Dict[str, Any]:
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
        smart_subtasks=smart_subtasks,
    )

    if item:
        # Get additional context
        is_blocked = (
            mgr.is_item_blocked(list_key, item.item_key)
            if respect_dependencies
            else False
        )
        is_subtask = getattr(item, "parent_item_id", None) is not None

        return {
            "success": True,
            "next_item": map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")),
            "is_blocked": is_blocked,
            "is_subtask": is_subtask,
            "context": {
                "smart_subtasks_used": smart_subtasks,
                "dependencies_considered": respect_dependencies,
            },
        }
    else:
        return {
            "success": True,
            "next_item": None,
            "message": f"No available items in list '{list_key}'",
        }


@conditional_tool
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

    # Get items structure
    items = mgr.get_list_items(list_key)

    # Get all items and their blocking status
    all_items = mgr.get_list_items(list_key)
    blocked_items = []
    available_items = []

    for item in all_items:
        if item.status == "pending":
            can_start_info = mgr.can_start_item(list_key, item.item_key)
            if can_start_info["can_start"]:
                available_items.append(
                    {
                        "key": item.item_key,
                        "content": item.content,
                        "position": item.position,
                    }
                )
            else:
                blocked_items.append(
                    {
                        "key": item.item_key,
                        "content": item.content,
                        "reason": can_start_info["reason"],
                        "blocked_by_dependencies": can_start_info[
                            "blocked_by_dependencies"
                        ],
                        "blocked_by_subtasks": can_start_info["blocked_by_subtasks"],
                        "blockers": can_start_info["blockers"],
                        "pending_subtasks": can_start_info["pending_subtasks"],
                    }
                )

    # Get cross-list dependencies summary
    db_list = mgr.db.get_list_by_key(list_key)
    dependencies = mgr.db.get_all_dependencies_for_list(db_list.id) if db_list else []

    dependency_summary = {
        "total_dependencies": len(dependencies),
        "as_dependent": 0,  # How many items in this list depend on others
        "as_required": 0,  # How many items in this list block others
    }

    for dep in dependencies:
        # Check if the dependent item is in this list
        dependent_item = mgr.db.get_item_by_id(dep.dependent_item_id)
        if dependent_item and dependent_item.list_id == db_list.id:
            dependency_summary["as_dependent"] += 1

        # Check if the required item is in this list
        required_item = mgr.db.get_item_by_id(dep.required_item_id)
        if required_item and required_item.list_id == db_list.id:
            dependency_summary["as_required"] += 1

    return {
        "success": True,
        "list_key": list_key,
        "progress": progress.to_dict(),
        "next_task": map_item_content_to_title(clean_to_dict_result(next_task.to_dict(), "item")) if next_task else None,
        "blocked_items": blocked_items,
        "available_items": available_items,
        "items": [map_item_content_to_title(clean_to_dict_result(item.to_dict(), "item")) for item in items],
        "dependency_summary": dependency_summary,
        "recommendations": {
            "action": (
                "start_next"
                if next_task
                else (
                    "all_completed"
                    if progress.total > 0 and progress.completed == progress.total
                    else "add_items"
                )
            ),
            "next_task_key": next_task.item_key if next_task else None,
            "blocked_count": len(blocked_items),
            "available_count": len(available_items),
        },
    }


# ===== ITEM MANAGEMENT MCP TOOLS =====


@conditional_tool
@mcp_error_handler
async def todo_delete_item(list_key: str, item_key: str, mgr=None) -> Dict[str, Any]:
    """Delete a todo item from a list permanently.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Key of the item to delete (required)

    Returns:
        Dictionary with success status and confirmation message
    """
    success = mgr.delete_item(list_key, item_key)
    if success:
        return {
            "success": True,
            "message": f"Item '{item_key}' deleted from list '{list_key}'",
        }
    else:
        return {
            "success": False,
            "error": f"Item '{item_key}' not found in list '{list_key}'",
        }



@conditional_tool
@mcp_error_handler
async def todo_rename_item(
    list_key: str,
    item_key: str,
    new_key: Optional[str] = None,
    new_title: Optional[str] = None,
    subitem_key: Optional[str] = None,
    mgr=None
) -> Dict[str, Any]:
    """Rename item key and/or title.

    Args:
        list_key: Key of the list containing the item (required)
        item_key: Current key of the item, or parent key if renaming subitem (required)
        new_key: New key for the item/subitem (optional)
        new_title: New title for the item/subitem (optional)
        subitem_key: If provided, renames the subitem instead of parent item (optional)

    Returns:
        Dictionary with success status and updated item details

    Examples:
        # Rename item key only
        await todo_rename_item("project", "old_task", new_key="new_task")
        
        # Rename item title only  
        await todo_rename_item("project", "task1", new_title="Updated Title")
        
        # Rename both key and title
        await todo_rename_item("project", "old", new_key="new", new_title="New Title")
        
        # Rename subitem
        await todo_rename_item("project", "parent", new_key="new_sub", subitem_key="old_sub")
    """
    # Determine parent_item_key based on subitem_key parameter
    parent_item_key = item_key if subitem_key else None
    actual_item_key = subitem_key if subitem_key else item_key
    
    updated_item = mgr.rename_item(
        list_key=list_key,
        item_key=actual_item_key,
        new_key=new_key,
        new_content=new_title,  # Map new_title to new_content for internal API
        parent_item_key=parent_item_key
    )
    
    # Convert to dict with data cleaning and map content → title for response
    item_dict = clean_to_dict_result(updated_item.to_dict(), "item")
    if "content" in item_dict:
        item_dict["title"] = item_dict.pop("content")  # Map content → title
    
    return {
        "success": True,
        "item": item_dict,
        "message": f"Item '{actual_item_key}' renamed in list '{list_key}'",
    }


@conditional_tool
@mcp_error_handler
async def todo_rename_list(
    list_key: str,
    new_key: Optional[str] = None,
    new_title: Optional[str] = None,
    mgr=None
) -> Dict[str, Any]:
    """Rename list key and/or title.

    Args:
        list_key: Current key of the list to rename (required)
        new_key: New key for the list (optional)
        new_title: New title for the list (optional)

    Returns:
        Dictionary with success status and updated list details

    Examples:
        # Rename list key only
        await todo_rename_list("old_project", new_key="new_project")
        
        # Rename list title only
        await todo_rename_list("project", new_title="Updated Project Title")
        
        # Rename both key and title
        await todo_rename_list("old", new_key="new", new_title="New Title")
    """
    updated_list = mgr.rename_list(
        current_key=list_key,
        new_key=new_key,
        new_title=new_title
    )
    
    return {
        "success": True,
        "list": clean_to_dict_result(updated_list.to_dict(), "list"),
        "message": f"List '{list_key}' renamed successfully",
    }


# ===== SYSTEM METADATA MCP TOOL =====


@conditional_tool
@mcp_error_handler
async def todo_get_schema_info(mgr=None) -> Dict[str, Any]:
    """Get system schema information including available enums and constants.

    Returns:
        Dictionary with available system values for validation and UI
    """
    return {
        "success": True,
        "schema_info": {
            "item_statuses": ["pending", "in_progress", "completed", "failed"],
            "list_types": ["sequential"],
            "dependency_types": ["blocks", "requires", "related"],
            "history_actions": ["created", "updated", "status_changed", "deleted"],
        },
        "descriptions": {
            "item_statuses": {
                "pending": "Task is waiting to be started",
                "in_progress": "Task is currently being worked on",
                "completed": "Task has been finished successfully",
                "failed": "Task could not be completed",
            },
            "list_types": {
                "sequential": "Tasks should be completed in order",
            },
            "dependency_types": {
                "blocks": "This item blocks another from starting",
                "requires": "This item requires another to be completed first",
                "related": "Items are related but not blocking",
            },
        },
    }


# ===== LIST TAG MANAGEMENT MCP TOOLS =====


@conditional_tool
@mcp_error_handler
async def todo_create_tag(name: str, color: str = "blue", mgr=None) -> Dict[str, Any]:
    """Create a new tag in the system.

    Args:
        name: Tag name (required, will be normalized to lowercase)
        color: Tag color (default: blue, supports: red, green, blue, yellow, orange, purple, cyan, magenta)

    Returns:
        Dictionary with success status and created tag details
    """
    tag = mgr.create_tag(name, color)
    return {
        "success": True,
        "tag": clean_to_dict_result(tag.to_dict(), "tag"),
        "message": f"Tag '{name}' created successfully",
    }


@conditional_tool
@mcp_error_handler
async def todo_add_list_tag(list_key: str, tag_name: str, mgr=None) -> Dict[str, Any]:
    """Add a tag to a list (creates tag if it doesn't exist).

    Args:
        list_key: Key of the list to tag (required)
        tag_name: Name of the tag to add (required, will be normalized to lowercase)

    Returns:
        Dictionary with success status and assignment details
    """
    assignment = mgr.add_tag_to_list(list_key, tag_name)
    return {
        "success": True,
        "assignment": clean_to_dict_result(assignment.to_dict(), "assignment"),
        "message": f"Tag '{tag_name}' added to list '{list_key}'",
    }


@conditional_tool
@mcp_error_handler
async def todo_remove_list_tag(
    list_key: str, tag_name: str, mgr=None
) -> Dict[str, Any]:
    """Remove a tag from a list.

    Args:
        list_key: Key of the list to remove tag from (required)
        tag_name: Name of the tag to remove (required)

    Returns:
        Dictionary with success status and removal confirmation
    """
    success = mgr.remove_tag_from_list(list_key, tag_name)
    return {
        "success": success,
        "message": f"Tag '{tag_name}' {'removed from' if success else 'was not assigned to'} list '{list_key}'",
    }


@conditional_tool
@mcp_error_handler
async def todo_get_lists_by_tag(tag_names: List[str], mgr=None) -> Dict[str, Any]:
    """Get all lists that have ANY of the specified tags.

    Args:
        tag_names: List of tag names to filter by (required)

    Returns:
        Dictionary with success status, matching lists, and metadata
    """
    lists = mgr.get_lists_by_tags(tag_names)

    # Enhance lists with tag information
    enhanced_lists = []
    for todo_list in lists:
        list_data = clean_to_dict_result(todo_list.to_dict(), "list")

        # Get tags for this list
        tags = mgr.get_tags_for_list(todo_list.list_key)
        list_data["tags"] = [clean_to_dict_result(tag.to_dict(), "tag") for tag in tags]

        # Get progress stats
        progress = mgr.get_progress(todo_list.list_key)
        list_data["progress"] = progress.to_dict()

        enhanced_lists.append(list_data)

    return {
        "success": True,
        "lists": enhanced_lists,
        "count": len(lists),
        "filter_tags": tag_names,
        "message": f"Found {len(lists)} list(s) with tags: {', '.join(tag_names)}",
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
