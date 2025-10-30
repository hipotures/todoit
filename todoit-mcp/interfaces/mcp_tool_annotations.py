"""
MCP Tool Annotations for TODOIT
Defines MCP protocol annotations for all 51 tools
"""

from typing import Dict

# MCP Tool Annotations
# ====================
# readOnlyHint: True if tool only reads data, never modifies
# destructiveHint: True if tool modifies/deletes data (default: True if readOnlyHint=False)
# idempotentHint: True if calling multiple times with same args produces same result
# openWorldHint: True if tool interacts with external systems (default: True for MCP)

TOOL_ANNOTATIONS: Dict[str, Dict[str, bool]] = {
    # ═══════════════════════════════════════════════════════════════════════════
    # READ-ONLY TOOLS (15 tools)
    # ═══════════════════════════════════════════════════════════════════════════
    # These tools only read data, never modify state

    # Core list reads
    "todo_get_list": {
        "readOnlyHint": True,
    },
    "todo_list_all": {
        "readOnlyHint": True,
    },

    # Core item reads
    "todo_get_item": {
        "readOnlyHint": True,
    },
    "todo_get_list_items": {
        "readOnlyHint": True,
    },
    "todo_get_item_history": {
        "readOnlyHint": True,
    },
    "todo_get_item_hierarchy": {
        "readOnlyHint": True,
    },

    # Progress and workflow reads
    "todo_get_progress": {
        "readOnlyHint": True,
    },
    "todo_get_next_pending": {
        "readOnlyHint": True,
    },
    "todo_get_next_pending_smart": {
        "readOnlyHint": True,
    },
    "todo_get_next_pending_enhanced": {
        "readOnlyHint": True,
    },
    "todo_get_comprehensive_status": {
        "readOnlyHint": True,
    },
    "todo_get_cross_list_progress": {
        "readOnlyHint": True,
    },

    # Property reads
    "todo_get_list_property": {
        "readOnlyHint": True,
    },
    "todo_get_list_properties": {
        "readOnlyHint": True,
    },
    "todo_get_item_property": {
        "readOnlyHint": True,
    },
    "todo_get_item_properties": {
        "readOnlyHint": True,
    },
    "todo_get_all_items_properties": {
        "readOnlyHint": True,
    },

    # Search and query operations
    "todo_find_items_by_property": {
        "readOnlyHint": True,
    },
    "todo_find_items_by_status": {
        "readOnlyHint": True,
    },

    # Dependency reads
    "todo_can_complete_item": {
        "readOnlyHint": True,
    },
    "todo_is_item_blocked": {
        "readOnlyHint": True,
    },
    "todo_can_start_item": {
        "readOnlyHint": True,
    },
    "todo_get_item_blockers": {
        "readOnlyHint": True,
    },
    "todo_get_items_blocked_by": {
        "readOnlyHint": True,
    },
    "todo_get_dependency_graph": {
        "readOnlyHint": True,
    },

    # System metadata
    "todo_get_schema_info": {
        "readOnlyHint": True,
    },
    "todo_project_overview": {
        "readOnlyHint": True,
    },

    # Tag reads
    "todo_get_lists_by_tag": {
        "readOnlyHint": True,
    },

    # Reports (read-only aggregation)
    "todo_report_errors": {
        "readOnlyHint": True,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # IDEMPOTENT, NON-DESTRUCTIVE TOOLS (18 tools)
    # ═══════════════════════════════════════════════════════════════════════════
    # These tools create or modify data but are safe to retry (idempotent)
    # and don't destroy existing data (non-destructive)

    # List creation and modification
    "todo_create_list": {
        "idempotentHint": True,
        "destructiveHint": False,
    },
    "todo_archive_list": {
        "idempotentHint": True,
        "destructiveHint": False,
    },
    "todo_unarchive_list": {
        "idempotentHint": True,
        "destructiveHint": False,
    },

    # Item creation
    "todo_add_item": {
        "idempotentHint": True,
        "destructiveHint": False,
    },
    "todo_quick_add": {
        "idempotentHint": True,
        "destructiveHint": False,
    },

    # Status updates (idempotent - setting same status multiple times is safe)
    "todo_update_item_status": {
        "idempotentHint": True,
        "destructiveHint": False,  # Changing status is not destructive
    },

    # Property operations (upsert pattern - idempotent)
    "todo_set_list_property": {
        "idempotentHint": True,
        "destructiveHint": False,
    },
    "todo_set_item_property": {
        "idempotentHint": True,
        "destructiveHint": False,
    },

    # Tag operations (idempotent assignments)
    "todo_create_tag": {
        "idempotentHint": True,
        "destructiveHint": False,
    },
    "todo_add_list_tag": {
        "idempotentHint": True,
        "destructiveHint": False,
    },

    # Dependency operations (idempotent relationships)
    "todo_add_item_dependency": {
        "idempotentHint": True,
        "destructiveHint": False,
    },

    # Import/Export (idempotent operations)
    "todo_import_from_markdown": {
        "idempotentHint": True,
        "destructiveHint": False,  # Imports data, doesn't destroy existing
    },
    "todo_export_to_markdown": {
        "idempotentHint": True,
        "destructiveHint": False,  # Read-only export operation
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # IDEMPOTENT, DESTRUCTIVE TOOLS (5 tools)
    # ═══════════════════════════════════════════════════════════════════════════
    # These tools modify/remove data but are safe to retry (same result)

    "todo_remove_list_tag": {
        "idempotentHint": True,
        "destructiveHint": True,
    },
    "todo_remove_item_dependency": {
        "idempotentHint": True,
        "destructiveHint": True,
    },
    "todo_delete_list_property": {
        "idempotentHint": True,
        "destructiveHint": True,
    },
    "todo_delete_item_property": {
        "idempotentHint": True,
        "destructiveHint": True,
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # NON-IDEMPOTENT, DESTRUCTIVE TOOLS (7 tools)
    # ═══════════════════════════════════════════════════════════════════════════
    # These tools permanently modify/delete data and should not be retried blindly

    "todo_delete_list": {
        "idempotentHint": False,
        "destructiveHint": True,
    },
    "todo_delete_item": {
        "idempotentHint": False,
        "destructiveHint": True,
    },
    "todo_rename_list": {
        "idempotentHint": False,
        "destructiveHint": True,  # Changes keys which could break references
    },
    "todo_rename_item": {
        "idempotentHint": False,
        "destructiveHint": True,  # Changes keys which could break references
    },
    "todo_move_to_subitem": {
        "idempotentHint": False,
        "destructiveHint": True,  # Restructures hierarchy
    },
}


def get_tool_annotations(tool_name: str) -> Dict[str, bool]:
    """
    Get MCP annotations for a given tool name.

    Args:
        tool_name: Name of the tool function (e.g., "todo_create_list")

    Returns:
        Dict with MCP annotation hints (readOnlyHint, destructiveHint, idempotentHint)

    Examples:
        >>> get_tool_annotations("todo_get_list")
        {'readOnlyHint': True}

        >>> get_tool_annotations("todo_create_list")
        {'idempotentHint': True, 'destructiveHint': False}

        >>> get_tool_annotations("todo_delete_list")
        {'idempotentHint': False, 'destructiveHint': True}
    """
    # Return annotations for known tools, or safe defaults for unknown
    if tool_name in TOOL_ANNOTATIONS:
        return TOOL_ANNOTATIONS[tool_name]
    else:
        # Safe default: assume destructive, non-idempotent (most cautious)
        return {
            "destructiveHint": True,
            "idempotentHint": False,
        }


def validate_annotations() -> Dict[str, str]:
    """
    Validate that all annotations are correctly defined.

    Returns:
        Dict with validation results and any issues found
    """
    issues = []

    for tool_name, annotations in TOOL_ANNOTATIONS.items():
        # Check for conflicting annotations
        if annotations.get("readOnlyHint") and annotations.get("destructiveHint"):
            issues.append(
                f"{tool_name}: Cannot be both readOnly and destructive"
            )

        if annotations.get("readOnlyHint") and annotations.get("idempotentHint"):
            issues.append(
                f"{tool_name}: Read-only tools don't need idempotentHint"
            )

    return {
        "valid": len(issues) == 0,
        "total_tools": len(TOOL_ANNOTATIONS),
        "issues": issues,
    }


# Validate annotations on module load (development check)
if __name__ == "__main__":
    validation = validate_annotations()
    print(f"Total tools annotated: {validation['total_tools']}")
    print(f"Valid: {validation['valid']}")
    if validation['issues']:
        print("Issues found:")
        for issue in validation['issues']:
            print(f"  - {issue}")
