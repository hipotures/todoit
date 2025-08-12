"""
Test JSON output format for item next command
Verifies that TODOIT_OUTPUT_FORMAT=json works correctly for item next command
"""
import os
import json
import pytest
from click.testing import CliRunner
from interfaces.cli import cli


class TestItemNextJsonOutput:
    """Test JSON output format for item next and next-smart commands"""
    
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
    
    def test_item_next_json_output_with_pending_task(self):
        """Test item next command with JSON output when pending task exists"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add a pending task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Pending Task'])
            assert result.exit_code == 0
            
            # Test JSON output for next task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 1
            assert len(output_data['data']) == 1
            
            # Check data structure
            task_data = output_data['data'][0]
            assert 'Task' in task_data
            assert 'Key' in task_data
            assert 'Position' in task_data
            assert 'Status' in task_data
            assert task_data['Task'] == 'Pending Task'
            assert task_data['Key'] == 'task1'
            assert task_data['Position'] == '1'
    
    def test_item_next_json_output_with_multiple_pending_tasks(self):
        """Test item next command with JSON output when multiple pending tasks exist (should return first)"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add multiple pending tasks
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'First Task'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task2', 'Second Task'])
            assert result.exit_code == 0
            
            # Test JSON output for next task (should return first)
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data['count'] == 1
            assert len(output_data['data']) == 1
            
            # Should return the first task (position 1)
            task_data = output_data['data'][0]
            assert task_data['Task'] == 'First Task'
            assert task_data['Key'] == 'task1'
            assert task_data['Position'] == '1'
    
    def test_item_next_json_output_no_pending_tasks(self):
        """Test item next command with JSON output when no pending tasks exist"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add a completed task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Completed Task'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'status', 'testlist', 'task1', '--status', 'completed'])
            assert result.exit_code == 0
            
            # Test JSON output when no pending tasks
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 0
            assert output_data['data'] == []
    
    def test_item_next_json_output_skip_in_progress_tasks(self):
        """Test item next command with JSON output skips in_progress tasks"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add tasks with different statuses
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'In Progress Task'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task2', 'Pending Task'])
            assert result.exit_code == 0
            
            # Set first task to in_progress
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'status', 'testlist', 'task1', '--status', 'in_progress'])
            assert result.exit_code == 0
            
            # Test JSON output - should return the pending task, not in_progress
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data['count'] == 1
            assert len(output_data['data']) == 1
            
            # Should return the pending task (task2)
            task_data = output_data['data'][0]
            assert task_data['Task'] == 'Pending Task'
            assert task_data['Key'] == 'task2'
            assert task_data['Position'] == '2'
    
    def test_item_next_table_format_still_works(self):
        """Test that table format still works correctly (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table
        
        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Test Task'])
            assert result.exit_code == 0
            
            # Test table output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Should not be JSON format
            assert not result.output.startswith('{')
            assert 'Test Task' in result.output
            assert 'task1' in result.output
    
    def test_item_next_yaml_format(self):
        """Test that YAML format works correctly"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'yaml'
        
        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Test Task'])
            assert result.exit_code == 0
            
            # Test YAML output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Should be YAML format
            assert 'title:' in result.output
            assert 'count:' in result.output
            assert 'data:' in result.output
            assert 'Test Task' in result.output
            assert 'task1' in result.output
    
    def test_item_next_xml_format(self):
        """Test that XML format works correctly"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'xml'
        
        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Test Task'])
            assert result.exit_code == 0
            
            # Test XML output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next', 'testlist'])
            assert result.exit_code == 0
            
            # Should be XML format
            assert '<todoit_output>' in result.output
            assert '<title>' in result.output
            assert '<count>' in result.output
            assert '<data>' in result.output
            assert 'Test Task' in result.output
            assert 'task1' in result.output
    
    # Tests for item next-smart command
    
    def test_item_next_smart_json_output_with_pending_task(self):
        """Test item next-smart command with JSON output when pending task exists"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add a pending task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Pending Task'])
            assert result.exit_code == 0
            
            # Test JSON output for next-smart task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next-smart', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 1
            assert len(output_data['data']) == 1
            
            # Check data structure
            task_data = output_data['data'][0]
            assert 'Type' in task_data
            assert 'Task' in task_data
            assert 'Key' in task_data
            assert 'Position' in task_data
            assert 'Status' in task_data
            assert task_data['Type'] == 'Task'  # Should be Task, not Subtask
            assert task_data['Task'] == 'Pending Task'
            assert task_data['Key'] == 'task1'
            assert task_data['Position'] == '1'
    
    def test_item_next_smart_json_output_with_subtask(self):
        """Test item next-smart command with JSON output when next item is a subtask"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            # Add a parent task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'parent', 'Parent Task'])
            assert result.exit_code == 0
            
            # Add a subtask
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add-subtask', 'testlist', 'parent', 'subtask1', 'Subtask 1'])
            assert result.exit_code == 0
            
            # Test JSON output for next-smart task (should prioritize subtask)
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next-smart', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format
            output_data = json.loads(result.output)
            assert output_data['count'] == 1
            assert len(output_data['data']) == 1
            
            # Check that it returns the subtask
            task_data = output_data['data'][0]
            assert task_data['Type'] == 'Subtask'  # Should be Subtask
            assert task_data['Task'] == 'Subtask 1'
            assert task_data['Key'] == 'subtask1'
    
    def test_item_next_smart_json_output_no_pending_tasks(self):
        """Test item next-smart command with JSON output when no pending tasks exist"""
        os.environ['TODOIT_OUTPUT_FORMAT'] = 'json'
        
        with self.runner.isolated_filesystem():
            # Create a test list with completed task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Completed Task'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'status', 'testlist', 'task1', '--status', 'completed'])
            assert result.exit_code == 0
            
            # Test JSON output when no pending tasks
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next-smart', 'testlist'])
            assert result.exit_code == 0
            
            # Verify JSON format for empty result
            output_data = json.loads(result.output)
            assert 'title' in output_data
            assert 'count' in output_data
            assert 'data' in output_data
            assert output_data['count'] == 0
            assert output_data['data'] == []
    
    def test_item_next_smart_table_format_still_works(self):
        """Test that table format still works correctly for next-smart (default behavior)"""
        # Don't set TODOIT_OUTPUT_FORMAT, should default to table
        
        with self.runner.isolated_filesystem():
            # Create a test list and task
            result = self.runner.invoke(cli, ['--db', 'test.db', 'list', 'create', 'testlist', '--title', 'Test List'])
            assert result.exit_code == 0
            
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'add', 'testlist', 'task1', 'Test Task'])
            assert result.exit_code == 0
            
            # Test table output
            result = self.runner.invoke(cli, ['--db', 'test.db', 'item', 'next-smart', 'testlist'])
            assert result.exit_code == 0
            
            # Should not be JSON format
            assert not result.output.startswith('{')
            assert 'Test Task' in result.output
            assert 'task1' in result.output
            assert 'Task' in result.output  # Should show Type column