"""
Unit tests for separate positioning logic for main tasks and subtasks
Tests that main tasks and subtasks have independent position numbering
"""

import pytest

from core.manager import TodoManager


class TestSeparatePositioning:
    """Test suite for separate positioning functionality"""

    def test_main_tasks_sequential_positioning(self, manager):
        """Test that main tasks get sequential positions 1, 2, 3, etc."""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add multiple main tasks
        task1 = manager.add_item("test_list", "task_1", "Item 1")
        task2 = manager.add_item("test_list", "task_2", "Item 2")
        task3 = manager.add_item("test_list", "task_3", "Item 3")

        # Verify positions are sequential
        assert task1.position == 1
        assert task2.position == 2
        assert task3.position == 3

    def test_subtasks_sequential_positioning_per_parent(self, manager):
        """Test that subtasks get sequential positions within each parent"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add parent tasks
        parent1 = manager.add_item("test_list", "parent_1", "Parent 1")
        parent2 = manager.add_item("test_list", "parent_2", "Parent 2")

        # Add subtasks to parent 1
        sub1_1 = manager.add_subitem("test_list", "parent_1", "sub_1_1", "Subitem 1-1")
        sub1_2 = manager.add_subitem("test_list", "parent_1", "sub_1_2", "Subitem 1-2")
        sub1_3 = manager.add_subitem("test_list", "parent_1", "sub_1_3", "Subitem 1-3")

        # Add subtasks to parent 2
        sub2_1 = manager.add_subitem("test_list", "parent_2", "sub_2_1", "Subitem 2-1")
        sub2_2 = manager.add_subitem("test_list", "parent_2", "sub_2_2", "Subitem 2-2")

        # Verify parent positions are independent
        assert parent1.position == 1
        assert parent2.position == 2

        # Verify subtasks have sequential positions within each parent
        assert sub1_1.position == 1
        assert sub1_2.position == 2
        assert sub1_3.position == 3

        assert sub2_1.position == 1
        assert sub2_2.position == 2

    def test_mixed_workflow_realistic_scenario(self, manager):
        """Test realistic workflow with mixed main tasks and subtasks"""
        # Create list
        todo_list = manager.create_list("video_project", "Video Project")

        # Add scenes (main tasks)
        scene1 = manager.add_item("video_project", "scene_001", "Scene 001")
        scene2 = manager.add_item("video_project", "scene_002", "Scene 002")
        scene3 = manager.add_item("video_project", "scene_003", "Scene 003")

        # Add workflow subtasks to each scene
        workflow_steps = ["scene_gen", "image_gen", "audio_gen", "video_gen"]

        # Scene 1 subtasks
        scene1_subs = []
        for step in workflow_steps:
            sub = manager.add_subitem(
                "video_project",
                "scene_001",
                f"scene_001_{step}",
                f"{step} for scene 001",
            )
            scene1_subs.append(sub)

        # Scene 2 subtasks
        scene2_subs = []
        for step in workflow_steps:
            sub = manager.add_subitem(
                "video_project",
                "scene_002",
                f"scene_002_{step}",
                f"{step} for scene 002",
            )
            scene2_subs.append(sub)

        # Scene 3 subtasks
        scene3_subs = []
        for step in workflow_steps:
            sub = manager.add_subitem(
                "video_project",
                "scene_003",
                f"scene_003_{step}",
                f"{step} for scene 003",
            )
            scene3_subs.append(sub)

        # Verify main tasks have sequential positions
        assert scene1.position == 1
        assert scene2.position == 2
        assert scene3.position == 3

        # Verify each scene's subtasks have sequential positions
        for i, sub in enumerate(scene1_subs, 1):
            assert sub.position == i

        for i, sub in enumerate(scene2_subs, 1):
            assert sub.position == i

        for i, sub in enumerate(scene3_subs, 1):
            assert sub.position == i

    def test_database_positioning_independence(self, manager):
        """Test that database correctly handles independent positioning"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Test get_next_position for main tasks
        next_main_1 = manager.db.get_next_position(todo_list.id, parent_item_id=None)
        assert next_main_1 == 1

        # Add main item
        main1 = manager.add_item("test_list", "main_1", "Main 1")

        # Test get_next_position for main tasks again
        next_main_2 = manager.db.get_next_position(todo_list.id, parent_item_id=None)
        assert next_main_2 == 2

        # Test get_next_position for subtasks of main1
        next_sub_1 = manager.db.get_next_position(todo_list.id, parent_item_id=main1.id)
        assert next_sub_1 == 1

        # Add subitem
        sub1 = manager.add_subitem("test_list", "main_1", "sub_1", "Sub 1")

        # Test get_next_position for subtasks again
        next_sub_2 = manager.db.get_next_position(todo_list.id, parent_item_id=main1.id)
        assert next_sub_2 == 2

        # Add another main item - should still get position 2
        main2 = manager.add_item("test_list", "main_2", "Main 2")
        assert main2.position == 2

    def test_position_consistency_after_multiple_operations(self, manager):
        """Test position consistency after multiple add operations"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Interleave main tasks and subtasks
        main1 = manager.add_item("test_list", "main_1", "Main 1")  # pos 1
        sub1_1 = manager.add_subitem(
            "test_list", "main_1", "sub_1_1", "Sub 1-1"
        )  # pos 1
        main2 = manager.add_item("test_list", "main_2", "Main 2")  # pos 2
        sub1_2 = manager.add_subitem(
            "test_list", "main_1", "sub_1_2", "Sub 1-2"
        )  # pos 2
        sub2_1 = manager.add_subitem(
            "test_list", "main_2", "sub_2_1", "Sub 2-1"
        )  # pos 1
        main3 = manager.add_item("test_list", "main_3", "Main 3")  # pos 3

        # Verify main item positions
        assert main1.position == 1
        assert main2.position == 2
        assert main3.position == 3

        # Verify subitem positions within each parent
        assert sub1_1.position == 1
        assert sub1_2.position == 2
        assert sub2_1.position == 1

    def test_no_position_conflicts_in_database(self, manager):
        """Test that there are no position conflicts in the database"""
        # Create list
        todo_list = manager.create_list("test_list", "Test List")

        # Add many items in mixed order
        items = []
        for i in range(1, 4):
            # Add main item
            main = manager.add_item("test_list", f"main_{i}", f"Main {i}")
            items.append(main)

            # Add multiple subtasks
            for j in range(1, 4):
                sub = manager.add_subitem(
                    "test_list", f"main_{i}", f"sub_{i}_{j}", f"Sub {i}-{j}"
                )
                items.append(sub)

        # Get all items from database to verify no conflicts
        all_items = manager.get_list_items("test_list")

        # Check main tasks have unique positions among themselves
        main_tasks = [item for item in all_items if item.parent_item_id is None]
        main_positions = [item.position for item in main_tasks]
        assert len(main_positions) == len(set(main_positions))  # All unique
        assert main_positions == [1, 2, 3]  # Sequential

        # Check subtasks have unique positions within each parent
        for main_task in main_tasks:
            subtasks = [
                item for item in all_items if item.parent_item_id == main_task.id
            ]
            sub_positions = [item.position for item in subtasks]
            assert len(sub_positions) == len(
                set(sub_positions)
            )  # All unique within parent
            assert sub_positions == [1, 2, 3]  # Sequential within parent
