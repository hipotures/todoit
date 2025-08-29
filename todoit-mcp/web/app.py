"""
TODOIT Web Interface
FastAPI application for web-based TODO management
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.manager import TodoManager
from core.models import ItemStatus

# Initialize FastAPI app
app = FastAPI(
    title="TODOIT Web Interface",
    description="Web-based TODO list management",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global manager instance
manager = None

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value.strip('"\'')

def get_manager():
    """Get or create TodoManager instance"""
    global manager
    if manager is None:
        # Load .env file first
        load_env_file()
        
        # Get database path with fallbacks
        db_path = os.environ.get("TODOIT_DB_PATH")
        if not db_path:
            # Try common locations
            possible_paths = [
                "/tmp/test_todoit.db",
                str(Path.home() / "todoit.db"),
                "./todoit.db"
            ]
            db_path = possible_paths[0]  # Default to /tmp
            
        manager = TodoManager(db_path)
    return manager

# Request/Response Models
class ItemUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    
class ConfigUpdate(BaseModel):
    columns: Dict[str, bool]

# Routes

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/lists")
async def get_all_lists(limit: int = 50, offset: int = 0, search: str = "", favorites_only: bool = False, tag: str = ""):
    """Get paginated list of TODO lists with stats and properties"""
    try:
        mgr = get_manager()
        all_lists = mgr.list_all()
        
        # Filter lists
        filtered_lists = []
        for list_obj in all_lists:
            # Search filter
            if search and search.lower() not in list_obj.title.lower() and search.lower() not in list_obj.list_key.lower():
                continue
                
            # Get properties
            properties = {}
            is_favorite = False
            try:
                # Get all common properties for this list
                known_props = ['is_favorite', 'priority', 'category', 'owner', 'deadline', 'color']
                for prop_key in known_props:
                    try:
                        prop_result = mgr.get_list_property(list_obj.list_key, prop_key)
                        # TodoManager returns string value directly
                        if prop_result and isinstance(prop_result, str):
                            properties[prop_key] = prop_result
                            if prop_key == 'is_favorite' and prop_result == 'true':
                                is_favorite = True
                    except:
                        continue
            except:
                pass
            
            # Favorites filter
            if favorites_only and not is_favorite:
                continue
            
            # Tag filter
            if tag:
                # Get list tags using TodoManager's tag system
                list_tags = []
                try:
                    tags_result = mgr.get_tags_for_list(list_obj.list_key)
                    list_tags = [t.name for t in tags_result] if tags_result else []
                except:
                    pass
                
                # If tag filter is specified but list doesn't have the tag, skip
                if tag and tag not in list_tags:
                    continue
            
            # Get item stats
            items = mgr.get_list_items(list_obj.list_key, limit=1000)
            total_items = len(items)
            
            # Count by status
            def _status_str(s: Any) -> str:
                try:
                    return s.value if hasattr(s, 'value') else str(s)
                except Exception:
                    return str(s)

            pending_count = sum(1 for item in items if _status_str(getattr(item, 'status', 'pending')) == 'pending')
            in_progress_count = sum(1 for item in items if _status_str(getattr(item, 'status', 'pending')) == 'in_progress')
            completed_count = sum(1 for item in items if _status_str(getattr(item, 'status', 'pending')) == 'completed')
            failed_count = sum(1 for item in items if _status_str(getattr(item, 'status', 'pending')) == 'failed')
            
            # Get last activity
            last_updated = list_obj.updated_at
            if items:
                # Find most recent item update
                for item in items:
                    if hasattr(item, 'updated_at') and item.updated_at:
                        try:
                            # Handle timezone awareness
                            item_updated = item.updated_at
                            if hasattr(item_updated, 'replace') and item_updated.tzinfo is not None:
                                item_updated = item_updated.replace(tzinfo=None)
                            if hasattr(last_updated, 'replace') and last_updated.tzinfo is not None:
                                last_updated = last_updated.replace(tzinfo=None)
                            
                            if item_updated > last_updated:
                                last_updated = item_updated
                        except (TypeError, AttributeError):
                            # Skip if datetime comparison fails
                            pass
            
            filtered_lists.append({
                'list_key': list_obj.list_key,
                'title': list_obj.title,
                'description': list_obj.description,
                'status': getattr(list_obj.status, 'value', str(list_obj.status)),
                'is_favorite': is_favorite,
                'properties': properties,
                'properties_count': len(properties),
                'total_items': total_items,
                'pending_items': pending_count,
                'in_progress_items': in_progress_count,
                'completed_items': completed_count,
                'failed_items': failed_count,
                'completion_percentage': round((completed_count / total_items * 100) if total_items > 0 else 0, 1),
                'created_at': str(list_obj.created_at),
                'updated_at': str(last_updated)
            })
        
        # Sort by list_key (alphabetical)
        filtered_lists.sort(key=lambda x: x['list_key'])
        
        # Apply pagination
        total_count = len(filtered_lists)
        paginated_lists = filtered_lists[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated_lists,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags")
async def get_all_tags():
    """Get all available tags"""
    try:
        mgr = get_manager()
        
        # Use TodoManager's built-in tag system
        all_tags = mgr.get_all_tags()
        tag_names = [tag.name for tag in all_tags] if all_tags else []
        
        return {
            "success": True,
            "tags": sorted(tag_names)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/{list_key}")
async def get_list_details(list_key: str):
    """Get detailed information about a specific list"""
    try:
        mgr = get_manager()
        
        # Get list info
        lists = mgr.list_all()
        list_obj = next((l for l in lists if l.list_key == list_key), None)
        if not list_obj:
            raise HTTPException(status_code=404, detail=f"List '{list_key}' not found")
        
        # Get all properties for this list
        properties = {}
        is_favorite = False
        try:
            favorite_prop = mgr.get_list_property(list_key, "is_favorite")
            if isinstance(favorite_prop, str) and favorite_prop == 'true':
                is_favorite = True
                properties['is_favorite'] = 'true'
        except Exception:
            # Property missing or manager error – keep defaults
            pass
        
        # TODO: Get all properties (would need TodoManager enhancement)
        
        return {
            "success": True,
            "list": {
                'list_key': list_obj.list_key,
                'title': list_obj.title,
                'description': list_obj.description,
                'status': getattr(list_obj.status, 'value', str(list_obj.status)),
                'list_type': getattr(list_obj.list_type, 'value', str(list_obj.list_type)),
                'is_favorite': is_favorite,
                'properties': properties,
                'created_at': str(list_obj.created_at),
                'updated_at': str(list_obj.updated_at)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/{list_key}/items")
async def get_list_items(list_key: str, limit: int = 100, offset: int = 0):
    """Get paginated items for specific list with subitems"""
    try:
        mgr = get_manager()
        
        # Get all items for this list
        all_items = mgr.get_list_items(list_key, limit=10000)  # Get all to organize properly
        
        # Organize items with subitems
        organized_items = []
        items_by_id = {getattr(item, 'id', None): item for item in all_items if hasattr(item, 'id')}
        
        for item in all_items:
            # Convert item to dict
            if hasattr(item, 'to_dict'):
                item_dict = item.to_dict()
            elif hasattr(item, '__dict__'):
                item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
            else:
                item_dict = item if isinstance(item, dict) else {}
            
            # Only process root items (no parent)
            if not item_dict.get('parent_item_id'):
                # Find subitems
                subitems = []
                item_id = item_dict.get('id')
                for child in all_items:
                    child_dict = child.to_dict() if hasattr(child, 'to_dict') else (child.__dict__ if hasattr(child, '__dict__') else child)
                    if child_dict.get('parent_item_id') == item_id:
                        # Get properties for this subitem
                        subitem_properties = {}
                        subitem_known_props = ['priority', 'assignee', 'deadline', 'notes', 'difficulty', 'estimated_time', 'test_priority']
                        for prop_key in subitem_known_props:
                            try:
                                result = mgr.get_item_property(list_key, child_dict.get('item_key', ''), prop_key, parent_item_key=item_dict.get('item_key', ''))
                                # TodoManager returns string value directly
                                if result and isinstance(result, str):
                                    subitem_properties[prop_key] = result
                            except:
                                continue
                        
                        clean_child = {
                            'item_key': child_dict.get('item_key', ''),
                            'content': child_dict.get('content', ''),
                            'status': str(child_dict.get('status', 'pending')),
                            'position': child_dict.get('position', 0),
                            'created_at': str(child_dict.get('created_at', '')),
                            'updated_at': str(child_dict.get('updated_at', '')),
                            'properties': subitem_properties,
                            'properties_count': len(subitem_properties)
                        }
                        subitems.append(clean_child)
                
                # Sort subitems by position
                subitems.sort(key=lambda x: x['position'])
                
                # Get properties for main item
                item_properties = {}
                known_props = ['priority', 'category', 'assignee', 'deadline', 'tags', 'notes', 'difficulty']
                for prop_key in known_props:
                    try:
                        result = mgr.get_item_property(list_key, item_dict.get('item_key', ''), prop_key)
                        # TodoManager returns string value directly
                        if result and isinstance(result, str):
                            item_properties[prop_key] = result
                    except:
                        continue
                
                organized_item = {
                    'item_key': item_dict.get('item_key', ''),
                    'content': item_dict.get('content', ''),
                    'status': str(item_dict.get('status', 'pending')),
                    'position': item_dict.get('position', 0),
                    'created_at': str(item_dict.get('created_at', '')),
                    'updated_at': str(item_dict.get('updated_at', '')),
                    'subitems_count': len(subitems),
                    'subitems': subitems,
                    'properties': item_properties,
                    'properties_count': len(item_properties)
                }
                organized_items.append(organized_item)
        
        # Sort by position
        organized_items.sort(key=lambda x: x['position'])
        
        # Apply pagination
        total_count = len(organized_items)
        paginated_items = organized_items[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated_items,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/items/{list_key}/{item_key}")
async def update_item(list_key: str, item_key: str, update: ItemUpdate):
    """Update item content or status"""
    try:
        mgr = get_manager()
        
        # Update content if provided
        if update.content is not None:
            mgr.rename_item(
                list_key=list_key,
                item_key=item_key,
                new_content=update.content
            )
        
        # Update status if provided
        if update.status is not None:
            mgr.update_item_status(
                list_key=list_key,
                item_key=item_key,
                status=update.status
            )
        
        return {"success": True, "message": "Item updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/subitems/{list_key}/{item_key}/{subitem_key}")
async def update_subitem(list_key: str, item_key: str, subitem_key: str, update: ItemUpdate):
    """Update subitem content or status"""
    try:
        mgr = get_manager()
        
        # Update subitem content if provided
        if update.content is not None:
            # For subitems, pass subitem key as item_key and parent as parent_item_key
            mgr.rename_item(
                list_key=list_key,
                item_key=subitem_key,
                new_content=update.content,
                parent_item_key=item_key,
            )
        
        # Update subitem status if provided
        if update.status is not None:
            mgr.update_item_status(
                list_key=list_key,
                item_key=subitem_key,
                status=update.status,
                parent_item_key=item_key
            )
            
            # Explicitly trigger parent status synchronization
            try:
                # Get the parent item to sync its status
                parent_items = mgr.get_list_items(list_key)
                parent_item = next((item for item in parent_items if getattr(item, 'item_key', None) == item_key), None)
                if parent_item and hasattr(parent_item, 'id'):
                    mgr._sync_parent_status(parent_item.id)
            except Exception as e:
                print(f"Warning: Could not sync parent status: {e}")
        
        return {"success": True, "message": "Subitem updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists/{list_key}/favorite")
async def toggle_favorite(list_key: str):
    """Toggle favorite status for a list"""
    try:
        mgr = get_manager()
        
        # Get current favorite status
        try:
            current_prop = mgr.get_list_property(list_key, "is_favorite")
            is_currently_favorite = isinstance(current_prop, str) and current_prop == 'true'
        except Exception:
            is_currently_favorite = False
        
        # Toggle the favorite status
        new_status = not is_currently_favorite
        mgr.set_list_property(list_key, "is_favorite", str(new_status).lower())
        
        return {
            "success": True, 
            "is_favorite": new_status,
            "message": f"List {'added to' if new_status else 'removed from'} favorites"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get user configuration"""
    # For now, return default config. In production, this would be user-specific
    return {
        "success": True,
        "config": {
            "columns": {
                "position": False,
                "created_at": False,
                "updated_at": False,
                "list_title": True,
                "item_key": True,
                "content": True,
                "status": True,
                "favorite": True
            },
            "itemsPerPage": 50,
            "theme": "light"
        }
    }

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update user configuration"""
    try:
        # In production, this would save to user preferences database
        # For now, just return success
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "config": config.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/{list_key}/properties")
async def get_list_properties(list_key: str):
    """Get all properties for a specific list (complete set)."""
    try:
        mgr = get_manager()
        # Validate existence
        lst = mgr.get_list(list_key)
        if not lst:
            raise HTTPException(status_code=404, detail=f"List '{list_key}' not found")

        # Fetch all properties directly from manager
        properties = mgr.get_list_properties(list_key)
        return {
            "success": True,
            "list_key": list_key,
            "properties": properties,
            "properties_count": len(properties),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists/{list_key}/properties")
async def set_list_property(list_key: str, property_data: dict):
    """Set a property for a list"""
    try:
        mgr = get_manager()
        
        property_key = property_data.get('key')
        property_value = property_data.get('value')
        
        if not property_key:
            raise HTTPException(status_code=400, detail="Property key is required")
        
        # Set the property
        result = mgr.set_list_property(list_key, property_key, str(property_value))
        
        # TodoManager returns the property object directly, not a dict
        return {
            "success": True,
            "message": f"Property '{property_key}' set successfully",
            "property": {
                "key": property_key,
                "value": property_value
            }
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lists/{list_key}/properties/{property_key}")
async def delete_list_property(list_key: str, property_key: str):
    """Delete a property from a list"""
    try:
        mgr = get_manager()
        
        # Delete by setting empty value (or implement proper delete in TodoManager)
        result = mgr.set_list_property(list_key, property_key, "")
        
        return {
            "success": True,
            "message": f"Property '{property_key}' deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === BATCH ENDPOINTS ===
@app.get("/api/lists/{list_key}/items/properties-batch")
async def get_items_properties_batch(list_key: str):
    """Get properties for all items in a list in a single request (performance optimization)"""
    try:
        # Use the MCP function which handles the manager correctly
        from interfaces.mcp_server import todo_get_all_items_properties
        mgr = get_manager()
        result = await todo_get_all_items_properties(list_key, mgr=mgr)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["properties"],
                "count": result["count"]
            }
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        error_details = f"Error getting batch properties: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)  # Log to server console
        raise HTTPException(status_code=500, detail=f"Error getting batch properties: {str(e)}")

@app.get("/api/lists/{list_key}/items/{item_key}/properties")
async def get_item_properties(list_key: str, item_key: str):
    """Get all properties for a specific item (complete set)."""
    try:
        mgr = get_manager()
        props = mgr.get_item_properties(list_key, item_key)
        return {
            "success": True,
            "list_key": list_key,
            "item_key": item_key,
            "properties": props,
            "properties_count": len(props),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists/{list_key}/items/{item_key}/properties")
async def set_item_property(list_key: str, item_key: str, property_data: dict):
    """Set a property for an item"""
    try:
        mgr = get_manager()
        
        property_key = property_data.get('key')
        property_value = property_data.get('value')
        
        if not property_key:
            raise HTTPException(status_code=400, detail="Property key is required")
        
        result = mgr.set_item_property(list_key, item_key, property_key, str(property_value))
        
        # TodoManager returns the property object directly
        return {
            "success": True,
            "message": f"Property '{property_key}' set successfully",
            "property": {
                "key": property_key,
                "value": property_value
            }
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lists/{list_key}/items/{item_key}/subitems/{subitem_key}/properties")
async def get_subitem_properties(list_key: str, item_key: str, subitem_key: str):
    """Get all properties for a specific subitem (complete set)."""
    try:
        mgr = get_manager()
        props = mgr.get_item_properties(list_key, subitem_key, parent_item_key=item_key)
        return {
            "success": True,
            "list_key": list_key,
            "item_key": item_key,
            "subitem_key": subitem_key,
            "properties": props,
            "properties_count": len(props),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists/{list_key}/items/{item_key}/subitems/{subitem_key}/properties")
async def set_subitem_property(list_key: str, item_key: str, subitem_key: str, property_data: dict):
    """Set a property for a subitem"""
    try:
        mgr = get_manager()
        
        property_key = property_data.get('key')
        property_value = property_data.get('value')
        
        if not property_key:
            raise HTTPException(status_code=400, detail="Property key is required")
        
        result = mgr.set_item_property(list_key, subitem_key, property_key, str(property_value), parent_item_key=item_key)
        
        # TodoManager returns the property object directly
        return {
            "success": True,
            "message": f"Subitem property '{property_key}' set successfully",
            "property": {
                "key": property_key,
                "value": property_value
            }
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lists/{list_key}/items/{item_key}/properties/{property_key}")
async def delete_item_property(list_key: str, item_key: str, property_key: str):
    """Delete a property from an item"""
    try:
        mgr = get_manager()
        
        success = mgr.delete_item_property(list_key, item_key, property_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {
            "success": True,
            "message": f"Property '{property_key}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/lists/{list_key}/items/{item_key}/subitems/{subitem_key}/properties/{property_key}")
async def delete_subitem_property(list_key: str, item_key: str, subitem_key: str, property_key: str):
    """Delete a property from a subitem"""
    try:
        mgr = get_manager()
        
        success = mgr.delete_item_property(list_key, subitem_key, property_key, parent_item_key=item_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return {
            "success": True,
            "message": f"Property '{property_key}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lists/{list_key}/sync-parent-statuses")
async def sync_parent_statuses(list_key: str):
    """Manually sync all parent statuses in a list"""
    try:
        mgr = get_manager()
        
        # Get all items in the list
        all_items = mgr.get_list_items(list_key, limit=10000)
        
        # Find all parent items (items that have subitems)
        parent_items = []
        parent_ids = set()
        
        for item in all_items:
            item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item.__dict__ if hasattr(item, '__dict__') else item)
            parent_id = item_dict.get('parent_item_id')
            if parent_id and parent_id not in parent_ids:
                parent_ids.add(parent_id)
                # Find the parent item by ID
                parent_item = next((i for i in all_items if getattr(i, 'id', None) == parent_id), None)
                if parent_item:
                    parent_items.append(parent_item)
        
        # Sync status for each parent
        synced_count = 0
        for parent_item in parent_items:
            try:
                if hasattr(parent_item, 'id'):
                    mgr._sync_parent_status(parent_item.id)
                    synced_count += 1
            except Exception as e:
                print(f"Error syncing parent {getattr(parent_item, 'item_key', 'unknown')}: {e}")
        
        return {
            "success": True,
            "message": f"Synced {synced_count} parent statuses",
            "synced_count": synced_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        mgr = get_manager()
        # Try a simple operation to verify database connection
        lists = mgr.list_all(limit=1)
        return {
            "success": True,
            "status": "healthy",
            "database": "connected",
            "lists_count": len(lists)
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Not found", "detail": str(exc.detail)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc.detail)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
