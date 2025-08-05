"""
TODOIT MCP - Todo Manager
Programmatic API for TODO list management - core business logic
"""
import os
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from .database import Database, TodoListDB, TodoItemDB, ListRelationDB, TodoHistoryDB, ListPropertyDB
from .models import (
    TodoList, TodoItem, ListRelation, TodoHistory, ProgressStats, ListProperty,
    TodoListCreate, TodoItemCreate, ListRelationCreate, TodoHistoryCreate,
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
                updates["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed"]:
                updates["completed_at"] = datetime.utcnow()
        
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
        
        return self._db_to_model(db_item, TodoItem)
    
    def get_next_pending(self, 
                        list_key: str,
                        respect_dependencies: bool = True) -> Optional[TodoItem]:
        """7. Pobiera następne zadanie do wykonania"""
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
            # Sprawdź zależności parent/child
            if db_item.parent_item_id:
                parent = self.db.get_item_by_id(db_item.parent_item_id)
                if parent and parent.status != "completed":
                    continue
            
            # Sprawdź zależności między listami
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
        """8. Zwraca postęp realizacji listy"""
        # Pobierz listę
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Pobierz statystyki
        stats = self.db.get_list_stats(db_list.id)
        
        # Oblicz procent ukończenia
        completion_percentage = 0.0
        if stats["total"] > 0:
            completion_percentage = (stats["completed"] / stats["total"]) * 100
        
        return ProgressStats(
            total=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            pending=stats["pending"],
            failed=stats["failed"],
            completion_percentage=completion_percentage
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
            return None
        
        # Get property
        db_property = self.db.get_list_property(db_list.id, property_key)
        return db_property.property_value if db_property else None
    
    def get_list_properties(self, list_key: str) -> Dict[str, str]:
        """Get all properties for a list as key-value dict"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return {}
        
        # Get all properties
        db_properties = self.db.get_list_properties(db_list.id)
        return {prop.property_key: prop.property_value for prop in db_properties}
    
    def delete_list_property(self, list_key: str, property_key: str) -> bool:
        """Delete a property from a list"""
        # Get list
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return False
        
        # Delete property
        return self.db.delete_list_property(db_list.id, property_key)