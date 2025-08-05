"""
TODOIT MCP Server
MCP (Model Context Protocol) interface for TodoManager
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from core.manager import TodoManager


class TodoMCPServer:
    """MCP Server interface for TodoManager"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize MCP server with TodoManager"""
        self.manager = TodoManager(db_path)
        self.server = Server("todoit-mcp")
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools for TodoManager"""
        
        # === ETAP 1: 10 kluczowych funkcji ===
        
        @self.server.tool()
        async def todo_create_list(arguments: dict) -> dict:
            """Create a new TODO list with optional initial items"""
            try:
                todo_list = self.manager.create_list(
                    list_key=arguments["list_key"],
                    title=arguments["title"],
                    items=arguments.get("items"),
                    list_type=arguments.get("list_type", "sequential"),
                    metadata=arguments.get("metadata", {})
                )
                return {
                    "success": True,
                    "list": todo_list.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_list(arguments: dict) -> dict:
            """Get TODO list by key or ID"""
            try:
                todo_list = self.manager.get_list(arguments["key"])
                if todo_list:
                    return {
                        "success": True,
                        "list": todo_list.to_dict()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"List '{arguments['key']}' not found"
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_delete_list(arguments: dict) -> dict:
            """Delete TODO list (with dependency validation)"""
            try:
                success = self.manager.delete_list(arguments["key"])
                return {
                    "success": success,
                    "message": f"List '{arguments['key']}' deleted successfully" if success else "List not found"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_list_all(arguments: dict) -> dict:
            """List all TODO lists"""
            try:
                lists = self.manager.list_all(limit=arguments.get("limit"))
                return {
                    "success": True,
                    "lists": [todo_list.to_dict() for todo_list in lists],
                    "count": len(lists)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_add_item(arguments: dict) -> dict:
            """Add item to TODO list"""
            try:
                item = self.manager.add_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    content=arguments["content"],
                    position=arguments.get("position"),
                    metadata=arguments.get("metadata", {})
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_update_item_status(arguments: dict) -> dict:
            """Update item status with multi-state support"""
            try:
                item = self.manager.update_item_status(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    status=arguments.get("status"),
                    completion_states=arguments.get("completion_states")
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_next_pending(arguments: dict) -> dict:
            """Get next pending item to work on"""
            try:
                item = self.manager.get_next_pending(
                    list_key=arguments["list_key"],
                    respect_dependencies=arguments.get("respect_dependencies", True)
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
        
        @self.server.tool()
        async def todo_get_progress(arguments: dict) -> dict:
            """Get progress statistics for a list"""
            try:
                progress = self.manager.get_progress(arguments["list_key"])
                return {
                    "success": True,
                    "progress": progress.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_import_from_markdown(arguments: dict) -> dict:
            """Import lists from markdown file (supports multi-column)"""
            try:
                lists = self.manager.import_from_markdown(
                    file_path=arguments["file_path"],
                    base_key=arguments.get("base_key")
                )
                return {
                    "success": True,
                    "lists": [todo_list.to_dict() for todo_list in lists],
                    "count": len(lists),
                    "message": f"Imported {len(lists)} list(s) from {arguments['file_path']}"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_export_to_markdown(arguments: dict) -> dict:
            """Export list to markdown format [x] text"""
            try:
                self.manager.export_to_markdown(
                    list_key=arguments["list_key"],
                    file_path=arguments["file_path"]
                )
                return {
                    "success": True,
                    "message": f"List '{arguments['list_key']}' exported to {arguments['file_path']}"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # === Funkcje pomocnicze ===
        
        @self.server.tool()
        async def todo_get_item(arguments: dict) -> dict:
            """Get specific item from list"""
            try:
                item = self.manager.get_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"]
                )
                if item:
                    return {
                        "success": True,
                        "item": item.to_dict()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Item '{arguments['item_key']}' not found in list '{arguments['list_key']}'"
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_list_items(arguments: dict) -> dict:
            """Get all items from a list"""
            try:
                items = self.manager.get_list_items(
                    list_key=arguments["list_key"],
                    status=arguments.get("status")
                )
                return {
                    "success": True,
                    "items": [item.to_dict() for item in items],
                    "count": len(items)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_create_list_relation(arguments: dict) -> dict:
            """Create relation between lists"""
            try:
                relation = self.manager.create_list_relation(
                    source_list_id=arguments["source_list_id"],
                    target_list_id=arguments["target_list_id"],
                    relation_type=arguments["relation_type"],
                    relation_key=arguments.get("relation_key"),
                    metadata=arguments.get("metadata", {})
                )
                return {
                    "success": True,
                    "relation": relation.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_lists_by_relation(arguments: dict) -> dict:
            """Get lists by relation type and key"""
            try:
                lists = self.manager.get_lists_by_relation(
                    relation_type=arguments["relation_type"],
                    relation_key=arguments["relation_key"]
                )
                return {
                    "success": True,
                    "lists": [todo_list.to_dict() for todo_list in lists],
                    "count": len(lists)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_item_history(arguments: dict) -> dict:
            """Get history of changes for an item"""
            try:
                history = self.manager.get_item_history(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    limit=arguments.get("limit")
                )
                return {
                    "success": True,
                    "history": [entry.to_dict() for entry in history],
                    "count": len(history)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # === Convenient wrapper tools ===
        
        @self.server.tool()
        async def todo_quick_add(arguments: dict) -> dict:
            """Quick add multiple items to a list"""
            try:
                items = arguments["items"]  # List of strings
                list_key = arguments["list_key"]
                
                created_items = []
                for i, content in enumerate(items):
                    item_key = f"quick_item_{i+1}_{len(content)}"  # Simple unique key
                    item = self.manager.add_item(
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
        
        @self.server.tool()
        async def todo_mark_completed(arguments: dict) -> dict:
            """Mark item as completed (shortcut)"""
            try:
                item = self.manager.update_item_status(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    status="completed"
                )
                return {
                    "success": True,
                    "item": item.to_dict(),
                    "message": f"Item '{arguments['item_key']}' marked as completed"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_start_item(arguments: dict) -> dict:
            """Start working on item (shortcut)"""
            try:
                item = self.manager.update_item_status(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    status="in_progress"
                )
                return {
                    "success": True,
                    "item": item.to_dict(),
                    "message": f"Started working on '{arguments['item_key']}'"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_project_overview(arguments: dict) -> dict:
            """Get overview of project with multiple lists"""
            try:
                project_key = arguments["project_key"]
                
                # Get lists by project relation
                lists = self.manager.get_lists_by_relation("project", project_key)
                
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
                    progress = self.manager.get_progress(todo_list.list_key)
                    
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


async def main():
    """Run the MCP server"""
    server = TodoMCPServer()
    
    async with stdio_server() as streams:
        await server.server.run(streams[0], streams[1])


if __name__ == "__main__":
    asyncio.run(main())