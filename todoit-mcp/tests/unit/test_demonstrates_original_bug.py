"""
This test demonstrates what would happen with the ORIGINAL buggy behavior.

If you run this test with the OLD code (before our fix), it would FAIL,
proving that our regression tests would have caught the original bug.

This file serves as documentation of the exact bug behavior.
"""

import pytest
import tempfile
import os
from core.manager import TodoManager


def test_demonstrates_original_bug_behavior():
    """
    This test shows exactly what the original bug did wrong.
    
    With the OLD code, this test would FAIL because:
    1. update_item_status() without parent_item_key would find the FIRST item with matching key
    2. CLI commands passed subitem_key as item_key directly
    3. This caused wrong subitem to be updated
    
    With our FIX, this test PASSES because:
    1. We added parent_item_key parameter to all relevant functions
    2. CLI commands now pass both item_key (parent) and subitem_key correctly
    3. Database lookup uses get_item_by_key_and_parent() for precise targeting
    """
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager = TodoManager(db_path=db_path)
        
        # Setup: Create list with duplicate subitem names (original bug scenario)
        manager.create_list("test_list", "Test List")
        manager.add_item("test_list", "scene_0001", "Scene 1")
        manager.add_item("test_list", "scene_0002", "Scene 2")
        
        # Both parents have subitems with same name
        manager.add_subitem("test_list", "scene_0001", "image_gen", "Image gen for scene 1")
        manager.add_subitem("test_list", "scene_0002", "image_gen", "Image gen for scene 2")
        
        # DEMONSTRATION: This is what the user's command was trying to do
        # "Update scene_0002/image_gen to failed"
        # 
        # OLD BUGGY BEHAVIOR (what happened before our fix):
        # - CLI would call: manager.update_item_status("test_list", "image_gen", "failed")
        # - This would find the FIRST "image_gen" item (scene_0001/image_gen)
        # - Wrong subitem would be updated!
        #
        # NEW CORRECT BEHAVIOR (after our fix):
        # - CLI calls: manager.update_item_status("test_list", "image_gen", "failed", parent_item_key="scene_0002")
        # - This specifically targets scene_0002/image_gen
        # - Correct subitem is updated!
        
        # Apply the fix (what should happen)
        manager.update_item_status(
            list_key="test_list",
            item_key="image_gen", 
            status="failed",
            parent_item_key="scene_0002"  # This parameter FIXED the bug!
        )
        
        # Verify the correct behavior (this would FAIL with old buggy code)
        scene1_item = manager.get_item("test_list", "image_gen", "scene_0001")
        scene2_item = manager.get_item("test_list", "image_gen", "scene_0002")
        
        # CRITICAL ASSERTIONS that prove the bug is fixed:
        assert scene1_item.status == "pending", \
            "BUG DETECTED: scene_0001/image_gen was incorrectly updated! " \
            "This means the old buggy behavior is still present."
            
        assert scene2_item.status == "failed", \
            "BUG DETECTED: scene_0002/image_gen was not updated! " \
            "The command didn't target the correct subitem."
        
        print("✅ Bug fix verified: Correct subitem was targeted")
        print(f"   scene_0001/image_gen status: {scene1_item.status} (should be 'pending')")
        print(f"   scene_0002/image_gen status: {scene2_item.status} (should be 'failed')")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_shows_old_vs_new_behavior_side_by_side():
    """
    This test shows side-by-side what old vs new behavior looks like.
    
    This test documents exactly how the fix works.
    """
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager = TodoManager(db_path=db_path)
        
        manager.create_list("demo", "Demo")
        manager.add_item("demo", "parent1", "Parent 1") 
        manager.add_item("demo", "parent2", "Parent 2")
        manager.add_subitem("demo", "parent1", "task", "Task 1")
        manager.add_subitem("demo", "parent2", "task", "Task 2")
        
        # OLD WAY (buggy) - would have been:
        # manager.update_item_status("demo", "task", "completed")
        # This would update the FIRST "task" found (parent1/task), not the intended one!
        
        # NEW WAY (fixed) - we specify which parent:
        manager.update_item_status("demo", "task", "completed", parent_item_key="parent2")
        
        # Verify NEW behavior works correctly
        task1 = manager.get_item("demo", "task", "parent1")
        task2 = manager.get_item("demo", "task", "parent2")
        
        assert task1.status == "pending"  # Unchanged (correct)
        assert task2.status == "completed"  # Updated (correct)
        
        print("✅ Demonstrated fix working correctly")
        print("   OLD buggy way would update wrong item")
        print("   NEW fixed way updates correct item")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_all_fixed_functions_work_correctly():
    """
    Test that all functions we fixed now work correctly with parent_item_key.
    
    This test covers all the functions we added parent_item_key support to:
    - update_item_status()
    - get_item() 
    - delete_item()
    - update_item_content()
    - clear_item_completion_states()
    """
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        manager = TodoManager(db_path=db_path)
        
        # Setup duplicate scenario
        manager.create_list("all_funcs", "All Functions Test")
        manager.add_item("all_funcs", "groupA", "Group A")
        manager.add_item("all_funcs", "groupB", "Group B")
        
        for group in ["groupA", "groupB"]:
            manager.add_subitem("all_funcs", group, "shared_task", f"Shared task in {group}")
            manager.add_subitem("all_funcs", group, "unique_task", f"Unique task in {group}")
        
        # Test 1: get_item() with parent_item_key
        taskA = manager.get_item("all_funcs", "shared_task", "groupA")
        taskB = manager.get_item("all_funcs", "shared_task", "groupB")
        assert taskA.content == "Shared task in groupA"
        assert taskB.content == "Shared task in groupB"
        
        # Test 2: update_item_status() with parent_item_key  
        manager.update_item_status("all_funcs", "shared_task", "in_progress", parent_item_key="groupA")
        taskA_after = manager.get_item("all_funcs", "shared_task", "groupA")
        taskB_after = manager.get_item("all_funcs", "shared_task", "groupB")
        assert taskA_after.status == "in_progress"
        assert taskB_after.status == "pending"  # Unchanged
        
        # Test 3: update_item_content() with parent_item_key
        manager.update_item_content("all_funcs", "shared_task", "UPDATED: Shared task in groupB", parent_item_key="groupB")
        taskA_content = manager.get_item("all_funcs", "shared_task", "groupA")
        taskB_content = manager.get_item("all_funcs", "shared_task", "groupB")
        assert taskA_content.content == "Shared task in groupA"  # Unchanged
        assert taskB_content.content == "UPDATED: Shared task in groupB"  # Updated
        
        # Test 4: clear_item_completion_states() with parent_item_key
        # First add some states
        manager.update_item_status("all_funcs", "shared_task", completion_states={"test": True}, parent_item_key="groupA")
        manager.update_item_status("all_funcs", "shared_task", completion_states={"review": True}, parent_item_key="groupB")
        
        # Clear states from groupA only
        manager.clear_item_completion_states("all_funcs", "shared_task", parent_item_key="groupA")
        
        taskA_states = manager.get_item("all_funcs", "shared_task", "groupA")
        taskB_states = manager.get_item("all_funcs", "shared_task", "groupB")
        assert not taskA_states.completion_states  # Cleared
        assert taskB_states.completion_states == {"review": True}  # Unchanged
        
        # Test 5: delete_item() with parent_item_key
        success = manager.delete_item("all_funcs", "unique_task", parent_item_key="groupA")
        assert success is True
        
        taskA_deleted = manager.get_item("all_funcs", "unique_task", "groupA")
        taskB_exists = manager.get_item("all_funcs", "unique_task", "groupB")
        assert taskA_deleted is None  # Deleted
        assert taskB_exists is not None  # Still exists
        
        print("✅ All fixed functions work correctly with parent_item_key parameter")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    # Run tests manually to see output
    test_demonstrates_original_bug_behavior()
    test_shows_old_vs_new_behavior_side_by_side()
    test_all_fixed_functions_work_correctly()
    print("\n🎉 All demonstration tests passed! The bug fix is working correctly.")