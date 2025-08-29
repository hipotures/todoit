"""
TODOIT MCP - Manager Base Class
Base class with core initialization and helper methods
"""

import os
from typing import Any, Dict, List, Optional


class ManagerBase:
    """Base class with core initialization and common helper methods"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize TodoManager with database connection"""
        if db_path is None:
            # Check for TODOIT_DB_PATH environment variable
            db_path = os.getenv("TODOIT_DB_PATH")
            if db_path:
                # Expand environment variables like $HOME
                db_path = os.path.expandvars(db_path)
            if db_path is None:
                from rich.console import Console

                console = Console()
                console.print(
                    "[bold red]❌ Error:[/] Database path not specified!", style="red"
                )
                console.print()
                console.print(
                    "[yellow]TODOIT requires explicit database configuration.[/]"
                )
                console.print()
                console.print("[cyan]Quick fix:[/]")
                console.print(
                    "  [white]export TODOIT_DB_PATH=/path/to/your/todoit.db[/]"
                )
                console.print("  [white]todoit list all[/]")
                console.print()
                console.print("[cyan]Or use parameter:[/]")
                console.print(
                    "  [white]todoit --db-path /path/to/your/todoit.db list all[/]"
                )
                console.print()
                console.print("[dim]Database path must be explicitly configured[/]")
                raise SystemExit(1)

        # Initialize environment variables
        self.force_tags = self._get_force_tags()

        # Validate database path before creating Database instance
        try:
            import pathlib

            from .database import Database

            db_file = pathlib.Path(db_path)

            # Ensure parent directory exists
            db_file.parent.mkdir(parents=True, exist_ok=True)

            # Check write permissions on parent directory
            if not os.access(db_file.parent, os.W_OK):
                from rich.console import Console

                console = Console()
                console.print(
                    f"[bold red]❌ Error:[/] No write permission to directory: {db_file.parent}"
                )
                console.print(f"[yellow]Fix:[/] chmod 755 {db_file.parent}")
                raise SystemExit(1)

            self.db = Database(db_path)

        except (OSError, PermissionError) as e:
            from rich.console import Console

            console = Console()
            console.print(
                f"[bold red]❌ Database Error:[/] Cannot access database file"
            )
            console.print(f"[white]Path:[/] {db_path}")
            console.print(f"[white]Error:[/] {e}")
            console.print()
            console.print("[cyan]Possible solutions:[/]")
            console.print("  [white]• Check if directory exists and is writable[/]")
            console.print("  [white]• Use absolute path: /path/to/your/todoit.db[/]")
            console.print("  [white]• Check permissions: ls -la $(dirname path)[/]")
            raise SystemExit(1)
        except Exception as e:
            # Catch SQLAlchemy and other database errors
            from rich.console import Console

            console = Console()
            console.print(f"[bold red]❌ Database Connection Error:[/]")
            console.print(f"[white]Path:[/] {db_path}")
            console.print(f"[white]Error:[/] {str(e)}")
            console.print()
            if "unable to open database file" in str(e):
                console.print("[cyan]Possible causes:[/]")
                console.print("  [white]• Invalid database path[/]")
                console.print("  [white]• Missing directory permissions[/]")
                console.print("  [white]• Path contains special characters[/]")
                console.print()
                console.print("[cyan]Try:[/]")
                console.print("  [white]export TODOIT_DB_PATH=/path/to/your/test.db[/]")
                console.print("  [white]todoit list all[/]")
            raise SystemExit(1)

    def _get_force_tags(self) -> List[str]:
        """Get forced tags from TODOIT_FORCE_TAGS environment variable

        FORCE_TAGS creates environment isolation - all operations are limited
        to lists with these tags, and new lists automatically get these tags.
        """
        env_tags = os.environ.get("TODOIT_FORCE_TAGS", "").split(",")
        return [tag.strip().lower() for tag in env_tags if tag.strip()]

    def _db_to_model(self, db_obj: Any, model_class: type) -> Any:
        """Convert database object to Pydantic model"""
        if db_obj is None:
            return None

        # Convert SQLAlchemy object to dict
        obj_dict = {}
        for column in db_obj.__table__.columns:
            # Map database column name to model field name
            if column.name == "metadata":
                # meta_data in SQLAlchemy maps to metadata in Pydantic
                value = getattr(db_obj, "meta_data")
            else:
                value = getattr(db_obj, column.name)
            obj_dict[column.name] = value

        return model_class.model_validate(obj_dict)

    def _record_history(
        self,
        item_id: Optional[int] = None,
        list_id: Optional[int] = None,
        action: str = "updated",
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        user_context: str = "programmatic_api",
    ):
        """Record change in history"""
        history_data = {
            "item_id": item_id,
            "list_id": list_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "user_context": user_context,
        }
        self.db.create_history_entry(history_data)
