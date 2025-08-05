"""
TODOIT MCP - Todo Manager
Programmatic API for TODO list management - core business logic
"""
import os
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone

from .database import Database, TodoListDB, TodoItemDB, ListRelationDB, TodoHistoryDB, ListPropertyDB
from .models import (
    TodoList, TodoItem, ListRelation, TodoHistory, ProgressStats, ListProperty,
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
    
    # === ETAP 1: 10 kluczowych funkcji ===
    
    def create_list(self, 
                   list_key: str, 
                   title: str, 
                   items: Optional[List[str]] = None,
                   list_type: str = "sequential",
                   metadata: Optional[Dict] = None) -> TodoList:
        """1. Tworzy nową listę TODO z opcjonalnymi zadaniami"""
        # Sprawdź czy lista już istnieje
        existing = self.db.get_list_by_key(list_key)
        if existing:
            raise ValueError(f"Lista '{list_key}' już istnieje")
        
        # Przygotuj dane listy
        list_data = {
            "list_key": list_key,
            "title": title,
            "list_type": list_type,
            "meta_data": metadata or {}
        }
        
        # Utwórz listę
        db_list = self.db.create_list(list_data)
        
        # Dodaj zadania jeśli podane
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
        
        # Zapisz w historii
        self._record_history(
            list_id=db_list.id,
            action="created",
            new_value={"list_key": list_key, "title": title}
        )
        
        return self._db_to_model(db_list, TodoList)
    
    def get_list(self, key: Union[str, int]) -> Optional[TodoList]:
        """2. Pobiera listę po kluczu lub ID"""
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))
        
        return self._db_to_model(db_list, TodoList)
    
    def delete_list(self, key: Union[str, int]) -> bool:
        """3. Usuwa listę (z walidacją powiązań)"""
        # Pobierz listę
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            db_list = self.db.get_list_by_id(int(key))
        else:
            db_list = self.db.get_list_by_key(str(key))
        
        if not db_list:
            raise ValueError(f"Lista '{key}' nie istnieje")
        
        # Sprawdź czy lista ma zależne listy
        dependent_lists = self.db.get_dependent_lists(db_list.id)
        if dependent_lists:
            deps = ", ".join([l.list_key for l in dependent_lists])
            raise ValueError(f"Nie można usunąć listy '{key}' - ma zależne listy: {deps}")
        
        # Usuń historię powiązaną z listą i jej zadaniami
        from .database import TodoHistoryDB
        items = self.db.get_list_items(db_list.id)
        for item in items:
            # Usuń historię dla każdego zadania
            with self.db.get_session() as session:
                history_entries = session.query(TodoHistoryDB).filter(
                    TodoHistoryDB.item_id == item.id
                ).all()
                for entry in history_entries:
                    session.delete(entry)
                session.commit()
        
        # Usuń historię powiązaną z listą
        with self.db.get_session() as session:
            history_entries = session.query(TodoHistoryDB).filter(
                TodoHistoryDB.list_id == db_list.id
            ).all()
            for entry in history_entries:
                session.delete(entry)
            session.commit()
        
        # Usuń wszystkie zadania (kaskadowo)
        self.db.delete_list_items(db_list.id)
        
        # Usuń relacje gdzie lista jest źródłem
        self.db.delete_list_relations(db_list.id)
        
        # Usuń listę
        return self.db.delete_list(db_list.id)
    
    def list_all(self, limit: Optional[int] = None) -> List[TodoList]:
        """4. Listuje wszystkie listy TODO"""
        db_lists = self.db.get_all_lists(limit=limit)
        return [self._db_to_model(db_list, TodoList) for db_list in db_lists]
    
    def add_item(self, 
                list_key: str, 
                item_key: str, 
                content: str,
                position: Optional[int] = None,
                metadata: Optional[Dict] = None) -> TodoItem:
        """5. Dodaje zadanie do listy"""
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Sprawdź czy zadanie już istnieje
        existing_item = self.db.get_item_by_key(db_list.id, item_key)
        if existing_item:
            raise ValueError(f"Zadanie '{item_key}' już istnieje w liście '{list_key}'")
        
        # Ustaw pozycję jeśli nie podana
        if position is None:
            position = self.db.get_next_position(db_list.id)
        
        # Przygotuj dane zadania
        item_data = {
            "list_id": db_list.id,
            "item_key": item_key,
            "content": content,
            "position": position,
            "meta_data": metadata or {}
        }
        
        # Utwórz zadanie
        db_item = self.db.create_item(item_data)
        
        # Zapisz w historii
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action="created",
            new_value={"item_key": item_key, "content": content}
        )
        
        return self._db_to_model(db_item, TodoItem)
    
    def update_item_status(self, 
                          list_key: str, 
                          item_key: str,
                          status: Optional[str] = None,
                          completion_states: Optional[Dict[str, Any]] = None) -> TodoItem:
        """6. Aktualizuje status zadania z obsługą multi-state"""
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Pobierz zadanie
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        if not db_item:
            raise ValueError(f"Zadanie '{item_key}' nie istnieje w liście '{list_key}'")
        
        # Przygotuj dane do aktualizacji
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
        
        # Aktualizuj zadanie
        db_item = self.db.update_item(db_item.id, updates)
        
        # Zapisz w historii (konwertuj datetime do string dla JSON)
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
        """7. Pobiera następne zadanie do wykonania (enhanced with Phase 2 blocking logic)"""
        # Use smart subtask logic if requested
        if smart_subtasks:
            return self.get_next_pending_with_subtasks(list_key)
        
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None
        
        # Pobierz zadania oczekujące
        pending_items = self.db.get_items_by_status(db_list.id, "pending")
        
        if not respect_dependencies:
            return self._db_to_model(pending_items[0], TodoItem) if pending_items else None
        
        # Sprawdź zależności
        for db_item in pending_items:
            # Phase 1: Sprawdź zależności parent/child (subtasks)
            if db_item.parent_item_id:
                parent = self.db.get_item_by_id(db_item.parent_item_id)
                if parent and parent.status != "completed":
                    continue
            
            # Phase 2: Sprawdź cross-list dependencies (item blocked by other items)
            if self.db.is_item_blocked(db_item.id):
                continue  # Skip blocked items
            
            # Legacy: Sprawdź zależności między listami (old list-level dependencies)
            dependencies = self.db.get_list_dependencies(db_list.id)
            if dependencies:
                can_proceed = True
                for dep in dependencies:
                    # Sprawdź czy metadane zawierają regułę item_n_requires_item_n
                    if dep.metadata and dep.metadata.get("rule") == "item_n_requires_item_n":
                        # Znajdź odpowiadający item w liście źródłowej
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
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Basic stats
        stats = self.db.get_list_stats(db_list.id)
        
        # Oblicz procent ukończenia
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
        """9. Importuje listy z pliku markdown (obsługuje multi-column)"""
        if not os.path.exists(file_path):
            raise ValueError(f"Plik '{file_path}' nie istnieje")
        
        lists_data = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith('['):
                    # Parsowanie wszystkich kolumn [ ] lub [x]
                    columns = []
                    content = line
                    
                    # Wyciągnij wszystkie stany
                    while content.startswith('['):
                        if len(content) < 3:
                            break
                        state = content[1] == 'x' or content[1] == 'X'
                        columns.append(state)
                        content = content[4:].strip()  # Skip [x] lub [ ]
                    
                    if not content:
                        continue
                    
                    # Dla każdej kolumny tworzymy osobną listę
                    for i, state in enumerate(columns):
                        if i not in lists_data:
                            lists_data[i] = []
                        lists_data[i].append({
                            "content": content,
                            "completed": state,
                            "position": len(lists_data[i]) + 1
                        })
        
        if not lists_data:
            raise ValueError("Nie znaleziono zadań w formacie markdown w pliku")
        
        # Tworzenie list
        created_lists = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_key = base_key or f"import_{timestamp}"
        
        for i, items in lists_data.items():
            list_key = f"{base_key}_col{i+1}" if len(lists_data) > 1 else base_key
            list_title = f"Imported list {i+1}" if len(lists_data) > 1 else "Imported list"
            
            # Utwórz listę
            todo_list = self.create_list(
                list_key=list_key,
                title=list_title,
                metadata={"imported_from": file_path, "import_timestamp": timestamp}
            )
            
            # Dodaj zadania
            for item in items:
                item_obj = self.add_item(
                    list_key=list_key,
                    item_key=f"item_{item['position']}",
                    content=item["content"],
                    position=item["position"]
                )
                
                # Ustaw status jeśli ukończone
                if item["completed"]:
                    self.update_item_status(
                        list_key=list_key,
                        item_key=f"item_{item['position']}",
                        status="completed"
                    )
            
            created_lists.append(todo_list)
        
        # Tworzenie powiązań między listami (lista N+1 zależy od listy N)
        for i in range(len(created_lists) - 1):
            self.create_list_relation(
                source_list_id=created_lists[i].id,
                target_list_id=created_lists[i+1].id,
                relation_type="dependency",
                metadata={"rule": "item_n_requires_item_n"}
            )
        
        return created_lists
    
    def export_to_markdown(self, list_key: str, file_path: str) -> None:
        """10. Eksportuje listę do formatu markdown [x] tekst"""
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Pobierz zadania
        items = self.db.get_list_items(db_list.id)
        
        # Eksportuj do pliku
        with open(file_path, 'w', encoding='utf-8') as f:
            # Nagłówek
            f.write(f"# {db_list.title}\n\n")
            if db_list.description:
                f.write(f"{db_list.description}\n\n")
            
            # Zadania
            for item in sorted(items, key=lambda x: x.position):
                status_mark = '[x]' if item.status == 'completed' else '[ ]'
                f.write(f"{status_mark} {item.content}\n")
        
        # Zapisz w historii
        self._record_history(
            list_id=db_list.id,
            action="exported",
            new_value={"file_path": file_path, "format": "markdown"}
        )
    
    # === Funkcje pomocnicze ===
    
    def create_list_relation(self, 
                           source_list_id: int,
                           target_list_id: int,
                           relation_type: str,
                           relation_key: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> ListRelation:
        """Tworzy powiązanie między listami"""
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
        """Pobiera listy powiązane relacją (np. project_id)"""
        db_lists = self.db.get_lists_by_relation(relation_type, relation_key)
        return [self._db_to_model(db_list, TodoList) for db_list in db_lists]
    
    def get_item(self, list_key: str, item_key: str) -> Optional[TodoItem]:
        """Pobiera konkretne zadanie"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None
        
        db_item = self.db.get_item_by_key(db_list.id, item_key)
        return self._db_to_model(db_item, TodoItem)
    
    def get_list_items(self, list_key: str, status: Optional[str] = None) -> List[TodoItem]:
        """Pobiera wszystkie zadania z listy"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return []
        
        db_items = self.db.get_list_items(db_list.id, status=status)
        return [self._db_to_model(db_item, TodoItem) for db_item in db_items]
    
    def get_item_history(self, list_key: str, item_key: str, limit: Optional[int] = None) -> List[TodoHistory]:
        """Pobiera historię zmian zadania"""
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
    
    # ===== SUBTASK MANAGEMENT METHODS (Phase 1) =====
    
    def add_subtask(self, list_key: str, parent_key: str, subtask_key: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> TodoItem:
        """Add a subtask to an existing task"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
        all_items = self.db.get_list_items(db_list.id, status='pending')
        for item in all_items:
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
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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
        self.db.update_item(db_item.id, {"parent_item_id": parent_item.id})
        
        # Record history
        self._record_history(
            item_id=db_item.id,
            list_id=db_list.id,
            action=HistoryAction.UPDATED,
            old_value={"parent_item_id": old_parent_id},
            new_value={"parent_item_id": parent_item.id}
        )
        
        return self._db_to_model(db_item, TodoItem)
    
    def can_complete_item(self, list_key: str, item_key: str) -> Dict[str, Any]:
        """
        Check if an item can be completed (no pending subtasks)
        Returns dict with can_complete flag and details
        """
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
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