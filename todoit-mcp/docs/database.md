# Database Schema

The database schema is defined using SQLAlchemy ORM models in `core/database.py`. The following tables are used to store data:

*   **`todo_lists`**: Stores information about TODO lists.
*   **`todo_items`**: Stores information about individual TODO items.
*   **`list_relations`**: Stores relationships between TODO lists.
*   **`list_properties`**: Stores key-value properties for TODO lists.
*   **`todo_history`**: Stores a history of changes made to TODO items and lists.
*   **`item_dependencies`**: Stores dependencies between TODO items across different lists.
