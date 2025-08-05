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