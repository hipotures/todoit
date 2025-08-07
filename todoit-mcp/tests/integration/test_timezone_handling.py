"""
Integration tests for timezone handling.
Tests that UTC timestamps are stored correctly and displayed as local time.
"""

import pytest
from datetime import datetime, timezone
from core.manager import TodoManager
from interfaces.cli_modules.display import _format_date


class TestTimezoneHandling:
    """Test timezone handling across the system"""

    @pytest.fixture
    def temp_manager(self, temp_db):
        """Create manager with test database"""
        return TodoManager(temp_db)

    def test_utc_storage_in_database(self, temp_manager):
        """Test that timestamps are stored as UTC in database"""
        # Create list and item
        test_list = temp_manager.create_list("timezone_test", "Timezone Test")
        test_item = temp_manager.add_item("timezone_test", "test_item", "Test content")
        
        # Get the raw database times
        db_list = temp_manager.db.get_list_by_key("timezone_test")
        db_item = temp_manager.db.get_item_by_key(db_list.id, "test_item")
        
        # Verify timestamps are reasonable (within last few seconds)
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Database stores naive UTC datetime
        time_diff_list = abs((now_utc - db_list.created_at).total_seconds())
        time_diff_item = abs((now_utc - db_item.created_at).total_seconds())
        
        assert time_diff_list < 5  # Should be created within last 5 seconds
        assert time_diff_item < 5  # Should be created within last 5 seconds

    def test_utc_datetime_helper_function(self):
        """Test the utc_now helper function"""
        from core.database import utc_now
        
        utc_time = utc_now()
        current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Should be very close to current UTC time
        time_diff = abs((current_utc - utc_time).total_seconds())
        assert time_diff < 1  # Should be within 1 second
        
        # Should be naive datetime (no timezone info)
        assert utc_time.tzinfo is None

    def test_date_formatting_converts_to_local_time(self):
        """Test that _format_date converts UTC to local time"""
        # Create a known UTC datetime
        utc_datetime = datetime(2025, 8, 7, 12, 0, 0)  # Noon UTC, naive
        
        # Format it (should convert to local time)
        formatted = _format_date(utc_datetime)
        
        # Should be a valid formatted string
        assert len(formatted) > 10
        assert "2025-08-07" in formatted
        
        # The hour should be different from 12 if we're not in UTC timezone
        # (This test may vary depending on system timezone)
        local_now = datetime.now()
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        timezone_offset_hours = (local_now - utc_now).total_seconds() / 3600
        
        if abs(timezone_offset_hours) > 0.1:  # If we have significant timezone offset
            assert "12:00" not in formatted  # Should be adjusted to local time

    def test_date_formatting_handles_none(self):
        """Test that _format_date handles None values"""
        result = _format_date(None)
        assert result == "Never"

    def test_date_formatting_handles_timezone_aware(self):
        """Test that _format_date handles timezone-aware datetime"""
        # Create timezone-aware UTC datetime
        utc_datetime = datetime(2025, 8, 7, 12, 0, 0, tzinfo=timezone.utc)
        
        # Format it
        formatted = _format_date(utc_datetime)
        
        # Should handle it properly
        assert len(formatted) > 10
        assert "2025-08-07" in formatted

    def test_item_status_updates_use_utc(self, temp_manager):
        """Test that status updates (started_at, completed_at) use UTC"""
        # Create item
        temp_manager.create_list("status_test", "Status Test")
        temp_manager.add_item("status_test", "status_item", "Status test content")
        
        # Update to in_progress (sets started_at)
        temp_manager.update_item_status("status_test", "status_item", status="in_progress")
        
        # Update to completed (sets completed_at)
        temp_manager.update_item_status("status_test", "status_item", status="completed")
        
        # Get the item
        item = temp_manager.get_item("status_test", "status_item")
        
        # Verify timestamps exist and are recent
        assert item.started_at is not None
        assert item.completed_at is not None
        
        # Should be within last few seconds (stored as UTC)
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        started_diff = abs((now_utc - item.started_at).total_seconds())
        completed_diff = abs((now_utc - item.completed_at).total_seconds())
        
        assert started_diff < 5
        assert completed_diff < 5

    def test_history_timestamps_use_utc(self, temp_manager):
        """Test that history timestamps use UTC"""
        # Create item and make changes
        temp_manager.create_list("history_test", "History Test")
        temp_manager.add_item("history_test", "history_item", "Original content")
        temp_manager.update_item_content("history_test", "history_item", "Updated content")
        
        # Get history
        history = temp_manager.get_item_history("history_test", "history_item")
        
        assert len(history) >= 2  # Should have creation and update history
        
        # Check that timestamps are recent UTC times
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for entry in history:
            time_diff = abs((now_utc - entry.timestamp).total_seconds())
            assert time_diff < 10  # Should be within last 10 seconds

    def test_no_deprecated_datetime_warnings(self):
        """Test that we don't use deprecated datetime.utcnow()"""
        import warnings
        
        # This test ensures we're using the new timezone-aware approach
        from core.database import utc_now
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Call our UTC helper function
            timestamp = utc_now()
            
            # Should not generate any deprecation warnings
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 0, f"Found deprecation warnings: {[str(w.message) for w in deprecation_warnings]}"
            
            # Verify we got a valid timestamp
            assert isinstance(timestamp, datetime)
            assert timestamp.tzinfo is None  # Should be naive for SQLite compatibility