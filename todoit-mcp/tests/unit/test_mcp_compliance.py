"""
MCP Compliance Tests for TODOIT
Tests that verify adherence to MCP protocol best practices
"""

import pytest
from interfaces.mcp_tool_annotations import (
    TOOL_ANNOTATIONS,
    get_tool_annotations,
    validate_annotations,
)


class TestMCPAnnotations:
    """Test MCP tool annotations are properly defined"""

    def test_all_tools_have_annotations(self):
        """Verify that all 51 tools have annotation mappings"""
        # Expected 51 tools based on audit
        assert len(TOOL_ANNOTATIONS) >= 51, (
            f"Expected at least 51 tools, got {len(TOOL_ANNOTATIONS)}"
        )

    def test_annotations_validation(self):
        """Verify that annotations are logically consistent"""
        validation = validate_annotations()
        assert validation["valid"], (
            f"Annotation validation failed: {validation['issues']}"
        )

    def test_no_conflicting_readonly_and_destructive(self):
        """Read-only tools should never be marked as destructive"""
        for tool_name, annotations in TOOL_ANNOTATIONS.items():
            if annotations.get("readOnlyHint"):
                assert not annotations.get("destructiveHint"), (
                    f"{tool_name} cannot be both readOnly and destructive"
                )

    def test_readonly_tools_dont_have_idempotent_hint(self):
        """Read-only tools don't need idempotentHint"""
        for tool_name, annotations in TOOL_ANNOTATIONS.items():
            if annotations.get("readOnlyHint"):
                assert not annotations.get("idempotentHint"), (
                    f"{tool_name} is read-only, doesn't need idempotentHint"
                )

    def test_get_tool_annotations_returns_dict(self):
        """get_tool_annotations should always return a dict"""
        result = get_tool_annotations("todo_get_list")
        assert isinstance(result, dict)
        assert "readOnlyHint" in result

    def test_get_tool_annotations_unknown_tool_safe_defaults(self):
        """Unknown tools should get safe default annotations"""
        result = get_tool_annotations("unknown_tool_xyz")
        assert result.get("destructiveHint") is True
        assert result.get("idempotentHint") is False


class TestReadOnlyTools:
    """Test that read-only tools are properly categorized"""

    # Expected read-only tools based on audit
    EXPECTED_READONLY_TOOLS = [
        "todo_get_list",
        "todo_list_all",
        "todo_get_item",
        "todo_get_list_items",
        "todo_get_item_history",
        "todo_get_item_hierarchy",
        "todo_get_progress",
        "todo_get_next_pending",
        "todo_get_next_pending_smart",
        "todo_get_next_pending_enhanced",
        "todo_get_comprehensive_status",
        "todo_get_cross_list_progress",
        "todo_get_list_property",
        "todo_get_list_properties",
        "todo_get_item_property",
        "todo_get_item_properties",
        "todo_get_all_items_properties",
        "todo_find_items_by_property",
        "todo_find_items_by_status",
        "todo_can_complete_item",
        "todo_is_item_blocked",
        "todo_can_start_item",
        "todo_get_item_blockers",
        "todo_get_items_blocked_by",
        "todo_get_dependency_graph",
        "todo_get_schema_info",
        "todo_project_overview",
        "todo_get_lists_by_tag",
        "todo_report_errors",
    ]

    def test_all_expected_readonly_tools_are_annotated(self):
        """Verify all expected read-only tools have readOnlyHint=True"""
        for tool_name in self.EXPECTED_READONLY_TOOLS:
            annotations = get_tool_annotations(tool_name)
            assert annotations.get("readOnlyHint") is True, (
                f"{tool_name} should have readOnlyHint=True"
            )

    def test_readonly_tools_not_marked_destructive(self):
        """Read-only tools should not have destructiveHint"""
        readonly_tools = [
            name
            for name, ann in TOOL_ANNOTATIONS.items()
            if ann.get("readOnlyHint")
        ]

        for tool_name in readonly_tools:
            annotations = TOOL_ANNOTATIONS[tool_name]
            assert not annotations.get("destructiveHint"), (
                f"{tool_name} is read-only but marked destructive"
            )


class TestIdempotentTools:
    """Test that idempotent tools are properly categorized"""

    # Expected idempotent, non-destructive tools
    EXPECTED_IDEMPOTENT_NONDESTRUCTIVE = [
        "todo_create_list",
        "todo_archive_list",
        "todo_unarchive_list",
        "todo_add_item",
        "todo_quick_add",
        "todo_update_item_status",
        "todo_set_list_property",
        "todo_set_item_property",
        "todo_create_tag",
        "todo_add_list_tag",
        "todo_add_item_dependency",
        "todo_import_from_markdown",
        "todo_export_to_markdown",
    ]

    def test_idempotent_nondestructive_tools_annotated(self):
        """Verify idempotent non-destructive tools have correct annotations"""
        for tool_name in self.EXPECTED_IDEMPOTENT_NONDESTRUCTIVE:
            annotations = get_tool_annotations(tool_name)
            assert annotations.get("idempotentHint") is True, (
                f"{tool_name} should have idempotentHint=True"
            )
            assert annotations.get("destructiveHint") is False, (
                f"{tool_name} should have destructiveHint=False"
            )


class TestDestructiveTools:
    """Test that destructive tools are properly categorized"""

    # Expected destructive tools
    EXPECTED_DESTRUCTIVE = [
        "todo_delete_list",
        "todo_delete_item",
        "todo_rename_list",
        "todo_rename_item",
        "todo_move_to_subitem",
        "todo_delete_list_property",
        "todo_delete_item_property",
        "todo_remove_list_tag",
        "todo_remove_item_dependency",
    ]

    def test_destructive_tools_annotated(self):
        """Verify destructive tools have destructiveHint=True"""
        for tool_name in self.EXPECTED_DESTRUCTIVE:
            annotations = get_tool_annotations(tool_name)
            assert annotations.get("destructiveHint") is True, (
                f"{tool_name} should have destructiveHint=True"
            )

    def test_nonidempotent_destructive_tools(self):
        """Verify truly dangerous tools are not marked idempotent"""
        dangerous_tools = [
            "todo_delete_list",
            "todo_delete_item",
            "todo_rename_list",
            "todo_rename_item",
            "todo_move_to_subitem",
        ]

        for tool_name in dangerous_tools:
            annotations = get_tool_annotations(tool_name)
            # These should NOT be idempotent (or explicitly False)
            assert annotations.get("idempotentHint") is not True, (
                f"{tool_name} should not be marked idempotent"
            )


class TestToolCategorization:
    """Test that all tools are categorized correctly"""

    def test_all_tools_have_at_least_one_hint(self):
        """Every tool should have at least one annotation hint"""
        for tool_name, annotations in TOOL_ANNOTATIONS.items():
            has_hint = (
                annotations.get("readOnlyHint") is not None
                or annotations.get("destructiveHint") is not None
                or annotations.get("idempotentHint") is not None
            )
            assert has_hint, f"{tool_name} has no annotation hints"

    def test_readonly_tools_count(self):
        """Verify we have expected number of read-only tools (29+)"""
        readonly_count = sum(
            1
            for ann in TOOL_ANNOTATIONS.values()
            if ann.get("readOnlyHint")
        )
        assert readonly_count >= 29, (
            f"Expected at least 29 read-only tools, got {readonly_count}"
        )

    def test_idempotent_tools_count(self):
        """Verify we have expected number of idempotent tools (13+)"""
        idempotent_count = sum(
            1
            for ann in TOOL_ANNOTATIONS.values()
            if ann.get("idempotentHint")
        )
        assert idempotent_count >= 13, (
            f"Expected at least 13 idempotent tools, got {idempotent_count}"
        )

    def test_destructive_tools_count(self):
        """Verify we have expected number of destructive tools (9+)"""
        destructive_count = sum(
            1
            for ann in TOOL_ANNOTATIONS.values()
            if ann.get("destructiveHint")
        )
        assert destructive_count >= 9, (
            f"Expected at least 9 destructive tools, got {destructive_count}"
        )


class TestMCPServerIntegration:
    """Test that MCP server properly uses annotations"""

    def test_conditional_tool_decorator_exists(self):
        """Verify conditional_tool decorator is importable"""
        from interfaces.mcp_server import conditional_tool

        assert callable(conditional_tool)

    def test_mcp_server_imports_annotations(self):
        """Verify mcp_server imports get_tool_annotations"""
        import interfaces.mcp_server as mcp_server

        assert hasattr(mcp_server, "get_tool_annotations")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
