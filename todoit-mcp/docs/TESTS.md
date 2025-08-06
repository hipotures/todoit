# Plan Rozbudowy Testów dla TODOIT MCP

## Kontekst: Aplikacja dla Jednego Użytkownika

Ten plan został dostosowany do specyfiki projektu: **aplikacji desktopowej dla jednego użytkownika**. W związku z tym, priorytety zostały przesunięte z testów związanych z współbieżnością, pracą zespołową i obciążeniem, na rzecz **niezawodności logiki biznesowej, odporności na błędy użytkownika i spójności przepływów pracy**.

## Analiza Obecnego Stanu

Projekt TODOIT MCP posiada już solidną bazę testową z ponad 120 testami w 11 plikach testowych. Obecne testy skupiają się głównie na:
- Testach integracyjnych z prawdziwą bazą danych
- Testach CLI z użyciem CliRunner
- Testach MCP tools
- Podstawowej walidacji modeli Pydantic

Jednak brakuje trzech kluczowych kategorii testów, które znacząco poprawiłyby jakość i niezawodność systemu w kontekście docelowego użytkownika.

## 1. Prawdziwe Testy Jednostkowe (z Mockami)

### Dlaczego są ważne?
Testy jednostkowe z mockami są znacznie szybsze (ms zamiast sekund) i pozwalają precyzyjnie zidentyfikować błąd w konkretnej jednostce kodu bez uruchamiania całego stosu technologicznego.

### Plan Implementacji

#### 1.1 Testy TodoManager z Mockowaną Bazą Danych

**Plik:** `tests/test_manager_unit.py`

```python
import pytest
from unittest.mock import Mock, MagicMock, patch
from core.manager import TodoManager
from core.models import TodoList, TodoItem, ItemStatus

class TestTodoManagerUnit:
    """Unit tests for TodoManager with mocked database"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        mock = MagicMock()
        mock.get_list_by_key.return_value = MagicMock(id=1, list_key="test")
        return mock
    
    @pytest.fixture
    def manager_with_mock(self, mock_db):
        """Create TodoManager with mocked database"""
        with patch('core.manager.Database') as MockDatabase:
            MockDatabase.return_value = mock_db
            manager = TodoManager(":memory:")
            manager.db = mock_db
            return manager
    
    def test_get_next_pending_algorithm(self, manager_with_mock, mock_db):
        """Test next pending task algorithm logic without DB"""
        # Setup mock data
        mock_items = [
            MagicMock(id=1, item_key="task1", status="in_progress", 
                     parent_item_id=None, position=1),
            MagicMock(id=2, item_key="task2", status="pending", 
                     parent_item_id=1, position=1),
            MagicMock(id=3, item_key="task3", status="pending", 
                     parent_item_id=1, position=2),
        ]
        mock_db.get_root_items.return_value = [mock_items[0]]
        mock_db.get_item_children.return_value = mock_items[1:3]
        mock_db.is_item_blocked.return_value = False
        
        # Test algorithm
        next_task = manager_with_mock.get_next_pending_with_subtasks("test")
        
        # Verify correct task selected (should be task2 - first subtask of in-progress parent)
        assert next_task.item_key == "task2"
        mock_db.get_root_items.assert_called_once()
    
    def test_auto_complete_parent_logic(self, manager_with_mock, mock_db):
        """Test parent auto-completion logic without DB"""
        # Setup
        parent = MagicMock(id=1, status="in_progress")
        child = MagicMock(id=2, parent_item_id=1)
        
        mock_db.get_item_by_key.return_value = child
        mock_db.get_item_by_id.return_value = parent
        mock_db.check_all_children_completed.return_value = True
        
        # Execute
        result = manager_with_mock.auto_complete_parent("test", "child1")
        
        # Verify
        assert result == True
        mock_db.update_item.assert_called_once()
        # Verify status was updated to completed
        update_args = mock_db.update_item.call_args[0]
        assert update_args[1]['status'] == 'completed'
```

#### 1.2 Testy Logiki Biznesowej bez I/O

**Plik:** `tests/test_business_logic_unit.py`

```python
class TestBusinessLogicUnit:
    """Pure business logic tests without any I/O"""
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection algorithm"""
        from core.validators import detect_circular_dependency
        
        # Create mock dependency graph
        dependencies = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["E"],
            "D": ["A"],  # Circular: A -> B -> D -> A
        }
        
        # Should detect circular dependency
        assert detect_circular_dependency("A", dependencies) == True
        assert detect_circular_dependency("E", dependencies) == False
    
    def test_priority_scoring_algorithm(self):
        """Test task priority scoring without database"""
        from core.algorithms import calculate_priority_score
        
        task_data = {
            "status": "in_progress",
            "has_subtasks": True,
            "pending_subtasks": 3,
            "position": 2,
            "depth": 1
        }
        
        score = calculate_priority_score(task_data)
        assert score == 1  # In-progress with subtasks = highest priority
```

#### 1.3 Testy MCP Server z Mockowanym Managerem

**Plik:** `tests/test_mcp_server_unit.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from interfaces.mcp_server import todo_create_list, todo_add_item

class TestMCPServerUnit:
    """Unit tests for MCP server with mocked manager"""
    
    @pytest.mark.asyncio
    async def test_todo_create_list_error_handling(self):
        """Test MCP tool error handling without real manager"""
        with patch('interfaces.mcp_server.init_manager') as mock_init:
            mock_manager = AsyncMock()
            mock_manager.create_list.side_effect = ValueError("List already exists")
            mock_init.return_value = mock_manager
            
            result = await todo_create_list("test", "Test List")
            
            assert result["success"] == False
            assert result["error"] == "List already exists"
            assert result["error_type"] == "validation"
```

## 2. Bardziej Złożone Scenariusze End-to-End (E2E)

### Dlaczego są ważne?
Weryfikują, czy całościowe przepływy pracy działają zgodnie z oczekiwaniami i czy stan aplikacji poprawnie przechodzi między kolejnymi operacjami.

### Plan Implementacji

#### 2.1 Kompleksowy Workflow Użytkownika

**Plik:** `tests/test_e2e_workflows.py`

```python
import pytest
from click.testing import CliRunner
from interfaces.cli import cli

class TestE2EWorkflows:
    """End-to-end workflow tests"""
    
    def test_complete_project_workflow(self, temp_db_path):
        """Test complete project workflow from start to finish"""
        runner = CliRunner()
        
        # STEP 1: Create project structure
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'list', 'create', 'backend', 
            '--title', 'Backend Development'
        ])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'list', 'create', 'frontend',
            '--title', 'Frontend Development'
        ])
        assert result.exit_code == 0
        
        # STEP 2: Add tasks with subtasks
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'add', 'backend', 'api', 'REST API'
        ])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'add-subtask', 'backend', 
            'api', 'auth', 'Authentication endpoints'
        ])
        assert result.exit_code == 0
        
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'add', 'frontend', 'ui', 'User Interface'
        ])
        assert result.exit_code == 0
        
        # STEP 3: Create cross-list dependency
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'dep', 'add', 
            'frontend:ui', 'requires', 'backend:api'
        ])
        assert result.exit_code == 0
        
        # STEP 4: Verify UI is blocked
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'next', 'frontend'
        ])
        assert "No tasks available" in result.output or "blocked" in result.output.lower()
        
        # STEP 5: Complete backend API
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'done', 'backend', 'auth'
        ])
        assert result.exit_code == 0
        
        # Parent should auto-complete
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'list', 'show', 'backend', '--tree'
        ])
        assert "✓" in result.output or "completed" in result.output.lower()
        
        # STEP 6: Verify UI is now unblocked
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'item', 'next', 'frontend'
        ])
        assert "ui" in result.output.lower()
        
        # STEP 7: Delete backend list and verify dependencies
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'list', 'delete', 'backend', '--force'
        ])
        assert result.exit_code == 0
        
        # Check frontend still works
        result = runner.invoke(cli, [
            '--db', temp_db_path, 'list', 'show', 'frontend'
        ])
        assert result.exit_code == 0
```

#### 2.2 Workflow Pracy Zespołowej (Nie dotyczy)

**Plik:** `tests/test_e2e_team_workflow.py`

**Uwaga:** Ten scenariusz testowy, symulujący pracę wielu zespołów, nie jest priorytetem dla aplikacji desktopowej dla jednego użytkownika i jego implementacja może zostać pominięta.

<details>
<summary>Oryginalny kod testu (zwinięty)</summary>

```python
class TestE2ETeamWorkflow:
    """Test team collaboration workflows"""
    
    def test_multi_team_project(self, temp_db_path):
        """Test workflow for multiple teams working on same project"""
        runner = CliRunner()
        
        teams = ['design', 'backend', 'frontend', 'qa']
        
        # Create lists for each team
        for team in teams:
            result = runner.invoke(cli, [
                '--db', temp_db_path, 'list', 'create', team,
                '--title', f'{team.title()} Team Tasks'
            ])
            assert result.exit_code == 0
        
        # Add tasks with dependencies mimicking real workflow
        # Design -> Backend -> Frontend -> QA
        
        # Design tasks
        runner.invoke(cli, ['--db', temp_db_path, 'item', 'add', 
                           'design', 'mockups', 'Create mockups'])
        runner.invoke(cli, ['--db', temp_db_path, 'item', 'add', 
                           'design', 'assets', 'Prepare assets'])
        
        # Backend tasks depending on design
        runner.invoke(cli, ['--db', temp_db_path, 'item', 'add', 
                           'backend', 'models', 'Create data models'])
        runner.invoke(cli, ['--db', temp_db_path, 'dep', 'add',
                           'backend:models', 'requires', 'design:mockups'])
        
        # Frontend depending on backend and design
        runner.invoke(cli, ['--db', temp_db_path, 'item', 'add',
                           'frontend', 'components', 'Build components'])
        runner.invoke(cli, ['--db', temp_db_path, 'dep', 'add',
                           'frontend:components', 'requires', 'backend:models'])
        runner.invoke(cli, ['--db', temp_db_path, 'dep', 'add',
                           'frontend:components', 'requires', 'design:assets'])
        
        # QA depending on frontend
        runner.invoke(cli, ['--db', temp_db_path, 'item', 'add',
                           'qa', 'testing', 'Test application'])
        runner.invoke(cli, ['--db', temp_db_path, 'dep', 'add',
                           'qa:testing', 'requires', 'frontend:components'])
        
        # Verify blocking chain
        result = runner.invoke(cli, ['--db', temp_db_path, 'item', 'next', 'qa'])
        assert "blocked" in result.output.lower() or "No tasks" in result.output
        
        # Complete tasks in order and verify unblocking
        for task in [('design', 'mockups'), ('design', 'assets'), 
                    ('backend', 'models'), ('frontend', 'components')]:
            runner.invoke(cli, ['--db', temp_db_path, 'item', 'done', task[0], task[1]])
        
        # Now QA should have available tasks
        result = runner.invoke(cli, ['--db', temp_db_path, 'item', 'next', 'qa'])
        assert "testing" in result.output.lower()
```
</details>

## 3. Testy Warunków Brzegowych i Obsługi Błędów

### Dlaczego są ważne?
Zapewniają, że aplikacja jest odporna na nieoczekiwane sytuacje i nie kończy pracy niekontrolowanym błędem.

### Plan Implementacji

#### 3.1 Testy Odporności na Uszkodzenia

**Plik:** `tests/test_edge_cases_robustness.py`

```python
import pytest
import tempfile
import os
from core.manager import TodoManager

class TestRobustness:
    """Test system robustness against edge cases"""
    
    def test_corrupted_database_recovery(self):
        """Test behavior with corrupted database file"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
            # Write garbage to simulate corruption
            tmp.write(b'This is not a valid SQLite database!')
        
        try:
            # Should handle gracefully
            with pytest.raises((Exception,)) as exc_info:
                manager = TodoManager(db_path)
            
            # Should be a meaningful error, not a crash
            assert "database" in str(exc_info.value).lower()
        finally:
            os.unlink(db_path)
    
    def test_database_locked_handling(self):
        """
        Test concurrent access handling.
        UWAGA: Niski priorytet w aplikacji dla jednego użytkownika.
        """
        import sqlite3
        import threading
        
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            db_path = tmp.name
            
            # Create manager
            manager1 = TodoManager(db_path)
            manager1.create_list("test", "Test List")
            
            # Lock database from another connection
            conn = sqlite3.connect(db_path)
            conn.execute("BEGIN EXCLUSIVE")
            
            # Try to access from manager
            with pytest.raises(Exception) as exc_info:
                manager2 = TodoManager(db_path)
                manager2.create_list("test2", "Test List 2")
            
            assert "locked" in str(exc_info.value).lower() or "database" in str(exc_info.value).lower()
            
            conn.close()
```

#### 3.2 Testy Limitów i Ekstremalnych Wartości

**Plik:** `tests/test_edge_cases_limits.py`

```python
class TestLimits:
    """Test system limits and extreme values"""
    
    def test_very_long_content(self, manager):
        """Test handling of very long task content"""
        # Create list
        list_obj = manager.create_list("test", "Test")
        
        # Try very long content (10KB)
        long_content = "A" * 10000
        
        # Should handle gracefully
        item = manager.add_item("test", "long", long_content)
        assert item.content == long_content
        
        # Verify it's stored and retrieved correctly
        retrieved = manager.get_item("test", "long")
        assert len(retrieved.content) == 10000
```

## 4. Struktura Organizacji Testów

### Proponowana Struktura Katalogów

```
tests/
├── unit/                      # Testy jednostkowe z mockami
│   ├── test_manager_unit.py
│   └── ...
├── integration/               # Obecne testy integracyjne
│   └── ...
├── e2e/                      # Scenariusze end-to-end
│   ├── test_e2e_workflows.py
│   └── ...
├── edge_cases/               # Testy warunków brzegowych
│   ├── test_edge_cases_robustness.py
│   └── ...
└── conftest.py              # Wspólne fixtures
```

## 5. Narzędzia i Biblioteki

### Rekomendowane Dodatki

```toml
# pyproject.toml - dodatkowe zależności testowe

[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.10.0",      # Integracja z mock
    "pytest-cov>=4.0.0",        # Coverage
]
```

## 6. Priorytety Implementacji (dla aplikacji jednoosobowej)

1.  **NAJWYŻSZY:** **Testy jednostkowe dla `TodoManager`** (core business logic). Zapewniają poprawność algorytmów w izolacji.
2.  **WYSOKI:** **Testy E2E dla głównego przepływu pracy użytkownika** (`test_complete_project_workflow`). Gwarantują, że kluczowe funkcje działają od początku do końca.
3.  **ŚREDNI:** **Testy warunków brzegowych dla danych wejściowych** (`test_edge_cases_invalid_input.py`). Zwiększają odporność aplikacji na błędy użytkownika.
4.  **NISKI:** Pozostałe testy warunków brzegowych i odporności na uszkodzenia.
5.  **POMIJANE:** Testy wydajnościowe, pracy zespołowej i współbieżności.

## 7. Podsumowanie

Implementacja tego planu znacząco poprawi:
- **Szybkość development** - szybkie testy jednostkowe dają natychmiastowy feedback
- **Pewność deploymentu** - E2E testy gwarantują działanie krytycznych ścieżek
- **Stabilność produkcyjną** - edge case testy zapobiegają nieoczekiwanym błędom

Rekomenduję rozpoczęcie od testów jednostkowych dla core business logic (TodoManager), następnie dodanie kluczowych scenariuszy E2E.
