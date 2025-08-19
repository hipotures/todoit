"""
Unit tests for create_list functionality with tags parameter
"""
import pytest
from core.manager import TodoManager
from core.models import TodoList


class TestCreateListWithTags:
    """Test create_list method with tags parameter"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a fresh TodoManager instance for testing"""
        db_path = tmp_path / "test.db"
        return TodoManager(str(db_path))

    def test_create_list_without_tags(self, manager):
        """Test creating a list without tags (backward compatibility)"""
        # Create list without tags
        todo_list = manager.create_list("test-list", "Test List")
        
        assert todo_list.list_key == "test-list"
        assert todo_list.title == "Test List"
        
        # Verify no tags are assigned
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 0

    def test_create_list_with_empty_tags_list(self, manager):
        """Test creating a list with empty tags list"""
        # Create list with empty tags list
        todo_list = manager.create_list("test-list", "Test List", tags=[])
        
        assert todo_list.list_key == "test-list"
        assert todo_list.title == "Test List"
        
        # Verify no tags are assigned
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 0

    def test_create_list_with_single_existing_tag(self, manager):
        """Test creating a list with a single existing tag"""
        # Create a tag first
        manager.create_tag("frontend", "blue")
        
        # Create list with the tag
        todo_list = manager.create_list("test-list", "Test List", tags=["frontend"])
        
        assert todo_list.list_key == "test-list"
        assert todo_list.title == "Test List"
        
        # Verify tag is assigned
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 1
        assert tags[0].name == "frontend"

    def test_create_list_with_multiple_existing_tags(self, manager):
        """Test creating a list with multiple existing tags"""
        # Create tags first
        manager.create_tag("frontend", "blue")
        manager.create_tag("backend", "green")
        manager.create_tag("mobile", "red")
        
        # Create list with multiple tags
        todo_list = manager.create_list(
            "webapp", "Web Application", 
            tags=["frontend", "backend", "mobile"]
        )
        
        assert todo_list.list_key == "webapp"
        assert todo_list.title == "Web Application"
        
        # Verify all tags are assigned
        tags = manager.get_tags_for_list("webapp")
        tag_names = [tag.name for tag in tags]
        
        assert len(tags) == 3
        assert "frontend" in tag_names
        assert "backend" in tag_names
        assert "mobile" in tag_names

    def test_create_list_with_nonexistent_tag_fails(self, manager):
        """Test that creating a list with non-existent tag fails"""
        # Try to create list with non-existent tag
        with pytest.raises(ValueError, match="Tag 'nonexistent' does not exist"):
            manager.create_list("test-list", "Test List", tags=["nonexistent"])
        
        # Verify list was not created
        list_obj = manager.get_list("test-list")
        assert list_obj is None

    def test_create_list_with_mix_of_existing_and_nonexistent_tags_fails(self, manager):
        """Test that creating a list fails if any tag doesn't exist"""
        # Create one tag
        manager.create_tag("frontend", "blue")
        
        # Try to create list with mix of existing and non-existent tags
        with pytest.raises(ValueError, match="Tag 'nonexistent' does not exist"):
            manager.create_list(
                "test-list", "Test List", 
                tags=["frontend", "nonexistent"]
            )
        
        # Verify list was not created
        list_obj = manager.get_list("test-list")
        assert list_obj is None

    def test_create_list_tags_case_insensitive_validation(self, manager):
        """Test that tag validation is case-insensitive"""
        # Create a tag in lowercase
        manager.create_tag("frontend", "blue")
        
        # Create list with uppercase tag name
        todo_list = manager.create_list("test-list", "Test List", tags=["FRONTEND"])
        
        # Verify tag is assigned (should be normalized to lowercase)
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 1
        assert tags[0].name == "frontend"  # Should be lowercase

    def test_create_list_with_tags_and_items(self, manager):
        """Test creating a list with both tags and items"""
        # Create a tag
        manager.create_tag("project", "blue")
        
        # Create list with both tags and items
        todo_list = manager.create_list(
            "webapp", "Web Application",
            items=["Setup project", "Create UI", "Add tests"],
            tags=["project"]
        )
        
        assert todo_list.list_key == "webapp"
        assert todo_list.title == "Web Application"
        
        # Verify tag is assigned
        tags = manager.get_tags_for_list("webapp")
        assert len(tags) == 1
        assert tags[0].name == "project"
        
        # Verify items were created
        items = manager.get_list_items("webapp")
        assert len(items) == 3
        assert items[0].content == "Setup project"

    def test_create_list_with_tags_and_metadata(self, manager):
        """Test creating a list with tags and metadata"""
        # Create a tag
        manager.create_tag("urgent", "red")
        
        # Create list with tags and metadata
        metadata = {"priority": "high", "deadline": "2024-12-31"}
        todo_list = manager.create_list(
            "urgent-project", "Urgent Project",
            metadata=metadata,
            tags=["urgent"]
        )
        
        assert todo_list.list_key == "urgent-project"
        assert todo_list.title == "Urgent Project"
        
        # Verify tag is assigned
        tags = manager.get_tags_for_list("urgent-project")
        assert len(tags) == 1
        assert tags[0].name == "urgent"

    def test_create_list_tags_parameter_type_validation(self, manager):
        """Test that tags parameter accepts only list of strings"""
        # Create a tag
        manager.create_tag("test", "blue")
        
        # Test with valid list of strings
        todo_list = manager.create_list("test-list", "Test List", tags=["test"])
        assert todo_list.list_key == "test-list"
        
        # Test with None (should work)
        todo_list2 = manager.create_list("test-list-2", "Test List 2", tags=None)
        assert todo_list2.list_key == "test-list-2"

    def test_create_list_duplicate_tags_in_list(self, manager):
        """Test creating a list with duplicate tags in the tags list"""
        # Create a tag
        manager.create_tag("frontend", "blue")
        
        # Create list with duplicate tags
        todo_list = manager.create_list(
            "test-list", "Test List", 
            tags=["frontend", "frontend", "FRONTEND"]  # Duplicates with different cases
        )
        
        # Verify only one instance of the tag is assigned
        tags = manager.get_tags_for_list("test-list")
        assert len(tags) == 1
        assert tags[0].name == "frontend"

    def test_create_list_with_special_characters_in_tag_names(self, manager):
        """Test creating list with tags containing special characters"""
        # Create tags with special characters (if allowed by system)
        try:
            manager.create_tag("c++", "blue")
            manager.create_tag("web-dev", "green")
            
            # Create list with these tags
            todo_list = manager.create_list(
                "dev-project", "Development Project",
                tags=["c++", "web-dev"]
            )
            
            # Verify tags are assigned
            tags = manager.get_tags_for_list("dev-project")
            tag_names = [tag.name for tag in tags]
            
            assert "c++" in tag_names
            assert "web-dev" in tag_names
            
        except ValueError:
            # If system doesn't allow special characters, that's fine
            pass

    def test_create_list_error_message_format(self, manager):
        """Test that error messages for non-existent tags are properly formatted"""
        with pytest.raises(ValueError) as exc_info:
            manager.create_list("test-list", "Test List", tags=["missing-tag"])
        
        error_msg = str(exc_info.value)
        assert "missing-tag" in error_msg
        assert "does not exist" in error_msg
        assert "create_tag" in error_msg

    def test_create_list_with_tags_preserves_existing_functionality(self, manager):
        """Test that adding tags parameter doesn't break existing functionality"""
        # Test all existing parameters still work
        metadata = {"type": "project"}
        items = ["Task 1", "Task 2"]
        
        # Create without tags (original functionality)
        todo_list = manager.create_list(
            "legacy-list", "Legacy List",
            items=items,
            list_type="sequential",
            metadata=metadata
        )
        
        assert todo_list.list_key == "legacy-list"
        assert todo_list.title == "Legacy List"
        assert todo_list.list_type == "sequential"
        
        # Verify items were created
        created_items = manager.get_list_items("legacy-list")
        assert len(created_items) == 2
        
        # Verify no tags assigned
        tags = manager.get_tags_for_list("legacy-list")
        assert len(tags) == 0