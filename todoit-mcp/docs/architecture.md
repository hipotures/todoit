# Architecture

TODOIT MCP is designed with a modular architecture that separates concerns into three main layers:

1.  **Core Layer**: This layer contains the core business logic of the application.
    *   `database.py`: Manages all database interactions, including table creation, data retrieval, and updates. It uses SQLAlchemy for ORM.
    *   `manager.py`: Implements the `TodoManager` class, which serves as the main programmatic API for managing TODO lists and items. It encapsulates all business logic and interacts with the database layer.
    *   `models.py`: Defines the Pydantic models used for data validation and serialization throughout the application.

2.  **Interfaces Layer**: This layer provides user-facing interfaces for interacting with the application.
    *   `cli.py`: Implements the command-line interface (CLI) using the `click` library. It provides a rich set of commands for managing TODO lists and items from the command line.
    *   `mcp_server.py`: (If applicable) Implements the MCP server for integration with other systems.

3.  **Migrations Layer**: This layer contains SQL scripts for database migrations.
    *   `init_db.sql`: Initializes the database with the initial schema.
    *   `002_item_dependencies.sql`: Adds the `item_dependencies` table for cross-list dependencies.
