
"""
TODOIT MCP - Todo Manager
Programmatic API for TODO list management - core business logic
"""
import os
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

from .database import Database, TodoListDB, TodoItemDB, ListRelationDB, TodoHistoryDB, ListPropertyDB, ItemPropertyDB, ItemDependencyDB, utc_now
from .models import (
    TodoList, TodoItem, ListRelation, TodoHistory, ProgressStats, ListProperty, ItemProperty,
    TodoListCreate, TodoItemCreate, ListRelationCreate, TodoHistoryCreate,  
    ItemDependency, DependencyType,
    ItemStatus, ListType, RelationType, HistoryAction
)


class TodoManager:
    """Programmatic API for TODO management - core business logic"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize TodoManager with database connection"""
        if db_path is None:
            # Use default location in user's home directory
            import os
            from pathlib import Path
            
            todoit_dir = Path.home() / ".todoit"
            todoit_dir.mkdir(exist_ok=True)
            db_path = str(todoit_dir / "todoit.db")
        
        self.db = Database(db_path)
    
    def _db_to_model(self, db_obj: Any, model_class: type) -> Any:
        """Convert database object to Pydantic model"""
        if db_obj is None:
            return None
        
        # Convert SQLAlchemy object to dict
        obj_dict = {}
        for column in db_obj.__table__.columns:
            # Map database column name to model field name
            if column.name == 'metadata':
                # meta_data in SQLAlchemy maps to metadata in Pydantic
                value = getattr(db_obj, 'meta_data')
            else:
                value = getattr(db_obj, column.name)
            obj_dict[column.name] = value
        
        return model_class.model_validate(obj_dict)
    
    def _record_history(self, item_id: Optional[int] = None, list_id: Optional[int] = None,
                       action: str = "updated", old_value: Optional[Dict] = None,
                       new_value: Optional[Dict] = None, user_context: str = "programmatic_api"):
        """Record change in history"""
        history_data = {
            "item_id": item_id,
            "list_id": list_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "user_context": user_context
        }
        self.db.create_history_entry(history_data)
    
    # === STAGE 1: 10 key functions ===
    
    def create_list(self, 
                   list_key: str, 
                   title: str, 
                   items: Optional[List[str]] = None,
                   list_type: str = "sequential",
                   metadata: Optional[Dict] = None) -> TodoList:
        """1. Creates a new TODO list with optional tasks"""
        # Validate list key - must contain at least one letter a-z to distinguish from IDs
        import re
        if not re.search(r'[a-zA-Z]', list_key):
            raise ValueError(f"List key '{list_key}' must contain at least one letter (a-z) to distinguish from numeric IDs")
        
        # Check if the list already exists
        existing = self.db.get_list_by_key(list_key)
        if existing:
            raise ValueError(f"List '{list_key}' already exists")
        
        # Prepare list data
        list_data = {
            "list_key": list_key,
            "title": title,
            "list_type": list_type,
            "meta_data": metadata or {}
        }
        
        # Create the list
        db_list = self.db.create_list(list_data)
        
        # Add tasks if provided
        if items:
            for position, content in enumerate(items):
                item_key = f"item_{position + 1}"
                item_data = {
                    "list_id": db_list.id,
                    "item_key": item_key,
                    "content": content,
                    "position": position + 1,
                    "meta_data": {}
                }
                self.db.create_item(item_data)
        
        # Save to history
        self._record_history(
            list_id=db_list.id,
            action="created",
            new_value={"list_key": list_key, "title": title}
        )
        
        return self._db_to_model(db_list, TodoList)
    
    def get_list(self, key: Union[str, int]) -> Optional[TodoList]:
        """2. Gets a list by key or ID"""
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))
        
        return self._db_to_model(db_list, TodoList)
    
    def delete_list(self, key: Union[str, int]) -> bool:
        """3. Deletes a list (with relationship validation)"""
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")

        # For force delete, remove all list relations first
        # This breaks circular dependencies and orphans dependent lists
        with self.db.get_session() as session:
            # Remove all relations where this list is involved (as source or target)
            session.query(ListRelationDB).filter(
                (ListRelationDB.source_list_id == db_list.id) |
                (ListRelationDB.target_list_id == db_list.id)
            ).delete(synchronize_session=False)
            session.commit()

        # After removing relations, check if the list still has dependent lists
        # (this should now be empty, but keeping for safety)
        dependent_lists = self.db.get_dependent_lists(db_list.id)
        if dependent_lists:
            deps = ", ".join([l.list_key for l in dependent_lists])
            raise ValueError(f"Cannot delete list '{key}' - it has dependent lists: {deps}")

        with self.db.get_session() as session:
            # Re-fetch the list in the current session to ensure it's attached
            db_list_in_session = session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            if not db_list_in_session:
                return False

            # Get item IDs for cleanup
            item_ids = [item.id for item in db_list_in_session.items]

            # Delete item dependencies FIRST (before deleting items)
            if item_ids:
                session.query(ItemDependencyDB).filter(
                    (ItemDependencyDB.dependent_item_id.in_(item_ids)) |
                    (ItemDependencyDB.required_item_id.in_(item_ids))
                ).delete(synchronize_session=False)

            # Delete item properties FIRST (before deleting items)
            if item_ids:
                session.query(ItemPropertyDB).filter(ItemPropertyDB.item_id.in_(item_ids)).delete(synchronize_session=False)

            # Delete item history
            if item_ids:
                session.query(TodoHistoryDB).filter(TodoHistoryDB.item_id.in_(item_ids)).delete(synchronize_session=False)

            # Delete list history
            session.query(TodoHistoryDB).filter(TodoHistoryDB.list_id == db_list.id).delete(synchronize_session=False)

            # Delete list properties
            session.query(ListPropertyDB).filter(ListPropertyDB.list_id == db_list.id).delete(synchronize_session=False)

            # Delete list relations
            session.query(ListRelationDB).filter(
                (ListRelationDB.source_list_id == db_list.id) |
                (ListRelationDB.target_list_id == db_list.id)
            ).delete(synchronize_session=False)
            
            # Items are deleted via cascade="all, delete-orphan" on the list's items relationship.
            # Deleting the list will trigger the deletion of its items.
            session.delete(db_list_in_session)
            session.commit()
        return True
    
    def archive_list(self, key: Union[str, int], force: bool = False) -> TodoList:
        """Archive a TODO list (sets status to 'archived')
        
        Args:
            key: List key or ID to archive
            force: If False, prevents archiving lists with incomplete tasks
        """
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")
        
        if db_list.status == 'archived':
            raise ValueError(f"List '{key}' is already archived")
        
        # Check if all tasks are completed unless force=True
        if not force:
            progress = self.get_progress(db_list.list_key)
            if progress.total > 0 and progress.completed < progress.total:
                incomplete_count = progress.total - progress.completed
                raise ValueError(
                    f"Cannot archive list with incomplete tasks. "
                    f"Incomplete: {incomplete_count}/{progress.total} tasks. "
                    f"Use force=True to archive anyway."
                )

        with self.db.get_session() as session:
            # Re-fetch the list in the current session
            db_list_in_session = session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            if not db_list_in_session:
                raise ValueError(f"List '{key}' not found")
            
            # Update status to archived
            db_list_in_session.status = 'archived'
            db_list_in_session.updated_at = utc_now()
            session.commit()
            
            # Convert to Pydantic model and return
            return TodoList(
                id=db_list_in_session.id,
                list_key=db_list_in_session.list_key,
                title=db_list_in_session.title,
                description=db_list_in_session.description,
                list_type=db_list_in_session.list_type,
                status=db_list_in_session.status,
                parent_list_id=db_list_in_session.parent_list_id,
                metadata=db_list_in_session.meta_data or {},
                created_at=db_list_in_session.created_at,
                updated_at=db_list_in_session.updated_at
            )
    
    def unarchive_list(self, key: Union[str, int]) -> TodoList:
        """Unarchive a TODO list (sets status to 'active')"""
        # Get the list
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))

        if not db_list:
            raise ValueError(f"List '{key}' does not exist")
        
        if db_list.status == 'active':
            raise ValueError(f"List '{key}' is already active")

        with self.db.get_session() as session:
            # Re-fetch the list in the current session
            db_list_in_session = session.query(TodoListDB).filter(TodoListDB.id == db_list.id).first()
            if not db_list_in_session:
                raise ValueError(f"List '{key}' not found")
            
            # Update status to active
            db_list_in_session.status = 'active'
            db_list_in_session.updated_at = utc_now()
            session.commit()
            
            # Convert to Pydantic model and return
            return TodoList(
                id=db_list_in_session.id,
                list_key=db_list_in_session.list_key,
                title=db_list_in_session.title,
                description=db_list_in_session.description,
                list_type=db_list_in_session.list_type,
                status=db_list_in_session.status,
                parent_list_id=db_list_in_session.parent_list_id,
                metadata=db_list_in_session.meta_data or {},
                created_at=db_list_in_session.created_at,
                updated_at=db_list_in_session.updated_at
            )
    
    def list_all(self, limit: Optional[int] = None, include_archived: bool = False) -> List[TodoList]:
        """4. Lists all TODO lists"""
        db_lists = self.db.get_all_lists(limit=limit)
        
        # Filter by status unless include_archived is True
        if not include_archived:
            db_lists = [db_list for db_list in db_lists if db_list.status != 'archived']
        
        return [self._db_to_model(db_list, TodoList) for db_list in db_lists]
    
    def get_archived_lists(self, limit: Optional[int] = None) -> List[TodoList]:
        """Get only archived lists"""
        db_lists = self.db.get_all_lists(limit=limit)
        archived_lists = [db_list for db_list in db_lists if db_list.status == 'archived']
        return [self._db_to_model(db_list, TodoList) for db_list in archived_lists]
    
    def add_item(self, 
                list_key: str, 
                item_key: str, 
                content: str,
                position: Optional[int] = None,
                metadata: Optional[Dict] = None) -> TodoItem:
        """5. Adds a task to a list"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Check if the task already exists
        existing_item = self.db.get_item_by_key(db_list.id, item_key)
        if existing_item:
            raise ValueError(f"Task '{item_key}' already exists in list '{list_key}'")
        
        # Set position if not provided
        if position is None:
            position = self.db.get_next_position(db_list.id)
        
        # Prepare task data
        item_data = {
            "list_id": db_list.id,
            "item_key": item_key,
            "content": content,
            "position": position,
            "meta_data": metadata or {}
        }
        
        # Create the task
        db_item = self.db.create_item(item_data)
        
        # Save to history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="created",
            new_value={"item_key": item_key, "content": content}
        )
        
        # ===== SYNCHRONIZATION: Add to 1:1 child lists =====
        try:
            self._sync_add_to_children(list_key, item_key, content, position, metadata)
        except Exception as e:
            print(f"Warning: Failed to sync item '{item_key}' to child lists: {e}")
            # Continue - don't fail the main operation
        
        return self._db_to_model(db_item, TodoItem)
    
    def update_item_status(self, 
                          list_key: str, 
                          item_key: str,
                          status: Optional[str] = None,
                          completion_states: Optional[Dict[str, Any]] = None) -> TodoItem:
        """6. Updates task status with multi-state support"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get the task
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Task '{item_key}' does not exist in list '{list_key}'")
        
        # Prepare data for update
        old_values = {
            "status": db_item.status,
            "completion_states": db_item.completion_states
        }
        
        updates = {}
        if status:
            updates["status"] = status
            if status == "in_progress":
                updates["started_at"] = datetime.now(timezone.utc)
            elif status in ["completed", "failed"]:
                updates["completed_at"] = datetime.now(timezone.utc)
        
        if completion_states:
            current_states = db_item.completion_states or {}
            current_states.update(completion_states)
            updates["completion_states"] = current_states
        
        # Update the task
        db_item = self.db.update_item(db_item.id, updates)
        
        # Save to history (convert datetime to string for JSON)
        new_value_for_history = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                new_value_for_history[key] = value.isoformat()
            else:
                new_value_for_history[key] = value
        
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="updated",
            old_value=old_values,
            new_value=new_value_for_history
        )
        
        # Auto-complete parent if this item was completed and all siblings are also completed
        if status == "completed":
            self.auto_complete_parent(list_key, item_key)
        
        return self._db_to_model(db_item, TodoItem)
    
    def get_next_pending(self, 
                        list_key: str,
                        respect_dependencies: bool = True,
                        smart_subtasks: bool = False) -> Optional[TodoItem]:
        """7. Gets the next task to be executed (enhanced with Phase 2 blocking logic)"""
        # Use smart subtask logic if requested
        if smart_subtasks:
            return self.get_next_pending_with_subtasks(list_key)
        
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None
        
        # Get pending tasks
        pending_items = self.db.get_items_by_status(db_list.id, "pending")
        
        if not respect_dependencies:
            return self._db_to_model(pending_items[0], TodoItem) if pending_items else None
        
        # Check dependencies
        for db_item in pending_items:
            # Phase 1: Check parent/child dependencies (subtasks)
            if db_item.parent_item_id:
                parent = self.db.get_item_by_id(db_item.parent_item_id)
                if parent and parent.status != "completed":
                    continue
            
            # Phase 2: Check cross-list dependencies (item blocked by other items)
            if self.db.is_item_blocked(db_item.id):
                continue  # Skip blocked items
            
            # Legacy: Check dependencies between lists (old list-level dependencies)
            dependencies = self.db.get_list_dependencies(db_list.id)
            if dependencies:
                can_proceed = True
                for dep in dependencies:
                    # Check if metadata contains the item_n_requires_item_n rule
                    if dep.metadata and dep.metadata.get("rule") == "item_n_requires_item_n":
                        # Find the corresponding item in the source list
                        source_item = self.db.get_item_at_position(dep.source_list_id, db_item.position)
                        if source_item and source_item.status != "completed":
                            can_proceed = False
                            break
                
                if not can_proceed:
                    continue
            
            return self._db_to_model(db_item, TodoItem)
        
        return None
    
    def get_progress(self, list_key: str) -> ProgressStats:
        """8. Phase 3: Enhanced progress tracking with hierarchies and dependencies"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Basic stats
        stats = self.db.get_list_stats(db_list.id)
        
        # Calculate completion percentage
        completion_percentage = 0.0
        if stats["total"] > 0:
            completion_percentage = (stats["completed"] / stats["total"]) * 100
        
        # Phase 3: Enhanced statistics
        all_items = self.db.get_list_items(db_list.id)
        
        # Count hierarchy structure
        root_items = [item for item in all_items if item.parent_item_id is None]
        subtasks = [item for item in all_items if item.parent_item_id is not None]
        
        # Calculate maximum hierarchy depth
        max_depth = 0
        for item in all_items:
            depth = self.db.get_item_depth(item.id)
            max_depth = max(max_depth, depth)
        
        # Count blocked items (Phase 2 cross-list dependencies)
        blocked_count = 0
        available_count = 0
        for item in all_items:
            if item.status in ['pending']:
                if self.db.is_item_blocked(item.id):
                    blocked_count += 1
                else:
                    available_count += 1
        
        # Count cross-list dependencies involving this list
        dependencies = self.db.get_all_dependencies_for_list(db_list.id)
        
        return ProgressStats(
            total=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            pending=stats["pending"],
            failed=stats["failed"],
            completion_percentage=completion_percentage,
            blocked=blocked_count,
            available=available_count,
            root_items=len(root_items),
            subtasks=len(subtasks),
            hierarchy_depth=max_depth,
            dependency_count=len(dependencies)
        )
    
    def import_from_markdown(self, file_path: str, base_key: Optional[str] = None) -> List[TodoList]:
        """9. Imports lists from a markdown file (supports multi-column)"""
        if not os.path.exists(file_path):
            raise ValueError(f"File '{file_path}' does not exist")
        
        lists_data = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Handle both formats: "[x]" and "- [x]"
                original_line = line
                if line.startswith('- ['):
                    line = line[2:].strip()  # Remove "- " prefix
                
                if line.startswith('['):
                    # Parse all columns [ ] or [x]
                    columns = []
                    content = line
                    
                    # Extract all states
                    while content.startswith('['):
                        if len(content) < 3:
                            break
                        state = content[1] == 'x' or content[1] == 'X'
                        columns.append(state)
                        content = content[4:].strip()  # Skip [x] or [ ]
                    
                    if not content:
                        continue
                    
                    # For each column, we create a separate list
                    for i, state in enumerate(columns):
                        if i not in lists_data:
                            lists_data[i] = []
                        lists_data[i].append({
                            "content": content,
                            "completed": state,
                            "position": len(lists_data[i]) + 1
                        })
        
        if not lists_data:
            raise ValueError("No tasks found in markdown format in the file")
        
        # Create lists
        created_lists = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_key = base_key or f"import_{timestamp}"
        
        for i, items in lists_data.items():
            list_key = f"{base_key}_col{i+1}" if len(lists_data) > 1 else base_key
            list_title = f"Imported list {i+1}" if len(lists_data) > 1 else "Imported list"
            
            # Create the list
            todo_list = self.create_list(
                list_key=list_key,
                title=list_title,
                metadata={"imported_from": file_path, "import_timestamp": timestamp}
            )
            
            # Add tasks
            for item in items:
                item_obj = self.add_item(
                    list_key=list_key,
                    item_key=f"item_{item['position']}",
                    content=item["content"],
                    position=item["position"]
                )
                
                # Set status if completed
                if item["completed"]:
                    self.update_item_status(
                        list_key=list_key,
                        item_key=f"item_{item['position']}",
                        status="completed"
                    )
            
            created_lists.append(todo_list)
        
        # Create relationships between lists (list N+1 depends on list N)
        for i in range(len(created_lists) - 1):
            self.create_list_relation(
                source_list_id=created_lists[i].id,
                target_list_id=created_lists[i+1].id,
                relation_type="dependency",
                metadata={"rule": "item_n_requires_item_n"}
            )
        
        return created_lists
    
    def export_to_markdown(self, list_key: str, file_path: str) -> None:
        """10. Exports a list to markdown format [x] text"""
        # Get the list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get tasks
        items = self.db.get_list_items(db_list.id)
        
        # Export to file
        with open(file_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# {db_list.title}\n\n")
            if db_list.description:
                f.write(f"{db_list.description}\n\n")
            
            # Tasks
            for item in sorted(items, key=lambda x: x.position):
                status_mark = '[x]' if item.status == 'completed' else '[ ]'
                f.write(f"{status_mark} {item.content}\n")
        
        # Save to history
        self._record_history(
            list_id=db_list.id,
            action="exported",
            new_value={"file_path": file_path, "format": "markdown"}
        )
    
    # === Helper functions ===
    
    def create_list_relation(self, 
                           source_list_id: int,
                           target_list_id: int,
                           relation_type: str,
                           relation_key: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> ListRelation:
        """Creates a relationship between lists"""
        relation_data = {
            "source_list_id": source_list_id,
            "target_list_id": target_list_id,
            "relation_type": relation_type,
            "relation_key": relation_key,
            "meta_data": metadata or {}
        }
        
        db_relation = self.db.create_list_relation(relation_data)
        return self._db_to_model(db_relation, ListRelation)
    
    def get_lists_by_relation(self, 
                             relation_type: str, 
                             relation_key: str) -> List[TodoList]:
        """Gets lists related by a relationship (e.g., project_id)"""
        db_lists = self.db.get_lists_by_relation(relation_type, relation_key)
        return [self._db_to_model(db_list, TodoList) for db_list in db_lists]
    
    def get_item(self, list_key: str, item_key: str) -> Optional[TodoItem]:
        """Gets a specific task"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        return self._db_to_model(db_item, TodoItem)
    
    def get_list_items(self, list_key: str, status: Optional[str] = None) -> List[TodoItem]:
        """Gets all tasks from a list"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return []
        
        db_items = self.db.get_list_items(db_list.id, status=status)
        return [self._db_to_model(db_item, TodoItem) for db_item in db_items]
    
    def get_item_history(self, list_key: str, item_key: str, limit: Optional[int] = None) -> List[TodoHistory]:
        """Gets the change history of a task"""
        item = self.get_item(list_key, item_key)
        if not item:
            return []
        
        db_history = self.db.get_item_history(item.id, limit=limit)
        return [self._db_to_model(entry, TodoHistory) for entry in db_history]
    
    # === List Properties Methods ===
    
    def set_list_property(self, list_key: str, property_key: str, property_value: str) -> ListProperty:
        """Set a property for a list (create or update)"""
        
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        # Create or update property
        db_property = self.db.create_list_property(db_list.id, property_key, property_value)
        return self._db_to_model(db_property, ListProperty)
    
    def get_list_property(self, list_key: str, property_key: str) -> Optional[str]:
        """Get a property value for a list"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        # Get property
        db_property = self.db.get_list_property(db_list.id, property_key)
        return db_property.property_value if db_property else None
    
    def get_list_properties(self, list_key: str) -> Dict[str, str]:
        """Get all properties for a list as key-value dict"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        # Get all properties
        db_properties = self.db.get_list_properties(db_list.id)
        return {prop.property_key: prop.property_value for prop in db_properties}
    
    def delete_list_property(self, list_key: str, property_key: str) -> bool:
        """Delete a property from a list"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        # Delete property
        return self.db.delete_list_property(db_list.id, property_key)
    
    # ===== ITEM PROPERTIES METHODS =====
    
    def set_item_property(self, list_key: str, item_key: str, property_key: str, property_value: str) -> ItemProperty:
        """Set property for an item (create or update)"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Create/update property
        db_property = self.db.create_item_property(db_item.id, property_key, property_value)
        return self._db_to_model(db_property, ItemProperty)

    def get_item_property(self, list_key: str, item_key: str, property_key: str) -> Optional[str]:
        """Get single property value for an item"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        return self.db.get_item_property(db_item.id, property_key)

    def get_item_properties(self, list_key: str, item_key: str) -> Dict[str, str]:
        """Get all properties for an item"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        return self.db.get_item_properties(db_item.id)

    def delete_item_property(self, list_key: str, item_key: str, property_key: str) -> bool:
        """Delete property from an item"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        return self.db.delete_item_property(db_item.id, property_key)
    
    # ===== SUBTASK MANAGEMENT METHODS (Phase 1) =====
    
    def add_subtask(self, list_key: str, parent_key: str, subtask_key: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> TodoItem:
        """Add a subtask to an existing task"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get parent item
        parent_item = self.db.get_item_by_key(db_list.id, parent_key)
        if not parent_item:
            raise ValueError(f"Parent task '{parent_key}' not found in list '{list_key}'")
        
        # Check if subtask_key already exists in the list
        existing_item = self.db.get_item_by_key(db_list.id, subtask_key)
        if existing_item:
            raise ValueError(f"Item key '{subtask_key}' already exists in list '{list_key}'")
        
        # Get next position for subtask (after existing subtasks of this parent)
        existing_subtasks = self.db.get_item_children(parent_item.id)
        if existing_subtasks:
            # Position after the last subtask
            max_subtask_position = max(subtask.position for subtask in existing_subtasks)
            position = max_subtask_position + 1
        else:
            # First subtask gets position after parent
            position = parent_item.position + 1
            # Shift other items to make room
            self.db.shift_positions(db_list.id, position, 1)
        
        # Create subtask
        item_data = {
            "list_id": db_list.id,
            "item_key": subtask_key,
            "content": content,
            "position": position,
            "status": "pending",
            "parent_item_id": parent_item.id,
            "meta_data": metadata or {}
        }
        
        db_item = self.db.create_item(item_data)
        
        # Record history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action=HistoryAction.CREATED,
            new_value={"content": content, "parent": parent_key}
        )
        
        return self._db_to_model(db_item, TodoItem)
    
    def get_subtasks(self, list_key: str, parent_key: str) -> List[TodoItem]:
        """Get all subtasks for a given parent task"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get parent item
        parent_item = self.db.get_item_by_key(db_list.id, parent_key)
        if not parent_item:
            raise ValueError(f"Parent task '{parent_key}' not found in list '{list_key}'")
        
        # Get children
        children = self.db.get_item_children(parent_item.id)
        return [self._db_to_model(child, TodoItem) for child in children]
    
    def get_item_hierarchy(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """Get full hierarchy for an item (item + all subtasks recursively)"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key) 
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        def build_hierarchy(item_db) -> Dict[str, Any]:
            """Recursively build hierarchy structure"""
            item_model = self._db_to_model(item_db, TodoItem)
            children = self.db.get_item_children(item_db.id)
            
            hierarchy = {
                "item": item_model.to_dict(),
                "subtasks": [build_hierarchy(child) for child in children]
            }
            
            return hierarchy
        
        return build_hierarchy(db_item)
    
    def get_next_pending_with_subtasks(self, list_key: str) -> Optional[TodoItem]:
        """
        Phase 3: Smart next task algorithm combining Phase 1 + Phase 2
        1. Find all pending tasks (root and subtasks)
        2. Filter out blocked (cross-list dependencies - Phase 2)
        3. For each unblocked pending task:
           a. If has pending subtasks → return first pending subtask
           b. If no subtasks → return task itself
        4. Priority:
           - Tasks with in_progress parents (continue working on started tasks)
           - Tasks without cross-list dependencies
           - Tasks by position
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Phase 3: Enhanced algorithm - collect all candidates with priority scoring
        candidates = []
        
        # Get all root items (both pending and in_progress for subtask checking)
        root_items = self.db.get_root_items(db_list.id)
        
        for item in root_items:
            # Priority 1: In-progress parent with pending subtasks (continue working)
            if item.status == 'in_progress':
                children = self.db.get_item_children(item.id)
                pending_children = [child for child in children if child.status == 'pending']
                
                for child in pending_children:
                    # Phase 2: Check if subtask is blocked by cross-list dependencies
                    if not self.db.is_item_blocked(child.id):
                        candidates.append({
                            'item': child,
                            'priority': 1,  # Highest priority - continue in-progress work
                            'parent_position': item.position,
                            'item_position': child.position
                        })
            
            # Priority 2: Pending parent tasks
            elif item.status == 'pending':
                # Phase 2: Check if parent is blocked by cross-list dependencies
                if self.db.is_item_blocked(item.id):
                    continue  # Skip blocked items
                
                # Check if parent has pending subtasks
                children = self.db.get_item_children(item.id)
                pending_children = [child for child in children if child.status == 'pending']
                
                if pending_children:
                    # Return first unblocked pending subtask
                    for child in pending_children:
                        if not self.db.is_item_blocked(child.id):
                            candidates.append({
                                'item': child,
                                'priority': 2,  # Medium priority - new subtask
                                'parent_position': item.position,
                                'item_position': child.position
                            })
                            break  # Take first available subtask
                else:
                    # No subtasks, return parent task itself
                    candidates.append({
                        'item': item,
                        'priority': 3,  # Lower priority - root task
                        'parent_position': item.position,
                        'item_position': 0
                    })
        
        # Phase 3: Also check orphaned subtasks (subtasks with completed/failed parents)
        all_pending_items = self.db.get_list_items(db_list.id, status='pending')
        for item in all_pending_items:
            if item.parent_item_id:  # This is a subtask
                parent = self.db.get_item_by_id(item.parent_item_id)
                if parent and parent.status in ['completed', 'failed']:
                    # Orphaned subtask - can be worked on independently
                    if not self.db.is_item_blocked(item.id):
                        candidates.append({
                            'item': item,
                            'priority': 4,  # Lowest priority - orphaned subtask
                            'parent_position': parent.position if parent else 999,
                            'item_position': item.position
                        })
        
        # Sort candidates by priority, then parent position, then item position
        candidates.sort(key=lambda x: (x['priority'], x['parent_position'], x['item_position']))
        
        # Return first candidate
        if candidates:
            return self._db_to_model(candidates[0]['item'], TodoItem)
        
        # No available tasks found
        return None
    
    def auto_complete_parent(self, list_key: str, item_key: str) -> bool:
        """
        Auto-complete parent task if all its subtasks are completed
        Returns True if parent was auto-completed, False otherwise
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get item  
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Check if this item has a parent
        if not db_item.parent_item_id:
            return False  # This is a root item, no parent to complete
        
        # Get parent
        parent_item = self.db.get_item_by_id(db_item.parent_item_id)
        if not parent_item or parent_item.status == 'completed':
            return False  # Parent doesn't exist or is already completed
        
        # Check if all children of parent are completed
        if self.db.check_all_children_completed(parent_item.id):
            # Auto-complete the parent
            self.db.update_item(parent_item.id, {
                'status': 'completed',
                'completed_at': datetime.now(timezone.utc)
            })
            
            # Record history
            self._record_history(
                item_id=parent_item.id,
                list_id=db_list.id,
                action=HistoryAction.COMPLETED,
                old_value={"status": parent_item.status},
                new_value={"status": "completed", "auto_completed": True}
            )
            
            return True
        
        return False
    
    def move_to_subtask(self, list_key: str, item_key: str, new_parent_key: str) -> TodoItem:
        """Convert an existing task to be a subtask of another task"""
        # Get list  
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get item to move
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Get new parent
        parent_item = self.db.get_item_by_key(db_list.id, new_parent_key)
        if not parent_item:
            raise ValueError(f"Parent task '{new_parent_key}' not found in list '{list_key}'")
        
        # Prevent circular references
        if parent_item.id == db_item.id:
            raise ValueError("Cannot make item a subtask of itself")
        
        # Check if new parent is not already a descendant of this item
        parent_path = self.db.get_item_path(parent_item.id)
        if any(path_item.id == db_item.id for path_item in parent_path):
            raise ValueError("Cannot create circular reference in subtask hierarchy")
        
        # Update the item to have the new parent
        old_parent_id = db_item.parent_item_id
        updated_item = self.db.update_item(db_item.id, {"parent_item_id": parent_item.id})
        
        # Record history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action=HistoryAction.UPDATED,
            old_value={"parent_item_id": old_parent_id},
            new_value={"parent_item_id": parent_item.id}
        )
        
        return self._db_to_model(updated_item, TodoItem)
    
    def can_complete_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """
        Check if an item can be completed (no pending subtasks)
        Returns dict with can_complete flag and details
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' does not exist")
        
        # Get item
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Check for pending children
        has_pending = self.db.has_pending_children(db_item.id)
        children = self.db.get_item_children(db_item.id)
        pending_children = [child for child in children if child.status in ['pending', 'in_progress']]
        
        return {
            "can_complete": not has_pending,
            "has_subtasks": len(children) > 0,
            "pending_subtasks": len(pending_children),
            "pending_subtask_keys": [child.item_key for child in pending_children],
            "total_subtasks": len(children)
        }
    
    # ===== CROSS-LIST DEPENDENCIES METHODS (Phase 2) =====
    
    def add_item_dependency(self, dependent_list: str, dependent_item: str,
                           required_list: str, required_item: str,
                           dependency_type: str = "blocks",
                           metadata: Optional[Dict[str, Any]] = None) -> 'ItemDependency':
        """Add dependency between tasks from different lists"""
        from .models import ItemDependency, DependencyType
        
        # Get dependent item
        dependent_db_list = self.db.get_list_by_key(dependent_list)
        if not dependent_db_list:
            raise ValueError(f"Dependent list '{dependent_list}' not found")
        
        dependent_db_item = self.db.get_item_by_key(dependent_db_list.id, dependent_item)
        if not dependent_db_item:
            raise ValueError(f"Dependent item '{dependent_item}' not found in list '{dependent_list}'")
        
        # Get required item
        required_db_list = self.db.get_list_by_key(required_list)
        if not required_db_list:
            raise ValueError(f"Required list '{required_list}' not found")
        
        required_db_item = self.db.get_item_by_key(required_db_list.id, required_item)
        if not required_db_item:
            raise ValueError(f"Required item '{required_item}' not found in list '{required_list}'")
        
        # Validate dependency type
        try:
            dep_type = DependencyType(dependency_type)
        except ValueError:
            raise ValueError(f"Invalid dependency type: {dependency_type}")

        # Check for circular dependencies
        all_deps = self.db.get_all_item_dependencies()
        graph = {}
        for dep in all_deps:
            if dep.dependent_item_id not in graph:
                graph[dep.dependent_item_id] = []
            graph[dep.dependent_item_id].append(dep.required_item_id)

        path = [required_db_item.id]
        visited = {required_db_item.id}
        while path:
            current_node = path.pop(0)
            if current_node == dependent_db_item.id:
                raise ValueError("Circular dependency detected")
            for neighbor in graph.get(current_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
        
        # Create dependency
        dependency_data = {
            "dependent_item_id": dependent_db_item.id,
            "required_item_id": required_db_item.id,
            "dependency_type": dep_type.value,
            "meta_data": metadata or {}
        }
        
        db_dependency = self.db.create_item_dependency(dependency_data)
        
        # Record history for both items
        self._record_history(
            item_id=dependent_db_item.id,
            list_id=dependent_db_list.id,
            action=HistoryAction.UPDATED,
            new_value={
                "dependency_added": f"now depends on {required_list}:{required_item}",
                "dependency_type": dep_type.value
            }
        )
        
        self._record_history(
            item_id=required_db_item.id,
            list_id=required_db_list.id,
            action=HistoryAction.UPDATED,
            new_value={
                "dependency_added": f"now blocks {dependent_list}:{dependent_item}",
                "dependency_type": dep_type.value
            }
        )
        
        return self._db_to_model(db_dependency, ItemDependency)
    
    def remove_item_dependency(self, dependent_list: str, dependent_item: str,
                              required_list: str, required_item: str) -> bool:
        """Remove dependency between tasks from different lists"""
        # Get dependent item
        dependent_db_list = self.db.get_list_by_key(dependent_list)
        if not dependent_db_list:
            raise ValueError(f"Dependent list '{dependent_list}' not found")
        
        dependent_db_item = self.db.get_item_by_key(dependent_db_list.id, dependent_item)
        if not dependent_db_item:
            raise ValueError(f"Dependent item '{dependent_item}' not found in list '{dependent_list}'")
        
        # Get required item
        required_db_list = self.db.get_list_by_key(required_list)
        if not required_db_list:
            raise ValueError(f"Required list '{required_list}' not found")
        
        required_db_item = self.db.get_item_by_key(required_db_list.id, required_item)
        if not required_db_item:
            raise ValueError(f"Required item '{required_item}' not found in list '{required_list}'")
        
        # Remove dependency
        success = self.db.delete_item_dependency(dependent_db_item.id, required_db_item.id)
        
        if success:
            # Record history
            self._record_history(
                item_id=dependent_db_item.id,
                list_id=dependent_db_list.id,
                action=HistoryAction.UPDATED,
                new_value={"dependency_removed": f"no longer depends on {required_list}:{required_item}"}
            )
        
        return success
    
    def get_item_blockers(self, list_key: str, item_key: str) -> List['TodoItem']:
        """Get all items that block this item (not completed required items)"""
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Get blocking items
        blockers = self.db.get_item_blockers(db_item.id)
        return [self._db_to_model(blocker, TodoItem) for blocker in blockers]
    
    def get_items_blocked_by(self, list_key: str, item_key: str) -> List['TodoItem']:
        """Get all items blocked by this item"""
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Get blocked items
        blocked = self.db.get_items_blocked_by(db_item.id)
        return [self._db_to_model(item, TodoItem) for item in blocked]
    
    def is_item_blocked(self, list_key: str, item_key: str) -> bool:
        """Check if item is blocked by uncompleted cross-list dependencies"""
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        return self.db.is_item_blocked(db_item.id)
    
    def can_start_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """
        Check if task can be started (all dependencies completed, no pending subtasks)
        Combines both Phase 1 (subtasks) and Phase 2 (cross-list dependencies) logic
        """
        # Get item
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")
        
        # Check if item is already completed or in progress
        if db_item.status in ['completed', 'in_progress']:
            return {
                "can_start": False,
                "reason": f"Item is already {db_item.status}",
                "blocked_by_dependencies": False,
                "blocked_by_subtasks": False,
                "blockers": [],
                "pending_subtasks": []
            }
        
        # Check cross-list dependencies
        blockers = self.db.get_item_blockers(db_item.id)
        is_blocked_by_deps = len(blockers) > 0
        
        # Check subtasks (if this is a parent with pending subtasks)
        pending_children = []
        if db_item.parent_item_id is None:  # Only check for root items
            children = self.db.get_item_children(db_item.id)
            pending_children = [child for child in children if child.status in ['pending', 'in_progress']]
        
        is_blocked_by_subtasks = len(pending_children) > 0
        
        can_start = not (is_blocked_by_deps or is_blocked_by_subtasks)
        
        return {
            "can_start": can_start,
            "blocked_by_dependencies": is_blocked_by_deps,
            "blocked_by_subtasks": is_blocked_by_subtasks,
            "blockers": [{"id": b.id, "key": b.item_key, "content": b.content} for b in blockers],
            "pending_subtasks": [{"id": s.id, "key": s.item_key, "content": s.content} for s in pending_children],
            "reason": self._get_blocking_reason(is_blocked_by_deps, is_blocked_by_subtasks, blockers, pending_children)
        }
    
    def _get_blocking_reason(self, blocked_by_deps: bool, blocked_by_subtasks: bool, 
                           blockers: List, pending_subtasks: List) -> str:
        """Generate human-readable blocking reason"""
        reasons = []
        
        if blocked_by_deps:
            blocker_names = [f"{b.item_key}" for b in blockers[:3]]  # Show first 3
            if len(blockers) > 3:
                blocker_names.append(f"and {len(blockers) - 3} more")
            reasons.append(f"blocked by dependencies: {', '.join(blocker_names)}")
        
        if blocked_by_subtasks:
            subtask_names = [f"{s.item_key}" for s in pending_subtasks[:3]]  # Show first 3
            if len(pending_subtasks) > 3:
                subtask_names.append(f"and {len(pending_subtasks) - 3} more")
            reasons.append(f"has pending subtasks: {', '.join(subtask_names)}")
        
        if not reasons:
            return "ready to start"
        
        return "; ".join(reasons)
    
    def get_cross_list_progress(self, project_key: str) -> Dict[str, Any]:
        """Get progress for all lists in a project with dependency information"""
        # Get project lists
        project_lists = self.get_lists_by_relation("project", project_key)
        if not project_lists:
            return {
                "project_key": project_key,
                "lists": [],
                "total_items": 0,
                "total_completed": 0,
                "overall_progress": 0.0,
                "dependencies": []
            }
        
        result = {
            "project_key": project_key,
            "lists": [],
            "total_items": 0,
            "total_completed": 0,
            "overall_progress": 0.0,
            "dependencies": []
        }
        
        # Get dependency graph
        dependency_graph = self.db.get_dependency_graph_for_project(project_key)
        result["dependencies"] = dependency_graph["dependencies"]
        
        # Process each list
        for todo_list in project_lists:
            progress = self.get_progress(todo_list.list_key)
            items = self.get_list_items(todo_list.list_key)
            
            # Count blocked items
            blocked_count = 0
            for item in items:
                if self.db.is_item_blocked(item.id):
                    blocked_count += 1
            
            list_info = {
                "list": todo_list.to_dict(),
                "progress": progress.to_dict(),
                "blocked_items": blocked_count,
                "items": [item.to_dict() for item in items]
            }
            
            result["lists"].append(list_info)
            result["total_items"] += progress.total
            result["total_completed"] += progress.completed
        
        # Calculate overall progress
        if result["total_items"] > 0:
            result["overall_progress"] = (result["total_completed"] / result["total_items"]) * 100
        
        return result
    
    def get_dependency_graph(self, project_key: str) -> Dict[str, Any]:
        """Get dependency graph for visualization"""
        return self.db.get_dependency_graph_for_project(project_key)

    def delete_item(self, list_key: str, item_key: str) -> bool:
        """Deletes an item and all its subtasks and dependencies."""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        item_to_delete = self.db.get_item_by_key(db_list.id, item_key)
        if not item_to_delete:
            return False # Item doesn't exist, so nothing to delete

        # Get all subtasks recursively
        all_subtasks = self._get_all_subtasks_recursive(item_to_delete.id)
        
        # Delete all subtasks first (reverse order to avoid FK issues)
        for subtask in reversed(all_subtasks):
            # Delete dependencies for this subtask
            self.db.delete_all_dependencies_for_item(subtask.id)
            # Delete properties for this subtask
            self.db.delete_all_item_properties(subtask.id)
            # Delete history for this subtask
            self.db.delete_item_history(subtask.id)
            # Delete the subtask
            self.db.delete_item(subtask.id)
        
        # Delete dependencies for the main item
        self.db.delete_all_dependencies_for_item(item_to_delete.id)
        
        # Delete properties for the main item
        self.db.delete_all_item_properties(item_to_delete.id)
        
        # Delete history for the main item
        self.db.delete_item_history(item_to_delete.id)
        
        # Delete the main item
        self.db.delete_item(item_to_delete.id)
        
        return True

    def update_item_content(self, list_key: str, item_key: str, new_content: str) -> TodoItem:
        """Updates the content/description of a TODO item."""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"List '{list_key}' not found")

        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Item '{item_key}' not found in list '{list_key}'")

        # Store old content for history
        old_content = db_item.content
        
        # Update the database
        updated_item = self.db.update_item_content(db_item.id, new_content)
        if not updated_item:
            raise ValueError(f"Failed to update item content")

        # Record history
        self._record_history(
            item_id=db_item.id,
            action=HistoryAction.UPDATED,
            old_value={"content": old_content},
            new_value={"content": new_content},
            user_context="content_update"
        )

        return self._db_to_model(updated_item, TodoItem)

    def _get_all_subtasks_recursive(self, item_id: int) -> List:
        """Get all subtasks of an item recursively"""
        all_subtasks = []
        children = self.db.get_item_children(item_id)
        
        for child in children:
            all_subtasks.append(child)
            # Get subtasks of this child recursively
            all_subtasks.extend(self._get_all_subtasks_recursive(child.id))
        
        return all_subtasks

    def _get_item_and_subtasks_recursive(self, session, item_id: int) -> List:
        """Helper method to get item and all its subtasks recursively"""
        items = []
        
        # Get the item itself
        item = session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
        if item:
            items.append(item)
            
            # Get all children recursively
            children = session.query(TodoItemDB).filter(TodoItemDB.parent_item_id == item_id).all()
            for child in children:
                items.extend(self._get_item_and_subtasks_recursive(session, child.id))
        
        return items

    def _get_item_depth(self, session, item_id: int) -> int:
        """Helper method to get the depth of an item in the hierarchy"""
        depth = 0
        current_id = item_id
        
        while current_id:
            item = session.query(TodoItemDB).filter(TodoItemDB.id == current_id).first()
            if not item or not item.parent_item_id:
                break
            current_id = item.parent_item_id
            depth += 1
            
        return depth
    
    def link_list_1to1(self, 
                      source_list_key: str, 
                      target_list_key: str, 
                      target_title: Optional[str] = None) -> Dict[str, Any]:
        """Create a linked copy of a list with 1:1 task mapping and automatic relation.
        
        Creates a complete copy of the source list including all items and properties,
        but with all item statuses reset to 'pending'. Establishes a 'project' relation
        between the source and target lists.
        
        Args:
            source_list_key: Key of the existing list to copy from
            target_list_key: Key for the new list to create (must not exist)
            target_title: Optional custom title for new list
            
        Returns:
            Dict with operation results and statistics
            
        Raises:
            ValueError: If source list doesn't exist or target list already exists
        """
        # Step 1: Validation
        source_list = self.get_list(source_list_key)
        if not source_list:
            raise ValueError(f"Source list '{source_list_key}' does not exist")
            
        existing_target = self.get_list(target_list_key)
        if existing_target:
            raise ValueError(f"Target list '{target_list_key}' already exists")
        
        # Step 2: Create target list
        if target_title is None:
            target_title = f"{source_list.title} - Linked"
            
        target_list = self.create_list(
            list_key=target_list_key,
            title=target_title,
            list_type="linked",
            metadata=source_list.metadata or {}
        )
        
        # Step 3: Copy list properties
        source_properties = self.get_list_properties(source_list_key)
        list_properties_copied = 0
        
        for property_key, property_value in source_properties.items():
            self.set_list_property(target_list_key, property_key, property_value)
            list_properties_copied += 1
        
        # Step 4: Copy items with status reset
        source_items = self.get_list_items(source_list_key)
        items_copied = 0
        item_properties_copied = 0
        
        for source_item in source_items:
            # Create new item with status reset to pending
            target_item = self.add_item(
                list_key=target_list_key,
                item_key=source_item.item_key,  # Keep same item key
                content=source_item.content,
                position=source_item.position,
                metadata=source_item.metadata or {}
            )
            items_copied += 1
            
            # Copy item properties
            source_item_properties = self.get_item_properties(source_list_key, source_item.item_key)
            for prop_key, prop_value in source_item_properties.items():
                self.set_item_property(target_list_key, source_item.item_key, prop_key, prop_value)
                item_properties_copied += 1
        
        # Step 5: Create project relation
        relation_key = f"{source_list_key}_linked"
        relation_metadata = {
            "linked_from": source_list_key,
            "relationship": "1:1",
            "created_by": "link_command"
        }
        
        self.create_list_relation(
            source_list_id=source_list.id,
            target_list_id=target_list.id,
            relation_type="project", 
            relation_key=relation_key,
            metadata=relation_metadata
        )
        
        # Step 6: Return detailed report
        return {
            "success": True,
            "source_list": source_list_key,
            "target_list": target_list_key,
            "target_list_id": target_list.id,
            "target_list_created": True,
            "items_copied": items_copied,
            "list_properties_copied": list_properties_copied,
            "item_properties_copied": item_properties_copied,
            "all_items_set_to_pending": True,
            "relation_created": True,
            "relation_key": relation_key,
            "relation_type": "project",
            "operation": "link_list_1to1"
        }
    
    # ===== LINKED LIST SYNCHRONIZATION HELPERS =====
    
    def _get_1to1_child_lists(self, parent_list_id: int) -> List[Any]:
        """Get child lists linked with 1:1 relationship where this list is the parent"""
        relations = self.db.get_list_relations(parent_list_id, as_source=True)
        child_lists = []
        
        for relation in relations:
            if (relation.relation_type == 'project' and 
                relation.meta_data and 
                relation.meta_data.get('relationship') == '1:1'):
                child_lists.append(relation)
        
        return child_lists
    
    def _sync_add_to_children(self, parent_list_key: str, item_key: str, content: str, 
                             position: Optional[int] = None, metadata: Optional[Dict] = None):
        """Synchronously add item to all 1:1 child lists"""
        # Get parent list
        parent_list = self.db.get_list_by_key(parent_list_key)
        if not parent_list:
            return
        
        # Find all 1:1 child lists
        child_relations = self._get_1to1_child_lists(parent_list.id)
        
        for relation in child_relations:
            try:
                # Get child list
                child_list = self.db.get_list_by_id(relation.target_list_id)
                if not child_list:
                    continue
                
                # Check if item already exists in child
                existing_child_item = self.db.get_item_by_key(child_list.id, item_key)
                if existing_child_item:
                    continue  # Skip if already exists
                
                # Set position for child list
                child_position = position
                if child_position is None:
                    child_position = self.db.get_next_position(child_list.id)
                
                # Prepare child item data
                child_item_data = {
                    "list_id": child_list.id,
                    "item_key": item_key,
                    "content": content,
                    "position": child_position,
                    "status": "pending",  # Always start as pending in child
                    "meta_data": metadata or {}
                }
                
                # Create child item
                child_db_item = self.db.create_item(child_item_data)
                
                # Copy item properties if any exist in parent
                if metadata:
                    parent_item = self.db.get_item_by_key(parent_list.id, item_key)
                    if parent_item:
                        parent_properties = self.db.get_item_properties(parent_item.id)
                        for prop in parent_properties:
                            self.db.create_item_property(
                                child_db_item.id, 
                                prop.property_key, 
                                prop.property_value
                            )
                
                # Record history for child
                self._record_history(
                    item_id=child_db_item.id,
                    list_id=child_list.id,
                    action="created",
                    new_value={"item_key": item_key, "content": content, "synced_from_parent": True}
                )
                
            except Exception as e:
                # Log error but don't fail the main operation
                print(f"Warning: Failed to sync item '{item_key}' to child list {relation.target_list_id}: {e}")
                continue
