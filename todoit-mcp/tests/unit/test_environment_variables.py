"""
Unit tests for environment variable handling in TodoManager
"""

import os
import tempfile
import pytest
from unittest.mock import patch
from core.manager import TodoManager


class TestEnvironmentVariables:
    """Test environment variable handling in TodoManager"""

    def test_todoit_db_path_environment_variable(self):
        """Test TODOIT_DB_PATH environment variable"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {"TODOIT_DB_PATH": test_db_path}, clear=True):
            manager = TodoManager()
            assert manager.db.db_path == test_db_path

    def test_todoit_db_path_with_home_expansion(self):
        """Test TODOIT_DB_PATH with $HOME expansion"""
        # Create a test path with $HOME variable
        test_filename = "test_todoit.db"
        home_path = f"$HOME/{test_filename}"
        expected_path = os.path.expandvars(home_path)
        
        # Keep existing environment, just set TODOIT_DB_PATH
        with patch.dict(os.environ, {"TODOIT_DB_PATH": home_path}):
            manager = TodoManager()
            assert manager.db.db_path == expected_path

    def test_no_environment_variable_raises_system_exit(self):
        """Test that missing TODOIT_DB_PATH raises SystemExit"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                TodoManager()

    def test_explicit_db_path_overrides_environment(self):
        """Test that explicit db_path parameter overrides environment variable"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp1:
            env_db_path = tmp1.name
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp2:
            explicit_db_path = tmp2.name
        
        with patch.dict(os.environ, {"TODOIT_DB_PATH": env_db_path}, clear=True):
            manager = TodoManager(explicit_db_path)
            assert manager.db.db_path == explicit_db_path

    def test_force_tags_environment_variable(self):
        """Test TODOIT_FORCE_TAGS environment variable"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {
            "TODOIT_DB_PATH": test_db_path,
            "TODOIT_FORCE_TAGS": "dev,test,staging"
        }, clear=True):
            manager = TodoManager()
            assert manager.force_tags == ["dev", "test", "staging"]

    def test_force_tags_with_spaces_and_empty_values(self):
        """Test TODOIT_FORCE_TAGS with spaces and empty values"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {
            "TODOIT_DB_PATH": test_db_path,
            "TODOIT_FORCE_TAGS": " dev , , test , , staging "
        }, clear=True):
            manager = TodoManager()
            assert manager.force_tags == ["dev", "test", "staging"]

    def test_force_tags_case_normalization(self):
        """Test TODOIT_FORCE_TAGS case normalization"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {
            "TODOIT_DB_PATH": test_db_path,
            "TODOIT_FORCE_TAGS": "DEV,Test,STAGING"
        }, clear=True):
            manager = TodoManager()
            assert manager.force_tags == ["dev", "test", "staging"]

    def test_empty_force_tags(self):
        """Test empty TODOIT_FORCE_TAGS"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {
            "TODOIT_DB_PATH": test_db_path,
            "TODOIT_FORCE_TAGS": ""
        }, clear=True):
            manager = TodoManager()
            assert manager.force_tags == []

    def test_no_force_tags_environment(self):
        """Test when TODOIT_FORCE_TAGS is not set"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            test_db_path = tmp.name
        
        with patch.dict(os.environ, {"TODOIT_DB_PATH": test_db_path}, clear=True):
            manager = TodoManager()
            assert manager.force_tags == []