# Contributing to TODOIT

## Development environment
1. Clone the repository:
   ```bash
   git clone https://github.com/hipotures/todoit.git
   cd todoit/todoit-mcp
   ```
2. Install in editable mode with development dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Initialize the SQLite database if needed:
   ```bash
   python -c "from core.manager import TodoManager; TodoManager()"
   ```

## Code style
- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines.
- Format code with [Black](https://github.com/psf/black) (line length 88).
- Sort imports using [isort](https://github.com/PyCQA/isort).
- Maintain type hints and check with [mypy](https://mypy-lang.org/).

## Commit guidelines
- Make small, focused commits.
- Use present-tense, descriptive messages (e.g., `Add item model`).
- Reference related issues or tasks when applicable.

## Running tests
From the `todoit-mcp` directory run:
```bash
pytest
```
