"""
TODOIT MCP - Database Layer
SQLAlchemy models and database operations
"""

import os
import re
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    Index,
    event,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from sqlalchemy.engine import Engine

from .models import (
    TodoList as TodoListModel,
    TodoItem as TodoItemModel,
    TodoHistory as TodoHistoryModel,
    ListProperty as ListPropertyModel,
    ItemProperty as ItemPropertyModel,
    ItemDependency as ItemDependencyModel,
    ListTag as ListTagModel,
    ListTagAssignment as ListTagAssignmentModel,
    ProgressStats,
    ListType,
    ListStatus,
    ItemStatus,
    HistoryAction,
    DependencyType,
)

Base = declarative_base()


def utc_now():
    """Get current UTC timestamp - replaces deprecated datetime.utcnow()"""
    return datetime.now(timezone.utc).replace(
        tzinfo=None
    )  # Store as naive UTC for SQLite compatibility


# SQLAlchemy ORM Models
class TodoListDB(Base):
    """SQLAlchemy model for todo_lists table"""

    __tablename__ = "todo_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_key = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    list_type = Column(String(20), default="sequential")
    status = Column(String(20), default="active")
    meta_data = Column("metadata", JSON, default=lambda: {})
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    items = relationship(
        "TodoItemDB", back_populates="list", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_todo_lists_list_key", "list_key"),
    )


class TodoItemDB(Base):
    """SQLAlchemy model for todo_items table"""

    __tablename__ = "todo_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("todo_lists.id"), nullable=False)
    item_key = Column(String(100), nullable=False)
    content = Column(String(1000), nullable=False)
    position = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    completion_states = Column(JSON, default=lambda: {})
    parent_item_id = Column(Integer, ForeignKey("todo_items.id"))
    meta_data = Column("metadata", JSON, default=lambda: {})
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    list = relationship("TodoListDB", back_populates="items")
    parent = relationship("TodoItemDB", remote_side=[id], back_populates="children")
    children = relationship("TodoItemDB", back_populates="parent")

    # Indexes
    __table_args__ = (
        Index("idx_todo_items_list_id", "list_id"),
        Index("idx_todo_items_status", "status"),
        Index("idx_todo_items_position", "list_id", "position"),
        Index("idx_todo_items_parent", "parent_item_id"),
        Index("idx_todo_items_unique_key", "list_id", "parent_item_id", "item_key", unique=True),
        Index("idx_todo_items_parent_status", "parent_item_id", "status"),
    )




class ListPropertyDB(Base):
    """SQLAlchemy model for list_properties table"""

    __tablename__ = "list_properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("todo_lists.id"), nullable=False)
    property_key = Column(String(100), nullable=False)
    property_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    # Relationships
    todo_list = relationship("TodoListDB", foreign_keys=[list_id])

    # Indexes
    __table_args__ = (
        Index("idx_list_properties_list_id", "list_id"),
        Index("idx_list_properties_key", "property_key"),
        Index("idx_list_properties_unique", "list_id", "property_key", unique=True),
    )


class ItemPropertyDB(Base):
    """SQLAlchemy model for item_properties table"""

    __tablename__ = "item_properties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("todo_items.id"), nullable=False)
    property_key = Column(String(100), nullable=False)
    property_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now)

    # Relationships
    todo_item = relationship("TodoItemDB", foreign_keys=[item_id])

    # Indexes
    __table_args__ = (
        Index("idx_item_properties_item_id", "item_id"),
        Index("idx_item_properties_key", "property_key"),
        Index(
            "idx_item_properties_key_value", "property_key", "property_value"
        ),  # Optimizes property search queries
        Index("idx_item_properties_unique", "item_id", "property_key", unique=True),
    )


class ListTagDB(Base):
    """SQLAlchemy model for list_tags table"""

    __tablename__ = "list_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(20), default="blue")
    created_at = Column(DateTime, default=utc_now)

    # Indexes
    __table_args__ = (Index("idx_list_tags_name", "name"),)


class ListTagAssignmentDB(Base):
    """SQLAlchemy model for list_tag_assignments table - many-to-many relationship"""

    __tablename__ = "list_tag_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("todo_lists.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("list_tags.id"), nullable=False)
    assigned_at = Column(DateTime, default=utc_now)

    # Relationships
    todo_list = relationship("TodoListDB", foreign_keys=[list_id])
    tag = relationship("ListTagDB", foreign_keys=[tag_id])

    # Indexes
    __table_args__ = (
        Index("idx_list_tag_assignments_list_id", "list_id"),
        Index("idx_list_tag_assignments_tag_id", "tag_id"),
        Index("idx_list_tag_assignments_unique", "list_id", "tag_id", unique=True),
    )


class TodoHistoryDB(Base):
    """SQLAlchemy model for todo_history table"""

    __tablename__ = "todo_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("todo_items.id"))
    list_id = Column(Integer, ForeignKey("todo_lists.id"))
    action = Column(String(20), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    user_context = Column(String(50), default="system")
    timestamp = Column(DateTime, default=utc_now)

    # Relationships
    item = relationship("TodoItemDB")
    list = relationship("TodoListDB")

    # Indexes
    __table_args__ = (
        Index("idx_todo_history_item", "item_id"),
        Index("idx_todo_history_list", "list_id"),
        Index("idx_todo_history_timestamp", "timestamp"),
    )


class ItemDependencyDB(Base):
    """SQLAlchemy model for item_dependencies table - Phase 2"""

    __tablename__ = "item_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dependent_item_id = Column(Integer, ForeignKey("todo_items.id"), nullable=False)
    required_item_id = Column(Integer, ForeignKey("todo_items.id"), nullable=False)
    dependency_type = Column(String(20), default="blocks")
    meta_data = Column("metadata", JSON, default=lambda: {})
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    dependent_item = relationship("TodoItemDB", foreign_keys=[dependent_item_id])
    required_item = relationship("TodoItemDB", foreign_keys=[required_item_id])

    # Indexes
    __table_args__ = (
        Index("idx_item_deps_dependent", "dependent_item_id"),
        Index("idx_item_deps_required", "required_item_id"),
        Index("idx_item_deps_type", "dependency_type"),
        Index(
            "idx_item_deps_unique", "dependent_item_id", "required_item_id", unique=True
        ),
    )


class Database:
    """Database connection and operations manager"""

    def __init__(self, db_path: str = "todoit.db"):
        """Initialize database connection"""
        self.db_path = os.path.abspath(db_path)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Enable foreign key constraints for SQLite
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if "sqlite" in str(dbapi_connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Create all tables
        self.create_tables()

        # Run Phase 2 migration if needed
        self.run_phase2_migration()
        
        # Note: Subtask flexibility migration is available via migrate_subtask_keys.py
        # It's not run automatically to give users full control over schema changes

    @staticmethod
    def natural_sort_key(text: str) -> List[Union[int, str]]:
        """Convert a string to a list for natural sorting.
        
        Examples:
            'scene_0020' -> ['scene_', 20]
            'test_10' -> ['test_', 10]
            '0014_jane' -> [14, '_jane']
        """
        def convert(text_part):
            return int(text_part) if text_part.isdigit() else text_part.lower()
        
        return [convert(c) for c in re.split('([0-9]+)', text)]
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def execute_migration(self, sql_file_path: str):
        """Execute SQL migration file"""
        with open(sql_file_path, "r") as f:
            sql_content = f.read()

        from sqlalchemy import text
        with self.engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]
            for statement in statements:
                # Skip comments and empty lines
                if statement and not statement.startswith('--'):
                    conn.execute(text(statement))
            conn.commit()

    def run_phase2_migration(self):
        """Run Phase 2 migration to add item_dependencies table"""
        try:
            # Check if table already exists
            from sqlalchemy import text

            with self.get_session() as session:
                result = session.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='item_dependencies'"
                    )
                )
                if result.fetchone():
                    return  # Table already exists

            # Execute migration
            migration_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "migrations",
                "002_item_dependencies.sql",
            )
            if os.path.exists(migration_path):
                self.execute_migration(migration_path)
            else:
                # Create table directly if migration file not found
                Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            print(f"Warning: Could not run Phase 2 migration: {e}")
            # Continue anyway - table might already exist

    def run_subtask_flexibility_migration(self):
        """Run migration to enable duplicate subtask keys across different parent tasks"""
        try:
            # Check if new index already exists
            from sqlalchemy import text
            
            with self.get_session() as session:
                result = session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_todo_items_unique_key_hierarchical'")
                )
                if result.fetchone():
                    print("Subtask flexibility migration already applied")
                    return
                    
            # Run migration
            import os
            migration_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "004_subtask_key_flexibility.sql")
            if os.path.exists(migration_path):
                print("Running subtask flexibility migration...")
                self.execute_migration(migration_path)
                print("✅ Subtask flexibility migration completed successfully!")
            else:
                print(f"Warning: Migration file not found: {migration_path}")
        except Exception as e:
            print(f"Error: Could not run subtask flexibility migration: {e}")
            raise

    # TodoList operations
    def create_list(self, list_data: Dict[str, Any]) -> TodoListDB:
        """Create a new TODO list"""
        with self.get_session() as session:
            db_list = TodoListDB(**list_data)
            session.add(db_list)
            session.commit()
            session.refresh(db_list)
            return db_list

    def get_list_by_id(self, list_id: int) -> Optional[TodoListDB]:
        """Get list by ID"""
        with self.get_session() as session:
            return session.query(TodoListDB).filter(TodoListDB.id == list_id).first()

    def get_list_by_key(self, list_key: str) -> Optional[TodoListDB]:
        """Get list by key"""
        with self.get_session() as session:
            return (
                session.query(TodoListDB)
                .filter(TodoListDB.list_key == list_key)
                .first()
            )

    def get_all_lists(self, limit: Optional[int] = None) -> List[TodoListDB]:
        """Get all lists with natural sorting"""
        with self.get_session() as session:
            # Get all lists first, then sort naturally in Python
            lists = session.query(TodoListDB).all()
            
            # Sort using natural sort key
            lists.sort(key=lambda lst: self.natural_sort_key(lst.list_key))
            
            # Apply limit after sorting
            if limit and len(lists) > limit:
                lists = lists[:limit]
                
            return lists

    def update_list(
        self, list_id: int, updates: Dict[str, Any]
    ) -> Optional[TodoListDB]:
        """Update list"""
        with self.get_session() as session:
            db_list = session.query(TodoListDB).filter(TodoListDB.id == list_id).first()
            if db_list:
                for key, value in updates.items():
                    if hasattr(db_list, key):
                        setattr(db_list, key, value)
                session.commit()
                session.refresh(db_list)
            return db_list

    def delete_list(self, list_id: int) -> bool:
        """Delete list"""
        with self.get_session() as session:
            db_list = session.query(TodoListDB).filter(TodoListDB.id == list_id).first()
            if db_list:
                session.delete(db_list)
                session.commit()
                return True
            return False


    # TodoItem operations
    def create_item(self, item_data: Dict[str, Any]) -> TodoItemDB:
        """Create a new TODO item"""
        with self.get_session() as session:
            db_item = TodoItemDB(**item_data)
            session.add(db_item)
            session.commit()
            session.refresh(db_item)
            return db_item

    def get_item_by_id(self, item_id: int) -> Optional[TodoItemDB]:
        """Get item by ID"""
        with self.get_session() as session:
            return session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()

    def get_item_by_key(self, list_id: int, item_key: str) -> Optional[TodoItemDB]:
        """Get item by list_id and item_key"""
        with self.get_session() as session:
            return (
                session.query(TodoItemDB)
                .filter(TodoItemDB.list_id == list_id, TodoItemDB.item_key == item_key)
                .first()
            )

    def get_item_by_key_and_parent(self, list_id: int, item_key: str, parent_item_id: Optional[int] = None) -> Optional[TodoItemDB]:
        """Get item by list_id, item_key and parent_item_id for precise subtask lookup"""
        with self.get_session() as session:
            query = session.query(TodoItemDB).filter(
                TodoItemDB.list_id == list_id,
                TodoItemDB.item_key == item_key,
                TodoItemDB.parent_item_id == parent_item_id
            )
            return query.first()

    def get_list_items(
        self, list_id: int, status: Optional[str] = None, limit: Optional[int] = None
    ) -> List[TodoItemDB]:
        """Get all items for a list with natural sorting by item_key"""
        with self.get_session() as session:
            query = session.query(TodoItemDB).filter(TodoItemDB.list_id == list_id)
            if status:
                query = query.filter(TodoItemDB.status == status)
            
            # Get all items first, then sort naturally in Python
            items = query.all()
            
            # Separate main items and subitems
            main_items = [item for item in items if item.parent_item_id is None]
            subitems = [item for item in items if item.parent_item_id is not None]
            
            # Sort main items naturally by item_key
            main_items.sort(key=lambda item: self.natural_sort_key(item.item_key))
            
            # Group subitems by parent and sort each group naturally
            subitems_by_parent = {}
            for subitem in subitems:
                parent_id = subitem.parent_item_id
                if parent_id not in subitems_by_parent:
                    subitems_by_parent[parent_id] = []
                subitems_by_parent[parent_id].append(subitem)
            
            # Sort each subitem group naturally
            for parent_id in subitems_by_parent:
                subitems_by_parent[parent_id].sort(key=lambda item: self.natural_sort_key(item.item_key))
            
            # Combine: main items first, then subitems grouped by parent
            result = []
            for main_item in main_items:
                result.append(main_item)
                # Add subitems for this parent
                if main_item.id in subitems_by_parent:
                    result.extend(subitems_by_parent[main_item.id])
            
            # Add any orphaned subitems at the end
            for parent_id, orphaned_subitems in subitems_by_parent.items():
                # Check if this parent was already processed
                if not any(item.id == parent_id for item in main_items):
                    result.extend(orphaned_subitems)
            
            # Apply limit after sorting
            if limit is not None and limit >= 0:
                result = result[:limit]
                
            return result

    def get_items_by_status(self, list_id: int, status: str) -> List[TodoItemDB]:
        """Get items by status with natural sorting"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB)
                .filter(TodoItemDB.list_id == list_id, TodoItemDB.status == status)
                .all()
            )
            
            # Use same natural sorting logic as get_list_items
            main_items = [item for item in items if item.parent_item_id is None]
            subitems = [item for item in items if item.parent_item_id is not None]
            
            # Sort main items naturally by item_key
            main_items.sort(key=lambda item: self.natural_sort_key(item.item_key))
            
            # Group and sort subitems
            subitems_by_parent = {}
            for subitem in subitems:
                parent_id = subitem.parent_item_id
                if parent_id not in subitems_by_parent:
                    subitems_by_parent[parent_id] = []
                subitems_by_parent[parent_id].append(subitem)
            
            for parent_id in subitems_by_parent:
                subitems_by_parent[parent_id].sort(key=lambda item: self.natural_sort_key(item.item_key))
            
            # Combine results
            result = []
            for main_item in main_items:
                result.append(main_item)
                if main_item.id in subitems_by_parent:
                    result.extend(subitems_by_parent[main_item.id])
            
            # Add orphaned subitems
            for parent_id, orphaned_subitems in subitems_by_parent.items():
                if not any(item.id == parent_id for item in main_items):
                    result.extend(orphaned_subitems)
            
            return result

    def update_item(
        self, item_id: int, updates: Dict[str, Any]
    ) -> Optional[TodoItemDB]:
        """Update item"""
        with self.get_session() as session:
            db_item = session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
            if db_item:
                for key, value in updates.items():
                    if hasattr(db_item, key):
                        setattr(db_item, key, value)
                session.commit()
                session.refresh(db_item)
            return db_item

    def update_item_content(
        self, item_id: int, new_content: str
    ) -> Optional[TodoItemDB]:
        """Update item content"""
        return self.update_item(item_id, {"content": new_content})

    def rename_item(
        self, 
        item_id: int, 
        new_key: Optional[str] = None, 
        new_content: Optional[str] = None
    ) -> Optional[TodoItemDB]:
        """Update item key and/or content in database"""
        if new_key is None and new_content is None:
            raise ValueError("At least one of new_key or new_content must be provided")
            
        updates = {}
        if new_key is not None:
            updates["item_key"] = new_key
        if new_content is not None:
            updates["content"] = new_content
            
        return self.update_item(item_id, updates)

    def delete_item(self, item_id: int) -> bool:
        """Delete item (and related records)"""
        with self.get_session() as session:
            db_item = session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
            if db_item:
                # Delete related records first to avoid foreign key constraints
                # Delete history records
                session.query(TodoHistoryDB).filter(TodoHistoryDB.item_id == item_id).delete(synchronize_session=False)
                
                # Delete item properties
                session.query(ItemPropertyDB).filter(ItemPropertyDB.item_id == item_id).delete(synchronize_session=False)
                
                # Delete dependencies where this item is involved
                session.query(ItemDependencyDB).filter(
                    (ItemDependencyDB.dependent_item_id == item_id) | 
                    (ItemDependencyDB.required_item_id == item_id)
                ).delete(synchronize_session=False)
                
                # Finally delete the item itself
                session.delete(db_item)
                session.commit()
                return True
            return False

    def get_next_position(self, list_id: int, parent_item_id: Optional[int] = None) -> int:
        """Get next position for new item in list
        
        Args:
            list_id: The list ID
            parent_item_id: If provided, get next position among siblings (subtasks of same parent)
                           If None, get next position among root items (main tasks)
        """
        with self.get_session() as session:
            query = session.query(func.max(TodoItemDB.position)).filter(
                TodoItemDB.list_id == list_id
            )
            
            if parent_item_id is None:
                # Get max position among root items (main tasks)
                query = query.filter(TodoItemDB.parent_item_id.is_(None))
            else:
                # Get max position among siblings (subtasks of same parent)
                query = query.filter(TodoItemDB.parent_item_id == parent_item_id)
            
            max_pos = query.scalar()
            return (max_pos or 0) + 1

    def get_max_position(self, list_id: int) -> int:
        """Get maximum position in list"""
        with self.get_session() as session:
            max_pos = (
                session.query(func.max(TodoItemDB.position))
                .filter(TodoItemDB.list_id == list_id)
                .scalar()
            )
            return max_pos or 0

    def shift_positions(self, list_id: int, from_position: int, shift: int):
        """Shift positions of items"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB)
                .filter(
                    TodoItemDB.list_id == list_id, TodoItemDB.position >= from_position
                )
                .all()
            )
            for item in items:
                item.position += shift
            session.commit()

    def get_item_at_position(self, list_id: int, position: int) -> Optional[TodoItemDB]:
        """Get item at specific position"""
        with self.get_session() as session:
            return (
                session.query(TodoItemDB)
                .filter(TodoItemDB.list_id == list_id, TodoItemDB.position == position)
                .first()
            )

    # Statistics and progress
    def get_list_stats(self, list_id: int) -> Dict[str, int]:
        """Get statistics for a list"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB).filter(TodoItemDB.list_id == list_id).all()
            )

            stats = {
                "total": len(items),
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "failed": 0,
            }

            for item in items:
                if item.status in stats:
                    stats[item.status] += 1

            return stats


    # History operations
    def create_history_entry(self, history_data: Dict[str, Any]) -> TodoHistoryDB:
        """Create history entry"""
        with self.get_session() as session:
            db_history = TodoHistoryDB(**history_data)
            session.add(db_history)
            session.commit()
            session.refresh(db_history)
            return db_history

    def get_item_history(
        self, item_id: int, limit: Optional[int] = None
    ) -> List[TodoHistoryDB]:
        """Get history for an item"""
        with self.get_session() as session:
            query = (
                session.query(TodoHistoryDB)
                .filter(TodoHistoryDB.item_id == item_id)
                .order_by(TodoHistoryDB.timestamp.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()

    def get_list_history(
        self, list_id: int, limit: Optional[int] = None
    ) -> List[TodoHistoryDB]:
        """Get history for a list"""
        with self.get_session() as session:
            query = (
                session.query(TodoHistoryDB)
                .filter(TodoHistoryDB.list_id == list_id)
                .order_by(TodoHistoryDB.timestamp.desc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()

    # Bulk operations
    def bulk_update_items(
        self, list_id: int, filter_criteria: Dict[str, Any], updates: Dict[str, Any]
    ) -> List[TodoItemDB]:
        """Bulk update items"""
        with self.get_session() as session:
            query = session.query(TodoItemDB).filter(TodoItemDB.list_id == list_id)

            # Apply filters
            for key, value in filter_criteria.items():
                if hasattr(TodoItemDB, key):
                    query = query.filter(getattr(TodoItemDB, key) == value)

            items = query.all()

            # Apply updates
            for item in items:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

            session.commit()
            return items

    def delete_list_items(self, list_id: int):
        """Delete all items in a list"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB).filter(TodoItemDB.list_id == list_id).all()
            )
            for item in items:
                session.delete(item)
            session.commit()

    # List Properties methods
    def create_list_property(
        self, list_id: int, property_key: str, property_value: str
    ) -> ListPropertyDB:
        """Create or update a list property"""
        with self.get_session() as session:
            # Try to find existing property
            existing = (
                session.query(ListPropertyDB)
                .filter(
                    ListPropertyDB.list_id == list_id,
                    ListPropertyDB.property_key == property_key,
                )
                .first()
            )

            if existing:
                # Update existing property
                existing.property_value = property_value
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Create new property
                property_obj = ListPropertyDB(
                    list_id=list_id,
                    property_key=property_key,
                    property_value=property_value,
                )
                session.add(property_obj)
                session.commit()
                session.refresh(property_obj)
                return property_obj

    def get_list_property(
        self, list_id: int, property_key: str
    ) -> Optional[ListPropertyDB]:
        """Get a specific list property"""
        with self.get_session() as session:
            return (
                session.query(ListPropertyDB)
                .filter(
                    ListPropertyDB.list_id == list_id,
                    ListPropertyDB.property_key == property_key,
                )
                .first()
            )

    def get_list_properties(self, list_id: int) -> List[ListPropertyDB]:
        """Get all properties for a list"""
        with self.get_session() as session:
            return (
                session.query(ListPropertyDB)
                .filter(ListPropertyDB.list_id == list_id)
                .order_by(ListPropertyDB.property_key)
                .all()
            )

    def delete_list_property(self, list_id: int, property_key: str) -> bool:
        """Delete a list property"""
        with self.get_session() as session:
            property_obj = (
                session.query(ListPropertyDB)
                .filter(
                    ListPropertyDB.list_id == list_id,
                    ListPropertyDB.property_key == property_key,
                )
                .first()
            )

            if property_obj:
                session.delete(property_obj)
                session.commit()
                return True
            return False

    # Item properties CRUD operations
    def create_item_property(
        self, item_id: int, property_key: str, property_value: str
    ) -> ItemPropertyDB:
        """Create or update item property (UPSERT)"""
        with self.get_session() as session:
            existing = (
                session.query(ItemPropertyDB)
                .filter(
                    ItemPropertyDB.item_id == item_id,
                    ItemPropertyDB.property_key == property_key,
                )
                .first()
            )

            if existing:
                existing.property_value = property_value
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                return existing
            else:
                property_obj = ItemPropertyDB(
                    item_id=item_id,
                    property_key=property_key,
                    property_value=property_value,
                )
                session.add(property_obj)
                session.commit()
                session.refresh(property_obj)
                return property_obj

    def get_item_property(self, item_id: int, property_key: str) -> Optional[str]:
        """Get single item property value"""
        with self.get_session() as session:
            property_obj = (
                session.query(ItemPropertyDB)
                .filter(
                    ItemPropertyDB.item_id == item_id,
                    ItemPropertyDB.property_key == property_key,
                )
                .first()
            )
            return property_obj.property_value if property_obj else None

    def get_item_properties(self, item_id: int) -> Dict[str, str]:
        """Get all properties for an item"""
        with self.get_session() as session:
            properties = (
                session.query(ItemPropertyDB)
                .filter(ItemPropertyDB.item_id == item_id)
                .all()
            )
            return {prop.property_key: prop.property_value for prop in properties}

    def delete_item_property(self, item_id: int, property_key: str) -> bool:
        """Delete item property"""
        with self.get_session() as session:
            property_obj = (
                session.query(ItemPropertyDB)
                .filter(
                    ItemPropertyDB.item_id == item_id,
                    ItemPropertyDB.property_key == property_key,
                )
                .first()
            )

            if property_obj:
                session.delete(property_obj)
                session.commit()
                return True
            return False

    def find_items_by_property(
        self,
        list_id: int,
        property_key: str,
        property_value: str,
        limit: Optional[int] = None,
    ) -> List[TodoItemDB]:
        """Find items by property value with optional limit

        Args:
            list_id: List ID to search in
            property_key: Property name to match
            property_value: Property value to match
            limit: Maximum number of results (None = all)

        Returns:
            List of TodoItemDB objects matching the criteria
        """
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB)
                .join(ItemPropertyDB, TodoItemDB.id == ItemPropertyDB.item_id)
                .filter(TodoItemDB.list_id == list_id)
                .filter(ItemPropertyDB.property_key == property_key)
                .filter(ItemPropertyDB.property_value == property_value)
                .all()
            )

            # Sort naturally by item_key
            items.sort(key=lambda item: self.natural_sort_key(item.item_key))

            # Apply limit after sorting
            if limit is not None:
                items = items[:limit]

            return items

    def find_subitems_by_status(
        self,
        list_id: int,
        conditions: Dict[str, str],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find grouped parent-subitem matches based on sibling status conditions

        Args:
            list_id: List ID to search in
            conditions: Dictionary of {subitem_key: expected_status}
            limit: Maximum number of parent matches to return

        Returns:
            List of dictionaries with format:
            [
                {
                    "parent": TodoItemDB object,
                    "matching_subitems": [TodoItemDB objects that match conditions]
                },
                ...
            ]
        """
        with self.get_session() as session:
            matches = []

            # Find all unique parent_item_id values in the list
            parents_query = (
                session.query(TodoItemDB.parent_item_id)
                .filter(
                    TodoItemDB.list_id == list_id,
                    TodoItemDB.parent_item_id.isnot(None),
                )
                .distinct()
            )

            for (parent_id,) in parents_query:
                # Get parent item
                parent_item = session.query(TodoItemDB).filter(TodoItemDB.id == parent_id).first()
                if not parent_item:
                    continue

                # Get all subitems for this parent
                siblings = (
                    session.query(TodoItemDB)
                    .filter(TodoItemDB.parent_item_id == parent_id)
                    .all()
                )
                # Sort naturally by item_key
                siblings.sort(key=lambda item: self.natural_sort_key(item.item_key))

                # Create a dict of sibling statuses
                sibling_dict = {s.item_key: s.status for s in siblings}

                # Check if this sibling group satisfies all conditions
                all_conditions_met = all(
                    sibling_dict.get(key) == status for key, status in conditions.items()
                )

                if all_conditions_met:
                    # Collect subitems that are mentioned in conditions
                    matching_subitems = []
                    for sibling in siblings:
                        if sibling.item_key in conditions:
                            matching_subitems.append(sibling)

                    # Add this match to results
                    matches.append({
                        "parent": parent_item,
                        "matching_subitems": matching_subitems
                    })

                    # Check limit on number of matches (parent groups)
                    if len(matches) >= limit:
                        return matches

            return matches

    # Hierarchical item operations (for subtasks)
    def get_item_children(self, item_id: int) -> List[TodoItemDB]:
        """Get all direct children (subtasks) of an item"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB)
                .filter(TodoItemDB.parent_item_id == item_id)
                .all()
            )
            # Sort naturally by item_key
            items.sort(key=lambda item: self.natural_sort_key(item.item_key))
            return items

    def get_item_with_hierarchy(self, item_id: int) -> Optional[TodoItemDB]:
        """Get item with all its children recursively"""
        with self.get_session() as session:
            item = session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
            if not item:
                return None

            # Load children recursively
            def load_children(parent_item):
                children = (
                    session.query(TodoItemDB)
                    .filter(TodoItemDB.parent_item_id == parent_item.id)
                    .all()
                )
                # Sort naturally by item_key
                children.sort(key=lambda item: self.natural_sort_key(item.item_key))

                for child in children:
                    load_children(child)  # Recursive loading

                return children

            load_children(item)
            return item

    def has_subtasks(self, item_id: int) -> bool:
        """Check if an item has any subtasks"""
        with self.get_session() as session:
            from sqlalchemy import exists

            return session.query(
                exists().where(TodoItemDB.parent_item_id == item_id)
            ).scalar()

    def get_children_status_summary(self, item_id: int, session=None) -> Dict[str, int]:
        """Get count of children by status - optimized single query"""
        if session:
            return self._get_children_status_summary_with_session(item_id, session)
        else:
            with self.get_session() as new_session:
                return self._get_children_status_summary_with_session(
                    item_id, new_session
                )

    def _get_children_status_summary_with_session(
        self, item_id: int, session
    ) -> Dict[str, int]:
        """Internal method to get children status summary with provided session"""
        from sqlalchemy import func, case

        result = (
            session.query(
                func.count().label("total"),
                func.sum(case((TodoItemDB.status == "failed", 1), else_=0)).label(
                    "failed"
                ),
                func.sum(case((TodoItemDB.status == "pending", 1), else_=0)).label(
                    "pending"
                ),
                func.sum(case((TodoItemDB.status == "completed", 1), else_=0)).label(
                    "completed"
                ),
                func.sum(case((TodoItemDB.status == "in_progress", 1), else_=0)).label(
                    "in_progress"
                ),
            )
            .filter(TodoItemDB.parent_item_id == item_id)
            .first()
        )

        if not result or result.total == 0:
            return {}

        return {
            "total": result.total,
            "failed": result.failed or 0,
            "pending": result.pending or 0,
            "completed": result.completed or 0,
            "in_progress": result.in_progress or 0,
        }

    def check_all_children_completed(self, item_id: int) -> bool:
        """Check if all direct children of an item are completed"""
        summary = self.get_children_status_summary(item_id)
        if not summary:
            return True  # No children means nothing to block completion
        return summary["completed"] == summary["total"]

    def get_root_items(self, list_id: int) -> List[TodoItemDB]:
        """Get all root items (items without parent) in a list"""
        with self.get_session() as session:
            items = (
                session.query(TodoItemDB)
                .filter(
                    TodoItemDB.list_id == list_id, TodoItemDB.parent_item_id.is_(None)
                )
                .all()
            )
            # Sort naturally by item_key
            items.sort(key=lambda item: self.natural_sort_key(item.item_key))
            return items

    def get_item_depth(self, item_id: int) -> int:
        """Get the depth level of an item in hierarchy (0 = root, 1 = first level, etc.)"""
        with self.get_session() as session:
            depth = 0
            current_item = (
                session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
            )

            while current_item and current_item.parent_item_id:
                depth += 1
                current_item = (
                    session.query(TodoItemDB)
                    .filter(TodoItemDB.id == current_item.parent_item_id)
                    .first()
                )

                # Prevent infinite loops
                if depth > 10:  # Max 10 levels deep
                    break

            return depth

    def get_item_path(self, item_id: int) -> List[TodoItemDB]:
        """Get the full path from root to item (including the item itself)"""
        with self.get_session() as session:
            path = []
            current_item = (
                session.query(TodoItemDB).filter(TodoItemDB.id == item_id).first()
            )

            while current_item:
                path.insert(0, current_item)  # Insert at beginning to maintain order
                if current_item.parent_item_id:
                    current_item = (
                        session.query(TodoItemDB)
                        .filter(TodoItemDB.id == current_item.parent_item_id)
                        .first()
                    )
                else:
                    break

                # Prevent infinite loops
                if len(path) > 10:
                    break

            return path

    def has_pending_children(self, item_id: int) -> bool:
        """Check if item has any pending children (subtasks)"""
        with self.get_session() as session:
            pending_child = (
                session.query(TodoItemDB)
                .filter(
                    TodoItemDB.parent_item_id == item_id,
                    TodoItemDB.status.in_(["pending", "in_progress"]),
                )
                .first()
            )

            return pending_child is not None

    # ===== ITEM DEPENDENCIES OPERATIONS (Phase 2) =====

    def create_item_dependency(
        self, dependency_data: Dict[str, Any]
    ) -> ItemDependencyDB:
        """Create cross-list item dependency"""
        with self.get_session() as session:
            # Check if both items exist
            dependent_item = (
                session.query(TodoItemDB)
                .filter(TodoItemDB.id == dependency_data["dependent_item_id"])
                .first()
            )
            required_item = (
                session.query(TodoItemDB)
                .filter(TodoItemDB.id == dependency_data["required_item_id"])
                .first()
            )

            if not dependent_item:
                raise ValueError(
                    f"Dependent item with ID {dependency_data['dependent_item_id']} not found"
                )
            if not required_item:
                raise ValueError(
                    f"Required item with ID {dependency_data['required_item_id']} not found"
                )

            # Check for circular dependencies
            if self._would_create_circular_dependency(
                dependency_data["dependent_item_id"],
                dependency_data["required_item_id"],
            ):
                raise ValueError(
                    "Creating this dependency would create a circular reference"
                )

            # Create dependency
            db_dependency = ItemDependencyDB(**dependency_data)
            session.add(db_dependency)
            session.commit()
            session.refresh(db_dependency)
            return db_dependency

    def get_item_dependencies(
        self, item_id: int, as_dependent: bool = True
    ) -> List[ItemDependencyDB]:
        """Get dependencies for an item"""
        with self.get_session() as session:
            if as_dependent:
                # Get what this item depends on (what blocks this item)
                return (
                    session.query(ItemDependencyDB)
                    .filter(ItemDependencyDB.dependent_item_id == item_id)
                    .all()
                )
            else:
                # Get what depends on this item (what this item blocks)
                return (
                    session.query(ItemDependencyDB)
                    .filter(ItemDependencyDB.required_item_id == item_id)
                    .all()
                )

    def delete_item_dependency(
        self, dependent_item_id: int, required_item_id: int
    ) -> bool:
        """Delete specific item dependency"""
        with self.get_session() as session:
            dependency = (
                session.query(ItemDependencyDB)
                .filter(
                    ItemDependencyDB.dependent_item_id == dependent_item_id,
                    ItemDependencyDB.required_item_id == required_item_id,
                )
                .first()
            )

            if dependency:
                session.delete(dependency)
                session.commit()
                return True
            return False

    def get_item_blockers(self, item_id: int) -> List[TodoItemDB]:
        """Get all items that block this item (not completed required items)"""
        with self.get_session() as session:
            # Get dependencies where this item is dependent
            dependencies = (
                session.query(ItemDependencyDB)
                .filter(ItemDependencyDB.dependent_item_id == item_id)
                .all()
            )

            blockers = []
            for dep in dependencies:
                required_item = (
                    session.query(TodoItemDB)
                    .filter(TodoItemDB.id == dep.required_item_id)
                    .first()
                )

                # Only include if required item is not completed
                if required_item and required_item.status != "completed":
                    blockers.append(required_item)

            return blockers

    def get_items_blocked_by(self, item_id: int) -> List[TodoItemDB]:
        """Get all items blocked by this item"""
        with self.get_session() as session:
            # Get dependencies where this item is required
            dependencies = (
                session.query(ItemDependencyDB)
                .filter(ItemDependencyDB.required_item_id == item_id)
                .all()
            )

            blocked_items = []
            for dep in dependencies:
                dependent_item = (
                    session.query(TodoItemDB)
                    .filter(TodoItemDB.id == dep.dependent_item_id)
                    .first()
                )

                if dependent_item:
                    blocked_items.append(dependent_item)

            return blocked_items

    def is_item_blocked(self, item_id: int) -> bool:
        """Check if item is blocked by uncompleted dependencies"""
        blockers = self.get_item_blockers(item_id)
        return len(blockers) > 0

    def get_all_dependencies_for_list(self, list_id: int) -> List[ItemDependencyDB]:
        """Get all dependencies involving items from a specific list"""
        with self.get_session() as session:
            # Get items from this list
            list_items = (
                session.query(TodoItemDB).filter(TodoItemDB.list_id == list_id).all()
            )
            item_ids = [item.id for item in list_items]

            if not item_ids:
                return []

            # Get dependencies where items from this list are involved
            dependencies = (
                session.query(ItemDependencyDB)
                .filter(
                    (ItemDependencyDB.dependent_item_id.in_(item_ids))
                    | (ItemDependencyDB.required_item_id.in_(item_ids))
                )
                .all()
            )

            return dependencies

    def _would_create_circular_dependency(
        self, dependent_item_id: int, required_item_id: int
    ) -> bool:
        """Check if adding this dependency would create a circular reference"""
        with self.get_session() as session:
            # Check if required_item depends on dependent_item (directly or indirectly)
            visited = set()

            def has_dependency_path(from_item: int, to_item: int) -> bool:
                if from_item in visited:
                    return False  # Prevent infinite recursion
                visited.add(from_item)

                # Direct dependency check
                direct_deps = (
                    session.query(ItemDependencyDB)
                    .filter(ItemDependencyDB.dependent_item_id == from_item)
                    .all()
                )

                for dep in direct_deps:
                    if dep.required_item_id == to_item:
                        return True  # Direct circular dependency

                    # Recursive check
                    if has_dependency_path(dep.required_item_id, to_item):
                        return True

                return False

            return has_dependency_path(required_item_id, dependent_item_id)

    def get_dependency_graph_for_project(self, project_key: str) -> Dict[str, Any]:
        """Get complete dependency graph for a project (related lists)"""
        with self.get_session() as session:
            # Get all lists in the project
            project_lists = self.get_lists_by_relation("project", project_key)
            if not project_lists:
                return {"lists": [], "dependencies": []}

            list_ids = [lst.id for lst in project_lists]

            # Get all items from these lists
            all_items = (
                session.query(TodoItemDB).filter(TodoItemDB.list_id.in_(list_ids)).all()
            )

            item_ids = [item.id for item in all_items]

            # Get all dependencies between items in these lists
            dependencies = (
                session.query(ItemDependencyDB)
                .filter(
                    ItemDependencyDB.dependent_item_id.in_(item_ids),
                    ItemDependencyDB.required_item_id.in_(item_ids),
                )
                .all()
            )

            return {
                "lists": [
                    {"id": lst.id, "key": lst.list_key, "title": lst.title}
                    for lst in project_lists
                ],
                "items": [
                    {
                        "id": item.id,
                        "key": item.item_key,
                        "content": item.content,
                        "list_id": item.list_id,
                        "status": item.status,
                    }
                    for item in all_items
                ],
                "dependencies": [
                    {
                        "id": dep.id,
                        "dependent": dep.dependent_item_id,
                        "required": dep.required_item_id,
                        "type": dep.dependency_type,
                    }
                    for dep in dependencies
                ],
            }

    def get_all_item_dependencies(self) -> List[ItemDependencyDB]:
        """Get all item dependencies from the database."""
        with self.get_session() as session:
            return session.query(ItemDependencyDB).all()

    def delete_all_dependencies_for_item(self, item_id: int) -> int:
        """Delete all dependencies involving the given item (as dependent or required)"""
        with self.get_session() as session:
            deleted_count = (
                session.query(ItemDependencyDB)
                .filter(
                    (ItemDependencyDB.dependent_item_id == item_id)
                    | (ItemDependencyDB.required_item_id == item_id)
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count

    def delete_all_item_properties(self, item_id: int) -> int:
        """Delete all properties for the given item"""
        with self.get_session() as session:
            deleted_count = (
                session.query(ItemPropertyDB)
                .filter(ItemPropertyDB.item_id == item_id)
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count

    def delete_item_history(self, item_id: int) -> int:
        """Delete all history entries for the given item"""
        with self.get_session() as session:
            deleted_count = (
                session.query(TodoHistoryDB)
                .filter(TodoHistoryDB.item_id == item_id)
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count

    # ===== LIST TAG OPERATIONS =====

    def create_tag(self, tag_data: Dict[str, Any]) -> ListTagDB:
        """Create a new tag"""
        with self.get_session() as session:
            tag = ListTagDB(**tag_data)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag

    def get_tag_by_id(self, tag_id: int) -> Optional[ListTagDB]:
        """Get tag by ID"""
        with self.get_session() as session:
            return session.query(ListTagDB).filter(ListTagDB.id == tag_id).first()

    def get_tag_by_name(self, name: str) -> Optional[ListTagDB]:
        """Get tag by name"""
        with self.get_session() as session:
            return (
                session.query(ListTagDB).filter(ListTagDB.name == name.lower()).first()
            )

    def get_all_tags(self) -> List[ListTagDB]:
        """Get all tags"""
        with self.get_session() as session:
            return session.query(ListTagDB).order_by(ListTagDB.name).all()

    def delete_tag(self, tag_id: int) -> bool:
        """Delete tag and all its assignments"""
        with self.get_session() as session:
            # First delete all assignments
            session.query(ListTagAssignmentDB).filter(
                ListTagAssignmentDB.tag_id == tag_id
            ).delete(synchronize_session=False)

            # Then delete the tag
            deleted_count = (
                session.query(ListTagDB)
                .filter(ListTagDB.id == tag_id)
                .delete(synchronize_session=False)
            )

            session.commit()
            return deleted_count > 0

    def add_tag_to_list(self, list_id: int, tag_id: int) -> ListTagAssignmentDB:
        """Add tag to list (create assignment)"""
        with self.get_session() as session:
            # Check if assignment already exists
            existing = (
                session.query(ListTagAssignmentDB)
                .filter(
                    ListTagAssignmentDB.list_id == list_id,
                    ListTagAssignmentDB.tag_id == tag_id,
                )
                .first()
            )

            if existing:
                return existing

            assignment = ListTagAssignmentDB(list_id=list_id, tag_id=tag_id)
            session.add(assignment)
            session.commit()
            session.refresh(assignment)
            return assignment

    def remove_tag_from_list(self, list_id: int, tag_id: int) -> bool:
        """Remove tag from list (delete assignment)"""
        with self.get_session() as session:
            deleted_count = (
                session.query(ListTagAssignmentDB)
                .filter(
                    ListTagAssignmentDB.list_id == list_id,
                    ListTagAssignmentDB.tag_id == tag_id,
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count > 0

    def get_tags_for_list(self, list_id: int) -> List[ListTagDB]:
        """Get all tags for a specific list"""
        with self.get_session() as session:
            return (
                session.query(ListTagDB)
                .join(ListTagAssignmentDB, ListTagDB.id == ListTagAssignmentDB.tag_id)
                .filter(ListTagAssignmentDB.list_id == list_id)
                .order_by(ListTagDB.name)
                .all()
            )

    def get_lists_by_tags(self, tag_names: List[str]) -> List[TodoListDB]:
        """Get lists that have ANY of the specified tags"""
        if not tag_names:
            return []

        with self.get_session() as session:
            # Normalize tag names to lowercase
            normalized_names = [name.lower() for name in tag_names]

            return (
                session.query(TodoListDB)
                .join(ListTagAssignmentDB, TodoListDB.id == ListTagAssignmentDB.list_id)
                .join(ListTagDB, ListTagAssignmentDB.tag_id == ListTagDB.id)
                .filter(ListTagDB.name.in_(normalized_names))
                .distinct()
                .order_by(TodoListDB.list_key.asc())
                .all()
            )

    def delete_all_tag_assignments_for_list(self, list_id: int) -> int:
        """Delete all tag assignments for a list"""
        with self.get_session() as session:
            deleted_count = (
                session.query(ListTagAssignmentDB)
                .filter(ListTagAssignmentDB.list_id == list_id)
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted_count
