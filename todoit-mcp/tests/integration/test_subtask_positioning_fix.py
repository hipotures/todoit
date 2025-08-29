"""
Integration test for subitem positioning fix
Tests that subtasks are positioned correctly without conflicts
"""

import pytest
from click.testing import CliRunner

from interfaces.cli import cli


class TestSubtaskPositioningFix:
    """Integration test for subitem positioning fix"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner"""
        return CliRunner()

    def run_cli(self, cmd_string, db_path):
        """Helper to run CLI commands"""
        import shlex

        runner = CliRunner()
        cmd_list = shlex.split(cmd_string)
        result = runner.invoke(cli, ["--db-path", db_path] + cmd_list)
        if result.exit_code != 0:
            print(f"CLI command failed: {cmd_string}")
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        return result

    def run_cli_old(self, runner, cmd_list):
        """Helper for isolated filesystem tests"""
        return runner.invoke(cli, ["--db-path", "test.db"] + cmd_list)

    def test_subtask_positioning_no_conflicts(self, runner):
        """Test that subtasks are positioned without conflicts"""
        with runner.isolated_filesystem():
            # Create list
            result = self.run_cli_old(
                runner,
                [
                    "list",
                    "create",
                    "--list",
                    "test_positioning",
                    "--title",
                    "Test Positioning",
                ],
            )
            assert result.exit_code == 0

            # Add multiple main tasks
            for i in range(1, 4):
                result = self.run_cli_old(
                    runner,
                    [
                        "item",
                        "add",
                        "--list",
                        "test_positioning",
                        "--item",
                        f"item{i}",
                        "--title",
                        f"Item {i}",
                    ],
                )
                assert result.exit_code == 0

            # Add multiple subtasks to each task
            for task_num in range(1, 4):
                for sub_num in range(1, 4):
                    result = self.run_cli_old(
                        runner,
                        [
                            "item",
                            "add",
                            "--list",
                            "test_positioning",
                            "--item",
                            f"item{task_num}",
                            "--subitem",
                            f"item{task_num}_sub{sub_num}",
                            "--title",
                            f"Subitem {sub_num} for Item {task_num}",
                        ],
                    )
                    assert (
                        result.exit_code == 0
                    ), f"Failed to add subitem {sub_num} to item {task_num}: {result.output}"

            # Verify all items are displayed correctly
            result = self.run_cli_old(
                runner, ["list", "show", "--list", "test_positioning"]
            )
            assert result.exit_code == 0

            output = result.output

            # Verify each main task and its subtasks are present
            for task_num in range(1, 4):
                assert (
                    f"│ {task_num}        │ item{task_num}" in output
                ), f"Item {task_num} should be displayed"

                # Verify subitems are displayed with correct hierarchical numbering
                for sub_num in range(1, 4):
                    assert (
                        f"│ {task_num}.{sub_num}      │   item{task_num}_sub{sub_num}"
                        in output
                    ), f"Subitem {task_num}.{sub_num} should be displayed"

    def test_database_positions_are_sequential(self, temp_db):
        """Test that database positions are sequential without conflicts"""
        import sqlite3

        # Create list and tasks with subtasks
        self.run_cli('list create --list test_db --title "Test DB"', temp_db)
        self.run_cli('item add --list test_db --item task1 --title "Item 1"', temp_db)
        self.run_cli('item add --list test_db --item task2 --title "Item 2"', temp_db)
        self.run_cli(
            'item add --list test_db --item task1 --subitem sub1 --title "Sub 1"',
            temp_db,
        )
        self.run_cli(
            'item add --list test_db --item task2 --subitem sub2 --title "Sub 2"',
            temp_db,
        )
        self.run_cli(
            'item add --list test_db --item task1 --subitem sub3 --title "Sub 3"',
            temp_db,
        )

        # Check database directly
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT item_key, position 
            FROM todo_items 
            WHERE list_id = 1 
            ORDER BY 
                parent_item_id IS NULL DESC,  -- Main tasks first
                parent_item_id,               -- Group subtasks by parent
                position                      -- Then by position within group
        """
        )
        positions = cursor.fetchall()

        conn.close()

        # Verify positions with new hierarchical positioning and ordering:
        # Order: main tasks first, then subtasks grouped by parent
        # - Main tasks: task1=1, task2=2
        # - Subtasks of task1: sub1=1, sub3=2 (order added: sub1 first, sub3 second)
        # - Subtasks of task2: sub2=1
        expected_positions = [
            ("task1", 1),  # Main task position 1
            ("task2", 2),  # Main item position 2
            ("sub1", 1),  # Subtask of task1, position 1 within parent
            (
                "sub3",
                2,
            ),  # Subtask of task1, position 2 within parent (added after sub1)
            ("sub2", 1),  # Subitem of task2, position 1 within parent
        ]

        assert (
            positions == expected_positions
        ), f"Expected {expected_positions}, got {positions}"

    def test_mixed_task_and_subtask_creation(self, temp_db):
        """Test mixed creation order doesn't cause position conflicts"""
        # Create list
        self.run_cli('list create --list test_mixed --title "Test Mixed"', temp_db)

        # Create task1
        result = self.run_cli(
            'item add --list test_mixed --item task1 --title "Item 1"', temp_db
        )
        assert result.exit_code == 0

        # Add subitem to task1
        result = self.run_cli(
            'item add --list test_mixed --item task1 --subitem sub1 --title "Sub 1"',
            temp_db,
        )
        assert result.exit_code == 0

        # Create task2 (after subitem)
        result = self.run_cli(
            'item add --list test_mixed --item task2 --title "Item 2"', temp_db
        )
        assert result.exit_code == 0

        # Add subitem to task2
        result = self.run_cli(
            'item add --list test_mixed --item task2 --subitem sub2 --title "Sub 2"',
            temp_db,
        )
        assert result.exit_code == 0

        # Add another subitem to task1
        result = self.run_cli(
            'item add --list test_mixed --item task1 --subitem sub3 --title "Sub 3"',
            temp_db,
        )
        assert result.exit_code == 0

        # Verify display works correctly
        result = self.run_cli("list show --list test_mixed", temp_db)
        assert result.exit_code == 0

        output = result.output

        # All items should be displayed
        assert "task1" in output
        assert "task2" in output
        assert "sub1" in output
        assert "sub2" in output
        assert "sub3" in output

    def test_hierarchy_organization_with_fixed_positioning(self, temp_db):
        """Test that hierarchy organization works correctly with fixed positioning"""
        # Create complex hierarchy
        self.run_cli(
            'list create --list test_hierarchy --title "Test Hierarchy"', temp_db
        )
        self.run_cli(
            'item add --list test_hierarchy --item main1 --title "Main 1"', temp_db
        )
        self.run_cli(
            'item add --list test_hierarchy --item main2 --title "Main 2"', temp_db
        )
        self.run_cli(
            'item add --list test_hierarchy --item main1 --subitem sub1_1 --title "Sub 1.1"',
            temp_db,
        )
        self.run_cli(
            'item add --list test_hierarchy --item main1 --subitem sub1_2 --title "Sub 1.2"',
            temp_db,
        )
        self.run_cli(
            'item add --list test_hierarchy --item main2 --subitem sub2_1 --title "Sub 2.1"',
            temp_db,
        )

        # Test list view
        result = self.run_cli("list show --list test_hierarchy", temp_db)
        assert result.exit_code == 0

        tree_output = result.output
        assert "Main 1" in tree_output
        assert "Main 2" in tree_output
        assert "Sub 1.1" in tree_output
        assert "Sub 1.2" in tree_output
        assert "Sub 2.1" in tree_output

        # Test table view
        result = self.run_cli("list show --list test_hierarchy", temp_db)
        assert result.exit_code == 0

        table_output = result.output
        # Verify hierarchical numbering
        assert "│ 1.1      │   sub1_1" in table_output
        assert "│ 1.2      │   sub1_2" in table_output
        assert "│ 2.1      │   sub2_1" in table_output
