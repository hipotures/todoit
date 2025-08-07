# Bash Completion Demo

## Jak uruchomić completion:

1. **Włącz completion dla tej sesji:**
```bash
# Dla bash:
eval "$(_COMPLETION_EXAMPLE_PY_COMPLETE=bash_source python completion_example.py)"

# Dla zsh - najpierw sprawdź czy działa:
_COMPLETION_EXAMPLE_PY_COMPLETE=zsh_source python completion_example.py

# Jeśli powyższe pokazuje completion script, wtedy:
eval "$(_COMPLETION_EXAMPLE_PY_COMPLETE=zsh_source python completion_example.py)"
```

2. **Testuj completion:**
```bash
python completion_example.py show 00<TAB>
# Powinno pokazać: 0008_emma 0009_fahrenheit_451 0010_great_gatsby 0011_gullivers_travels 0012_harry_potter

python completion_example.py show 001<TAB>  
# Powinno pokazać: 0010_great_gatsby 0011_gullivers_travels 0012_harry_potter
```

## Jak by to wyglądało w prawdziwym todoit:

```bash
# Dodać do ~/.bashrc or ~/.zshrc:
eval "$(_TODOIT_COMPLETE=bash_source todoit)"

# Potem użycie:
todoit list show 00<TAB>
todoit item add my_project<TAB> "New task"
```

## Co robi funkcja completion:

1. **complete_list_keys()** - wywoływana przy każdym TAB
2. **Łączy się z bazą** - `TodoManager(db_path)`  
3. **Pobiera wszystkie listy** - `manager.list_all()`
4. **Filtruje po tym co wpisałeś** - `if l.list_key.startswith(incomplete)`
5. **Zwraca matching opcje** - bash je wyświetla

**Performance:** Zapytanie do SQLite ~1-5ms, całkowicie nieodczuwalne.