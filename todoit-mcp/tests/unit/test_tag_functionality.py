"""
Unit tests for tag functionality
Tests core tag operations, validation, and business logic
"""
import pytest
from core.manager import TodoManager
from core.models import ListTag, ListTagAssignment
import tempfile
import os


@pytest.fixture
def temp_manager():
    """Create a temporary TodoManager for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    try:
        manager = TodoManager(db_path)
        yield manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


class TestTagManagement:
    """Test core tag management functionality"""
    
    def test_create_tag(self, temp_manager):
        """Test creating a new tag"""
        tag = temp_manager.create_tag("work", "blue")
        
        assert tag.name == "work"
        assert tag.color == "blue"
        assert tag.id > 0
        assert tag.created_at is not None
    
    def test_create_duplicate_tag(self, temp_manager):
        """Test creating duplicate tag raises error"""
        temp_manager.create_tag("work", "blue")
        
        with pytest.raises(ValueError, match="Tag 'work' already exists"):
            temp_manager.create_tag("work", "red")
    
    def test_get_tag_by_name(self, temp_manager):
        """Test retrieving tag by name"""
        created_tag = temp_manager.create_tag("urgent", "red")
        retrieved_tag = temp_manager.get_tag("urgent")
        
        assert retrieved_tag is not None
        assert retrieved_tag.name == "urgent"
        assert retrieved_tag.id == created_tag.id
    
    def test_get_all_tags(self, temp_manager):
        """Test getting all tags"""
        temp_manager.create_tag("work", "blue")
        temp_manager.create_tag("personal", "green")
        temp_manager.create_tag("urgent", "red")
        
        tags = temp_manager.get_all_tags()
        
        assert len(tags) == 3
        tag_names = [tag.name for tag in tags]
        assert "work" in tag_names
        assert "personal" in tag_names
        assert "urgent" in tag_names
    
    def test_delete_tag(self, temp_manager):
        """Test deleting a tag"""
        tag = temp_manager.create_tag("temp", "yellow")
        
        success = temp_manager.delete_tag("temp")
        assert success is True
        
        retrieved_tag = temp_manager.get_tag("temp")
        assert retrieved_tag is None


class TestListTagging:
    """Test list tagging functionality"""
    
    def test_add_tag_to_list(self, temp_manager):
        """Test adding tag to list"""
        # Create list and tag
        temp_manager.create_list("test_list", "Test List")
        temp_manager.create_tag("work", "blue")
        
        # Add tag to list
        assignment = temp_manager.add_tag_to_list("test_list", "work")
        
        assert assignment.list_id > 0
        assert assignment.tag_id > 0
        assert assignment.assigned_at is not None
    
    def test_add_tag_creates_if_not_exists(self, temp_manager):
        """Test that adding non-existent tag creates it"""
        temp_manager.create_list("test_list", "Test List")
        
        # This should create the tag automatically
        assignment = temp_manager.add_tag_to_list("test_list", "new_tag")
        
        assert assignment is not None
        
        # Verify tag was created
        tag = temp_manager.get_tag("new_tag")
        assert tag is not None
        assert tag.name == "new_tag"
    
    def test_remove_tag_from_list(self, temp_manager):
        """Test removing tag from list"""
        # Setup
        temp_manager.create_list("test_list", "Test List")
        temp_manager.add_tag_to_list("test_list", "work")
        
        # Remove tag
        success = temp_manager.remove_tag_from_list("test_list", "work")
        assert success is True
        
        # Verify removal
        tags = temp_manager.get_tags_for_list("test_list")
        assert len(tags) == 0
    
    def test_get_tags_for_list(self, temp_manager):
        """Test getting all tags for a specific list"""
        # Setup
        temp_manager.create_list("test_list", "Test List")
        temp_manager.add_tag_to_list("test_list", "work")
        temp_manager.add_tag_to_list("test_list", "urgent")
        
        # Test
        tags = temp_manager.get_tags_for_list("test_list")
        
        assert len(tags) == 2
        tag_names = [tag.name for tag in tags]
        assert "work" in tag_names
        assert "urgent" in tag_names
    
    def test_get_lists_by_tags(self, temp_manager):
        """Test filtering lists by tags"""
        # Setup
        temp_manager.create_list("project1", "Project 1")
        temp_manager.create_list("project2", "Project 2") 
        temp_manager.create_list("project3", "Project 3")
        
        temp_manager.add_tag_to_list("project1", "work")
        temp_manager.add_tag_to_list("project2", "work")
        temp_manager.add_tag_to_list("project3", "personal")
        
        # Test filtering by single tag
        work_lists = temp_manager.get_lists_by_tags(["work"])
        assert len(work_lists) == 2
        
        list_keys = [l.list_key for l in work_lists]
        assert "project1" in list_keys
        assert "project2" in list_keys
        
        # Test filtering by multiple tags (OR logic)
        all_lists = temp_manager.get_lists_by_tags(["work", "personal"])
        assert len(all_lists) == 3


class TestTagValidation:
    """Test tag validation and edge cases"""
    
    def test_tag_name_normalization(self, temp_manager):
        """Test that tag names are normalized to lowercase"""
        tag = temp_manager.create_tag("WORK", "blue")
        assert tag.name == "work"  # Should be normalized to lowercase
    
    def test_reserved_tag_names(self, temp_manager):
        """Test that reserved tag names are rejected"""
        with pytest.raises(ValueError, match="Tag name cannot be a reserved word"):
            temp_manager.create_tag("all", "blue")
        
        with pytest.raises(ValueError, match="Tag name cannot be a reserved word"):
            temp_manager.create_tag("none", "blue")
    
    def test_invalid_list_for_tagging(self, temp_manager):
        """Test adding tag to non-existent list"""
        with pytest.raises(ValueError, match="List 'nonexistent' not found"):
            temp_manager.add_tag_to_list("nonexistent", "work")


class TestTagFiltering:
    """Test tag-based filtering functionality"""
    
    def test_list_all_with_tag_filtering(self, temp_manager):
        """Test list_all with tag filtering"""
        # Setup
        temp_manager.create_list("work1", "Work List 1")
        temp_manager.create_list("work2", "Work List 2")
        temp_manager.create_list("personal1", "Personal List 1")
        
        temp_manager.add_tag_to_list("work1", "work")
        temp_manager.add_tag_to_list("work2", "work")  
        temp_manager.add_tag_to_list("personal1", "personal")
        
        # Test filtering
        work_lists = temp_manager.list_all(filter_tags=["work"])
        assert len(work_lists) == 2
        
        # Test no filtering
        all_lists = temp_manager.list_all()
        assert len(all_lists) == 3
        
        # Test filtering with non-existent tag
        empty_lists = temp_manager.list_all(filter_tags=["nonexistent"])
        assert len(empty_lists) == 0