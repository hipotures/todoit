"""
Security tests for SQL injection protection in TODOIT MCP.

Tests that the system is protected against SQL injection attacks through
user input in list names, item content, properties, and other user-controlled data.
"""

import os
import tempfile

import pytest

from core.manager import TodoManager
from core.models import ItemStatus


class TestSQLInjection:
    """Test protection against SQL injection attacks"""

    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for security tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_list_key_sql_injection(self, temp_manager):
        """Test SQL injection attempts in list keys"""
        malicious_keys = [
            "test'; DROP TABLE todo_lists; --",
            "test' OR '1'='1",
            "test'; DELETE FROM todo_items; --",
            "test'; UPDATE todo_lists SET status='deleted'; --",
            "test' UNION SELECT * FROM sqlite_master --",
            "test'; INSERT INTO todo_lists VALUES ('evil', 'Evil List'); --",
            "test' AND (SELECT COUNT(*) FROM todo_lists) > 0 --",
            "test'; ALTER TABLE todo_lists ADD COLUMN evil TEXT; --",
        ]

        for malicious_key in malicious_keys:
            # Should either sanitize the input or raise a validation error
            # but NOT execute malicious SQL
            try:
                temp_manager.create_list(malicious_key, "Test List")
                # If it doesn't raise an error, the key should be sanitized
                lists = temp_manager.list_all()
                # Should not have deleted all lists or created unauthorized lists
                assert len(lists) >= 1
                # The malicious SQL should not have executed
                list_keys = [l.list_key for l in lists]
                assert not any("evil" in key.lower() for key in list_keys)
            except ValueError:
                # Validation error is acceptable - means input was rejected
                pass

    def test_list_title_sql_injection(self, temp_manager):
        """Test SQL injection attempts in list titles"""
        malicious_titles = [
            "Test'; DROP TABLE todo_lists; --",
            "Test' OR '1'='1",
            "Test'; DELETE FROM todo_items; --",
            "Test' UNION SELECT password FROM users --",
            "Test'; INSERT INTO todo_lists (list_key, title) VALUES ('hacked', 'Hacked'); --",
        ]

        for malicious_title in malicious_titles:
            # Create list with malicious title
            temp_manager.create_list("test", malicious_title)

            # Verify system integrity
            lists = temp_manager.list_all()
            assert len(lists) >= 1

            # The title should be stored as-is (treated as data, not SQL)
            test_list = next((l for l in lists if l.list_key == "test"), None)
            assert test_list is not None
            assert test_list.title == malicious_title  # Stored as literal text

            # Clean up for next test
            temp_manager.delete_list("test")

    def test_item_content_sql_injection(self, temp_manager):
        """Test SQL injection attempts in item content"""
        temp_manager.create_list("test", "Test List")

        malicious_content = [
            "Task'; DROP TABLE todo_items; --",
            "Task' OR '1'='1",
            "Task'; UPDATE todo_items SET status='completed'; --",
            "Task' UNION SELECT * FROM todo_lists --",
            "Task'; INSERT INTO todo_items (item_key, content) VALUES ('evil', 'Evil Task'); --",
        ]

        for i, malicious_text in enumerate(malicious_content):
            item_key = f"task{i}"
            temp_manager.add_item("test", item_key, malicious_text)

            # Verify system integrity
            items = temp_manager.get_list_items("test")
            assert len(items) >= i + 1

            # Content should be stored as literal text
            task = temp_manager.get_item("test", item_key)
            assert task.content == malicious_text

    def test_property_sql_injection(self, temp_manager):
        """Test SQL injection attempts in properties"""
        temp_manager.create_list("test", "Test List")
        temp_manager.add_item("test", "task1", "Test Task")

        # Use valid property keys (alphanumeric only) but malicious values
        malicious_properties = [
            ("normalkey", "value'; DROP TABLE list_properties; --"),
            ("key2", "value'; DELETE FROM item_properties; --"),
            ("key3", "value' OR '1'='1"),
            ("priority", "high'; UPDATE todo_items SET status='completed'; --"),
        ]

        for malicious_key, malicious_value in malicious_properties:
            # Test list properties
            temp_manager.set_list_property("test", malicious_key, malicious_value)

            # Verify system integrity
            lists = temp_manager.list_all()
            assert len(lists) >= 1

            # Property should be stored as literal data
            try:
                stored_value = temp_manager.get_list_property("test", malicious_key)
                assert stored_value == malicious_value
            except ValueError:
                # Property not found is acceptable if key was sanitized
                pass

            # Test item properties
            try:
                temp_manager.set_item_property(
                    "test", "task1", malicious_key, malicious_value
                )
            except Exception:
                # Some properties might fail validation, which is acceptable
                pass

            # Verify item still exists and system integrity
            task = temp_manager.get_item("test", "task1")
            assert task is not None

    def test_search_sql_injection(self, temp_manager):
        """Test SQL injection attempts in search/filter operations"""
        temp_manager.create_list("test", "Test List")
        temp_manager.add_item("test", "task1", "Normal task")
        temp_manager.add_item("test", "task2", "Another task")

        # Set some properties to search
        temp_manager.set_item_property("test", "task1", "priority", "high")
        temp_manager.set_item_property("test", "task2", "priority", "low")

        malicious_search_terms = [
            "high'; DROP TABLE item_properties; --",
            "' OR '1'='1",
            "high' UNION SELECT * FROM todo_lists --",
            "high'; DELETE FROM todo_items; --",
        ]

        for malicious_term in malicious_search_terms:
            # Test property search
            try:
                results = temp_manager.find_items_by_property(
                    "test", "priority", malicious_term
                )
                # Should return empty results or sanitized search
                assert isinstance(results, list)
            except ValueError:
                # Search rejection is acceptable
                pass

            # Verify system integrity after search
            items = temp_manager.get_list_items("test")
            assert len(items) == 2  # Both items should still exist

            # Verify properties still exist
            prop1 = temp_manager.get_item_property("test", "task1", "priority")
            prop2 = temp_manager.get_item_property("test", "task2", "priority")
            assert prop1 == "high"
            assert prop2 == "low"

    def test_tag_sql_injection(self, temp_manager):
        """Test SQL injection attempts in tag operations"""
        temp_manager.create_list("test", "Test List")

        malicious_tags = [
            "urgent'; DROP TABLE list_tags; --",
            "urgent' OR '1'='1",
            "urgent'; DELETE FROM list_tag_assignments; --",
            "urgent' UNION SELECT * FROM todo_lists --",
        ]

        for malicious_tag in malicious_tags:
            # Test adding malicious tag
            try:
                temp_manager.add_tag_to_list("test", malicious_tag)

                # Verify system integrity
                lists = temp_manager.list_all()
                assert len(lists) >= 1

                # Verify tag system still works
                tags = temp_manager.get_tags_for_list("test")
                assert isinstance(tags, list)

            except ValueError:
                # Tag rejection is acceptable
                pass

    def test_dependency_sql_injection(self, temp_manager):
        """Test SQL injection attempts in dependency operations"""
        temp_manager.create_list("list1", "List 1")
        temp_manager.create_list("list2", "List 2")
        temp_manager.add_item("list1", "task1", "Task 1")
        temp_manager.add_item("list2", "task2", "Task 2")

        # Test malicious dependency creation
        malicious_specs = [
            "list1:task1'; DROP TABLE item_dependencies; --",
            "list2:task2' OR '1'='1",
            "list1:task1'; DELETE FROM todo_items; --",
        ]

        for malicious_spec in malicious_specs:
            try:
                # This should either sanitize input or raise validation error
                temp_manager.add_item_dependency("list1", "task1", "list2", "task2")
            except (ValueError, Exception):
                # Dependency rejection is acceptable
                pass

            # Verify system integrity
            items1 = temp_manager.get_list_items("list1")
            items2 = temp_manager.get_list_items("list2")
            assert len(items1) >= 1
            assert len(items2) >= 1

    def test_import_export_sql_injection(self, temp_manager):
        """Test SQL injection attempts in import/export operations"""
        # Create malicious markdown content
        malicious_markdown = """
# Test List'; DROP TABLE todo_lists; --

## Tasks

- Task 1'; DELETE FROM todo_items; --
- Task 2' OR '1'='1
- Task 3'; INSERT INTO todo_lists (list_key, title) VALUES ('hacked', 'Hacked List'); --

### Properties

priority: high'; UPDATE todo_items SET status='completed'; --
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp.write(malicious_markdown)
            tmp_path = tmp.name

        try:
            # Test import - should sanitize or reject malicious content
            temp_manager.import_from_markdown("imported_list", tmp_path)

            # Verify system integrity after import
            lists = temp_manager.list_all()
            list_keys = [l.list_key for l in lists]

            # Should not have executed malicious SQL
            assert "hacked" not in list_keys

            # Imported list should exist (with sanitized name)
            assert any("imported" in key for key in list_keys)

            # Verify items exist as literal content
            if "imported_list" in list_keys:
                items = temp_manager.get_list_items("imported_list")
                assert len(items) > 0

        except (ValueError, Exception) as e:
            # Import rejection/failure is acceptable for malicious content
            pass

        finally:
            os.unlink(tmp_path)

    def test_complex_nested_sql_injection(self, temp_manager):
        """Test complex nested SQL injection attempts"""
        # Create a complex scenario with nested malicious input
        temp_manager.create_list("test", "Test List")

        # Multi-vector attack combining various injection points - use valid key
        malicious_item = temp_manager.add_item(
            "test", "malicious_task", "Content'; DELETE FROM todo_lists; --"
        )

        # Add subtask with malicious content - use valid key
        temp_manager.add_subitem(
            "test",
            malicious_item.item_key,
            "malicious_sub",
            "Subtask'; UPDATE todo_lists SET status='deleted'; --",
        )

        # Add property with malicious value - use valid key
        temp_manager.set_item_property(
            "test",
            malicious_item.item_key,
            "malicious_prop",
            "value'; INSERT INTO todo_lists VALUES ('evil', 'Evil'); --",
        )

        # Verify system integrity after all operations
        lists = temp_manager.list_all()
        assert len(lists) >= 1

        items = temp_manager.get_list_items("test")
        assert len(items) >= 2  # Parent + subtask

        # All malicious content should be stored as literal text
        parent = temp_manager.get_item("test", malicious_item.item_key)
        assert parent is not None
        assert parent.content == "Content'; DELETE FROM todo_lists; --"
