"""
Test JSON output format for property commands
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for property list commands
"""
import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestPropertyJsonOutput:
    """Test JSON output format for property commands"""
    
    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
        # Clean environment before each test
        if 'TODOIT_OUTPUT_FORMAT' in os.environ:
            del os.environ['TODOIT_OUTPUT_FORMAT']
    
    def teardown_method(self):
        """Clean up after each test"""
        if 'TODOIT_OUTPUT_FORMAT' in os.environ:
            del os.environ['TODOIT_OUTPUT_FORMAT']
    
    def test_list_property_list_json_output_with_properties(self):
        """Test list property list command with JSON output when properties exist"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Set some properties
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'set', 'testlist', 'prop1', 'value1'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'set', 'testlist', 'prop2', 'value2'])
            assert result.exit_code == 0
            
            # Test JSON output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'list', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 2
            assert len(output_data['data']) == 2
            
            # Check data structure
            keys = [item['Key'] for item in output_data['data']]
            values = [item['Value'] for item in output_data['data']]
            assert 'prop1' in keys
            assert 'prop2' in keys
            assert 'value1' in values
            assert 'value2' in values
    
    def test_list_property_list_json_output_empty(self):
        """Test list property list command with JSON output when no properties exist"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list without properties
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Test JSON output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'list', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 0
            assert output_data['data'] == []
    
    def test_item_property_list_json_output_single_item(self):
        """Test item property list command with JSON output for single item"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list and item
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'testitem', 'Test Task'])
            assert result.exit_code == 0
            
            # Set some item properties
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'set', 'testlist', 'testitem', 'priority', 'high'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'set', 'testlist', 'testitem', 'category', 'work'])
            assert result.exit_code == 0
            
            # Test JSON output for specific item
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'list', 'testlist', 'testitem'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 2
            assert len(output_data['data']) == 2
            
            # Check data structure
            keys = [item['Key'] for item in output_data['data']]
            values = [item['Value'] for item in output_data['data']]
            assert 'priority' in keys
            assert 'category' in keys
            assert 'high' in values
            assert 'work' in values
    
    def test_item_property_list_json_output_single_item_empty(self):
        """Test item property list command with JSON output for single item with no properties"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list and item without properties
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'testitem', 'Test Task'])
            assert result.exit_code == 0
            
            # Test JSON output for specific item
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'list', 'testlist', 'testitem'])
            assert result.exit_code == 0
            
            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 0
            assert output_data['data'] == []
    
    def test_item_property_list_json_output_all_items(self):
        """Test item property list command with JSON output for all items in list"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list and items
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'item1', 'Task 1'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'item2', 'Task 2'])
            assert result.exit_code == 0
            
            # Set properties for items
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'set', 'testlist', 'item1', 'priority', 'high'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'set', 'testlist', 'item2', 'category', 'work'])
            assert result.exit_code == 0
            
            # Test JSON output for all items (no item_key specified)
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'list', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 2
            assert len(output_data['data']) == 2
            
            # Check data structure for all items
            item_keys = [item['Item Key'] for item in output_data['data']]
            prop_keys = [item['Property Key'] for item in output_data['data']]
            values = [item['Value'] for item in output_data['data']]
            assert 'item1' in item_keys
            assert 'item2' in item_keys
            assert 'priority' in prop_keys
            assert 'category' in prop_keys
            assert 'high' in values
            assert 'work' in values
    
    def test_item_property_list_json_output_all_items_empty(self):
        """Test item property list command with JSON output for all items when no properties exist"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list and items without properties
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'item1', 'Task 1'])
            assert result.exit_code == 0
            
            # Test JSON output for all items
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'property', 'list', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 0
            assert output_data['data'] == []
    
    def test_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Set a property
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'set', 'testlist', 'prop1', 'value1'])
            assert result.exit_code == 0
            
            # Test table output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'property', 'list', 'testlist'])
            assert result.exit_code == 0
            
            # Should not be JSON format
            assert not result.output.startswith('{')
            assert 'prop1' in result.output
            assert 'value1' in result.output