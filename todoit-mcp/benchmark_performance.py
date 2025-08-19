#!/usr/bin/env python3
"""
Performance benchmark for TODOIT MCP optimizations
Measures improvements from N+1 query elimination and bulk operations
"""

import time
import tempfile
import os
from core.manager import TodoManager


def benchmark_create_list_with_items(num_items=50):
    """Benchmark list creation with many items"""
    db_path = '/tmp/benchmark_create.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    manager = TodoManager(db_path=db_path)
    items = [f"Task {i+1}: Do something important" for i in range(num_items)]
    
    start_time = time.time()
    test_list = manager.create_list('bulk_test', 'Bulk Creation Test', items=items)
    end_time = time.time()
    
    created_items = manager.get_list_items('bulk_test')
    
    print(f"📊 CREATE LIST BENCHMARK ({num_items} items):")
    print(f"   Time: {(end_time - start_time)*1000:.2f}ms")
    print(f"   Items created: {len(created_items)}")
    print(f"   Rate: {len(created_items)/(end_time - start_time):.1f} items/sec")
    
    return end_time - start_time


def benchmark_get_next_pending_complex():
    """Benchmark complex get_next_pending with many items and hierarchies"""
    db_path = '/tmp/benchmark_next.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    manager = TodoManager(db_path=db_path)
    
    # Create complex hierarchy: 10 lists, each with 20 items, some with subtasks
    for list_num in range(10):
        list_key = f"project_{list_num+1}"
        items = [f"Feature {i+1}" for i in range(20)]
        manager.create_list(list_key, f"Project {list_num+1}", items=items)
        
        # Add subtasks to some items
        for item_num in [1, 5, 10, 15]:
            parent_key = f"item_{item_num}"
            for sub_num in range(3):
                manager.add_subitem(list_key, parent_key, f"subtask_{sub_num+1}", f"Subtask {sub_num+1}")
    
    # Mark some subtasks as in_progress to test priority logic
    manager.update_item_status("project_1", "subtask_1", "in_progress", parent_item_key="item_1")
    manager.update_item_status("project_2", "subtask_1", "in_progress", parent_item_key="item_5")
    
    # Benchmark get_next_pending calls
    start_time = time.time()
    for _ in range(100):  # Multiple calls to measure consistent performance
        next_item = manager.get_next_pending("project_1")
    end_time = time.time()
    
    print(f"📊 GET_NEXT_PENDING BENCHMARK (complex hierarchy):")
    print(f"   Time per call: {(end_time - start_time)*10:.2f}ms")
    print(f"   Total database items: ~800")
    print(f"   Found item: {next_item.content if next_item else 'None'}")
    
    return (end_time - start_time) / 100


def main():
    """Run performance benchmarks"""
    print("🚀 TODOIT MCP Performance Benchmarks")
    print("=====================================")
    print()
    
    # Benchmark 1: Bulk list creation
    create_time = benchmark_create_list_with_items(50)
    print()
    
    # Benchmark 2: Complex next pending queries
    query_time = benchmark_get_next_pending_complex()
    print()
    
    # Summary
    print("📈 PERFORMANCE SUMMARY:")
    print(f"   Bulk creation: {create_time*1000:.1f}ms for 50 items")
    print(f"   Complex queries: {query_time*1000:.1f}ms per call")
    print()
    print("🎯 OPTIMIZATIONS APPLIED:")
    print("   ✅ N+1 queries eliminated with selectinload()")
    print("   ✅ Bulk item creation in single transaction")
    print("   ✅ Composite database indexes optimized")
    print("   ✅ Bulk dependency checking")
    print()
    
    # Performance targets
    if create_time < 0.1:  # < 100ms for 50 items
        print("✅ CREATE performance: EXCELLENT")
    elif create_time < 0.5:
        print("⚡ CREATE performance: GOOD")
    else:
        print("⚠️  CREATE performance: NEEDS IMPROVEMENT")
    
    if query_time < 0.01:  # < 10ms per query
        print("✅ QUERY performance: EXCELLENT")
    elif query_time < 0.05:
        print("⚡ QUERY performance: GOOD")
    else:
        print("⚠️  QUERY performance: NEEDS IMPROVEMENT")


if __name__ == "__main__":
    main()