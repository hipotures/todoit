# Contributing to TODOIT MCP

Welcome! TODOIT is developed using AI-assisted development with Claude Code, and we welcome contributions from the community.

## 🚀 Quick Start

### Development Setup
```bash
# Clone the repository
git clone https://github.com/hipotures/todoit.git
cd todoit/todoit-mcp

# Install in development mode
pip install -e .[dev]

# Run tests to verify setup
pytest

# Install pre-commit hooks (optional)
pre-commit install
```

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
pytest
python -m interfaces.cli --help

# Format code
black core/ interfaces/ tests/
isort core/ interfaces/ tests/

# Type checking
mypy core/ --strict

# Commit and push
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

## 🎯 Ways to Contribute

### 1. Code Contributions
- **Bug Fixes** - Fix reported issues
- **Features** - Implement new functionality
- **Performance** - Optimize existing code
- **Tests** - Improve test coverage

### 2. Documentation
- **User Guides** - Improve CLI or MCP documentation
- **API Docs** - Enhance code documentation
- **Examples** - Add usage examples and tutorials
- **Translations** - Translate documentation (future)

### 3. Testing & Quality
- **Bug Reports** - Report issues with clear reproduction steps
- **Test Cases** - Add edge cases and integration tests
- **Performance Testing** - Benchmark and profile performance
- **Security Review** - Identify potential security issues

### 4. Community
- **Discussions** - Help answer questions
- **Reviews** - Review pull requests
- **Mentoring** - Help new contributors

## 📋 Development Guidelines

### Code Style
- **Python 3.12+** - Use modern Python features
- **Type Hints** - All functions should have type annotations
- **Black** - Code formatting (88 character line length)
- **isort** - Import organization
- **MyPy** - Static type checking

### Architecture Principles
- **Clean Architecture** - Core logic separated from interfaces
- **Single Responsibility** - Each class/function has one clear purpose
- **Dependency Injection** - Use constructor injection for dependencies
- **Database First** - SQLAlchemy models define the schema

### Testing Requirements
- **Unit Tests** - For core business logic (target: 90%+ coverage)
- **Integration Tests** - For database and API interactions
- **End-to-End Tests** - For complete workflow validation
- **Mocking** - Mock external dependencies appropriately

### Documentation Standards
- **Docstrings** - All public functions need docstrings
- **Type Annotations** - Include parameter and return types
- **Examples** - Include usage examples where helpful
- **Markdown** - Use clear formatting and structure

## 🔧 Technical Stack

### Core Technologies
- **SQLAlchemy 2.0** - ORM and database management
- **Pydantic V2** - Data validation and serialization
- **Click** - Command-line interface framework
- **Rich** - Terminal formatting and tables
- **FastMCP** - Model Context Protocol server

### Development Tools
- **pytest** - Test framework and runner
- **black** - Code formatter
- **isort** - Import sorter
- **mypy** - Static type checker
- **pre-commit** - Git hooks for code quality

## 📝 Pull Request Process

### Before Submitting
1. **Run Tests**: Ensure all tests pass (`pytest`)
2. **Format Code**: Run black and isort
3. **Type Check**: Run mypy with strict mode
4. **Update Docs**: Update relevant documentation
5. **Test Coverage**: Add tests for new functionality

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process
1. **Automated Checks** - CI/CD runs tests and quality checks
2. **Code Review** - Maintainer reviews code and architecture
3. **Discussion** - Address feedback and questions
4. **Merge** - Approved PRs are merged with squash commits

## 🧪 Testing Guidelines

### Test Organization
```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Database and API integration tests  
├── edge_cases/     # Edge cases and error conditions
├── e2e/           # End-to-end workflow tests
└── conftest.py    # Shared test fixtures
```

### Test Categories
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test component interactions
- **Edge Cases**: Test boundary conditions and error handling
- **End-to-End**: Test complete user workflows

### Writing Good Tests
```python
def test_descriptive_name_of_what_is_tested():
    # Arrange - Set up test data
    manager = TodoManager()
    
    # Act - Perform the action
    result = manager.create_list("test", "Test List")
    
    # Assert - Verify the result
    assert result.list_key == "test"
    assert result.title == "Test List"
```

## 🐛 Bug Reports

### Good Bug Reports Include
1. **Clear Title** - Summarize the issue
2. **Description** - What happened vs what was expected
3. **Steps to Reproduce** - Minimal reproduction steps
4. **Environment** - OS, Python version, TODOIT version
5. **Logs/Output** - Relevant error messages or output
6. **Impact** - How severe is the issue

### Bug Report Template
```markdown
## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Run command: `todoit list create test "Test"`
2. Run command: `todoit item add test item1 "Item 1"`
3. Observe error: ...

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.12.1]
- TODOIT: [e.g. 1.16.1]

## Additional Context
Any other context about the problem.
```

## 🎨 Feature Requests

### Good Feature Requests Include
1. **Problem Statement** - What problem does this solve?
2. **Proposed Solution** - How should it work?
3. **Use Cases** - Who would use this and how?
4. **Alternatives** - What alternatives have you considered?
5. **Implementation** - Any thoughts on implementation?

## 🏗️ Architecture Guidelines

### Core Layer (`core/`)
- **manager.py** - Business logic and orchestration
- **database.py** - Database layer and ORM models
- **models.py** - Pydantic data models and validation

### Interface Layer (`interfaces/`)
- **mcp_server.py** - MCP server for Claude Code integration
- **cli.py** - Command-line interface
- **cli_modules/** - Modular CLI command groups

### Design Patterns
- **Repository Pattern** - Database access through manager
- **Command Pattern** - CLI commands as individual functions
- **Factory Pattern** - Model creation and validation
- **Observer Pattern** - History tracking and audit trails

## 📦 Release Process

### Version Numbering
- **Semantic Versioning** - MAJOR.MINOR.PATCH
- **Breaking Changes** - Increment MAJOR version
- **New Features** - Increment MINOR version
- **Bug Fixes** - Increment PATCH version

### Release Checklist
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Build distribution packages
5. Create GitHub release
6. Update documentation

## 💬 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment
- Follow GitHub's community guidelines

### Communication
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Pull Requests** - Code contributions and reviews

### Getting Help
- **Documentation** - Check docs/ directory first
- **Discussions** - Ask questions in GitHub Discussions
- **Issues** - Create issues for bugs or specific problems

## 🙏 Recognition

Contributors are recognized in:
- **CHANGELOG.md** - Major contributions noted in release notes
- **README.md** - Contributors section (future)
- **GitHub** - Contributor graphs and statistics

Thank you for contributing to TODOIT! 🚀

---

*For questions about contributing, please open a discussion on GitHub.*