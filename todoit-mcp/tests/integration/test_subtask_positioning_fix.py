"""
Integration test for subtask positioning fix
Tests that subtasks are positioned correctly without conflicts
"""

import pytest
import subprocess
import tempfile
import os
import shlex
from pathlib import Path


class TestSubtaskPositioningFix:
    """Integration test for subtask positioning fix"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file path"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)

    def run_cli(self, cmd, db_path):
        """Helper to run CLI commands"""
        full_cmd = f"python -m interfaces.cli --db {db_path} {cmd}"

        result = subprocess.run(
            shlex.split(full_cmd),
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result

    def test_subtask_positioning_no_conflicts(self, temp_db_path):
        """Test that subtasks are positioned without conflicts"""
        # Create list
        result = self.run_cli('list create test_positioning --title "Test Positioning"', temp_db_path)
        assert result.returncode == 0

        # Add multiple main tasks
        for i in range(1, 4):
            result = self.run_cli(f'item add test_positioning task{i} "Task {i}"', temp_db_path)
            assert result.returncode == 0

        # Add multiple subtasks to each task
        for task_num in range(1, 4):
            for sub_num in range(1, 4):
                result = self.run_cli(f'item add-subtask test_positioning task{task_num} task{task_num}_sub{sub_num} "Subtask {sub_num} for Task {task_num}"', temp_db_path)
                assert result.returncode == 0, f"Failed to add subtask {sub_num} to task {task_num}: {result.stderr}"

        # Verify all items are displayed correctly
        result = self.run_cli('list show test_positioning', temp_db_path)
        assert result.returncode == 0

        output = result.stdout
        
        # Verify each main task and its subtasks are present
        for task_num in range(1, 4):
            assert f"│ {task_num}        │ task{task_num}      │" in output, f"Task {task_num} should be displayed"
            
            for sub_num in range(1, 4):
                assert f"│ {task_num}.{sub_num}      │ task{task_num}_sub{sub_num} │" in output, f"Subtask {task_num}.{sub_num} should be displayed"

    def test_database_positions_are_sequential(self, temp_db_path):
        """Test that database positions are sequential without conflicts"""
        import sqlite3
        
        # Create list and tasks with subtasks
        self.run_cli('list create test_db --title "Test DB"', temp_db_path)
        self.run_cli('item add test_db task1 "Task 1"', temp_db_path)
        self.run_cli('item add test_db task2 "Task 2"', temp_db_path) 
        self.run_cli('item add-subtask test_db task1 sub1 "Sub 1"', temp_db_path)
        self.run_cli('item add-subtask test_db task2 sub2 "Sub 2"', temp_db_path)
        self.run_cli('item add-subtask test_db task1 sub3 "Sub 3"', temp_db_path)

        # Check database directly
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT item_key, position 
            FROM todo_items 
            WHERE list_id = 1 
            ORDER BY 
                parent_item_id IS NULL DESC,  -- Main tasks first
                parent_item_id,               -- Group subtasks by parent
                position                      -- Then by position within group
        """)
        positions = cursor.fetchall()
        
        conn.close()

        # Verify positions with new hierarchical positioning and ordering:
        # Order: main tasks first, then subtasks grouped by parent
        # - Main tasks: task1=1, task2=2 
        # - Subtasks of task1: sub1=1, sub3=2 (order added: sub1 first, sub3 second)
        # - Subtasks of task2: sub2=1
        expected_positions = [
            ('task1', 1),   # Main task position 1
            ('task2', 2),   # Main task position 2  
            ('sub1', 1),    # Subtask of task1, position 1 within parent
            ('sub3', 2),    # Subtask of task1, position 2 within parent (added after sub1)
            ('sub2', 1)     # Subtask of task2, position 1 within parent
        ]
        
        assert positions == expected_positions, f"Expected {expected_positions}, got {positions}"

    def test_mixed_task_and_subtask_creation(self, temp_db_path):
        """Test mixed creation order doesn't cause position conflicts"""
        # Create list
        self.run_cli('list create test_mixed --title "Test Mixed"', temp_db_path)
        
        # Create task1
        result = self.run_cli('item add test_mixed task1 "Task 1"', temp_db_path)
        assert result.returncode == 0
        
        # Add subtask to task1
        result = self.run_cli('item add-subtask test_mixed task1 sub1 "Sub 1"', temp_db_path)
        assert result.returncode == 0
        
        # Create task2 (after subtask)
        result = self.run_cli('item add test_mixed task2 "Task 2"', temp_db_path)
        assert result.returncode == 0
        
        # Add subtask to task2
        result = self.run_cli('item add-subtask test_mixed task2 sub2 "Sub 2"', temp_db_path)
        assert result.returncode == 0
        
        # Add another subtask to task1
        result = self.run_cli('item add-subtask test_mixed task1 sub3 "Sub 3"', temp_db_path)
        assert result.returncode == 0

        # Verify display works correctly
        result = self.run_cli('list show test_mixed', temp_db_path)
        assert result.returncode == 0
        
        output = result.stdout
        
        # All items should be displayed
        assert "task1" in output
        assert "task2" in output
        assert "sub1" in output
        assert "sub2" in output  
        assert "sub3" in output

    def test_hierarchy_organization_with_fixed_positioning(self, temp_db_path):
        """Test that hierarchy organization works correctly with fixed positioning"""
        # Create complex hierarchy
        self.run_cli('list create test_hierarchy --title "Test Hierarchy"', temp_db_path)
        self.run_cli('item add test_hierarchy main1 "Main 1"', temp_db_path)
        self.run_cli('item add test_hierarchy main2 "Main 2"', temp_db_path)
        self.run_cli('item add-subtask test_hierarchy main1 sub1_1 "Sub 1.1"', temp_db_path)
        self.run_cli('item add-subtask test_hierarchy main1 sub1_2 "Sub 1.2"', temp_db_path)
        self.run_cli('item add-subtask test_hierarchy main2 sub2_1 "Sub 2.1"', temp_db_path)

        # Test tree view
        result = self.run_cli('list show test_hierarchy --tree', temp_db_path)
        assert result.returncode == 0
        
        tree_output = result.stdout
        assert "Main 1" in tree_output
        assert "Main 2" in tree_output
        assert "Sub 1.1" in tree_output
        assert "Sub 1.2" in tree_output
        assert "Sub 2.1" in tree_output

        # Test table view 
        result = self.run_cli('list show test_hierarchy', temp_db_path)
        assert result.returncode == 0
        
        table_output = result.stdout
        # Verify hierarchical numbering
        assert "│ 1.1      │ sub1_1 │" in table_output
        assert "│ 1.2      │ sub1_2 │" in table_output  
        assert "│ 2.1      │ sub2_1 │" in table_output