"""
Unit tests for TODOIT_FORCE_TAGS environment variable functionality
Tests environment isolation and automatic tagging behavior
"""

import pytest
import os
import tempfile
from unittest.mock import patch
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


class TestForceTags:
    """Test TODOIT_FORCE_TAGS functionality"""

    def test_get_force_tags_empty(self):
        """Test _get_force_tags when TODOIT_FORCE_TAGS is not set"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {}, clear=True):
            force_tags = _get_force_tags()
            assert force_tags == []

    def test_get_force_tags_single(self):
        """Test _get_force_tags with single tag"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev"}, clear=True):
            force_tags = _get_force_tags()
            assert force_tags == ["dev"]

    def test_get_force_tags_multiple(self):
        """Test _get_force_tags with multiple tags"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(
            os.environ, {"TODOIT_FORCE_TAGS": "dev,test,staging"}, clear=True
        ):
            force_tags = _get_force_tags()
            assert set(force_tags) == {"dev", "test", "staging"}

    def test_get_force_tags_whitespace_handling(self):
        """Test _get_force_tags handles whitespace correctly"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(
            os.environ, {"TODOIT_FORCE_TAGS": " dev , test , staging "}, clear=True
        ):
            force_tags = _get_force_tags()
            assert set(force_tags) == {"dev", "test", "staging"}

    def test_get_force_tags_empty_values(self):
        """Test _get_force_tags ignores empty values"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,,test,,,"}, clear=True):
            force_tags = _get_force_tags()
            assert set(force_tags) == {"dev", "test"}

    def test_get_force_tags_case_normalization(self):
        """Test _get_force_tags normalizes to lowercase"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(
            os.environ, {"TODOIT_FORCE_TAGS": "DEV,Test,STAGING"}, clear=True
        ):
            force_tags = _get_force_tags()
            assert set(force_tags) == {"dev", "test", "staging"}


class TestFilterTagsWithForce:
    """Test _get_filter_tags priority logic with FORCE_TAGS"""

    def test_filter_tags_normal_mode(self):
        """Test _get_filter_tags in normal mode (no FORCE_TAGS)"""
        from interfaces.cli_modules.tag_commands import _get_filter_tags

        with patch.dict(
            os.environ, {"TODOIT_FILTER_TAGS": "work,personal"}, clear=True
        ):
            # No FORCE_TAGS - should use FILTER_TAGS
            filter_tags = _get_filter_tags(["urgent"])
            assert set(filter_tags) == {"work", "personal", "urgent"}

    def test_filter_tags_force_mode_overrides(self):
        """Test FORCE_TAGS overrides FILTER_TAGS"""
        from interfaces.cli_modules.tag_commands import _get_filter_tags

        env = {
            "TODOIT_FORCE_TAGS": "dev,test",
            "TODOIT_FILTER_TAGS": "work,personal",  # Should be ignored
        }
        with patch.dict(os.environ, env, clear=True):
            filter_tags = _get_filter_tags()
            assert set(filter_tags) == {"dev", "test"}

    def test_filter_tags_force_mode_with_cli_tags(self):
        """Test FORCE_TAGS combines with CLI tags"""
        from interfaces.cli_modules.tag_commands import _get_filter_tags

        env = {
            "TODOIT_FORCE_TAGS": "dev,test",
            "TODOIT_FILTER_TAGS": "work,personal",  # Should be ignored
        }
        with patch.dict(os.environ, env, clear=True):
            filter_tags = _get_filter_tags(["urgent", "critical"])
            assert set(filter_tags) == {"dev", "test", "urgent", "critical"}

    def test_filter_tags_force_empty_with_cli(self):
        """Test when FORCE_TAGS empty, falls back to normal mode"""
        from interfaces.cli_modules.tag_commands import _get_filter_tags

        with patch.dict(os.environ, {"TODOIT_FILTER_TAGS": "work"}, clear=True):
            # No FORCE_TAGS set
            filter_tags = _get_filter_tags(["urgent"])
            assert set(filter_tags) == {"work", "urgent"}


class TestAutoTaggingIntegration:
    """Test auto-tagging behavior in list creation"""

    def test_auto_tagging_disabled_when_no_force_tags(self, manager):
        """Test no auto-tagging when FORCE_TAGS not set"""
        # Mock the CLI create function behavior
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {}, clear=True):
            force_tags = _get_force_tags()
            assert force_tags == []

            # Create list normally
            todo_list = manager.create_list("test-list", "Test List")

            # Should not have any tags
            tags = manager.get_tags_for_list("test-list")
            assert len(tags) == 0

    def test_auto_tagging_logic(self, manager):
        """Test the logic that would be used in CLI create command"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "dev,test"}, clear=True):
            force_tags = _get_force_tags()
            assert set(force_tags) == {"dev", "test"}

            # Create list
            todo_list = manager.create_list("test-list", "Test List")

            # Simulate CLI auto-tagging logic
            for tag_name in force_tags:
                try:
                    manager.add_tag_to_list("test-list", tag_name)
                except ValueError:
                    # Tag doesn't exist, create it
                    manager.create_tag(tag_name, "blue")
                    manager.add_tag_to_list("test-list", tag_name)

            # Verify tags were added
            tags = manager.get_tags_for_list("test-list")
            tag_names = [tag.name for tag in tags]
            assert set(tag_names) == {"dev", "test"}

    def test_auto_tagging_creates_missing_tags(self, manager):
        """Test auto-tagging creates tags that don't exist"""
        from interfaces.cli_modules.tag_commands import _get_force_tags

        with patch.dict(os.environ, {"TODOIT_FORCE_TAGS": "nonexistent"}, clear=True):
            force_tags = _get_force_tags()
            assert force_tags == ["nonexistent"]

            # Create list
            todo_list = manager.create_list("test-list", "Test List")

            # Verify tag doesn't exist initially in all tags
            all_tags = manager.get_all_tags()
            tag_names = [tag.name for tag in all_tags]
            assert "nonexistent" not in tag_names

            # Simulate CLI auto-tagging - add_tag_to_list auto-creates tags
            for tag_name in force_tags:
                manager.add_tag_to_list("test-list", tag_name)

            # Verify tag was created and assigned
            tags = manager.get_tags_for_list("test-list")
            assert len(tags) == 1
            assert tags[0].name == "nonexistent"

            # Verify tag now exists globally
            all_tags = manager.get_all_tags()
            tag_names = [tag.name for tag in all_tags]
            assert "nonexistent" in tag_names


class TestEnvironmentIsolation:
    """Test environment isolation through FORCE_TAGS"""

    def test_environment_isolation_concept(self, manager):
        """Test the concept of environment isolation"""
        # Setup: Create lists with different environment tags
        manager.create_tag("dev", "blue")
        manager.create_tag("prod", "red")

        # Create dev list
        dev_list = manager.create_list("dev-feature", "Dev Feature")
        manager.add_tag_to_list("dev-feature", "dev")

        # Create prod list
        prod_list = manager.create_list("prod-release", "Prod Release")
        manager.add_tag_to_list("prod-release", "prod")

        # Create untagged list
        untagged_list = manager.create_list("untagged", "Untagged List")

        # Test dev environment isolation
        dev_lists = manager.list_all(filter_tags=["dev"])
        dev_keys = [l.list_key for l in dev_lists]
        assert "dev-feature" in dev_keys
        assert "prod-release" not in dev_keys
        assert "untagged" not in dev_keys

        # Test prod environment isolation
        prod_lists = manager.list_all(filter_tags=["prod"])
        prod_keys = [l.list_key for l in prod_lists]
        assert "prod-release" in prod_keys
        assert "dev-feature" not in prod_keys
        assert "untagged" not in prod_keys

        # Test no filtering - should see all
        all_lists = manager.list_all()
        all_keys = [l.list_key for l in all_lists]
        assert "dev-feature" in all_keys
        assert "prod-release" in all_keys
        assert "untagged" in all_keys
