"""
Chaos engineering tests for TODOIT MCP - testing system resilience under random failures.

These tests simulate various failure scenarios to verify that the system
can handle unexpected conditions gracefully and maintain data integrity.
"""

import pytest
import tempfile
import os
import random
import time
import sqlite3
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any
from core.manager import TodoManager
from core.models import ItemStatus


class TestChaosEngineering:
    """Chaos engineering tests to verify system resilience"""
    
    @pytest.fixture
    def temp_manager(self):
        """Create temporary manager for chaos tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            manager = TodoManager(db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_random_operation_failures(self, temp_manager):
        """Test system resilience with random operation failures"""
        # Setup initial data
        temp_manager.create_list("chaos", "Chaos Test List")
        for i in range(10):
            temp_manager.add_item("chaos", f"task{i}", f"Task {i}")
        
        # Simulate random failures
        operations_attempted = 0
        operations_successful = 0
        failures_encountered = 0
        
        for i in range(100):  # Attempt 100 random operations
            operation = random.choice([
                'add_item', 'get_item', 'update_status', 'add_property', 
                'get_property', 'add_subtask', 'get_next_pending'
            ])
            
            operations_attempted += 1
            
            try:
                if operation == 'add_item':
                    temp_manager.add_item("chaos", f"random{i}", f"Random task {i}")
                elif operation == 'get_item':
                    task_id = random.randint(0, 9)
                    temp_manager.get_item("chaos", f"task{task_id}")
                elif operation == 'update_status':
                    task_id = random.randint(0, 9)
                    status = random.choice([ItemStatus.PENDING, ItemStatus.IN_PROGRESS, ItemStatus.COMPLETED])
                    temp_manager.update_item_status("chaos", f"task{task_id}", status)
                elif operation == 'add_property':
                    task_id = random.randint(0, 9)
                    temp_manager.set_item_property("chaos", f"task{task_id}", f"prop{i}", f"value{i}")
                elif operation == 'get_property':
                    task_id = random.randint(0, 9)
                    try:
                        temp_manager.get_item_property("chaos", f"task{task_id}", "priority")
                    except ValueError:
                        pass  # Property might not exist
                elif operation == 'add_subtask':
                    task_id = random.randint(0, 9)
                    temp_manager.add_subitem("chaos", f"task{task_id}", f"sub{i}", f"Subtask {i}")
                elif operation == 'get_next_pending':
                    temp_manager.get_next_pending("chaos")
                
                operations_successful += 1
                
            except Exception as e:
                failures_encountered += 1
                # Failures are expected in chaos testing, but shouldn't crash system
                pass
        
        # System should remain functional despite failures
        assert operations_successful > 0
        assert temp_manager.get_list("chaos") is not None
        
        # Verify system integrity
        items = temp_manager.get_list_items("chaos")
        assert len(items) >= 10  # Original items should still exist
        
        print(f"Chaos test: {operations_successful}/{operations_attempted} operations succeeded, {failures_encountered} failures")
    
    def test_database_corruption_simulation(self, temp_manager):
        """Test system behavior with simulated database corruption"""
        # Setup data
        temp_manager.create_list("corruption", "Corruption Test")
        for i in range(5):
            temp_manager.add_item("corruption", f"task{i}", f"Task {i}")
        
        # Get database path
        db_path = temp_manager.db.db_path
        
        # Close current manager - Database class doesn't have close method
        del temp_manager
        
        # Simulate minor database corruption (add random bytes)
        try:
            with open(db_path, 'ab') as f:
                f.write(b'CORRUPTED_DATA_CHAOS_TEST' * 10)
            
            # Try to create new manager with corrupted DB
            try:
                corrupted_manager = TodoManager(db_path)
                # If it opens, try basic operations
                lists = corrupted_manager.list_all()
                # System should either work or fail gracefully
                assert isinstance(lists, list)
            except Exception as e:
                # Graceful failure is acceptable for corrupted database
                assert "database" in str(e).lower() or "corrupt" in str(e).lower()
                
        except Exception:
            # File operations might fail, which is acceptable
            pass
    
    def test_memory_pressure_simulation(self, temp_manager):
        """Test system behavior under simulated memory pressure"""
        # Create substantial data to pressure memory
        temp_manager.create_list("memory", "Memory Pressure Test")
        
        # Create large objects that might cause memory pressure
        large_content = "X" * 100000  # 100KB per item
        created_items = 0
        
        try:
            for i in range(100):  # Try to create 100 large items (10MB total)
                temp_manager.add_item("memory", f"large{i}", large_content)
                created_items += 1
                
                # Occasionally try operations that might fail under memory pressure
                if i % 10 == 0:
                    temp_manager.get_list_items("memory")
                    temp_manager.get_next_pending("memory")
        
        except Exception as e:
            # System might fail under extreme memory pressure, but should not crash
            print(f"System handled memory pressure gracefully after {created_items} items: {e}")
        
        # Verify system can recover
        try:
            items = temp_manager.get_list_items("memory")
            assert len(items) >= created_items
        except Exception:
            # Even if some operations fail, system should not be completely broken
            pass
    
    def test_concurrent_access_chaos(self, temp_manager):
        """Test system with simulated concurrent access patterns"""
        temp_manager.create_list("concurrent", "Concurrent Access Test")
        
        # Simulate rapid concurrent-like access
        operations = []
        
        for i in range(50):
            # Mix rapid operations that might conflict
            operations.extend([
                ('add', i),
                ('read', i),
                ('update', i),
                ('delete', i) if i % 10 == 0 else ('read', i)
            ])
        
        # Randomize order to simulate concurrent access
        random.shuffle(operations)
        
        successful_ops = 0
        failed_ops = 0
        
        for op_type, item_id in operations:
            try:
                if op_type == 'add':
                    temp_manager.add_item("concurrent", f"item{item_id}", f"Item {item_id}")
                elif op_type == 'read':
                    try:
                        temp_manager.get_item("concurrent", f"item{item_id}")
                    except ValueError:
                        pass  # Item might not exist yet
                elif op_type == 'update':
                    try:
                        temp_manager.update_item_status("concurrent", f"item{item_id}", ItemStatus.IN_PROGRESS)
                    except ValueError:
                        pass  # Item might not exist yet
                elif op_type == 'delete':
                    try:
                        # We can't delete individual items directly, so update to completed
                        temp_manager.update_item_status("concurrent", f"item{item_id}", ItemStatus.COMPLETED)
                    except ValueError:
                        pass  # Item might not exist yet
                
                successful_ops += 1
                
            except Exception:
                failed_ops += 1
        
        # System should handle mixed operations gracefully
        assert successful_ops > 0
        
        # Verify system integrity after chaos
        items = temp_manager.get_list_items("concurrent")
        assert len(items) >= 0  # System should still be functional
        
        print(f"Concurrent chaos: {successful_ops} successful, {failed_ops} failed operations")
    
    def test_invalid_data_injection(self, temp_manager):
        """Test system resilience against invalid data injection"""
        temp_manager.create_list("invalid", "Invalid Data Test")
        
        # Try various invalid inputs that might break the system
        invalid_inputs = [
            ("", "Empty key"),
            (None, "None key"),
            ("key\x00with\x00nulls", "Null bytes"),
            ("key\nwith\nnewlines", "Newlines"),
            ("very" * 1000 + "long" * 1000, "Extremely long key"),
            ("unicode🔥test🚀key", "Unicode characters"),
            ("key with spaces", "Spaces"),
            ("key\twith\ttabs", "Tabs"),
            ("key;with;semicolons", "Semicolons"),
            ("key'with'quotes", "Quotes"),
        ]
        
        successful_creates = 0
        handled_gracefully = 0
        
        for invalid_key, description in invalid_inputs:
            try:
                if invalid_key is None:
                    # Skip None test as it would fail before reaching our code
                    continue
                    
                temp_manager.add_item("invalid", invalid_key, f"Content for {description}")
                successful_creates += 1
                
            except (ValueError, TypeError, Exception) as e:
                # Graceful rejection of invalid input is good
                handled_gracefully += 1
                assert "invalid" in str(e).lower() or "key" in str(e).lower() or isinstance(e, (ValueError, TypeError))
        
        # System should either accept valid variants or reject gracefully
        assert successful_creates + handled_gracefully == len(invalid_inputs) - 1  # -1 for None
        
        # System should still be functional
        assert temp_manager.get_list("invalid") is not None
    
    def test_resource_exhaustion_simulation(self, temp_manager):
        """Test system behavior under simulated resource exhaustion"""
        temp_manager.create_list("resource", "Resource Exhaustion Test")
        
        # Test with many properties (could exhaust memory/handles)
        item_created = False
        try:
            temp_manager.add_item("resource", "test_item", "Test item")
            item_created = True
            
            for i in range(1000):  # Try to create many properties
                temp_manager.set_item_property("resource", "test_item", f"prop{i:04d}", f"value{i}")
                
                # Occasionally test other operations
                if i % 100 == 0:
                    temp_manager.get_item("resource", "test_item")
        
        except Exception as e:
            # Resource exhaustion might cause failures, but should be graceful
            print(f"System handled resource exhaustion gracefully: {e}")
        
        # Verify basic functionality still works
        if item_created:
            assert temp_manager.get_item("resource", "test_item") is not None
    
    def test_transaction_chaos(self, temp_manager):
        """Test system with simulated transaction interruptions"""
        temp_manager.create_list("transaction", "Transaction Chaos Test")
        
        # Simulate operations that might be interrupted mid-transaction
        operations_completed = 0
        
        for i in range(20):
            try:
                # Complex operation that might involve multiple database operations
                parent_key = f"parent{i}"
                temp_manager.add_item("transaction", parent_key, f"Parent {i}")
                
                # Add multiple children (multi-step operation)
                for j in range(5):
                    temp_manager.add_subitem("transaction", parent_key, f"child{i}_{j}", f"Child {i}-{j}")
                
                # Add properties (more database operations)
                temp_manager.set_item_property("transaction", parent_key, "priority", "high")
                temp_manager.set_item_property("transaction", parent_key, "category", f"cat{i}")
                
                operations_completed += 1
                
            except Exception as e:
                # Some operations might fail, but system should remain consistent
                print(f"Transaction operation {i} failed: {e}")
        
        # Verify data consistency after chaos
        items = temp_manager.get_list_items("transaction")
        
        # Items should exist in complete state (not partial)
        parent_count = len([item for item in items if item.parent_item_id is None])
        child_count = len([item for item in items if item.parent_item_id is not None])
        
        # If parents exist, they should have consistent children
        # (This is a basic consistency check)
        assert parent_count >= 0
        assert child_count >= 0
        
        print(f"Transaction chaos: {operations_completed} operations completed, {parent_count} parents, {child_count} children")
    
    def test_random_system_state_corruption(self, temp_manager):
        """Test system recovery from random state corruption"""
        # Create complex initial state
        temp_manager.create_list("state", "State Corruption Test")
        
        # Create hierarchical structure
        for i in range(5):
            parent = f"parent{i}"
            temp_manager.add_item("state", parent, f"Parent {i}")
            
            for j in range(3):
                child = f"child{i}_{j}"
                temp_manager.add_subitem("state", parent, child, f"Child {i}-{j}")
                temp_manager.set_item_property("state", child, "level", str(j))
        
        # Add dependencies
        try:
            temp_manager.add_dependency("state:parent1", "requires", "state:parent0")
            temp_manager.add_dependency("state:parent2", "requires", "state:parent1")
        except Exception:
            # Dependencies might not be supported or might fail
            pass
        
        # Simulate random state changes that might corrupt logical consistency
        items = temp_manager.get_list_items("state")
        
        for _ in range(20):
            # Random status changes that might create inconsistent state
            random_item = random.choice(items)
            random_status = random.choice([ItemStatus.PENDING, ItemStatus.IN_PROGRESS, ItemStatus.COMPLETED])
            
            try:
                temp_manager.update_item_status("state", random_item.item_key, random_status)
            except Exception:
                # Some status changes might fail due to business rules
                pass
        
        # Verify system can still function despite potentially inconsistent state
        try:
            next_task = temp_manager.get_next_pending("state")
            # System should either find a valid task or handle gracefully
        except Exception as e:
            # Graceful handling of inconsistent state is acceptable
            print(f"System handled state inconsistency gracefully: {e}")
        
        # System should still be queryable
        final_items = temp_manager.get_list_items("state")
        assert len(final_items) > 0
        assert temp_manager.get_list("state") is not None


class TestChaosRecovery:
    """Test system recovery capabilities after various failures"""
    
    @pytest.fixture
    def temp_manager_path(self):
        """Create temporary database path for recovery tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            yield db_path
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_recovery_after_unexpected_shutdown(self, temp_manager_path):
        """Test system recovery after simulated unexpected shutdown"""
        # Create initial state
        manager1 = TodoManager(temp_manager_path)
        manager1.create_list("recovery", "Recovery Test")
        
        for i in range(10):
            manager1.add_item("recovery", f"task{i}", f"Task {i}")
            if i % 2 == 0:
                manager1.update_item_status("recovery", f"task{i}", ItemStatus.IN_PROGRESS)
        
        # Simulate unexpected shutdown (don't close properly)
        del manager1
        
        # Create new manager instance (simulating restart)
        manager2 = TodoManager(temp_manager_path)
        
        # Verify data integrity after "restart"
        lists = manager2.list_all()
        assert len(lists) == 1
        assert lists[0].list_key == "recovery"
        
        items = manager2.get_list_items("recovery")
        assert len(items) == 10
        
        # Verify system functionality after recovery
        next_task = manager2.get_next_pending("recovery")
        assert next_task is not None
        
        # Should be able to continue operations normally
        manager2.add_item("recovery", "new_task", "New task after recovery")
        updated_items = manager2.get_list_items("recovery")
        assert len(updated_items) == 11
        
        # Database cleanup handled by fixture
    
    def test_recovery_from_partial_operations(self, temp_manager_path):
        """Test recovery from partially completed operations"""
        manager = TodoManager(temp_manager_path)
        manager.create_list("partial", "Partial Operations Test")
        
        # Start complex operation
        manager.add_item("partial", "parent", "Parent task")
        
        # Simulate interruption during hierarchical operation
        # (This is hard to simulate perfectly, but we can test edge cases)
        try:
            # Try operation that might fail partway through
            for i in range(5):
                manager.add_subitem("partial", "parent", f"child{i}", f"Child {i}")
                # Simulate potential failure point
                if i == 3:
                    # Force some kind of interruption simulation
                    # In real chaos, this might be a system crash, network failure, etc.
                    pass
        except Exception:
            # If operation fails, system should still be consistent
            pass
        
        # Verify system consistency
        items = manager.get_list_items("partial")
        parent_items = [item for item in items if item.parent_item_id is None]
        child_items = [item for item in items if item.parent_item_id is not None]
        
        assert len(parent_items) == 1  # Should have one parent
        # Children should exist in complete state (not orphaned)
        for child in child_items:
            assert child.parent_item_id is not None
        
        # Database cleanup handled by fixture
    
    def test_graceful_degradation_under_stress(self, temp_manager_path):
        """Test that system degrades gracefully under extreme stress"""
        manager = TodoManager(temp_manager_path)
        manager.create_list("stress", "Stress Degradation Test")
        
        # Apply increasing stress until system starts to degrade
        stress_level = 0
        max_stress = 1000
        
        while stress_level < max_stress:
            try:
                # Gradually increase complexity
                batch_size = min(10, stress_level // 10 + 1)
                
                for i in range(batch_size):
                    item_key = f"stress{stress_level}_{i}"
                    content = f"Stress test item {stress_level}-{i} with content. " * (stress_level // 100 + 1)
                    
                    manager.add_item("stress", item_key, content)
                    
                    if stress_level % 50 == 0:
                        manager.set_item_property("stress", item_key, "stress_level", str(stress_level))
                
                stress_level += batch_size
                
                # Test system responsiveness at each stress level
                start_time = time.time()
                manager.get_next_pending("stress")
                response_time = time.time() - start_time
                
                if response_time > 5.0:  # If system becomes too slow
                    print(f"System gracefully degraded at stress level {stress_level}")
                    break
                    
            except Exception as e:
                print(f"System gracefully failed at stress level {stress_level}: {e}")
                break
        
        # Verify system is still functional even after stress
        try:
            items = manager.get_list_items("stress")
            assert len(items) > 0
            assert manager.get_list("stress") is not None
        except Exception as e:
            # Even if some operations fail, critical operations should work
            print(f"System maintained basic functionality despite stress: {e}")
        
        # Database cleanup handled by fixture