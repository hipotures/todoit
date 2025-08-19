"""
Unit tests for MCP todo_create_list functionality with tags parameter
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from interfaces.mcp_server import todo_create_list, init_manager


class TestMCPCreateListWithTags:
    """Test MCP todo_create_list function with tags parameter"""

    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        """Setup test database for each test"""
        self.db_path = str(tmp_path / "test.db")
        # Mock the init_manager to use our test database
        with patch('interfaces.mcp_server.manager', None):
            with patch('interfaces.mcp_server.init_manager') as mock_init:
                # Create a real manager with test database
                from core.manager import TodoManager
                self.test_manager = TodoManager(self.db_path)
                mock_init.return_value = self.test_manager
                yield

    @pytest.mark.asyncio
    async def test_mcp_create_list_without_tags(self):
        """Test MCP create_list without tags parameter"""
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List"
            )
        
        assert result["success"] is True
        assert "list" in result
        assert result["list"]["list_key"] == "test-list"
        assert result["list"]["title"] == "Test List"
        
        # Verify no tags are assigned
        tags = self.test_manager.get_tags_for_list("test-list")
        assert len(tags) == 0

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_none_tags(self):
        """Test MCP create_list with tags=None"""
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List",
                tags=None
            )
        
        assert result["success"] is True
        assert result["list"]["list_key"] == "test-list"

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_empty_tags(self):
        """Test MCP create_list with empty tags list"""
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List",
                tags=[]
            )
        
        assert result["success"] is True
        assert result["list"]["list_key"] == "test-list"
        
        # Verify no tags are assigned
        tags = self.test_manager.get_tags_for_list("test-list")
        assert len(tags) == 0

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_existing_tags(self):
        """Test MCP create_list with existing tags"""
        # Create tags first
        self.test_manager.create_tag("frontend", "blue")
        self.test_manager.create_tag("backend", "green")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="webapp",
                title="Web Application",
                tags=["frontend", "backend"]
            )
        
        assert result["success"] is True
        assert result["list"]["list_key"] == "webapp"
        assert result["list"]["title"] == "Web Application"
        
        # Verify tags are assigned
        tags = self.test_manager.get_tags_for_list("webapp")
        tag_names = [tag.name for tag in tags]
        assert len(tags) == 2
        assert "frontend" in tag_names
        assert "backend" in tag_names

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_nonexistent_tag(self):
        """Test MCP create_list fails with non-existent tag"""
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List",
                tags=["nonexistent"]
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "nonexistent" in result["error"]
        assert "does not exist" in result["error"]
        
        # Verify list was not created
        list_obj = self.test_manager.get_list("test-list")
        assert list_obj is None

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_all_parameters_and_tags(self):
        """Test MCP create_list with all parameters including tags"""
        # Create a tag
        self.test_manager.create_tag("project", "blue")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="full-test",
                title="Full Test List",
                items=["Task 1", "Task 2"],
                list_type="sequential",
                metadata={"priority": "high"},
                tags=["project"]
            )
        
        assert result["success"] is True
        assert result["list"]["list_key"] == "full-test"
        assert result["list"]["title"] == "Full Test List"
        assert result["list"]["list_type"] == "sequential"
        
        # Verify tag is assigned
        tags = self.test_manager.get_tags_for_list("full-test")
        assert len(tags) == 1
        assert tags[0].name == "project"
        
        # Verify items were created
        items = self.test_manager.get_list_items("full-test")
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_mcp_create_list_exception_handling(self):
        """Test MCP create_list exception handling"""
        # Mock manager to raise an exception
        mock_manager = MagicMock()
        mock_manager.create_list.side_effect = Exception("Database error")
        
        with patch('interfaces.mcp_server.init_manager', return_value=mock_manager):
            result = await todo_create_list(
                list_key="error-test",
                title="Error Test"
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_mcp_create_list_value_error_handling(self):
        """Test MCP create_list ValueError handling for non-existent tags"""
        # Create a tag but try to use non-existent one
        self.test_manager.create_tag("existing", "blue")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List",
                tags=["existing", "nonexistent"]
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "nonexistent" in result["error"]

    @pytest.mark.asyncio
    async def test_mcp_create_list_case_insensitive_tags(self):
        """Test MCP create_list with case-insensitive tag handling"""
        # Create a tag in lowercase
        self.test_manager.create_tag("frontend", "blue")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="test-list",
                title="Test List",
                tags=["FRONTEND"]  # Uppercase
            )
        
        assert result["success"] is True
        
        # Verify tag is assigned (normalized to lowercase)
        tags = self.test_manager.get_tags_for_list("test-list")
        assert len(tags) == 1
        assert tags[0].name == "frontend"

    @pytest.mark.asyncio 
    async def test_mcp_create_list_tags_parameter_optional(self):
        """Test that tags parameter is truly optional in MCP function"""
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            # Should work without specifying tags at all
            result = await todo_create_list(
                list_key="optional-test",
                title="Optional Test"
                # No tags parameter
            )
        
        assert result["success"] is True
        assert result["list"]["list_key"] == "optional-test"

    @pytest.mark.asyncio
    async def test_mcp_create_list_return_format_unchanged(self):
        """Test that return format is unchanged when using tags"""
        # Create a tag
        self.test_manager.create_tag("test-tag", "blue")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="format-test",
                title="Format Test",
                tags=["test-tag"]
            )
        
        # Verify return format matches expected MCP response structure
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        assert "list" in result
        assert isinstance(result["list"], dict)
        
        # Check that list contains expected fields
        list_data = result["list"]
        assert "list_key" in list_data
        assert "title" in list_data
        assert "list_type" in list_data
        
        # Verify clean_to_dict_result is working (no timestamps/IDs)
        assert "id" not in list_data
        assert "created_at" not in list_data
        assert "updated_at" not in list_data

    @pytest.mark.asyncio
    async def test_mcp_create_list_with_duplicate_tags(self):
        """Test MCP create_list with duplicate tags in input"""
        # Create a tag
        self.test_manager.create_tag("duplicate", "blue")
        
        with patch('interfaces.mcp_server.init_manager', return_value=self.test_manager):
            result = await todo_create_list(
                list_key="duplicate-test",
                title="Duplicate Test",
                tags=["duplicate", "duplicate", "DUPLICATE"]  # Same tag multiple times
            )
        
        assert result["success"] is True
        
        # Verify only one instance of the tag is assigned
        tags = self.test_manager.get_tags_for_list("duplicate-test")
        assert len(tags) == 1
        assert tags[0].name == "duplicate"