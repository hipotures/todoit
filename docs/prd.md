# Implementacja TODOIT MCP

Zaimplementuj system TODOIT MCP - uniwersalny system zarządzania listami TODO z integracją MCP dla Claude Code.

## Stack technologiczny
- Python 3.12+
- SQLite (embedded)
- SQLAlchemy 2.0 + Pydantic
- MCP SDK dla Claude Code
- Click + Rich dla CLI

## Architektura
```
Claude Code <--MCP--> TodoMCPServer <--API--> TodoManager <--ORM--> SQLite
                                                    ^
                                                    |
                                               Rich CLI
```

## Struktura projektu
```
todoit-mcp/
├── core/
│   ├── manager.py      # TodoManager z 37 funkcjami
│   ├── models.py       # Pydantic models
│   └── database.py     # SQLAlchemy layer
├── interfaces/
│   ├── mcp_server.py   # MCP wrapper
│   └── cli.py          # Rich CLI
├── migrations/
│   └── init_db.sql     # Schema (4 tabele)
├── requirements.txt
└── pyproject.toml
```

## Schemat bazy
- **todo_lists**: list_key (unique), title, type, metadata (JSON)
- **todo_items**: item_key, content, status, completion_states (JSON), metadata (JSON)
- **list_relations**: dla powiązań (project_id, tag, sprint_id)
- **todo_history**: audit log

## Kluczowe funkcje (Etap 1 - minimum 10)
1. create_list (pusta, -n count, -d folder)
2. get_list (po ID lub key)
3. delete_list (z walidacją powiązań)
4. list_all
5. add_item
6. update_item_status (z multi-state)
7. get_next_pending
8. get_progress
9. import_from_markdown (multi-column → powiązane listy)
10. export_to_markdown (format [x])

## Tworzenie list - 3 tryby
```python
# Pusta
create_list("projekt_x")

# Z N elementami
create_list("tasks", template="Task nr", count=10)
# → "Task nr 1", "Task nr 2", ..., "Task nr 10"

# Z folderu
create_list("deploy", template="Deploy ", directory="/configs/")
# → zadanie dla każdego pliku
```

## Import multi-column
```
[x] [ ] Task 1    → tworzy 2 powiązane listy
[x] [x] Task 2    → lista2[N] wymaga lista1[N] = completed
```

## Multi-state completion
```python
# Dla złożonych zadań z wieloma etapami:
completion_states = {
    "designed": True,
    "implemented": True,
    "tested": False,
    "deployed": False
}
```

## CLI z Rich
```bash
# Tworzenie list
todoit list create projekt_x                          # pusta
todoit list create tasks -n 10 -t "Task nr"          # 10 elementów
todoit list create deploy -d /configs/ -t "Deploy "  # z folderu

# Operacje
todoit list show 42              # przez ID
todoit list show projekt_x       # przez key
todoit list delete lista1        # z walidacją powiązań
todoit item check tasks task_1   # oznacz jako done

# Import/Export
todoit io import tasks.md        # multi-column → wiele list
todoit io export projekt_x out.md # format [x]
```

## MCP Tools
- todo_create_list
- todo_add_item  
- todo_check_item (z multi-state)
- todo_get_next
- todo_get_progress

## Etapy implementacji

### Etap 1: Minimum (10 funkcji)
- create_list, get_list, delete_list, list_all
- add_item, update_item_status, get_next_pending, get_progress
- import_from_markdown, export_to_markdown

### Etap 2: Podstawowe rozszerzenie (8 funkcji)
- update_list, update_item, delete_item, append_items
- get_items_by_status, bulk_check
- create_list_relation, get_lists_by_relation

### Etap 3: Zaawansowane (10 funkcji)
- update_item_states, reorder_items, extend_list, insert_item
- search_items, bulk_update
- set_item_dependency, get_dependencies
- get_timeline, get_blocked_items

### Etap 4: Pełny zestaw (9 funkcji)
- clone_list, merge_lists
- reset_item, archive_list, get_item_metadata, add_note
- handle_failed, retry_failed_items, get_stale_items

## Ważne
1. Programmatic API (TodoManager) jako core
2. MCP i CLI to tylko thin wrappers
3. Każda lista ma ID (int) i key (string) - można używać obu
4. Import markdown może tworzyć wiele powiązanych list
5. Delete list sprawdza powiązania (L1->L2)
6. Export do formatu [x] Task

Rozpocznij od core/models.py, potem database.py, manager.py (etap 1), i na końcu interfejsy.

--------------------

# TODOIT MCP - Inteligentny System List TODO

**TODOIT** (Todo It) - profesjonalny system zarządzania listami TODO zoptymalizowany pod automatyzację i integrację z AI.

## 🎯 Cel i Problem

### Obecne problemy:
- LLM ma trudności z aktualizacją plików markdown (częste grepowanie)
- Brak struktury relacyjnej między zadaniami
- Trudności w śledzeniu złożonych zależności między zadaniami
- Nieefektywne parsowanie wielostanowych zadań w plikach tekstowych

### Rozwiązanie:
TODOIT MCP - serwer Model Context Protocol z Programmatic API i bazą SQLite, oferujący strukturalne zarządzanie listami TODO.

## 🏗️ Architektura

### Podejście: **Programmatic API + MCP Interface**

```
Claude Code <--stdio/MCP protocol--> MCP Server <--Programmatic API--> SQLite DB
                                          │
                                    TodoManager
                                   (Core Logic)
```

### Wybór technologii: **Python** 

**Dlaczego Python:**
- Najpopularniejszy język dla narzędzi AI i automatyzacji
- SQLAlchemy - potężny ORM z migracjami
- Łatwiejsza integracja z Claude Code i narzędziami AI
- Type hints dla lepszej dokumentacji
- Prostota implementacji MCP

### Stack technologiczny:
- **Python 3.12+** (zgodnie z projektem)
- **MCP SDK** - oficjalny Python SDK od Anthropic
- **SQLAlchemy 2.0** - ORM z async support
- **SQLite** - lekka baza embedded
- **Pydantic** - walidacja danych i modele

## 📊 Model Danych

### Tabele w SQLite:

```sql
-- Główna tabela list TODO
CREATE TABLE todo_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_key TEXT UNIQUE NOT NULL,  -- np. "project_alpha", "shopping_weekly"
    title TEXT NOT NULL,
    description TEXT,
    list_type TEXT,  -- 'sequential', 'parallel', 'hierarchical'
    parent_list_id INTEGER REFERENCES todo_lists(id),
    metadata JSON,  -- dodatkowe dane jak project_id, tags, priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pojedyncze zadania
CREATE TABLE todo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES todo_lists(id),
    item_key TEXT NOT NULL,  -- lokalny klucz w ramach listy
    content TEXT NOT NULL,
    position INTEGER NOT NULL,  -- kolejność na liście
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    completion_states JSON,  -- dla multi-state jak {"tested": true, "deployed": false}
    parent_item_id INTEGER REFERENCES todo_items(id),
    metadata JSON,  -- np. assignee, due_date, priority, tags
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(list_id, item_key)
);

-- Relacje między listami
CREATE TABLE list_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_list_id INTEGER REFERENCES todo_lists(id),
    target_list_id INTEGER REFERENCES todo_lists(id),
    relation_type TEXT NOT NULL,  -- 'dependency', 'parent', 'related'
    relation_key TEXT,  -- np. project_id, sprint_id
    metadata JSON
);

-- Historia zmian (audit log)
CREATE TABLE todo_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES todo_items(id),
    list_id INTEGER REFERENCES todo_lists(id),
    action TEXT NOT NULL,  -- 'created', 'updated', 'completed', 'failed'
    old_value JSON,
    new_value JSON,
    user_context TEXT,  -- np. 'claude_code', 'manual', 'automation'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📋 Kompletna lista funkcji TODOIT (37 funkcji)

### Podstawowe operacje na listach
1. **create_list** - Tworzenie nowej listy TODO
   - Z opcjonalnymi zadaniami od razu
   - Z metadanymi (book_id, collection_name, itp.)
   - Z typem listy (sequential, parallel, hierarchical)

2. **get_list** - Pobieranie listy po kluczu
3. **update_list** - Aktualizacja metadanych listy
4. **delete_list** - Usuwanie listy (z opcją kaskadową)
5. **list_all** - Listowanie wszystkich list (z filtrowaniem)

### Operacje na zadaniach
6. **add_item** - Dodawanie pojedynczego zadania do listy
7. **update_item** - Aktualizacja treści zadania
8. **update_item_status** - Zmiana statusu (pending → in_progress → completed/failed)
9. **update_item_states** - Aktualizacja multi-state (np. generated: true, downloaded: false)
10. **delete_item** - Usuwanie zadania
11. **reorder_items** - Zmiana kolejności zadań

### Rozszerzanie list
12. **append_items** - Dodawanie wielu zadań na końcu listy
    - Automatyczne numerowanie pozycji
    - Zachowanie istniejącej kolejności
    - Opcja dodania na początku (prepend)

13. **extend_list** - Rozszerzenie listy o zadania z innej listy/źródła
    - Import z pliku YAML z scenami
    - Kopiowanie z szablonu
    - Merge z inną listą

14. **insert_item** - Wstawienie zadania w konkretne miejsce
    - Z przesunięciem kolejnych pozycji
    - Opcja wstawienia jako pod-zadanie

### Zapytania i wyszukiwanie
15. **get_next_pending** - Pobranie następnego zadania do zrobienia
    - Z respektowaniem zależności parent/child
    - Z filtrowaniem po metadanych

16. **get_items_by_status** - Wszystkie zadania o danym statusie
17. **get_progress** - Statystyki postępu listy (%, liczby)
18. **get_lists_by_relation** - Listy powiązane (np. przez thread_id, book_id)
19. **search_items** - Wyszukiwanie zadań po treści/metadanych

### Operacje grupowe
20. **bulk_update** - Aktualizacja wielu zadań jednocześnie
21. **bulk_check** - Oznaczanie wielu zadań jako wykonane
22. **clone_list** - Klonowanie listy (np. szablon dla nowej książki)
23. **merge_lists** - Łączenie list

### Relacje i zależności
24. **set_item_dependency** - Ustawienie zależności między zadaniami
25. **create_list_relation** - Powiązanie list (thread, book, group)
26. **get_dependencies** - Pobranie drzewa zależności

### Analityka i raporty
27. **get_timeline** - Historia zmian zadania/listy
28. **get_blocked_items** - Zadania zablokowane przez zależności

### Import/Export
29. **import_from_markdown** - Import z pliku markdown (migracja)
30. **export_to_markdown** - Export do markdown

### Funkcje pomocnicze
31. **reset_item** - Reset zadania do stanu pending
32. **archive_list** - Archiwizacja ukończonej listy
33. **get_item_metadata** - Pobranie/aktualizacja metadanych
34. **add_note** - Dodanie notatki do zadania

### Obsługa błędów i ponowne próby
35. **handle_failed** - Obsługa błędów w zadaniach
36. **retry_failed_items** - Ponowienie nieudanych zadań
37. **get_stale_items** - Zadania rozpoczęte ale nieukończone (timeout)

## 📊 Etapy wdrożenia TODOIT

### Etap 1: Minimalny zestaw funkcji (10 funkcji)
- **create_list** - Tworzenie listy (pusta, z N elementami, z folderu)
- **get_list** - Pobieranie listy po ID lub nazwie
- **delete_list** - Usuwanie listy (z walidacją powiązań)
- **list_all** - Listowanie wszystkich list
- **add_item** - Dodawanie zadania
- **update_item_status** - Zmiana statusu zadania
- **get_next_pending** - Następne zadanie do zrobienia
- **get_progress** - Postęp listy
- **import_from_markdown** - Import z [ ] [x]
- **export_to_markdown** - Export do [ ] [x]

### Etap 2: Rozszerzenie podstawowe (8 funkcji)
- **update_list** - Aktualizacja listy (analogicznie do create)
- **update_item** - Aktualizacja treści zadania
- **delete_item** - Usuwanie zadania
- **append_items** - Dodawanie wielu zadań
- **get_items_by_status** - Filtrowanie po statusie
- **bulk_check** - Oznaczanie wielu jako wykonane
- **create_list_relation** - Tworzenie powiązań między listami
- **get_lists_by_relation** - Pobieranie powiązanych list

### Etap 3: Rozszerzenie zaawansowane (10 funkcji)
- **update_item_states** - Multi-state completion
- **reorder_items** - Zmiana kolejności
- **extend_list** - Rozszerzanie z różnych źródeł
- **insert_item** - Wstawianie w konkretne miejsce
- **search_items** - Wyszukiwanie zadań
- **bulk_update** - Aktualizacja grupowa
- **set_item_dependency** - Zależności między zadaniami
- **get_dependencies** - Drzewo zależności
- **get_timeline** - Historia zmian
- **get_blocked_items** - Zablokowane zadania

### Etap 4: Pełny zestaw (9 funkcji)
- **clone_list** - Klonowanie listy
- **merge_lists** - Łączenie list
- **reset_item** - Reset do pending
- **archive_list** - Archiwizacja
- **get_item_metadata** - Zarządzanie metadanymi
- **add_note** - Notatki do zadań
- **handle_failed** - Obsługa błędów
- **retry_failed_items** - Ponowne próby
- **get_stale_items** - Timeout detection

## 🔧 Programmatic API (Core)

### TodoManager - Centralna logika biznesowa:

```python
# core/manager.py
"""
TODOIT MCP - Todo It Manager
Programmatic API dla zarządzania listami TODO
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from .models import TodoList, TodoItem, CompletionStates
from .database import Database

class TodoManager:
    """Programmatic API dla zarządzania TODO - core business logic"""
    
    def __init__(self, db_path: str = "todoit.db"):
        self.db = Database(db_path)
    
    # === Zarządzanie listami ===
    
    def create_list(self, 
                   key: str, 
                   title: str, 
                   items: Optional[List[str]] = None,
                   list_type: str = "sequential",
                   metadata: Optional[Dict] = None) -> TodoList:
        """Tworzy nową listę TODO z opcjonalnymi zadaniami"""
        if self.get_list(key):
            raise ValueError(f"Lista '{key}' już istnieje")
        
        # Tworzenie listy
        list_id = self.db.insert("todo_lists", {
            "list_key": key,
            "title": title,
            "list_type": list_type,
            "metadata": metadata or {}
        })
        
        # Dodawanie zadań jeśli podane
        if items:
            for position, content in enumerate(items):
                self.add_item(key, f"item_{position}", content, position)
        
        return self.get_list(key)
    
    def export_to_markdown(self, list_key: str, file_path: str) -> None:
        """Eksportuje listę do formatu markdown [x] tekst"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        items = self.db.get_list_items(todo_list.id)
        
        with open(file_path, 'w') as f:
            for item in sorted(items, key=lambda x: x.position):
                status = '[x]' if item.status == 'completed' else '[ ]'
                f.write(f"{status} {item.content}\n")
    
    def delete_list(self, key: Union[str, int]) -> bool:
        """Usuwa listę (z walidacją powiązań)"""
        todo_list = self.get_list(key)
        if not todo_list:
            raise ValueError(f"Lista '{key}' nie istnieje")
        
        # Sprawdź czy lista ma zależne listy
        dependent_lists = self.db.get_dependent_lists(todo_list.id)
        if dependent_lists:
            deps = ", ".join([l.list_key for l in dependent_lists])
            raise ValueError(f"Nie można usunąć listy '{key}' - ma zależne listy: {deps}")
        
        # Usuń wszystkie zadania
        self.db.delete_list_items(todo_list.id)
        
        # Usuń relacje gdzie lista jest źródłem
        self.db.delete_list_relations(todo_list.id)
        
        # Usuń listę
        self.db.delete("todo_lists", todo_list.id)
        
        return True
    
    def get_list(self, key: Union[str, int]) -> Optional[TodoList]:
        """Pobiera listę po kluczu lub ID"""
        # Sprawdź czy key to liczba (ID)
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            return self.db.get_list_by_id(int(key))
        else:
            return self.db.get_list_by_key(key)
    
    def update_list(self, key: Union[str, int], title: str = None, metadata: Dict = None) -> TodoList:
        """Aktualizuje dane listy"""
        todo_list = self.get_list(key)
        if not todo_list:
            raise ValueError(f"Lista '{key}' nie istnieje")
        
        updates = {}
        if title:
            updates["title"] = title
        if metadata:
            current_meta = todo_list.metadata or {}
            current_meta.update(metadata)
            updates["metadata"] = current_meta
        
        if updates:
            updates["updated_at"] = datetime.now()
            self.db.update("todo_lists", todo_list.id, updates)
        
        return self.get_list(key)
    
    def get_lists_by_relation(self, 
                             relation_type: str, 
                             relation_key: str) -> List[TodoList]:
        """Pobiera listy powiązane relacją (np. project_id)"""
        return self.db.get_lists_by_relation(relation_type, relation_key)
    
    # === Rozszerzanie list ===
    
    def append_items(self,
                    list_key: str,
                    items: List[Dict[str, Any]]) -> List[TodoItem]:
        """Dodaje wiele zadań na końcu listy"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        # Pobierz najwyższą pozycję
        last_position = self.db.get_max_position(todo_list.id)
        
        created_items = []
        for i, item_data in enumerate(items):
            if isinstance(item_data, str):
                # Prosty string jako content
                content = item_data
                item_key = f"appended_{last_position + i + 1}"
                metadata = {}
            else:
                # Słownik z pełnymi danymi
                content = item_data.get("content", "")
                item_key = item_data.get("key", f"appended_{last_position + i + 1}")
                metadata = item_data.get("metadata", {})
            
            item = self.add_item(
                list_key=list_key,
                item_key=item_key,
                content=content,
                position=last_position + i + 1,
                metadata=metadata
            )
            created_items.append(item)
        
        return created_items
    
    def extend_list(self,
                   list_key: str,
                   source_list_key: str = None,
                   source_file: str = None,
                   items: List[str] = None) -> int:
        """Rozszerza listę o zadania z innego źródła"""
        if source_list_key:
            # Kopiowanie z innej listy
            source_list = self.get_list(source_list_key)
            if not source_list:
                raise ValueError(f"Lista źródłowa '{source_list_key}' nie istnieje")
            
            source_items = self.db.get_list_items(source_list.id)
            items_to_add = [
                {
                    "content": item.content,
                    "metadata": {**item.metadata, "copied_from": source_list_key}
                }
                for item in source_items
            ]
            
        elif source_file:
            # Import z pliku YAML (np. lista zadań)
            import yaml
            with open(source_file, 'r') as f:
                data = yaml.safe_load(f)
                items_to_add = [
                    {"content": task["name"], "metadata": task}
                    for task in data.get("tasks", [])
                ]
                
        elif items:
            # Bezpośrednia lista zadań
            items_to_add = [{"content": item} for item in items]
        else:
            raise ValueError("Musisz podać source_list_key, source_file lub items")
        
        added_items = self.append_items(list_key, items_to_add)
        return len(added_items)
    
    def insert_item(self,
                   list_key: str,
                   item_key: str,
                   content: str,
                   position: int = None,
                   after_item_key: str = None,
                   metadata: Optional[Dict] = None) -> TodoItem:
        """Wstawia zadanie w konkretne miejsce listy"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        if after_item_key:
            # Wstaw po konkretnym zadaniu
            after_item = self.get_item(list_key, after_item_key)
            if not after_item:
                raise ValueError(f"Zadanie '{after_item_key}' nie istnieje")
            position = after_item.position + 1
        elif position is None:
            raise ValueError("Musisz podać position lub after_item_key")
        
        # Przesuń wszystkie zadania od tej pozycji w górę
        self.db.shift_positions(todo_list.id, position, 1)
        
        # Wstaw nowe zadanie
        return self.add_item(
            list_key=list_key,
            item_key=item_key,
            content=content,
            position=position,
            metadata=metadata
        )
    
    # === Zarządzanie zadaniami ===
    
    def add_item(self, 
                list_key: str, 
                item_key: str, 
                content: str,
                position: Optional[int] = None,
                metadata: Optional[Dict] = None) -> TodoItem:
        """Dodaje zadanie do listy"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        if position is None:
            position = self.db.get_next_position(todo_list.id)
        
        item_id = self.db.insert("todo_items", {
            "list_id": todo_list.id,
            "item_key": item_key,
            "content": content,
            "position": position,
            "metadata": metadata or {}
        })
        
        return self.get_item(list_key, item_key)
    
    def update_item_status(self, 
                          list_key: str, 
                          item_key: str,
                          status: Optional[str] = None,
                          completion_states: Optional[Dict[str, bool]] = None) -> TodoItem:
        """Aktualizuje status zadania z obsługą multi-state"""
        item = self.get_item(list_key, item_key)
        if not item:
            raise ValueError(f"Zadanie '{item_key}' nie istnieje w liście '{list_key}'")
        
        updates = {}
        if status:
            updates["status"] = status
            if status == "in_progress":
                updates["started_at"] = datetime.now()
            elif status in ["completed", "failed"]:
                updates["completed_at"] = datetime.now()
        
        if completion_states:
            current_states = item.completion_states or {}
            current_states.update(completion_states)
            updates["completion_states"] = current_states
        
        self.db.update_item(item.id, updates)
        self._record_history(item.id, "updated", updates)
        
        return self.get_item(list_key, item_key)
    
    def get_next_pending(self, 
                        list_key: str,
                        respect_dependencies: bool = True) -> Optional[TodoItem]:
        """Pobiera następne zadanie do wykonania"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            return None
        
        items = self.db.get_items_by_status(todo_list.id, "pending")
        
        if not respect_dependencies:
            return items[0] if items else None
        
        # Sprawdzanie zależności
        for item in items:
            # Sprawdź zależności parent/child
            if item.parent_item_id:
                parent = self.db.get_item_by_id(item.parent_item_id)
                if parent.status != "completed":
                    continue
            
            # Sprawdź zależności między listami (dla list powiązanych)
            dependencies = self.db.get_list_dependencies(todo_list.id)
            if dependencies:
                # Dla list powiązanych sprawdź czy odpowiedni item w poprzedniej liście jest completed
                can_proceed = True
                for dep in dependencies:
                    if dep.metadata.get("rule") == "item_n_requires_item_n":
                        # Znajdź odpowiadający item w liście źródłowej
                        source_item = self.db.get_item_at_position(dep.source_list_id, item.position)
                        if source_item and source_item.status != "completed":
                            can_proceed = False
                            break
                
                if not can_proceed:
                    continue
            
            return item
        
        return None
    
    def get_progress(self, list_key: str) -> Dict[str, Any]:
        """Zwraca postęp realizacji listy"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        stats = self.db.get_list_stats(todo_list.id)
        return {
            "total": stats["total"],
            "completed": stats["completed"],
            "in_progress": stats["in_progress"],
            "pending": stats["pending"],
            "failed": stats["failed"],
            "completion_percentage": (stats["completed"] / stats["total"] * 100) 
                                   if stats["total"] > 0 else 0
        }
    
    # === Operacje bulk ===
    
    def bulk_update(self, 
                   list_key: str,
                   filter_criteria: Dict[str, Any],
                   updates: Dict[str, Any]) -> int:
        """Aktualizuje wiele zadań jednocześnie"""
        todo_list = self.get_list(list_key)
        if not todo_list:
            raise ValueError(f"Lista '{list_key}' nie istnieje")
        
        affected_items = self.db.bulk_update_items(
            todo_list.id, 
            filter_criteria, 
            updates
        )
        
        return len(affected_items)
    
    # === Import/Export ===
    
    def import_from_markdown(self, file_path: str, base_key: str = None) -> List[TodoList]:
        """Importuje listy z pliku markdown (obsługuje multi-column)"""
        lists_data = {}
        
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip().startswith('['):
                    # Parsowanie wszystkich kolumn [ ] lub [x]
                    columns = []
                    content = line.strip()
                    
                    # Wyciągnij wszystkie stany
                    while content.startswith('['):
                        state = content[1] == 'x'
                        columns.append(state)
                        content = content[4:]  # Skip [x] lub [ ]
                    
                    # Dla każdej kolumny tworzymy osobną listę
                    for i, state in enumerate(columns):
                        if i not in lists_data:
                            lists_data[i] = []
                        lists_data[i].append({
                            "content": content.strip(),
                            "completed": state,
                            "position": len(lists_data[i])
                        })
        
        # Tworzenie list
        created_lists = []
        base_key = base_key or f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for i, items in lists_data.items():
            list_key = f"{base_key}_col{i+1}" if len(lists_data) > 1 else base_key
            todo_list = self.create_list(
                key=list_key,
                title=f"Imported list {i+1}" if len(lists_data) > 1 else "Imported list"
            )
            
            # Dodawanie zadań
            for item in items:
                self.add_item(
                    list_key,
                    f"item_{item['position']}",
                    item["content"],
                    position=item["position"]
                )
                
                if item["completed"]:
                    self.update_item_status(
                        list_key,
                        f"item_{item['position']}",
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
    
    def _record_history(self, item_id: int, action: str, changes: Dict):
        """Zapisuje zmianę do historii"""
        self.db.insert("todo_history", {
            "item_id": item_id,
            "action": action,
            "new_value": changes,
            "user_context": "programmatic_api"
        })
```

## 🔌 MCP Server Interface

### Implementacja serwera MCP:

```python
# interfaces/mcp_server.py
"""
TODOIT MCP Server
Interface MCP dla systemu zarządzania TODO
"""
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from core.manager import TodoManager

class TodoMCPServer:
    """MCP Server interface dla TodoManager"""
    
    def __init__(self, db_path: str = "todoit.db"):
        self.manager = TodoManager(db_path)
        self.server = Server("todoit")
        self._register_tools()
    
    def _register_tools(self):
        """Rejestruje wszystkie narzędzia MCP"""
        
        @self.server.tool()
        async def todo_create_list(arguments: dict) -> dict:
            """Tworzy nową listę TODO"""
            try:
                todo_list = self.manager.create_list(
                    key=arguments["list_key"],
                    title=arguments["title"],
                    items=arguments.get("items"),
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "list": todo_list.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_add_item(arguments: dict) -> dict:
            """Dodaje zadanie do listy"""
            try:
                item = self.manager.add_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    content=arguments["content"],
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_append_items(arguments: dict) -> dict:
            """Dodaje wiele zadań na końcu listy"""
            try:
                items = self.manager.append_items(
                    list_key=arguments["list_key"],
                    items=arguments["items"]
                )
                return {
                    "success": True,
                    "added_count": len(items),
                    "items": [item.to_dict() for item in items]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_extend_list(arguments: dict) -> dict:
            """Rozszerza listę o zadania z innego źródła"""
            try:
                count = self.manager.extend_list(
                    list_key=arguments["list_key"],
                    source_list_key=arguments.get("source_list_key"),
                    source_file=arguments.get("source_file"),
                    items=arguments.get("items")
                )
                return {
                    "success": True,
                    "extended_count": count
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_insert_item(arguments: dict) -> dict:
            """Wstawia zadanie w konkretne miejsce listy"""
            try:
                item = self.manager.insert_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    content=arguments["content"],
                    position=arguments.get("position"),
                    after_item_key=arguments.get("after_item_key"),
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_check_item(arguments: dict) -> dict:
            """Oznacza zadanie jako wykonane/niewykonane"""
            try:
                states = arguments.get("states", {})
                status = arguments.get("status")
                
                # Automatyczne ustawienie statusu na podstawie stanów
                if not status and states:
                    if all(states.values()):
                        status = "completed"
                    elif any(states.values()):
                        status = "in_progress"
                
                item = self.manager.update_item_status(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    status=status,
                    completion_states=states
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_next(arguments: dict) -> dict:
            """Pobiera następne zadanie do wykonania"""
            try:
                item = self.manager.get_next_pending(
                    list_key=arguments["list_key"],
                    respect_dependencies=arguments.get("respect_dependencies", True)
                )
                if item:
                    return {
                        "success": True,
                        "item": item.to_dict()
                    }
                else:
                    return {
                        "success": True,
                        "item": None,
                        "message": "Brak zadań do wykonania"
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_progress(arguments: dict) -> dict:
            """Pobiera postęp listy"""
            try:
                progress = self.manager.get_progress(arguments["list_key"])
                return {
                    "success": True,
                    "progress": progress
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_by_project(arguments: dict) -> dict:
            """Pobiera listy powiązane z project_id"""
            try:
                lists = self.manager.get_lists_by_relation(
                    relation_type="project",
                    relation_key=arguments["project_id"]
                )
                return {
                    "success": True,
                    "lists": [l.to_dict() for l in lists]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_bulk_update(arguments: dict) -> dict:
            """Aktualizuje wiele zadań jednocześnie"""
            try:
                count = self.manager.bulk_update(
                    list_key=arguments["list_key"],
                    filter_criteria=arguments.get("filter", {}),
                    updates=arguments["updates"]
                )
                return {
                    "success": True,
                    "updated_count": count
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

async def main():
    """Uruchamia serwer MCP"""
    server = TodoMCPServer()
    async with stdio_server() as streams:
        await server.server.run(streams[0], streams[1])

if __name__ == "__main__":
    asyncio.run(main())
```

## 🖥️ CLI Interface (Rich)

### Implementacja CLI z biblioteką Rich:

```python
# interfaces/cli.py
"""
TODOIT CLI
Command Line Interface z użyciem Rich dla lepszej prezentacji
"""
import click
import json
from typing import Optional, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich import box
from core.manager import TodoManager

console = Console()
manager = TodoManager()

# === Główna grupa komend ===

@click.group()
@click.option('--db', default='todoit.db', help='Ścieżka do bazy danych')
@click.pass_context
def cli(ctx, db):
    """TODOIT - Inteligentny system zarządzania TODO"""
    ctx.ensure_object(dict)
    ctx.obj['manager'] = TodoManager(db)
    global manager
    manager = ctx.obj['manager']

# === Komendy list ===

@cli.group()
def list():
    """Zarządzanie listami TODO"""
    pass

@list.command('create')
@click.argument('key')
@click.option('--title', help='Tytuł listy')
@click.option('-n', '--count', type=int, help='Liczba elementów do utworzenia')
@click.option('-t', '--template', help='Szablon tekstu (numer dodawany na końcu)')
@click.option('-d', '--directory', help='Folder z plikami do dodania')
@click.option('--type', default='sequential', type=click.Choice(['sequential', 'parallel', 'hierarchical']))
@click.option('--metadata', '-m', help='Metadata JSON')
def list_create(key, title, count, template, directory, type, metadata):
    """Tworzy nową listę TODO"""
    with console.status(f"[bold green]Tworzenie listy '{key}'..."):
        try:
            items = None
            
            # Generowanie elementów na podstawie opcji
            if count and template:
                # Automatyczna numeracja
                items = [f"{template} {i}" for i in range(1, count + 1)]
            elif directory:
                # Lista plików z folderu
                import os
                files = sorted(os.listdir(directory))
                items = [f"{template}{f}" if template else f for f in files]
            
            # Jeśli nie podano tytułu, użyj klucza
            if not title:
                title = key.replace('_', ' ').replace('-', ' ').title()
            
            meta = json.loads(metadata) if metadata else {}
            todo_list = manager.create_list(
                key=key,
                title=title,
                items=items,
                list_type=type,
                metadata=meta
            )
            
            # Wyświetl utworzoną listę
            panel = Panel(
                f"[bold cyan]ID:[/] {todo_list.id}\n"
                f"[bold cyan]Tytuł:[/] {todo_list.title}\n"
                f"[bold cyan]Klucz:[/] {todo_list.list_key}\n"
                f"[bold cyan]Typ:[/] {todo_list.list_type}\n"
                f"[bold cyan]Zadań:[/] {len(items) if items else 0}",
                title="✅ Lista utworzona",
                border_style="green"
            )
            console.print(panel)
            
        except Exception as e:
            console.print(f"[bold red]❌ Błąd:[/] {e}")

@list.command('update')
@click.argument('key')
@click.option('--title', help='Nowy tytuł listy')
@click.option('-n', '--count', type=int, help='Liczba elementów do dodania')
@click.option('-t', '--template', help='Szablon tekstu dla nowych elementów')
@click.option('-d', '--directory', help='Folder z plikami do dodania')
@click.option('--metadata', '-m', help='Metadata JSON do aktualizacji')
def list_update(key, title, count, template, directory, metadata):
    """Aktualizuje listę TODO (dodaje elementy lub zmienia metadane)"""
    try:
        todo_list = manager.get_list(key)
        if not todo_list:
            console.print(f"[red]Lista '{key}' nie istnieje[/]")
            return
        
        # Aktualizacja tytułu
        if title:
            manager.update_list(key, title=title)
        
        # Dodawanie nowych elementów
        items_to_add = []
        if count and template:
            # Pobierz aktualną liczbę elementów dla kontynuacji numeracji
            current_items = manager.db.get_list_items(todo_list.id)
            start_num = len(current_items) + 1
            items_to_add = [f"{template} {i}" for i in range(start_num, start_num + count)]
        elif directory:
            import os
            files = sorted(os.listdir(directory))
            items_to_add = [f"{template}{f}" if template else f for f in files]
        
        if items_to_add:
            manager.append_items(key, items_to_add)
        
        # Aktualizacja metadanych
        if metadata:
            meta = json.loads(metadata)
            manager.update_list(key, metadata=meta)
        
        console.print(f"[green]✅ Zaktualizowano listę '{key}'[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@list.command('show')
@click.argument('key')
@click.option('--tree', is_flag=True, help='Wyświetl jako drzewo')
def list_show(key, tree):
    """Wyświetla szczegóły listy"""
    try:
        todo_list = manager.get_list(key)
        if not todo_list:
            console.print(f"[red]Lista '{key}' nie istnieje[/]")
            return
        
        items = manager.db.get_list_items(todo_list.id)
        
        if tree:
            # Widok drzewa
            tree = Tree(f"📋 {todo_list.title} ({todo_list.list_key})")
            
            for item in items:
                status_icon = {
                    'pending': '⏳',
                    'in_progress': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(item.status, '❓')
                
                node = tree.add(f"{status_icon} {item.content}")
                
                # Dodaj stany completion jeśli istnieją
                if item.completion_states:
                    for state, value in item.completion_states.items():
                        icon = '✅' if value else '❌'
                        node.add(f"{icon} {state}")
            
            console.print(tree)
        else:
            # Widok tabeli
            table = Table(title=f"📋 {todo_list.title} (ID: {todo_list.id})", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Klucz", style="magenta")
            table.add_column("Zadanie", style="white")
            table.add_column("Status", style="yellow")
            table.add_column("Stany", style="blue")
            
            for item in items:
                status_style = {
                    'pending': 'yellow',
                    'in_progress': 'blue',
                    'completed': 'green',
                    'failed': 'red'
                }.get(item.status, 'white')
                
                states_str = ""
                if item.completion_states:
                    states = [f"{'✅' if v else '❌'}{k}" for k, v in item.completion_states.items()]
                    states_str = " ".join(states)
                
                table.add_row(
                    str(item.position),
                    item.item_key,
                    item.content,
                    f"[{status_style}]{item.status}[/]",
                    states_str
                )
            
            console.print(table)
            
            # Pokaż postęp
            progress = manager.get_progress(key)
            console.print(f"\n[bold]Lista ID:[/] {todo_list.id}")
            console.print(f"[bold]Postęp:[/] {progress['completion_percentage']:.1f}% "
                         f"({progress['completed']}/{progress['total']})")
            
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@list.command('delete')
@click.argument('key')
@click.option('--force', is_flag=True, help='Wymuś usunięcie')
def list_delete(key, force):
    """Usuwa listę TODO (z walidacją powiązań)"""
    try:
        todo_list = manager.get_list(key)
        if not todo_list:
            console.print(f"[red]Lista '{key}' nie istnieje[/]")
            return
        
        if not force and not Confirm.ask(f"Czy na pewno chcesz usunąć listę '{key}'?"):
            return
        
        manager.delete_list(key)
        console.print(f"[green]✅ Usunięto listę '{key}'[/]")
        
    except ValueError as e:
        console.print(f"[bold red]❌ {e}[/]")
        console.print("[yellow]Wskazówka: Najpierw usuń listy zależne[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@list.command('all')
@click.option('--filter', '-f', help='Filtruj po metadata (JSON)')
def list_all(filter):
    """Wyświetla wszystkie listy"""
    try:
        lists = manager.db.get_all_lists()
        
        if filter:
            filter_dict = json.loads(filter)
            lists = [l for l in lists if all(
                l.metadata.get(k) == v for k, v in filter_dict.items()
            )]
        
        table = Table(title="📋 Wszystkie listy TODO", box=box.ROUNDED)
        table.add_column("ID", style="dim", width=4)
        table.add_column("Klucz", style="cyan")
        table.add_column("Tytuł", style="white")
        table.add_column("Typ", style="yellow")
        table.add_column("Zadań", style="green")
        table.add_column("Ukończone", style="blue")
        table.add_column("Postęp", style="magenta")
        
        for todo_list in lists:
            progress = manager.get_progress(todo_list.list_key)
            table.add_row(
                str(todo_list.id),
                todo_list.list_key,
                todo_list.title,
                todo_list.list_type,
                str(progress['total']),
                str(progress['completed']),
                f"{progress['completion_percentage']:.1f}%"
            )
        
        console.print(table)
        console.print(f"\n[bold]Łącznie list:[/] {len(lists)}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

# === Komendy zadań ===

@cli.group()
def item():
    """Zarządzanie zadaniami"""
    pass

@item.command('add')
@click.argument('list_key')
@click.argument('item_key')
@click.argument('content')
@click.option('--metadata', '-m', help='Metadata JSON')
def item_add(list_key, item_key, content, metadata):
    """Dodaje zadanie do listy"""
    try:
        meta = json.loads(metadata) if metadata else {}
        item = manager.add_item(
            list_key=list_key,
            item_key=item_key,
            content=content,
            metadata=meta
        )
        console.print(f"[green]✅ Dodano zadanie '{item_key}' do listy '{list_key}'[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@item.command('check')
@click.argument('list_key')
@click.argument('item_key')
@click.option('--status', type=click.Choice(['completed', 'failed', 'in_progress']))
@click.option('--state', '-s', multiple=True, help='Stan w formacie klucz=wartość')
def item_check(list_key, item_key, status, state):
    """Oznacza zadanie jako wykonane/zmienia stan"""
    try:
        states = {}
        for s in state:
            k, v = s.split('=')
            states[k] = v.lower() in ['true', '1', 'yes']
        
        item = manager.update_item_status(
            list_key=list_key,
            item_key=item_key,
            status=status,
            completion_states=states if states else None
        )
        
        console.print(f"[green]✅ Zaktualizowano '{item_key}'[/]")
        if states:
            console.print("Stany:")
            for k, v in states.items():
                icon = '✅' if v else '❌'
                console.print(f"  {icon} {k}")
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@item.command('next')
@click.argument('list_key')
@click.option('--start', is_flag=True, help='Rozpocznij zadanie')
def item_next(list_key, start):
    """Pobiera następne zadanie do wykonania"""
    try:
        item = manager.get_next_pending(list_key)
        if not item:
            console.print(f"[yellow]Brak zadań do wykonania w liście '{list_key}'[/]")
            return
        
        panel = Panel(
            f"[bold cyan]Zadanie:[/] {item.content}\n"
            f"[bold cyan]Klucz:[/] {item.item_key}\n"
            f"[bold cyan]Pozycja:[/] {item.position}",
            title="⏭️ Następne zadanie",
            border_style="cyan"
        )
        console.print(panel)
        
        if start and Confirm.ask("Rozpocząć to zadanie?"):
            manager.update_item_status(list_key, item.item_key, status='in_progress')
            console.print("[green]✅ Zadanie rozpoczęte[/]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

# === Komendy rozszerzania ===

@item.command('append')
@click.argument('list_key')
@click.argument('items', nargs=-1, required=True)
def item_append(list_key, items):
    """Dodaje wiele zadań na końcu listy"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Dodawanie {len(items)} zadań...", total=len(items))
            
            created = manager.append_items(list_key, list(items))
            
            for i, item in enumerate(created):
                progress.update(task, advance=1, description=f"Dodano: {item.content}")
        
        console.print(f"[green]✅ Dodano {len(created)} zadań do listy '{list_key}'[/]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

# === Komendy analityczne ===

@cli.group()
def stats():
    """Statystyki i raporty"""
    pass

@stats.command('progress')
@click.argument('list_key')
@click.option('--detailed', is_flag=True, help='Szczegółowe statystyki')
def stats_progress(list_key, detailed):
    """Wyświetla postęp listy"""
    try:
        progress = manager.get_progress(list_key)
        todo_list = manager.get_list(list_key)
        
        # Panel z postępem
        panel = Panel(
            f"[bold cyan]Lista:[/] {todo_list.title}\n"
            f"[bold cyan]Ukończone:[/] {progress['completed']}/{progress['total']} "
            f"({progress['completion_percentage']:.1f}%)\n"
            f"[bold cyan]W trakcie:[/] {progress['in_progress']}\n"
            f"[bold cyan]Oczekujące:[/] {progress['pending']}\n"
            f"[bold cyan]Nieudane:[/] {progress['failed']}",
            title="📊 Postęp realizacji",
            border_style="blue"
        )
        console.print(panel)
        
        if detailed:
            # Wykres postępu
            total = progress['total']
            if total > 0:
                completed_bar = '█' * int(progress['completed'] / total * 30)
                in_progress_bar = '▒' * int(progress['in_progress'] / total * 30)
                pending_bar = '░' * int(progress['pending'] / total * 30)
                
                console.print(f"\n[green]{completed_bar}[/][yellow]{in_progress_bar}[/][dim]{pending_bar}[/]")
                
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

# === Komendy importu/exportu ===

@cli.group()
def io():
    """Import/Export danych"""
    pass

@io.command('import')
@click.argument('file_path')
@click.option('--key', help='Bazowy klucz dla importowanych list')
def io_import(file_path, key):
    """Importuje listy z pliku markdown (obsługuje multi-column)"""
    try:
        with console.status(f"[bold green]Importowanie z {file_path}..."):
            lists = manager.import_from_markdown(file_path, base_key=key)
        
        if len(lists) == 1:
            console.print(f"[green]✅ Zaimportowano 1 listę: '{lists[0].list_key}'[/]")
        else:
            console.print(f"[green]✅ Zaimportowano {len(lists)} powiązanych list:[/]")
            for i, lst in enumerate(lists):
                relation = " → zależy od poprzedniej" if i > 0 else ""
                console.print(f"  • {lst.list_key}{relation}")
        
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

@io.command('export')
@click.argument('list_key')
@click.argument('file_path')
def io_export(list_key, file_path):
    """Eksportuje listę do markdown [x] format"""
    try:
        manager.export_to_markdown(list_key, file_path)
        console.print(f"[green]✅ Wyeksportowano listę '{list_key}' do {file_path}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Błąd:[/] {e}")

# === Interaktywny tryb ===

@cli.command()
def interactive():
    """Tryb interaktywny z menu"""
    console.print(Panel.fit(
        "[bold cyan]TODOIT - Tryb Interaktywny[/]\n"
        "Wpisz 'help' aby zobaczyć dostępne komendy",
        border_style="cyan"
    ))
    
    while True:
        try:
            command = Prompt.ask("\n[bold cyan]todoit>[/]")
            
            if command.lower() in ['exit', 'quit', 'q']:
                break
            elif command.lower() == 'help':
                console.print("""
[bold]Dostępne komendy:[/]
  lists          - Pokaż wszystkie listy
  show <key>     - Pokaż szczegóły listy
  next <key>     - Następne zadanie z listy
  check <key> <item> - Oznacz zadanie jako wykonane
  progress <key> - Pokaż postęp listy
  help          - Ta pomoc
  exit          - Wyjście
                """)
            elif command.startswith('lists'):
                ctx = click.Context(list_all)
                list_all.invoke(ctx)
            elif command.startswith('show '):
                key = command.split()[1]
                ctx = click.Context(list_show)
                list_show.invoke(ctx, key=key, tree=False)
            elif command.startswith('next '):
                key = command.split()[1]
                ctx = click.Context(item_next)
                item_next.invoke(ctx, list_key=key, start=False)
            elif command.startswith('progress '):
                key = command.split()[1]
                ctx = click.Context(stats_progress)
                stats_progress.invoke(ctx, list_key=key, detailed=True)
            else:
                console.print(f"[red]Nieznana komenda: {command}[/]")
                
        except Exception as e:
            console.print(f"[red]Błąd: {e}[/]")
    
    console.print("[yellow]Do zobaczenia! 👋[/]")

if __name__ == '__main__':
    cli()
```

### Przykłady użycia CLI:

```bash
# Tworzenie pustej listy
todoit list create 0004_brave_new_world-generowanie_obrazów

# Tworzenie listy z N elementami (automatyczna numeracja)
todoit list create projekt_alpha -n 10 -t "Zadanie nr"
# Tworzy: "Zadanie nr 1", "Zadanie nr 2", ..., "Zadanie nr 10"

# Tworzenie listy na podstawie plików w folderze
todoit list create deployment_tasks -t "Deploy " -d /deploy/configs/
# Tworzy: "Deploy config1.yaml", "Deploy config2.yaml", ...

# Import z markdown (automatyczne powiązania dla multi-column)
todoit io import TODO-LISTS.md
# [x] [ ] Zadanie 1 → tworzy 2 powiązane listy
# [x] [x] Zadanie 2 → gdzie lista2[N] wymaga lista1[N] = completed

# Aktualizacja listy (analogicznie do create)
todoit list update projekt_alpha -n 5 -t "Nowe zadanie nr"

# Użycie ID lub nazwy
todoit list show 42              # przez ID
todoit list show projekt_alpha   # przez nazwę

# Usuwanie z walidacją powiązań
todoit list delete lista1
# Error: Cannot delete lista1 - has dependent list: lista2

# Export do formatu [x]
todoit io export projekt_alpha tasks.md
# Generuje: [x] Zadanie 1
#          [ ] Zadanie 2

# Inne operacje
todoit item check projekt_alpha task_1
todoit item next projekt_alpha --start
todoit stats progress deployment --detailed
todoit item append shopping "Masło" "Ser" "Jogurt"

# Tryb interaktywny
todoit interactive
```

### Konfiguracja Rich dla lepszego wyglądu:

```python
# config/cli_theme.py
from rich.theme import Theme

TODOIT_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "pending": "yellow",
    "in_progress": "blue",
    "completed": "green",
    "failed": "red"
})
```

## 🔌 MCP Server Interface

### Implementacja serwera MCP:

```python
# interfaces/mcp_server.py
"""
TODOIT MCP Server
Interface MCP dla systemu zarządzania TODO
"""
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from core.manager import TodoManager

class TodoMCPServer:
    """MCP Server interface dla TodoManager"""
    
    def __init__(self, db_path: str = "todoit.db"):
        self.manager = TodoManager(db_path)
        self.server = Server("todoit")
        self._register_tools()
    
    def _register_tools(self):
        """Rejestruje wszystkie narzędzia MCP"""
        
        @self.server.tool()
        async def todo_append_items(arguments: dict) -> dict:
            """Dodaje wiele zadań na końcu listy"""
            try:
                items = self.manager.append_items(
                    list_key=arguments["list_key"],
                    items=arguments["items"]
                )
                return {
                    "success": True,
                    "added_count": len(items),
                    "items": [item.to_dict() for item in items]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_extend_list(arguments: dict) -> dict:
            """Rozszerza listę o zadania z innego źródła"""
            try:
                count = self.manager.extend_list(
                    list_key=arguments["list_key"],
                    source_list_key=arguments.get("source_list_key"),
                    source_file=arguments.get("source_file"),
                    items=arguments.get("items")
                )
                return {
                    "success": True,
                    "extended_count": count
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_insert_item(arguments: dict) -> dict:
            """Wstawia zadanie w konkretne miejsce listy"""
            try:
                item = self.manager.insert_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    content=arguments["content"],
                    position=arguments.get("position"),
                    after_item_key=arguments.get("after_item_key"),
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_create_list(arguments: dict) -> dict:
            """Tworzy nową listę TODO"""
            try:
                todo_list = self.manager.create_list(
                    key=arguments["list_key"],
                    title=arguments["title"],
                    items=arguments.get("items"),
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "list": todo_list.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_add_item(arguments: dict) -> dict:
            """Dodaje zadanie do listy"""
            try:
                item = self.manager.add_item(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    content=arguments["content"],
                    metadata=arguments.get("metadata")
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_check_item(arguments: dict) -> dict:
            """Oznacza zadanie jako wykonane/niewykonane"""
            try:
                states = arguments.get("states", {})
                status = arguments.get("status")
                
                # Automatyczne ustawienie statusu na podstawie stanów
                if not status and states:
                    if all(states.values()):
                        status = "completed"
                    elif any(states.values()):
                        status = "in_progress"
                
                item = self.manager.update_item_status(
                    list_key=arguments["list_key"],
                    item_key=arguments["item_key"],
                    status=status,
                    completion_states=states
                )
                return {
                    "success": True,
                    "item": item.to_dict()
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_next(arguments: dict) -> dict:
            """Pobiera następne zadanie do wykonania"""
            try:
                item = self.manager.get_next_pending(
                    list_key=arguments["list_key"],
                    respect_dependencies=arguments.get("respect_dependencies", True)
                )
                if item:
                    return {
                        "success": True,
                        "item": item.to_dict()
                    }
                else:
                    return {
                        "success": True,
                        "item": None,
                        "message": "Brak zadań do wykonania"
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_progress(arguments: dict) -> dict:
            """Pobiera postęp listy"""
            try:
                progress = self.manager.get_progress(arguments["list_key"])
                return {
                    "success": True,
                    "progress": progress
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_get_by_thread(arguments: dict) -> dict:
            """Pobiera listy powiązane z thread_id"""
            try:
                lists = self.manager.get_lists_by_relation(
                    relation_type="thread",
                    relation_key=arguments["thread_id"]
                )
                return {
                    "success": True,
                    "lists": [l.to_dict() for l in lists]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.server.tool()
        async def todo_bulk_update(arguments: dict) -> dict:
            """Aktualizuje wiele zadań jednocześnie"""
            try:
                count = self.manager.bulk_update(
                    list_key=arguments["list_key"],
                    filter_criteria=arguments.get("filter", {}),
                    updates=arguments["updates"]
                )
                return {
                    "success": True,
                    "updated_count": count
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

async def main():
    """Uruchamia serwer MCP"""
    server = TodoMCPServer()
    async with stdio_server() as streams:
        await server.server.run(streams[0], streams[1])

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Kluczowe mechanizmy

### Tworzenie list - elastyczne opcje:
```python
# 1. Pusta lista
create_list(key="projekt_x")

# 2. Lista z N elementami (automatyczna numeracja)
create_list(key="tasks", template="Task nr", count=10)
# Tworzy: "Task nr 1", "Task nr 2", ..., "Task nr 10"

# 3. Lista na podstawie folderu
create_list(key="deploy", template="Deploy ", directory="/configs/")
# Tworzy zadania dla każdego pliku w folderze

# 4. Import z markdown (automatyczne powiązania)
import_from_markdown("tasks.md")
# [x] [ ] Task 1 → tworzy 2 powiązane listy
# gdzie lista2[N] wymaga lista1[N] = completed
```

### Identyfikacja list:
- Każda lista ma unikalne **ID** (liczba) i unikalny **key** (string)
- Można używać obu: `get_list("42")` lub `get_list("projekt_x")`

### Powiązania i zależności:
- Import multi-column automatycznie tworzy powiązane listy
- Lista L2 powiązana z L1 blokuje zadania N w L2 dopóki L1[N] != completed
- Nie można usunąć listy L1 jeśli istnieje powiązana L2

## 💡 Kluczowe funkcjonalności

### 1. Multi-state completion
Dla złożonych zadań z wieloma etapami:
```python
completion_states = {
    "designed": True,
    "implemented": True,
    "tested": False,
    "deployed": False
}
```

### 2. Hierarchiczne listy
- Listy mogą mieć pod-listy (parent_list_id)
- Zadania mogą mieć pod-zadania (parent_item_id)
- Automatyczne propagowanie statusów w górę hierarchii

### 3. Relacje między listami
- Po project_id dla zadań projektu
- Po sprint_id dla zadań sprintu
- Po tag dla grupowania tematycznego

### 4. Smart queries przez Programmatic API
```python
# Pobierz pierwsze niezrobione zadanie z uwzględnieniem zależności
next_item = manager.get_next_pending("project_alpha", respect_dependencies=True)

# Pobierz wszystkie listy dla projektu
project_lists = manager.get_lists_by_relation("project", "alpha")
```

## 🚀 Przykłady użycia

### 1. Projekt development:
```python
# Tworzenie listy
todo_create_list(
    list_key="project_alpha",
    title="Project Alpha - Development Tasks",
    items=["Setup repository", "Create database schema", "Implement API"],
    metadata={"project": "alpha", "team": "backend"}
)

# Śledzenie postępu z multi-state
todo_check_item(
    list_key="project_alpha",
    item_key="api",
    states={"designed": True, "implemented": True, "tested": False}
)
```

### 2. Pipeline deployment:
```python
# Hierarchiczna lista dla procesu
todo_create_list(
    list_key="deployment_pipeline",
    title="Deployment Pipeline Q1",
    list_type="sequential",
    metadata={"environment": "production", "quarter": "Q1"}
)

# Sprawdzanie postępu
progress = todo_get_progress(list_key="deployment_pipeline")
# {"total": 15, "completed": 8, "completion_percentage": 53.3}
```

### 3. Import z istniejącego markdown:
```python
# W kodzie Python (nie przez MCP)
manager = TodoManager()
manager.import_from_markdown("TODO-LIST.md", "imported_tasks")
```

### 4. Rozszerzanie list w trakcie pracy:
```python
# Dodawanie dodatkowych kroków
todo_append_items(
    list_key="deployment_pipeline",
    items=[
        {"content": "Run security scan", "metadata": {"priority": "high"}},
        {"content": "Update documentation", "metadata": {"assignee": "docs-team"}}
    ]
)

# Rozszerzenie o kroki post-deployment
todo_extend_list(
    list_key="deployment_pipeline",
    items=[
        "Monitor performance metrics",
        "Collect user feedback",
        "Plan optimization round"
    ]
)

# Wstawienie kroków walidacji
todo_insert_item(
    list_key="deployment_pipeline",
    item_key="validate_stage_1",
    content="Validate stage 1 completion",
    after_item_key="deploy_to_staging"
)

## 📦 Struktura projektu

```
todoit-mcp/
├── core/                   # Programmatic API (core logic)
│   ├── __init__.py
│   ├── manager.py         # TodoManager - główna logika
│   ├── models.py          # Modele danych (Pydantic)
│   ├── database.py        # Warstwa dostępu do DB
│   └── validators.py      # Reguły biznesowe
├── interfaces/            # Interfejsy dostępu
│   ├── mcp_server.py     # MCP Server
│   └── cli.py            # Rich CLI
├── config/               # Konfiguracja
│   └── cli_theme.py     # Motyw dla Rich CLI
├── migrations/           # Migracje DB (Alembic)
├── tests/
│   ├── test_manager.py   # Testy core API
│   ├── test_mcp.py      # Testy MCP interface
│   └── test_cli.py      # Testy CLI
├── scripts/
│   └── import_markdown.py # Migracja z markdown
├── todoit.db             # SQLite database
├── requirements.txt
├── pyproject.toml        # Konfiguracja projektu
└── README.md
```

### Requirements:
```txt
# Core
sqlalchemy>=2.0
pydantic>=2.0
python-dateutil

# MCP
mcp-server-sdk>=1.0

# CLI
click>=8.1
rich>=13.0

# Development
pytest>=7.0
pytest-asyncio
alembic

# Optional
pyyaml  # dla importu/exportu
```

### Uruchomienie:
```bash
# Instalacja
pip install -r requirements.txt

# Uruchomienie serwera MCP
python -m interfaces.mcp_server

# Konfiguracja w Claude Code MCP settings:
# Nazwa: todoit
# Komenda: python -m interfaces.mcp_server

# Uruchomienie CLI
todoit --help

# Lub jeśli nie zainstalowane globalnie
python -m interfaces.cli --help

# Tryb interaktywny
todoit interactive
```

### Przykład wyglądu CLI z Rich:

```
╭─────────────────── ✅ Lista utworzona ───────────────────╮
│ Tytuł: Project Alpha - Development                       │
│ Klucz: project_alpha                                     │
│ Typ: sequential                                          │
│ Zadań: 8                                                 │
╰──────────────────────────────────────────────────────────╯

╭──────────── 📋 Project Alpha - Development ──────────────╮
│ # │ Klucz      │ Zadanie           │ Status  │ Stany    │
├───┼────────────┼───────────────────┼─────────┼──────────┤
│ 1 │ setup_db   │ Setup database    │ done    │ ✅test   │
│ 2 │ api_design │ Design API        │ done    │ ✅review │
│ 3 │ api_impl   │ Implement API     │ working │ ✅code   │
│   │            │                   │         │ ❌test   │
│ 4 │ frontend   │ Create frontend   │ pending │          │
│ 5 │ testing    │ Integration tests │ pending │          │
╰──────────────────────────────────────────────────────────╯

Postęp: 40.0% (2/5)

[green]████████████████[/][yellow]████████[/][dim]████████████████[/]
```

## 🔐 Rozszerzalność na przyszłość

Dzięki Programmatic API, łatwo dodać w przyszłości:

### Web UI (gdy będzie potrzebne):
```python
# Streamlit, Gradio, lub własny frontend
# Wszystko używa tego samego TodoManager!
```

### pyproject.toml dla instalacji CLI:
```toml
[project]
name = "todoit-mcp"
version = "1.0.0"
description = "TODOIT - Inteligentny system zarządzania TODO"

[project.scripts]
todoit = "interfaces.cli:cli"

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
```

### Instalacja jako narzędzie:
```bash
# Instalacja w trybie edytowalnym (development)
pip install -e .

# Teraz można używać globalnie
todoit --help
todoit list all
todoit interactive
```

## 🎯 Korzyści tego podejścia

1. **Prostota**: Brak zbędnych warstw HTTP  
2. **Szybkość**: Bezpośredni dostęp do SQLite
3. **Modularność**: Programmatic API jako core
4. **Testowalność**: Łatwe testy jednostkowe core API + testowanie przez CLI
5. **Rozszerzalność**: Łatwo dodać nowe interfejsy w przyszłości
6. **Integracja**: Natywne wsparcie MCP dla Claude
7. **Developer Experience**: Rich CLI dla wygodnego testowania i debugowania
8. **Wizualizacja**: Czytelne tabele, drzewa i progress bary dzięki Rich

Ten design zapewnia prostotę początkową z możliwością łatwego rozszerzania w przyszłości!