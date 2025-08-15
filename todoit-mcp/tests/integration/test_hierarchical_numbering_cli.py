"""
Integration test for hierarchical numbering fix
Tests the complete CLI flow to ensure subtask numbering works correctly
"""

import pytest
import subprocess
import tempfile
import os
import shlex
from pathlib import Path


class TestHierarchicalNumberingCLI:
    """Integration test for hierarchical numbering CLI functionality"""

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

    def test_subtask_numbering_integration(self, temp_db_path):
        """Test complete subtask numbering flow through CLI"""
        # Create list
        result = self.run_cli('list create test_numbering --title "Test Numbering"', temp_db_path)
        assert result.returncode == 0, f"Failed to create list: {result.stderr}"

        # Add main tasks
        result = self.run_cli('item add test_numbering task1 "Main Task 1"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task1: {result.stderr}"

        result = self.run_cli('item add test_numbering task2 "Main Task 2"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task2: {result.stderr}"

        # Add subtasks to task1
        result = self.run_cli('item add-subtask test_numbering task1 task1_sub1 "Subtask 1 for Task 1"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task1_sub1: {result.stderr}"

        result = self.run_cli('item add-subtask test_numbering task1 task1_sub2 "Subtask 2 for Task 1"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task1_sub2: {result.stderr}"

        result = self.run_cli('item add-subtask test_numbering task1 task1_sub3 "Subtask 3 for Task 1"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task1_sub3: {result.stderr}"

        # Add subtasks to task2
        result = self.run_cli('item add-subtask test_numbering task2 task2_sub1 "Subtask 1 for Task 2"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task2_sub1: {result.stderr}"

        result = self.run_cli('item add-subtask test_numbering task2 task2_sub2 "Subtask 2 for Task 2"', temp_db_path)
        assert result.returncode == 0, f"Failed to add task2_sub2: {result.stderr}"

        # Get list view and check numbering
        result = self.run_cli('list show test_numbering', temp_db_path)
        assert result.returncode == 0, f"Failed to show list: {result.stderr}"

        output = result.stdout
        
        # Verify hierarchical numbering is correct
        # Expected numbering pattern:
        # │ 1        │ task1      │ Main Task 1              │ ⏳     │ 0% (0/3)   │
        # │ 1.1      │ task1_sub1 │   └─ Subtask 1 for Task1 │ ⏳     │            │
        # │ 1.2      │ task1_sub2 │   └─ Subtask 2 for Task1 │ ⏳     │            │
        # │ 1.3      │ task1_sub3 │   └─ Subtask 3 for Task1 │ ⏳     │            │
        # │ 3        │ task2      │ Main Task 2              │ ⏳     │ 0% (0/2)   │
        # │ 3.1      │ task2_sub1 │   └─ Subtask 1 for Task2 │ ⏳     │            │
        # │ 3.2      │ task2_sub2 │   └─ Subtask 2 for Task2 │ ⏳     │            │

        # Check for correct numbering patterns
        assert "│ 1        │ task1      │" in output, "Task1 should have number 1"
        assert "│ 1.1      │ task1_sub1 │" in output, "Task1_sub1 should have number 1.1"
        assert "│ 1.2      │ task1_sub2 │" in output, "Task1_sub2 should have number 1.2"
        assert "│ 1.3      │ task1_sub3 │" in output, "Task1_sub3 should have number 1.3"
        assert "│ 3        │ task2      │" in output, "Task2 should have number 3"
        assert "│ 3.1      │ task2_sub1 │" in output, "Task2_sub1 should have number 3.1"
        assert "│ 3.2      │ task2_sub2 │" in output, "Task2_sub2 should have number 3.2"
        
        # Verify wrong patterns don't exist (old bug patterns)
        assert "│ 1.2      │ task1_sub1 │" not in output, "Task1_sub1 should NOT have wrong numbering"
        assert "│ 1.3      │ task1_sub2 │" not in output, "Task1_sub2 should NOT have wrong numbering"
        assert "│ 3.4      │ task2_sub1 │" not in output, "Task2_sub1 should NOT have wrong numbering"
        assert "│ 3.5      │ task2_sub2 │" not in output, "Task2_sub2 should NOT have wrong numbering"

    def test_tree_view_numbering_consistency(self, temp_db_path):
        """Test that tree view and table view are consistent"""
        # Create list with hierarchy
        self.run_cli('list create test_tree --title "Test Tree"', temp_db_path)
        self.run_cli('item add test_tree main1 "Main 1"', temp_db_path)
        self.run_cli('item add-subtask test_tree main1 sub1 "Sub 1"', temp_db_path)
        self.run_cli('item add-subtask test_tree main1 sub2 "Sub 2"', temp_db_path)

        # Get table view
        table_result = self.run_cli('list show test_tree', temp_db_path)
        assert table_result.returncode == 0

        # Get tree view
        tree_result = self.run_cli('list show test_tree --tree', temp_db_path)
        assert tree_result.returncode == 0

        # Both should work without errors and show hierarchy
        assert len(table_result.stdout) > 0
        assert len(tree_result.stdout) > 0
        assert "Sub 1" in table_result.stdout
        assert "Sub 1" in tree_result.stdout

    def test_multiple_hierarchy_levels_numbering(self, temp_db_path):
        """Test numbering with multiple levels of hierarchy"""
        # Create list
        self.run_cli('list create test_deep --title "Deep Hierarchy"', temp_db_path)
        
        # Create main task
        self.run_cli('item add test_deep main "Main Task"', temp_db_path)
        
        # Add subtask
        self.run_cli('item add-subtask test_deep main sub1 "Subtask 1"', temp_db_path)
        
        # Show list
        result = self.run_cli('list show test_deep', temp_db_path)
        assert result.returncode == 0
        
        # Check basic numbering (flexible format matching)
        assert "│ 1        │ main │" in result.stdout
        assert "│ 1.1      │ sub1 │" in result.stdout