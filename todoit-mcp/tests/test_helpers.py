"""
Test helpers for mocking FORCE_TAGS functionality
Provides utilities to patch _check_list_access in CLI tests
"""

from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def mock_list_access(allow_access=True):
    """
    Context manager to mock _check_list_access for CLI tests
    
    Args:
        allow_access (bool): Whether to allow or deny list access
    
    Usage:
        with mock_list_access(allow_access=True):
            result = runner.invoke(command, args)
    """
    with patch('interfaces.cli_modules.item_commands._check_list_access') as mock_item_access, \
         patch('interfaces.cli_modules.list_commands._check_list_access') as mock_list_access_cmd:
        mock_item_access.return_value = allow_access
        mock_list_access_cmd.return_value = allow_access
        yield


@contextmanager  
def mock_force_tags_environment(force_tags_list=None):
    """
    Context manager to mock FORCE_TAGS environment
    
    Args:
        force_tags_list (List[str]): List of forced tags, or None for no filtering
    
    Usage:
        with mock_force_tags_environment(['dev']):
            # Test with dev environment isolation
    """
    if force_tags_list is None:
        force_tags_list = []
        
    with patch('interfaces.cli_modules.tag_commands._get_filter_tags') as mock_filter_tags:
        mock_filter_tags.return_value = force_tags_list
        yield