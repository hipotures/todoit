"""
Unit tests for FORCE_TAGS AND logic implementation
Tests the new get_lists_by_tags_all() method and _check_force_tags_access() logic
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from core.manager import TodoManager


@pytest.fixture
def manager():
    """Create temporary TodoManager for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name

    try:
        manager = TodoManager(db_path)
        yield manager
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


class TestGetListsByTagsAll:
    """Test database get_lists_by_tags_all() method for AND logic"""

    def test_get_lists_by_tags_all_single_tag(self, manager):
        """Test AND logic with single tag"""
        # Setup: Create tags
        manager.create_tag("dev", "blue")
        manager.create_tag("urgent", "red")

        # Create lists with different tag combinations
        list1 = manager.create_list("list1", "List 1")
        manager.add_tag_to_list("list1", "dev")

        list2 = manager.create_list("list2", "List 2")
        manager.add_tag_to_list("list2", "urgent")

        list3 = manager.create_list("list3", "List 3")
        manager.add_tag_to_list("list3", "dev")
        manager.add_tag_to_list("list3", "urgent")

        # Test: Get lists with dev tag only
        dev_lists = manager.db.get_lists_by_tags_all(["dev"])
        dev_keys = [l.list_key for l in dev_lists]
        
        # Should return both list1 and list3 (both have dev tag)
        assert set(dev_keys) == {"list1", "list3"}

    def test_get_lists_by_tags_all_multiple_tags_and_logic(self, manager):
        """Test AND logic with multiple tags - lists must have ALL tags"""
        # Setup: Create tags
        manager.create_tag("dev", "blue")
        manager.create_tag("urgent", "red")
        manager.create_tag("backend", "green")

        # Create lists with different tag combinations
        list1 = manager.create_list("list1", "Has dev only")
        manager.add_tag_to_list("list1", "dev")

        list2 = manager.create_list("list2", "Has dev+urgent")
        manager.add_tag_to_list("list2", "dev")
        manager.add_tag_to_list("list2", "urgent")

        list3 = manager.create_list("list3", "Has all three")
        manager.add_tag_to_list("list3", "dev")
        manager.add_tag_to_list("list3", "urgent")
        manager.add_tag_to_list("list3", "backend")

        list4 = manager.create_list("list4", "Has urgent+backend only")
        manager.add_tag_to_list("list4", "urgent")
        manager.add_tag_to_list("list4", "backend")

        # Test: Get lists that have BOTH dev AND urgent (AND logic)
        matching_lists = manager.db.get_lists_by_tags_all(["dev", "urgent"])
        matching_keys = [l.list_key for l in matching_lists]
        
        # Should return only list2 and list3 (both have dev AND urgent)
        assert set(matching_keys) == {"list2", "list3"}

    def test_get_lists_by_tags_all_no_matches(self, manager):
        """Test AND logic when no lists match all criteria"""
        # Setup: Create tags and lists
        manager.create_tag("dev", "blue")
        manager.create_tag("prod", "red")
        
        list1 = manager.create_list("list1", "Dev only")
        manager.add_tag_to_list("list1", "dev")

        list2 = manager.create_list("list2", "Prod only")
        manager.add_tag_to_list("list2", "prod")

        # Test: Get lists that have BOTH dev AND prod (no matches)
        matching_lists = manager.db.get_lists_by_tags_all(["dev", "prod"])
        
        assert len(matching_lists) == 0

    def test_get_lists_by_tags_all_empty_input(self, manager):
        """Test AND logic with empty tag list"""
        # Create some lists
        manager.create_list("list1", "List 1")
        
        # Test with empty tag list
        matching_lists = manager.db.get_lists_by_tags_all([])
        
        # Should return empty list (no criteria means no matches)
        assert len(matching_lists) == 0

    def test_get_lists_by_tags_all_nonexistent_tags(self, manager):
        """Test AND logic with nonexistent tags"""
        # Create a list with real tag
        manager.create_tag("dev", "blue")
        list1 = manager.create_list("list1", "List 1")
        manager.add_tag_to_list("list1", "dev")
        
        # Test with nonexistent tag
        matching_lists = manager.db.get_lists_by_tags_all(["nonexistent"])
        
        # Should return empty list
        assert len(matching_lists) == 0

    def test_get_lists_by_tags_all_case_sensitivity(self, manager):
        """Test AND logic handles case normalization"""
        # Setup: Create tags (always lowercase in DB)
        manager.create_tag("dev", "blue")
        
        list1 = manager.create_list("list1", "List 1")
        manager.add_tag_to_list("list1", "dev")

        # Test: Query with mixed case should work
        matching_lists = manager.db.get_lists_by_tags_all(["DEV"])
        matching_keys = [l.list_key for l in matching_lists]
        
        assert "list1" in matching_keys


class TestCheckForceTagsAccess:
    """Test _check_force_tags_access() method for access control"""

    def test_check_force_tags_access_no_force_tags(self, manager):
        """Test access check when no force_tags are set"""
        # Create a list
        manager.create_list("test-list", "Test List")
        
        # Test: When no force_tags, should allow access to any list
        assert manager._check_force_tags_access("test-list") is True
        assert manager._check_force_tags_access("nonexistent") is True

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,test"}, clear=True)
    def test_check_force_tags_access_with_force_tags_allowed(self):
        """Test access check when list has all required force_tags"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create manager with force_tags environment
            manager = TodoManager(db_path)
            
            # Setup: Create list - it will be auto-tagged with all force_tags
            list1 = manager.create_list("accessible-list", "Accessible List")
            
            # Verify auto-tagging worked
            tags = manager.get_tags_for_list("accessible-list")
            tag_names = [tag.name for tag in tags]
            assert set(tag_names) == {"dev", "test"}
            
            # Test: Should allow access (list has both dev AND test)
            assert manager._check_force_tags_access("accessible-list") is True
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,test"}, clear=True)
    def test_check_force_tags_access_with_force_tags_denied(self):
        """Test access check when list doesn't have all required force_tags"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create lists without force_tags first, then add force_tags to manager
            with patch.dict(os.environ, {}, clear=True):
                temp_manager = TodoManager(db_path)
                
                # Create tags and lists without auto-tagging
                temp_manager.create_tag("dev", "blue")
                temp_manager.create_tag("test", "red")
                
                # List with only dev tag (missing test)
                list1 = temp_manager.create_list("partial-list", "Partial List")
                temp_manager.add_tag_to_list("partial-list", "dev")
                
                # List with no force_tags
                list2 = temp_manager.create_list("untagged-list", "Untagged List")
            
            # Now create manager with force_tags environment
            manager = TodoManager(db_path)
            
            # Test: Should deny access (lists don't have both dev AND test)
            assert manager._check_force_tags_access("partial-list") is False
            assert manager._check_force_tags_access("untagged-list") is False
            assert manager._check_force_tags_access("nonexistent-list") is False
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev"}, clear=True)
    def test_check_force_tags_access_single_force_tag(self):
        """Test access check with single force_tag"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create manager with single force_tag
            manager = TodoManager(db_path)
            
            # List with dev tag (auto-tagged)
            list1 = manager.create_list("dev-list", "Dev List")
            
            # Create list without force_tags by temporarily disabling them
            with patch.dict(os.environ, {}, clear=True):
                temp_manager = TodoManager(db_path)
                list2 = temp_manager.create_list("other-list", "Other List")
            
            # Recreate manager with force_tags
            manager = TodoManager(db_path)
            
            # Test: Should allow access only to dev-tagged list
            assert manager._check_force_tags_access("dev-list") is True
            assert manager._check_force_tags_access("other-list") is False
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestForceTagsManagerIntegration:
    """Test force_tags integration in TodoManager methods"""

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,test"}, clear=True)
    def test_list_all_with_force_tags_and_logic(self):
        """Test list_all() uses AND logic for force_tags"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create lists without force_tags first
            with patch.dict(os.environ, {}, clear=True):
                temp_manager = TodoManager(db_path)
                
                # Setup: Create tags
                temp_manager.create_tag("dev", "blue")
                temp_manager.create_tag("test", "red")
                temp_manager.create_tag("other", "green")
                
                # Create lists with different tag combinations
                # This should be accessible (has both dev AND test)
                list1 = temp_manager.create_list("accessible", "Accessible List")
                temp_manager.add_tag_to_list("accessible", "dev")
                temp_manager.add_tag_to_list("accessible", "test")
                
                # This should NOT be accessible (has only dev, missing test)
                list2 = temp_manager.create_list("partial", "Partial List")
                temp_manager.add_tag_to_list("partial", "dev")
                
                # This should NOT be accessible (has no force_tags)
                list3 = temp_manager.create_list("untagged", "Untagged List")
                
                # This should be accessible (has dev, test, and extra tag)
                list4 = temp_manager.create_list("extra", "Extra Tagged List")
                temp_manager.add_tag_to_list("extra", "dev")
                temp_manager.add_tag_to_list("extra", "test")
                temp_manager.add_tag_to_list("extra", "other")
            
            # Now create manager with force_tags
            manager = TodoManager(db_path)
            
            # Test: list_all() should return only lists with ALL force_tags
            visible_lists = manager.list_all()
            visible_keys = [l.list_key for l in visible_lists]
            
            # Should only see lists that have BOTH dev AND test
            assert set(visible_keys) == {"accessible", "extra"}
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev"}, clear=True)
    def test_get_list_with_force_tags_access_control(self):
        """Test get_list() respects force_tags access control"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create accessible list with force_tags
            manager = TodoManager(db_path)
            
            # Accessible list (auto-tagged with dev)
            list1 = manager.create_list("dev-list", "Dev List")
            
            # Create inaccessible list without force_tags
            with patch.dict(os.environ, {}, clear=True):
                temp_manager = TodoManager(db_path)
                list2 = temp_manager.create_list("other-list", "Other List")
            
            # Recreate manager with force_tags
            manager = TodoManager(db_path)
            
            # Test: get_list() should respect access control
            accessible = manager.get_list("dev-list")
            inaccessible = manager.get_list("other-list")
            
            assert accessible is not None
            assert accessible.list_key == "dev-list"
            assert inaccessible is None  # Access denied
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,test"}, clear=True)
    def test_auto_tagging_in_create_list(self):
        """Test automatic tagging of new lists with force_tags"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create manager with force_tags
            manager = TodoManager(db_path)
            
            # Test: Create a new list
            new_list = manager.create_list("new-list", "New List")
            
            # Verify: Should be auto-tagged with all force_tags
            tags = manager.get_tags_for_list("new-list")
            tag_names = [tag.name for tag in tags]
            
            assert set(tag_names) == {"dev", "test"}
            
            # Verify: Tags were auto-created if they didn't exist
            all_tags = manager.get_all_tags()
            all_tag_names = [tag.name for tag in all_tags]
            assert "dev" in all_tag_names
            assert "test" in all_tag_names
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev"}, clear=True)
    def test_prevent_force_tag_removal(self):
        """Test prevention of force_tag removal from lists"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create manager with force_tags
            manager = TodoManager(db_path)
            
            # Setup: Create list with force_tag
            list1 = manager.create_list("dev-list", "Dev List")
            # List should be auto-tagged with "dev"
            
            # Test: Try to remove force_tag
            with pytest.raises(ValueError) as excinfo:
                manager.remove_tag_from_list("dev-list", "dev")
            
            assert "Cannot remove force tag" in str(excinfo.value)
            
            # Verify: Tag is still there
            tags = manager.get_tags_for_list("dev-list")
            tag_names = [tag.name for tag in tags]
            assert "dev" in tag_names
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev"}, clear=True)
    def test_block_modification_of_inaccessible_lists(self):
        """Test blocking modifications to lists without proper force_tags"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create manager WITHOUT force_tags first
            with patch.dict(os.environ, {}, clear=True):
                temp_manager = TodoManager(db_path)
                temp_manager.create_list("restricted-list", "Restricted List")
            
            # Now create manager WITH force_tags
            manager = TodoManager(db_path)
            
            # Test: Try to add tag to inaccessible list
            with pytest.raises(ValueError) as excinfo:
                manager.add_tag_to_list("restricted-list", "some-tag")
            
            assert "Access denied" in str(excinfo.value)
            assert "required force tags" in str(excinfo.value)
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestComparisonWithOriginalLogic:
    """Test comparison between AND logic and original OR logic"""

    def test_and_vs_or_logic_difference(self, manager):
        """Demonstrate difference between AND and OR logic"""
        # Setup: Create tags
        manager.create_tag("dev", "blue")
        manager.create_tag("test", "red")
        manager.create_tag("urgent", "green")
        
        # Create lists with different combinations
        list1 = manager.create_list("list1", "Has dev only")
        manager.add_tag_to_list("list1", "dev")
        
        list2 = manager.create_list("list2", "Has test only")  
        manager.add_tag_to_list("list2", "test")
        
        list3 = manager.create_list("list3", "Has dev+test")
        manager.add_tag_to_list("list3", "dev")
        manager.add_tag_to_list("list3", "test")
        
        list4 = manager.create_list("list4", "Has all three")
        manager.add_tag_to_list("list4", "dev")
        manager.add_tag_to_list("list4", "test") 
        manager.add_tag_to_list("list4", "urgent")
        
        # Test OR logic (original get_lists_by_tags)
        or_results = manager.db.get_lists_by_tags(["dev", "test"])
        or_keys = [l.list_key for l in or_results]
        # OR logic: lists that have dev OR test (any of them)
        assert set(or_keys) == {"list1", "list2", "list3", "list4"}
        
        # Test AND logic (new get_lists_by_tags_all)
        and_results = manager.db.get_lists_by_tags_all(["dev", "test"])
        and_keys = [l.list_key for l in and_results]
        # AND logic: lists that have dev AND test (both required)
        assert set(and_keys) == {"list3", "list4"}
        
        # Verify the difference
        or_only = set(or_keys) - set(and_keys)
        assert or_only == {"list1", "list2"}  # These have only one of the required tags