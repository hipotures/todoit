# Plan Refaktoringu TODOIT MCP - Ulepszona Architektura DDD+CQRS

> **⚠️ IMPORTANT UPDATE - 06.08.2025**  
> Ten dokument został zaktualizowany po nieudanym pierwszym podejściu do refaktoringu.
> Sekcja [🔥 LESSONS LEARNED](#lessons-learned) zawiera kluczowe wnioski i ulepszony proces.

## 📊 Analiza Obecnego Stanu

### Problemy Zidentyfikowane

#### 1. **manager.py** - Klasa "God Object"
- **Rozmiar**: 1219 linii kodu
- **Metod publicznych**: 37
- **Odpowiedzialności**: 7+ różnych domen
- **Naruszenia**: Single Responsibility Principle (SRP), Open/Closed Principle (OCP)

#### 2. **cli.py** - Monolityczny Moduł CLI
- **Rozmiar**: 1308 linii kodu
- **Komend**: 30
- **Grup komend**: 6
- **Problem**: Trudna nawigacja, duplikacja kodu pomocniczego

#### 3. **Ryzyko Ukrytej Złożoności w Serwisach** 🚨
- **Problem**: Tradycyjny podział na serwisy może prowadzić do zależności cyklicznych
- **Przykład**: SubtaskService potrzebuje ItemService, DependencyService potrzebuje obu
- **Konsekwencja**: Przeniesienie problemu "God Object" na poziom interakcji między serwisami

#### 4. **Zarządzanie Transakcjami Bazodanowymi** 🚨
- **Problem**: Jedna operacja użytkownika może obejmować wiele serwisów
- **Przykład**: `update_item_status` → `auto_complete_parent` (2 transakcje = ryzyko niespójności)
- **Konsekwencja**: Jeśli pierwsza operacja się powiedzie, a druga nie - niespójny stan bazy

#### 5. **Scope Creep - Mieszanie Refaktoringu z Nowymi Funkcjami** ⚠️
- **Problem**: Plan zawiera `_record_history` która może wyglądać na nową funkcjonalność
- **Sprawdzenie**: `_record_history` występuje 11 razy w obecnym kodzie - **to ISTNIEJĄCA funkcja!**
- **Decyzja**: Migrujemy 1:1, zero nowych funkcji

### Metryki Złożoności

```
Plik              | LOC  | Metody | Cyklomatyczna | Kognitywna
------------------|------|--------|---------------|------------
manager.py        | 1219 | 37     | ~150          | ~200
cli.py           | 1308 | 30     | ~120          | ~180
```

## 🎯 Cele Refaktoringu (Zaktualizowane)

1. **Separacja Odpowiedzialności** - każdy komponent ma jedną odpowiedzialność
2. **Eliminacja Zależności** - brak komunikacji między handlerami
3. **Transakcyjność** - Unit of Work pattern, jedna transakcja per use case
4. **Testowalność** - możliwość mockowania tylko repository
5. **Czytelność** - maksymalnie 200 linii na handler
6. **Zachowanie API** - pełna kompatybilność wsteczna
7. **Czysta Migracja** - zero nowych funkcji, tylko refaktoring struktury

## 🏗️ Nowa Architektura: Domain-Driven Design + CQRS

### Rozwiązanie Kluczowych Problemów

#### **Problem 1: Transakcyjna Niespójność**

**OBECNY PROBLEM** w `manager.py:273-276`:
```python
# ❌ PROBLEM: Dwie oddzielne transakcje = ryzyko niespójności
def update_item_status(self, list_key, item_key, status, ...):
    # Transakcja 1: Update item
    db_item = self.db.update_item(db_item.id, updates)  # COMMIT!
    
    # Transakcja 2: Auto-complete parent (może się nie udać!)
    if status == "completed":
        self.auto_complete_parent(list_key, item_key)  # COMMIT!
```

**ROZWIĄZANIE: Unit of Work Pattern**
```python
# ✅ ROZWIĄZANIE: Jedna transakcja = konsystencja gwarantowana
class UpdateItemStatusCommandHandler:
    def handle(self, command):
        with self.repository.transaction():  # Unit of Work
            # 1. Load aggregate (cały context w pamięci)
            todo_list = self.repository.get_list(command.list_key)
            
            # 2. Business logic (wszystkie zmiany w domain entities)
            item = todo_list.get_item(command.item_key)
            changes = item.update_status(command.status)  # W pamięci
            
            # 3. Auto-completion logic (w tej samej transakcji)
            if command.status == "completed":
                auto_changes = todo_list.handle_item_completion(item)
                changes.extend(auto_changes)
            
            # 4. History recording (migracja istniejącej funkcji)
            for change in changes:
                self.repository.record_change(change)
                
            # 5. JEDEN save na końcu (COMMIT tylko tutaj)
            return self.repository.save_list(todo_list)
```

#### **Problem 2: Scope Creep Prevention**

**ANALIZA**: `_record_history` w obecnym kodzie:
```bash
# Sprawdzenie: grep -n "_record_history" core/manager.py
53:    def _record_history(self, item_id: Optional[int] = None, ...)
106:        self._record_history(...)  # Lista utworzona
210:        self._record_history(...)  # Item dodany  
265:        self._record_history(...)  # Status zmieniony
# ... i tak dalej (11 wystąpień)
```

**DECYZJA: Czysta Migracja 1:1**
```python
# ✅ MIGRACJA: Exact same logic, different location
class DomainEventRecorder:
    """Migrated _record_history functionality - NO new features"""
    
    def record_item_created(self, item_id: int, list_id: int, item_key: str, content: str):
        """Exact migration of existing _record_history call"""
        history_data = {
            "item_id": item_id,
            "list_id": list_id, 
            "action": "created",  # Same as before
            "new_value": {"item_key": item_key, "content": content},  # Same format
            "user_context": "programmatic_api"  # Same default
        }
        self.repository.create_history_entry(history_data)  # Same call
```

#### **Problem 3: Eliminacja Zależności Cyklicznych**

**Zamiast** serwisów komunikujących się ze sobą:
```python
# ❌ PROBLEM: Zależności cykliczne
class SubtaskService:
    def __init__(self, db, item_service, dependency_service):
        self.item_service = item_service  # Zależność!
        self.dependency_service = dependency_service  # Zależność!
```

**Używamy** Aggregate pattern z Unit of Work:
```python
# ✅ ROZWIĄZANIE: Aggregate zawiera całą logikę
class TodoList:  # Aggregate Root
    def add_subtask_with_validation(self, parent_key: str, subtask_key: str, content: str):
        """All business logic in one place - no external dependencies"""
        
        # 1. Find parent (w tym agregacie) 
        parent = self.get_item(parent_key)
        if not parent:
            raise ValueError(f"Parent {parent_key} not found")
        
        # 2. Check dependencies (w tym samym agregacie)
        if parent.is_blocked_by_dependencies(self.dependency_graph):
            raise ValueError("Parent is blocked")
            
        # 3. Add subtask (domain logic)
        subtask = parent.add_subtask(subtask_key, content)
        
        # 4. History event (w tym samym agregacie)
        self._domain_events.append(SubtaskAdded(parent_key, subtask_key))
        
        return subtask
```

### Struktura Katalogów

```
todoit-mcp/
├── core/
│   ├── __init__.py
│   ├── domain/                        # Domain Layer - Czysta logika biznesowa
│   │   ├── __init__.py
│   │   ├── entities.py               # TodoList, TodoItem (agregaty)
│   │   ├── value_objects.py          # Status, Priority, DependencyType
│   │   ├── repositories.py           # Repository interfaces (abstrakcje)
│   │   └── exceptions.py             # Domain exceptions
│   ├── application/                   # Application Layer - Use Cases
│   │   ├── __init__.py
│   │   ├── commands/                 # Command handlers (write operations)
│   │   │   ├── __init__.py
│   │   │   ├── list_commands.py      # CreateList, DeleteList (150 linii)
│   │   │   ├── item_commands.py      # AddItem, UpdateStatus, DeleteItem (200 linii)
│   │   │   ├── subtask_commands.py   # AddSubtask, MoveToSubtask (180 linii)
│   │   │   ├── dependency_commands.py # AddDependency, RemoveDependency (200 linii)
│   │   │   └── io_commands.py        # ImportFromMarkdown, Export (150 linii)
│   │   ├── queries/                  # Query handlers (read operations)
│   │   │   ├── __init__.py
│   │   │   ├── list_queries.py       # GetList, GetAllLists (100 linii)
│   │   │   ├── item_queries.py       # GetItem, GetListItems (120 linii)
│   │   │   ├── hierarchy_queries.py  # GetSubtasks, GetHierarchy (150 linii)
│   │   │   ├── dependency_queries.py # GetBlockers, CanStartItem (180 linii)
│   │   │   ├── smart_queries.py      # GetNextPending, GetProgress (200 linii)
│   │   │   └── stats_queries.py      # GetStats, GetCrossListProgress (100 linii)
│   │   └── mediator.py               # Command/Query dispatcher (100 linii)
│   ├── infrastructure/               # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database_repository.py    # Implementacja Repository (300 linii)
│   │   ├── database.py              # SQLAlchemy models (bez zmian)
│   │   └── cache.py                 # Cache layer (opcjonalnie)
│   └── manager.py                   # Application Service - fasada (150 linii)
├── interfaces/
│   ├── __init__.py
│   ├── mcp_server.py                  # Bez zmian
│   └── cli/
│       ├── __init__.py                # Główny punkt wejścia (50 linii)
│       ├── base.py                    # Wspólne funkcje CLI (100 linii)
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── list_commands.py      # Komendy list (200 linii)
│       │   ├── item_commands.py      # Komendy zadań (300 linii)
│       │   ├── subtask_commands.py   # Komendy subtasków (200 linii)
│       │   ├── dependency_commands.py # Komendy zależności (250 linii)
│       │   ├── io_commands.py        # Import/Export (100 linii)
│       │   ├── property_commands.py  # Właściwości (150 linii)
│       │   └── stats_commands.py     # Statystyki (100 linii)
│       └── formatters/
│           ├── __init__.py
│           ├── table_formatter.py    # Formatowanie tabel
│           ├── tree_formatter.py     # Formatowanie drzewa
│           └── progress_formatter.py # Formatowanie progress barów
```

## 📋 Szczegółowy Plan Implementacji - DDD+CQRS

### Phase 1: Domain Layer - Encje i Obiekty Wartości

#### 1.1 Domain Entities

```python
# core/domain/entities.py
from typing import List, Optional, Dict, Any
from .value_objects import ItemStatus, DependencyType
from .exceptions import DomainValidationError

class TodoItem:
    """Domain entity representing a todo item"""
    
    def __init__(self, key: str, content: str, list_id: int):
        self.key = key
        self.content = content  
        self.list_id = list_id
        self.status = ItemStatus.PENDING
        self.parent_id: Optional[int] = None
        self.subtasks: List['TodoItem'] = []
        self.position = 1
        self.metadata: Dict[str, Any] = {}
    
    def add_subtask(self, subtask_key: str, content: str) -> 'TodoItem':
        """Add subtask to this item"""
        if self.has_subtask(subtask_key):
            raise DomainValidationError(f"Subtask '{subtask_key}' already exists")
        
        subtask = TodoItem(subtask_key, content, self.list_id)
        subtask.parent_id = self.id
        subtask.position = len(self.subtasks) + 1
        self.subtasks.append(subtask)
        
        return subtask
    
    def can_be_completed(self) -> bool:
        """Check if item can be completed (no pending subtasks)"""
        return not any(subtask.status == ItemStatus.PENDING for subtask in self.subtasks)
    
    def complete(self):
        """Mark item as completed"""
        if not self.can_be_completed():
            raise DomainValidationError("Cannot complete item with pending subtasks")
        self.status = ItemStatus.COMPLETED
    
    def is_blocked_by_dependencies(self, dependency_graph: Dict[int, List[int]]) -> bool:
        """Check if this item is blocked by cross-list dependencies"""
        blocking_items = dependency_graph.get(self.id, [])
        return len(blocking_items) > 0
    
    def has_subtask(self, subtask_key: str) -> bool:
        return any(subtask.key == subtask_key for subtask in self.subtasks)


class TodoList:
    """Domain entity representing a todo list"""
    
    def __init__(self, key: str, title: str):
        self.key = key
        self.title = title
        self.items: List[TodoItem] = []
        self.description: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_item(self, item_key: str, content: str) -> TodoItem:
        """Add new item to list"""
        if self.has_item(item_key):
            raise DomainValidationError(f"Item '{item_key}' already exists in list '{self.key}'")
        
        item = TodoItem(item_key, content, self.id)
        item.position = len(self.items) + 1
        self.items.append(item)
        
        return item
    
    def get_item(self, item_key: str) -> Optional[TodoItem]:
        """Get item by key"""
        return next((item for item in self.items if item.key == item_key), None)
    
    def has_item(self, item_key: str) -> bool:
        return any(item.key == item_key for item in self.items)
    
    def get_root_items(self) -> List[TodoItem]:
        """Get all root items (items without parent)"""
        return [item for item in self.items if item.parent_id is None]
    
    def calculate_progress(self) -> Dict[str, int]:
        """Calculate progress statistics"""
        total = len(self.items)
        completed = sum(1 for item in self.items if item.status == ItemStatus.COMPLETED)
        pending = sum(1 for item in self.items if item.status == ItemStatus.PENDING)
        in_progress = sum(1 for item in self.items if item.status == ItemStatus.IN_PROGRESS)
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "completion_percentage": (completed / total * 100) if total > 0 else 0
        }
```

#### 1.2 Value Objects

```python
# core/domain/value_objects.py
from enum import Enum

class ItemStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class DependencyType(Enum):
    BLOCKS = "blocks"
    REQUIRES = "requires"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class ListType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    KANBAN = "kanban"
```

#### 1.3 Repository Abstrakcje  

```python
# core/domain/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import TodoList, TodoItem

class TodoRepository(ABC):
    """Abstract repository for todo operations"""
    
    @abstractmethod
    def get_list(self, list_key: str) -> Optional[TodoList]:
        pass
    
    @abstractmethod
    def save_list(self, todo_list: TodoList) -> TodoList:
        pass
    
    @abstractmethod
    def delete_list(self, list_key: str) -> bool:
        pass
    
    @abstractmethod
    def get_all_lists(self, limit: Optional[int] = None) -> List[TodoList]:
        pass
    
    @abstractmethod
    def get_dependency_graph(self) -> Dict[int, List[int]]:
        """Get dependency graph for all items"""
        pass
    
    @abstractmethod
    def add_dependency(self, dependent_item_id: int, required_item_id: int, 
                      dependency_type: str) -> bool:
        pass
    
    @abstractmethod
    def remove_dependency(self, dependent_item_id: int, required_item_id: int) -> bool:
        pass
    
    @abstractmethod
    def transaction(self):
        """Context manager for database transactions"""
        pass
```

### Phase 2: Application Layer - Commands i Queries

#### 2.1 Command Handlers

```python
# core/application/commands/list_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, List
from ...domain.entities import TodoList
from ...domain.repositories import TodoRepository
from ...domain.exceptions import DomainValidationError

@dataclass
class CreateListCommand:
    list_key: str
    title: str
    description: Optional[str] = None
    items: Optional[List[str]] = None
    metadata: Optional[Dict] = None

class CreateListCommandHandler:
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def handle(self, command: CreateListCommand) -> TodoList:
        """Handle create list command"""
        with self.repository.transaction():
            # Check if list already exists
            existing_list = self.repository.get_list(command.list_key)
            if existing_list:
                raise DomainValidationError(f"List '{command.list_key}' already exists")
            
            # Create domain entity
            todo_list = TodoList(command.list_key, command.title)
            todo_list.description = command.description
            todo_list.metadata = command.metadata or {}
            
            # Add initial items if provided
            if command.items:
                for item_content in command.items:
                    item_key = f"item_{len(todo_list.items) + 1}"
                    todo_list.add_item(item_key, item_content)
            
            # Save to repository
            return self.repository.save_list(todo_list)


@dataclass
class DeleteListCommand:
    list_key: str

class DeleteListCommandHandler:
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def handle(self, command: DeleteListCommand) -> bool:
        """Handle delete list command"""
        with self.repository.transaction():
            todo_list = self.repository.get_list(command.list_key)
            if not todo_list:
                return False
            
            # Domain validation - check for dependencies
            dependency_graph = self.repository.get_dependency_graph()
            list_items_ids = [item.id for item in todo_list.items]
            
            # Check if any items in this list are required by other items
            for item_id, required_ids in dependency_graph.items():
                if any(req_id in list_items_ids for req_id in required_ids):
                    raise DomainValidationError(
                        f"Cannot delete list '{command.list_key}' - items are required by other tasks"
                    )
            
            return self.repository.delete_list(command.list_key)
```

#### 2.2 Query Handlers

```python
# core/application/queries/smart_queries.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from ...domain.entities import TodoItem
from ...domain.repositories import TodoRepository
from ...domain.value_objects import ItemStatus

@dataclass
class GetNextPendingWithSubtasksQuery:
    list_key: str

class GetNextPendingWithSubtasksQueryHandler:
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def handle(self, query: GetNextPendingWithSubtasksQuery) -> Optional[TodoItem]:
        """
        Phase 3 Smart Algorithm: Find next task considering hierarchies and dependencies
        This replaces the complex logic from manager.py with clean, testable handler
        """
        todo_list = self.repository.get_list(query.list_key)
        if not todo_list:
            return None
        
        dependency_graph = self.repository.get_dependency_graph()
        candidates = []
        
        # Priority 1: In-progress parent with unblocked pending subtasks
        for item in todo_list.get_root_items():
            if item.status == ItemStatus.IN_PROGRESS:
                pending_subtasks = [s for s in item.subtasks if s.status == ItemStatus.PENDING]
                for subtask in pending_subtasks:
                    if not subtask.is_blocked_by_dependencies(dependency_graph):
                        candidates.append((subtask, 1, item.position, subtask.position))
        
        # Priority 2: Pending parents with unblocked subtasks
        for item in todo_list.get_root_items():
            if item.status == ItemStatus.PENDING and not item.is_blocked_by_dependencies(dependency_graph):
                pending_subtasks = [s for s in item.subtasks if s.status == ItemStatus.PENDING]
                if pending_subtasks:
                    # Return first unblocked subtask
                    for subtask in pending_subtasks:
                        if not subtask.is_blocked_by_dependencies(dependency_graph):
                            candidates.append((subtask, 2, item.position, subtask.position))
                            break
                else:
                    # No subtasks - return parent itself
                    candidates.append((item, 3, item.position, 0))
        
        # Priority 3: Orphaned subtasks (completed/failed parents)
        all_items = todo_list.items
        for item in all_items:
            if item.parent_id and item.status == ItemStatus.PENDING:
                parent = next((i for i in all_items if i.id == item.parent_id), None)
                if parent and parent.status in [ItemStatus.COMPLETED, ItemStatus.FAILED]:
                    if not item.is_blocked_by_dependencies(dependency_graph):
                        candidates.append((item, 4, parent.position, item.position))
        
        # Sort by priority, then parent position, then item position
        candidates.sort(key=lambda x: (x[1], x[2], x[3]))
        
        return candidates[0][0] if candidates else None


@dataclass
class GetProgressQuery:
    list_key: str

class GetProgressQueryHandler:
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def handle(self, query: GetProgressQuery) -> Dict[str, Any]:
        """Get enhanced progress statistics"""
        todo_list = self.repository.get_list(query.list_key)
        if not todo_list:
            raise ValueError(f"List '{query.list_key}' not found")
        
        # Basic progress from domain entity
        basic_stats = todo_list.calculate_progress()
        
        # Enhanced statistics with dependencies
        dependency_graph = self.repository.get_dependency_graph()
        blocked_count = 0
        available_count = 0
        
        for item in todo_list.items:
            if item.status == ItemStatus.PENDING:
                if item.is_blocked_by_dependencies(dependency_graph):
                    blocked_count += 1
                else:
                    available_count += 1
        
        # Hierarchy statistics
        root_items = todo_list.get_root_items()
        subtasks = [item for item in todo_list.items if item.parent_id is not None]
        max_depth = self._calculate_max_depth(todo_list.items)
        
        return {
            **basic_stats,
            "blocked": blocked_count,
            "available": available_count,
            "root_items": len(root_items),
            "subtasks": len(subtasks),
            "hierarchy_depth": max_depth
        }
    
    def _calculate_max_depth(self, items: List[TodoItem]) -> int:
        """Calculate maximum hierarchy depth"""
        max_depth = 0
        for item in items:
            if item.parent_id is None:  # Root item
                depth = self._get_item_depth(item, items)
                max_depth = max(max_depth, depth)
        return max_depth
    
    def _get_item_depth(self, item: TodoItem, all_items: List[TodoItem]) -> int:
        """Get depth of item in hierarchy"""
        if not item.subtasks:
            return 0
        
        max_child_depth = 0
        for subtask in item.subtasks:
            child_depth = self._get_item_depth(subtask, all_items)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth + 1
```

#### 2.3 Mediator - Command/Query Dispatcher

```python
# core/application/mediator.py
from typing import Dict, Any, TypeVar, Generic, Type
from .commands.list_commands import CreateListCommand, CreateListCommandHandler, DeleteListCommand, DeleteListCommandHandler
from .commands.item_commands import AddItemCommand, AddItemCommandHandler, UpdateItemStatusCommand, UpdateItemStatusCommandHandler
from .commands.subtask_commands import AddSubtaskCommand, AddSubtaskCommandHandler
from .commands.dependency_commands import AddDependencyCommand, AddDependencyCommandHandler
from .queries.list_queries import GetListQuery, GetListQueryHandler, GetAllListsQuery, GetAllListsQueryHandler
from .queries.smart_queries import GetNextPendingWithSubtasksQuery, GetNextPendingWithSubtasksQueryHandler
from ..domain.repositories import TodoRepository

T = TypeVar('T')

class Mediator:
    """Command/Query dispatcher - eliminates dependencies between handlers"""
    
    def __init__(self, repository: TodoRepository):
        self.repository = repository
        self._handlers: Dict[Type, Any] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all command and query handlers"""
        # Command handlers
        self._handlers[CreateListCommand] = CreateListCommandHandler(self.repository)
        self._handlers[DeleteListCommand] = DeleteListCommandHandler(self.repository)
        self._handlers[AddItemCommand] = AddItemCommandHandler(self.repository)
        self._handlers[UpdateItemStatusCommand] = UpdateItemStatusCommandHandler(self.repository)
        self._handlers[AddSubtaskCommand] = AddSubtaskCommandHandler(self.repository)
        self._handlers[AddDependencyCommand] = AddDependencyCommandHandler(self.repository)
        
        # Query handlers  
        self._handlers[GetListQuery] = GetListQueryHandler(self.repository)
        self._handlers[GetAllListsQuery] = GetAllListsQueryHandler(self.repository)
        self._handlers[GetNextPendingWithSubtasksQuery] = GetNextPendingWithSubtasksQueryHandler(self.repository)
    
    def send(self, request) -> Any:
        """Send command or query to appropriate handler"""
        handler = self._handlers.get(type(request))
        if not handler:
            raise ValueError(f"No handler registered for {type(request).__name__}")
        
        return handler.handle(request)
```

### Phase 3: TodoManager jako Application Service

```python
# core/manager.py
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from .infrastructure.database_repository import DatabaseTodoRepository
from .application.mediator import Mediator
from .application.commands.list_commands import CreateListCommand, DeleteListCommand
from .application.commands.item_commands import AddItemCommand, UpdateItemStatusCommand
from .application.commands.subtask_commands import AddSubtaskCommand
from .application.commands.dependency_commands import AddDependencyCommand, RemoveDependencyCommand
from .application.queries.list_queries import GetListQuery, GetAllListsQuery
from .application.queries.smart_queries import GetNextPendingWithSubtasksQuery, GetProgressQuery
from .domain.entities import TodoList, TodoItem

class TodoManager:
    """
    Application Service - Facade maintaining backward compatibility
    Uses Mediator pattern to dispatch commands/queries to appropriate handlers
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize TodoManager with mediator and repository"""
        if db_path is None:
            todoit_dir = Path.home() / ".todoit"
            todoit_dir.mkdir(exist_ok=True)
            db_path = str(todoit_dir / "todoit.db")
        
        self.repository = DatabaseTodoRepository(db_path)
        self.mediator = Mediator(self.repository)
    
    # ===== LIST OPERATIONS =====
    
    def create_list(self, list_key: str, title: str, 
                   items: Optional[List[str]] = None,
                   list_type: str = "sequential",
                   metadata: Optional[Dict] = None) -> TodoList:
        """Creates a new TODO list with optional tasks"""
        command = CreateListCommand(
            list_key=list_key,
            title=title,
            items=items,
            metadata=metadata
        )
        return self.mediator.send(command)
    
    def get_list(self, key: Union[str, int]) -> Optional[TodoList]:
        """Gets a list by key or ID"""
        query = GetListQuery(list_key=str(key))
        return self.mediator.send(query)
    
    def delete_list(self, key: Union[str, int]) -> bool:
        """Deletes a list (with dependency validation)"""
        command = DeleteListCommand(list_key=str(key))
        return self.mediator.send(command)
    
    def list_all(self, limit: Optional[int] = None) -> List[TodoList]:
        """Lists all TODO lists"""
        query = GetAllListsQuery(limit=limit)
        return self.mediator.send(query)
    
    # ===== ITEM OPERATIONS =====
    
    def add_item(self, list_key: str, item_key: str, content: str,
                position: Optional[int] = None,
                metadata: Optional[Dict] = None) -> TodoItem:
        """Adds a task to a list"""
        command = AddItemCommand(
            list_key=list_key,
            item_key=item_key,
            content=content,
            position=position,
            metadata=metadata
        )
        return self.mediator.send(command)
    
    def update_item_status(self, list_key: str, item_key: str,
                          status: Optional[str] = None,
                          completion_states: Optional[Dict] = None) -> TodoItem:
        """Updates task status with auto-completion logic"""
        command = UpdateItemStatusCommand(
            list_key=list_key,
            item_key=item_key,
            status=status,
            completion_states=completion_states
        )
        return self.mediator.send(command)
    
    # ===== SUBTASK OPERATIONS =====
    
    def add_subtask(self, list_key: str, parent_key: str, subtask_key: str, 
                   content: str, metadata: Optional[Dict] = None) -> TodoItem:
        """Add a subtask to an existing task"""
        command = AddSubtaskCommand(
            list_key=list_key,
            parent_key=parent_key,
            subtask_key=subtask_key,
            content=content,
            metadata=metadata
        )
        return self.mediator.send(command)
    
    # ===== DEPENDENCY OPERATIONS =====
    
    def add_item_dependency(self, dependent_list: str, dependent_item: str,
                           required_list: str, required_item: str,
                           dependency_type: str = "blocks",
                           metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add cross-list dependency"""
        command = AddDependencyCommand(
            dependent_list=dependent_list,
            dependent_item=dependent_item,
            required_list=required_list,
            required_item=required_item,
            dependency_type=dependency_type,
            metadata=metadata
        )
        return self.mediator.send(command)
    
    # ===== SMART ALGORITHM OPERATIONS =====
    
    def get_next_pending_with_subtasks(self, list_key: str) -> Optional[TodoItem]:
        """Get next pending task using smart algorithm with subtask prioritization"""
        query = GetNextPendingWithSubtasksQuery(list_key=list_key)
        return self.mediator.send(query)
    
    def get_progress(self, list_key: str) -> Dict[str, Any]:
        """Get enhanced progress statistics"""
        query = GetProgressQuery(list_key=list_key)
        return self.mediator.send(query)
    
    # Add remaining 30+ methods following same pattern...
```

### Phase 4: Infrastructure Layer - Repository Implementacja

```python
# core/infrastructure/database_repository.py
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from ..domain.repositories import TodoRepository
from ..domain.entities import TodoList, TodoItem
from ..database import Database, TodoListDB, TodoItemDB

class DatabaseTodoRepository(TodoRepository):
    """SQLAlchemy implementation of TodoRepository"""
    
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        
    def get_list(self, list_key: str) -> Optional[TodoList]:
        """Get list by key and convert to domain entity"""
        db_list = self.db.get_list_by_key(list_key)
        if not db_list:
            return None
        
        # Convert database model to domain entity
        domain_list = TodoList(db_list.list_key, db_list.title)
        domain_list.description = db_list.description
        domain_list.id = db_list.id
        
        # Load items
        db_items = self.db.get_list_items(db_list.id)
        for db_item in db_items:
            domain_item = self._convert_item_to_domain(db_item)
            domain_list.items.append(domain_item)
        
        return domain_list
    
    def save_list(self, todo_list: TodoList) -> TodoList:
        """Save domain entity to database"""
        with self.transaction():
            # Save list
            if not hasattr(todo_list, 'id') or todo_list.id is None:
                db_list = self.db.create_list(todo_list.key, todo_list.title, todo_list.description)
                todo_list.id = db_list.id
            else:
                self.db.update_list(todo_list.id, {
                    'title': todo_list.title,
                    'description': todo_list.description
                })
            
            # Save items
            for item in todo_list.items:
                if not hasattr(item, 'id') or item.id is None:
                    db_item = self.db.create_item(
                        todo_list.id, item.key, item.content, 
                        item.position, item.parent_id, item.metadata
                    )
                    item.id = db_item.id
                else:
                    self.db.update_item(item.id, {
                        'content': item.content,
                        'status': item.status.value,
                        'position': item.position,
                        'parent_item_id': item.parent_id,
                        'metadata': item.metadata
                    })
            
            return todo_list
    
    def get_dependency_graph(self) -> Dict[int, List[int]]:
        """Get dependency graph from database"""
        dependencies = self.db.get_all_dependencies()
        graph = {}
        
        for dep in dependencies:
            if dep.dependent_item_id not in graph:
                graph[dep.dependent_item_id] = []
            graph[dep.dependent_item_id].append(dep.required_item_id)
        
        return graph
    
    @contextmanager
    def transaction(self):
        """Database transaction context manager"""
        with self.db.transaction():
            yield
    
    def _convert_item_to_domain(self, db_item: TodoItemDB) -> TodoItem:
        """Convert database model to domain entity"""
        domain_item = TodoItem(db_item.item_key, db_item.content, db_item.list_id)
        domain_item.id = db_item.id
        domain_item.position = db_item.position
        domain_item.parent_id = db_item.parent_item_id
        domain_item.metadata = db_item.metadata or {}
        # Convert status string to enum
        domain_item.status = ItemStatus(db_item.status)
        
        return domain_item
```

## 🚀 Harmonogram Implementacji

### Week 1: Domain Layer Foundation
- [x] **Day 1-2**: Domain entities (TodoList, TodoItem)  
- [x] **Day 3**: Value objects (Status, Priority, etc.)
- [x] **Day 4**: Repository abstractions
- [x] **Day 5**: Domain exceptions i validation

### Week 2: Application Layer - Commands
- [x] **Day 1**: List command handlers (Create, Delete, Update)
- [x] **Day 2**: Item command handlers (Add, Update Status, Delete)
- [x] **Day 3**: Subtask command handlers
- [x] **Day 4**: Dependency command handlers  
- [x] **Day 5**: Mediator pattern implementation

### Week 3: Application Layer - Queries  
- [x] **Day 1**: Basic query handlers (Get List, Get Item)
- [x] **Day 2**: Smart algorithm queries (Next Pending, Progress)
- [x] **Day 3**: Hierarchy queries (Subtasks, Hierarchy)
- [x] **Day 4**: Dependency queries (Blockers, Can Start)
- [x] **Day 5**: Statistics i cross-list queries

### Week 4: Infrastructure & Integration
- [x] **Day 1**: Database repository implementation
- [x] **Day 2**: TodoManager as application service facade
- [x] **Day 3**: MCP server integration updates
- [x] **Day 4**: Unit tests for domain layer
- [x] **Day 5**: Integration tests end-to-end

### Week 5: CLI Refactoring (Optional)
- [ ] **Day 1-2**: Command group separation
- [ ] **Day 3-4**: Formatter separation  
- [ ] **Day 5**: CLI integration testing

## ✅ Oczekiwane Korzyści

### Techniczne
1. **Pojedyncza Odpowiedzialność**: Każdy handler = jeden use case
2. **Transakcyjna Spójność**: Unit of Work eliminuje ryzyko partial failures
3. **Testowalność**: Możliwość mockowania tylko repository interface
4. **Rozszerzalność**: Dodawanie nowych funkcji = nowe handlery
5. **Czytelność**: Maksymalnie 200 linii na plik vs 1219 w manager.py

### Biznesowe
1. **Stabilność**: Eliminacja transakcyjnych race conditions
2. **Wydajność**: Lepsza kontrola nad operacjami bazodanowymi
3. **Utrzymanie**: Łatwiejsze dodawanie nowych funkcji
4. **Debugowanie**: Izolacja problemów do konkretnych handlerów
5. **Kompatybilność**: Zero breaking changes dla użytkowników

## ⚠️ Obszary Ryzyka

### 1. Migracja Stanu
- **Problem**: Przekształcenie istniejących danych
- **Mitygacja**: Database schema pozostaje bez zmian, tylko kod business logic się zmienia

### 2. Regresja Funkcjonalności  
- **Problem**: Utrata funkcji podczas przepisywania
- **Mitygacja**: Komprehensive test suite + unit testy dla każdego handlera

### 3. Performance Impact
- **Problem**: Dodatkowa abstrakcja może spowolnić operacje
- **Mitygacja**: Benchmarking + optymalizacja query patterns

### 4. Team Knowledge Transfer
- **Problem**: Zespół musi poznać DDD/CQRS patterns
- **Mitygacja**: Dokumentacja + code reviews + pair programming

## 🎯 Metryki Sukcesu

1. **Coverage**: >95% test coverage dla domain layer
2. **Performance**: <5% spadek performance względem obecnego kodu
3. **LOC Reduction**: Średnio <200 linii na plik (vs obecne >1000)
4. **Cyclomatic Complexity**: <10 per method (vs obecne >20)
5. **Zero Regressions**: Wszystkie istniejące testy muszą przechodzić

---

**Status**: ❌ **IMPLEMENTACJA NIEUDANA** - Refaktoring wymagał cofnięcia
**Rezultat**: 100/121 testów w najlepszym momencie vs 136/136 w oryginalnej wersji (15 testów utraconych)
**Branch**: `refactoring-ddd-cqrs-fixes-2025-08-06` (zachowany dla analizy)
**Baseline**: Przywrócono commit `755363b` z pełną funkcjonalnością

# 🔥 LESSONS LEARNED - Analiza Nieudanego Refaktoringu

## 📊 Analiza Katastrofy

### Co Poszło Nie Tak - Statystyki

```
ORYGINALNY SYSTEM (commit 755363b):
├── manager.py: 1,219 linii (40 metod)
├── Wszystkie testy: 136/136 PASS (100%)
└── Pełna funkcjonalność: ✅

REFACTORED SYSTEM (branch refactoring-ddd-cqrs-fixes-2025-08-06):
├── TodoApplicationService: 794 linii (46 metod)
├── Dodane pliki DDD+CQRS: ~2,000 linii nowego kodu
├── Najlepszy wynik: 100/121 PASS (82.6%)
├── Utracone testy: 15 (11%)
├── Utracone linie kodu: 425 (35% funkcjonalności)
└── Rezultat: COFNIĘCIE ❌
```

### Główne Błędy w Wykonaniu

#### 1. **💥 BIG BANG APPROACH** - Krytyczny Błąd
```diff
❌ CO ZROBILIŚMY:
- Usunięcie całego manager.py (1,219 linii) jednocześnie
- Zmiana wszystkich warstw naraz
- Wszystkie 136 testów przestały działać jednocześnie

✅ CO NALEŻAŁO ZROBIĆ:
+ Incremental Strangler Fig Pattern
+ Manager.py pozostaje, nowe handlery dodawane obok
+ Jeden use case na raz
+ Testy działają przez cały czas
```

#### 2. **🚨 UTRATA FUNKCJONALNOŚCI** - 35% kodu zginęło
```python
# ❌ METODY KTÓRE ZNIKNĘŁY W REFAKTORINGU:
UTRACONE_METODY = [
    '_db_to_model',           # Konwersja DB -> Model (krytyczna!)
    'import_from_markdown',   # Import z plików
    'export_to_markdown',     # Eksport do plików  
    'get_lists_by_relation',  # Relacje między listami
    'get_item_history',       # Historia zmian
    'build_hierarchy',        # Budowanie hierarchii
    '_get_blocking_reason'    # Szczegóły blokowania
]

# ✅ WSZYSTKIE METODY MUSZĄ BYĆ ZMAPOWANE 1:1
REQUIRED_MAPPING = {
    'manager.py_method': 'new_handler_equivalent',
    # Każda metoda musi mieć odpowiednik!
}
```

#### 3. **🔄 BREAKING API CHANGES** - Brak Kompatybilności
```diff
❌ ZŁAMALIŚMY KOMPATYBILNOŚĆ:
- TodoManager -> TodoApplicationService 
- init_manager() -> init_app_service()
- Różne return types w metodach

✅ ADAPTER PATTERN WYMAGANY:
+ class TodoManager(TodoApplicationService): pass
+ Zachowanie tego samego interface
+ Parity tests: old_result == new_result
```

#### 4. **⚡ BRAK PARITY VALIDATION** - Nie sprawdziliśmy zgodności
```python
# ❌ NIE MIELIŚMY:
def test_parity_between_old_and_new():
    old_manager = TodoManager()
    new_service = TodoApplicationService()
    
    # Test każdej metody
    for method_name in METHODS:
        old_result = getattr(old_manager, method_name)(*args)
        new_result = getattr(new_service, method_name)(*args)
        assert old_result == new_result  # ❌ To nigdy nie działało!

# ✅ PARITY TESTS OBOWIĄZKOWE:
class TestRefactoringParity:
    """Every method must produce identical results"""
    
    @pytest.mark.parametrize("method,args", ALL_METHOD_COMBINATIONS)
    def test_method_parity(self, method, args):
        assert old_method(*args) == new_method(*args)
```

## 🛠️ POPRAWIONY PROCES REFAKTORINGU

### Phase 0: Pre-Refactoring Preparation (Nowa Faza!)

#### 0.1 Full Behavior Documentation
```bash
# 📋 KROK 1: Udokumentuj każdą metodę w manager.py
pytest --doctest-modules  # Wszystkie docstrings muszą mieć przykłady
coverage run --source=core.manager pytest
coverage report --show-missing  # 100% coverage PRZED refaktoringiem

# 📋 KROK 2: Parity Test Suite
cat > tests/test_refactoring_parity.py << EOF
"""
Parity tests - porównanie old vs new implementation
Te testy MUSZĄ przechodzić przez cały refaktoring
"""
import pytest
from core.manager import TodoManager
from core.application.todo_application_service import TodoApplicationService

class TestRefactoringParity:
    @pytest.mark.parametrize("method", ['create_list', 'add_item', ...])
    def test_all_methods_exist(self, method):
        assert hasattr(TodoManager, method)
        assert hasattr(TodoApplicationService, method)
    
    def test_create_list_parity(self):
        # Identyczne wywołania muszą dać identyczne wyniki
        old = TodoManager()
        new = TodoApplicationService()
        
        old_result = old.create_list("test", "Test List")
        new_result = new.create_list("test", "Test List") 
        
        assert old_result.list_key == new_result.list_key
        assert old_result.title == new_result.title
        # ... wszystkie pola
EOF
```

#### 0.2 Behavior Specification
```python
# 📋 KROK 3: Behavioral Specification
@dataclass
class TodoManagerBehavior:
    """Complete specification of TodoManager behavior"""
    
    def create_list_spec(self) -> Dict[str, Any]:
        return {
            'input_validation': ['list_key required', 'title required'],
            'side_effects': ['creates DB record', 'records history'],
            'return_type': 'TodoList',
            'exceptions': ['ValueError for duplicates'],
            'dependencies': ['database.create_list_table']
        }
    
    def ALL_METHODS_SPECS(self) -> Dict[str, Dict]:
        return {method: getattr(self, f"{method}_spec")() 
                for method in TodoManager.__dict__ 
                if callable(getattr(TodoManager, method))}
```

### Phase 1: Incremental Strangler Fig (Poprawiony)

#### 1.1 Co-existing Implementation
```python
# ✅ MANAGER.PY POZOSTAJE NIETKNIĘTY
class TodoManager:
    """Original implementation - DO NOT TOUCH during refactoring"""
    
    def create_list(self, *args, **kwargs):
        # Existing logic unchanged
        pass

# ✅ NOWY KOD DODAWANY OBOK
class TodoApplicationService:
    """New implementation - being developed incrementally"""
    
    def __init__(self):
        self._use_new_implementation = os.getenv('USE_NEW_IMPL', 'false') == 'true'
        self._old_manager = TodoManager() if not self._use_new_implementation else None
    
    def create_list(self, *args, **kwargs):
        if self._use_new_implementation:
            # New DDD+CQRS implementation
            return self._handle_create_list_command(*args, **kwargs)
        else:
            # Delegate to old implementation
            return self._old_manager.create_list(*args, **kwargs)
```

#### 1.2 Per-Method Migration with Feature Flags
```python
# ✅ JEDNA METODA NA RAZ
class TodoApplicationService:
    def __init__(self):
        # Feature flags per method
        self._migrated_methods = set(os.getenv('MIGRATED_METHODS', '').split(','))
    
    def create_list(self, *args, **kwargs):
        if 'create_list' in self._migrated_methods:
            return self._new_create_list(*args, **kwargs)
        else:
            return self._old_manager.create_list(*args, **kwargs)
    
    def _new_create_list(self, *args, **kwargs):
        # New DDD implementation
        command = CreateListCommand(*args, **kwargs)
        return self.mediator.send(command)

# Test configuration
export MIGRATED_METHODS="create_list"  # Only this method uses new impl
pytest tests/test_parity.py::test_create_list_parity  # Must pass
```

### Phase 2: Validation-Driven Development

#### 2.1 Continuous Parity Testing
```bash
#!/bin/bash
# scripts/validate_migration.sh

# KAŻDY COMMIT MUSI PRZEJŚĆ TE TESTY:
echo "🧪 Running Parity Tests..."
pytest tests/test_refactoring_parity.py -v

echo "📊 Running Performance Comparison..."  
pytest tests/test_performance_parity.py -v

echo "🔄 Running Original Test Suite..."
pytest tests/ -v --ignore=tests/test_refactoring_parity.py

if [ $? -eq 0 ]; then
    echo "✅ Migration step PASSED - safe to continue"
else
    echo "❌ Migration step FAILED - fix before proceeding"
    exit 1
fi
```

#### 2.2 Backward Compatibility Contract
```python
# ✅ STRICT COMPATIBILITY TESTING
class TestBackwardCompatibility:
    """No existing code should break during refactoring"""
    
    def test_mcp_tools_still_work(self):
        # MCP tools must work with both implementations
        old_mgr = TodoManager()
        new_svc = TodoApplicationService()
        
        # Same MCP call should work with both
        mcp_result_old = todo_create_list(mgr=old_mgr, ...)
        mcp_result_new = todo_create_list(mgr=new_svc, ...)
        
        assert mcp_result_old == mcp_result_new
    
    def test_cli_commands_unchanged(self):
        # CLI should not change during refactoring
        result_old = cli.run(['create-list', 'test'])
        result_new = cli.run(['create-list', 'test'])  # After migration
        
        assert result_old.exit_code == result_new.exit_code
```

### Phase 3: Final Cutover (Bezpieczny)

#### 3.1 100% Migration Verification
```python
# ✅ WSZYSTKIE METODY MUSZĄ BYĆ ZMIGROWANE
def test_complete_migration():
    old_methods = set(dir(TodoManager))
    new_methods = set(dir(TodoApplicationService))
    
    missing_methods = old_methods - new_methods
    assert not missing_methods, f"Missing methods: {missing_methods}"
    
    # Every method must pass parity test
    for method in old_methods:
        if not method.startswith('_'):
            test_method_parity(method)
```

#### 3.2 A/B Testing in Production
```python
# ✅ GRADUAL ROLLOUT
class ProductionTodoService:
    def __init__(self):
        self.rollout_percentage = int(os.getenv('NEW_IMPL_ROLLOUT', '0'))
        
    def create_list(self, *args, **kwargs):
        import random
        if random.randint(1, 100) <= self.rollout_percentage:
            return self.new_service.create_list(*args, **kwargs)
        else:
            return self.old_manager.create_list(*args, **kwargs)

# Deployment plan:
# Week 1: NEW_IMPL_ROLLOUT=10   (10% traffic)
# Week 2: NEW_IMPL_ROLLOUT=50   (50% traffic) 
# Week 3: NEW_IMPL_ROLLOUT=100  (100% traffic)
# Week 4: Remove old implementation
```

## 🎯 Nowe Metryki Sukcesu

```yaml
MANDATORY_CRITERIA:
  zero_functionality_loss: "100% method parity required"
  zero_test_regression: "136/136 tests must pass throughout"
  performance_budget: "<5% performance degradation allowed"
  
MIGRATION_PHASES:
  phase_0: "Documentation & Parity Tests - 100% ready"
  phase_1: "Method-by-method migration - 1 method per day"
  phase_2: "A/B testing - 2 weeks minimum"
  phase_3: "Full cutover - only after 100% validation"
  
ROLLBACK_PLAN:
  trigger: "Any test failure or performance degradation >5%"
  action: "Immediate rollback to previous commit"
  recovery_time: "<5 minutes"
```

## 🚀 Rekomendacja: Start Fresh z Nowym Podejściem

**VERDICT**: Obecny branch refaktoringu (`refactoring-ddd-cqrs-fixes-2025-08-06`) powinien być **zarchiwizowany** jako study case.

**NEXT STEPS**:
1. ✅ Pozostań na commit `755363b` (136/136 testów)
2. ✅ Zaimplementuj Phase 0: Full Documentation & Parity Tests  
3. ✅ Dopiero potem start Phase 1: Incremental Strangler Fig
4. 🎯 **ZERO TOLERANCE** dla regresji funkcjonalnej

**ESTIMATED TIMELINE (Realistic)**:
- Phase 0 (Preparation): 2 tygodnie
- Phase 1 (Incremental): 8 tygodni (1 metoda per tydzień)
- Phase 2 (A/B Testing): 2 tygodnie  
- Phase 3 (Cutover): 1 tydzień
- **TOTAL: 3 miesiące** (vs poprzednia próba: 1 tydzień → FAIL)

---
*"The best code is working code. Refactoring that breaks functionality isn't refactoring - it's rewriting."*