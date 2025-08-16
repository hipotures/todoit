"""Tests for allowing duplicate subitem keys across different parents"""

import pytest
import tempfile
import os
from core.manager import TodoManager
from core.database import Database, TodoItemDB


@pytest.fixture
def temp_db_path():
    """Create temporary database file path"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_duplicate_subtask_keys_different_parents(temp_db_path):
    """Test that the same subitem key can be used for different parent tasks"""
    manager = TodoManager(db_path=temp_db_path)
    
    # Create a list
    manager.create_list("test_list", "Test List")
    
    # Create two parent tasks
    manager.add_item("test_list", "scene_0019", "Generate image using scene_19.yaml")
    manager.add_item("test_list", "scene_0020", "Generate image using scene_20.yaml")
    
    # Add subtasks with the same keys to both parents - this should work now
    manager.add_subitem("test_list", "scene_0019", "image_gen", "Image generation")
    manager.add_subitem("test_list", "scene_0019", "image_dwn", "Image download")
    
    manager.add_subitem("test_list", "scene_0020", "image_gen", "Image generation")  # Same key as above
    manager.add_subitem("test_list", "scene_0020", "image_dwn", "Image download")    # Same key as above
    
    # Verify all items exist
    list_items = manager.get_list_items("test_list")
    assert len(list_items) == 6  # 2 parents + 4 subtasks
    
    # Count subtasks with each key
    image_gen_count = sum(1 for item in list_items if item.item_key == "image_gen")
    image_dwn_count = sum(1 for item in list_items if item.item_key == "image_dwn")
    
    assert image_gen_count == 2
    assert image_dwn_count == 2


def test_duplicate_subtask_keys_same_parent_fails(temp_db_path):
    """Test that duplicate subitem keys within the same parent still fail"""
    manager = TodoManager(db_path=temp_db_path)
    
    # Create a list and parent item
    manager.create_list("test_list", "Test List")
    manager.add_item("test_list", "scene_0019", "Generate image using scene_19.yaml")
    
    # Add first subitem
    manager.add_subitem("test_list", "scene_0019", "image_gen", "Image generation")
    
    # Try to add another subitem with the same key to the same parent - should fail
    with pytest.raises(ValueError, match="Subitem key 'image_gen' already exists for parent 'scene_0019'"):
        manager.add_subitem("test_list", "scene_0019", "image_gen", "Another image generation")


def test_main_task_keys_still_unique(temp_db_path):
    """Test that main item keys (without parent) are still required to be unique"""
    manager = TodoManager(db_path=temp_db_path)
    
    # Create a list
    manager.create_list("test_list", "Test List")
    
    # Add first main item
    manager.add_item("test_list", "scene_0019", "Generate image using scene_19.yaml")
    
    # Try to add another main item with the same key - should fail
    with pytest.raises(ValueError, match="Item 'scene_0019' already exists in list 'test_list'"):
        manager.add_item("test_list", "scene_0019", "Another scene item")


def test_database_constraint_allows_duplicate_subtask_keys(temp_db_path):
    """Test the database constraint directly allows duplicate subitem keys with different parents"""
    db = Database(temp_db_path)
    
    # Create list
    with db.get_session() as session:
        from core.database import TodoListDB
        list_obj = TodoListDB(list_key="test", title="Test", status="active")
        session.add(list_obj)
        session.commit()
        list_id = list_obj.id
    
    # Create parent tasks
    parent1_data = {
        "list_id": list_id, 
        "item_key": "parent1", 
        "content": "Parent 1", 
        "position": 1,
        "parent_item_id": None
    }
    parent1 = db.create_item(parent1_data)
    
    parent2_data = {
        "list_id": list_id, 
        "item_key": "parent2", 
        "content": "Parent 2", 
        "position": 2,
        "parent_item_id": None
    }
    parent2 = db.create_item(parent2_data)
    
    # Create subtasks with same key for different parents - should work
    subtask1_data = {
        "list_id": list_id,
        "item_key": "same_key",  # Same key
        "content": "Subitem of parent1",
        "position": 1,
        "parent_item_id": parent1.id
    }
    subtask1 = db.create_item(subtask1_data)
    
    subtask2_data = {
        "list_id": list_id,
        "item_key": "same_key",  # Same key, different parent
        "content": "Subitem of parent2", 
        "position": 1,
        "parent_item_id": parent2.id
    }
    subtask2 = db.create_item(subtask2_data)
    
    # Both should be created successfully
    assert subtask1.id != subtask2.id
    assert subtask1.item_key == subtask2.item_key == "same_key"
    assert subtask1.parent_item_id != subtask2.parent_item_id


def test_get_item_by_key_and_parent_function(temp_db_path):
    """Test the new get_item_by_key_and_parent function works correctly"""
    db = Database(temp_db_path)
    
    # Setup data similar to previous test
    with db.get_session() as session:
        from core.database import TodoListDB
        list_obj = TodoListDB(list_key="test", title="Test", status="active")
        session.add(list_obj)
        session.commit()
        list_id = list_obj.id
    
    parent1 = db.create_item({
        "list_id": list_id, "item_key": "parent1", "content": "Parent 1", 
        "position": 1, "parent_item_id": None
    })
    
    parent2 = db.create_item({
        "list_id": list_id, "item_key": "parent2", "content": "Parent 2", 
        "position": 2, "parent_item_id": None
    })
    
    subtask1 = db.create_item({
        "list_id": list_id, "item_key": "same_key", "content": "Subitem of parent1",
        "position": 1, "parent_item_id": parent1.id
    })
    
    subtask2 = db.create_item({
        "list_id": list_id, "item_key": "same_key", "content": "Subitem of parent2",
        "position": 1, "parent_item_id": parent2.id
    })
    
    # Test the new function can distinguish between the two
    found_subtask1 = db.get_item_by_key_and_parent(list_id, "same_key", parent1.id)
    found_subtask2 = db.get_item_by_key_and_parent(list_id, "same_key", parent2.id)
    
    assert found_subtask1.id == subtask1.id
    assert found_subtask2.id == subtask2.id
    assert found_subtask1.content == "Subitem of parent1"
    assert found_subtask2.content == "Subitem of parent2"
    
    # Test searching for main tasks (parent_item_id=None)
    found_parent1 = db.get_item_by_key_and_parent(list_id, "parent1", None)
    assert found_parent1.id == parent1.id