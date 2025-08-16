#!/usr/bin/env python3
"""
TODOIT MCP - Subtask Key Flexibility Migration Tool

This script safely migrates your existing TODOIT database to support 
duplicate subtask keys across different parent tasks.

BEFORE MIGRATION: subtasks must have unique keys across entire list
AFTER MIGRATION:  subtasks can have same keys for different parents

Example:
  BEFORE: scene_0019_image_gen, scene_0020_image_gen (unique prefixes required)
  AFTER:  image_gen for scene_0019, image_gen for scene_0020 (same key allowed)

Usage:
  python migrate_subtask_keys.py [--db-path PATH] [--backup] [--dry-run]
  
Options:
  --db-path PATH    Path to database (default: todoit.db)
  --backup         Create backup before migration
  --dry-run        Show what would be changed without applying
  --force          Skip confirmation prompt
"""

import os
import sys
import argparse
import shutil
from datetime import datetime
from core.database import Database


def create_backup(db_path: str) -> str:
    """Create backup of database before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def check_database_status(db_path: str):
    """Check current database schema status"""
    print(f"🔍 Checking database: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return False
        
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current unique constraint
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_todo_items_unique_key'")
        old_index = cursor.fetchone()
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_todo_items_unique_key_hierarchical'")
        new_index = cursor.fetchone()
        
        print("\n📊 Current database status:")
        if old_index:
            print("  🔴 OLD constraint: UNIQUE(list_id, item_key)")
            print("      → Subtasks must have unique keys across entire list")
        
        if new_index:
            print("  🟢 NEW constraint: UNIQUE(list_id, parent_item_id, item_key)")
            print("      → Subtasks can have same keys for different parents")
            print("\n✅ Migration already applied!")
            return False
        else:
            print("  ⚠️  NEW constraint: NOT FOUND")
            print("      → Migration needed")
            
        # Count items that would be affected
        cursor.execute("""
            SELECT COUNT(*) FROM todo_items 
            WHERE parent_item_id IS NOT NULL
        """)
        subtask_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT list_id) FROM todo_items 
            WHERE parent_item_id IS NOT NULL
        """)
        affected_lists = cursor.fetchone()[0]
        
        print(f"\n📈 Impact analysis:")
        print(f"   • {subtask_count} subtasks in database")
        print(f"   • {affected_lists} lists with subtasks")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False


def run_migration(db_path: str, dry_run: bool = False):
    """Run the migration"""
    if dry_run:
        print("\n🧪 DRY RUN MODE - No changes will be made")
    else:
        print("\n🚀 Running migration...")
    
    try:
        if not dry_run:
            db = Database(db_path)
            print("✅ Migration completed successfully!")
            
            print("\n🎉 Benefits enabled:")
            print("   • Subtasks can use identical keys for different parents")
            print("   • find_subitems_by_status works with generic keys")
            print("   • No need for unique prefixes like scene_0019_image_gen")
            print("   • Standardized workflows across different tasks")
        else:
            print("✅ Dry run completed - migration ready to apply")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
        
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate TODOIT database to support duplicate subtask keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--db-path", 
        default="todoit.db",
        help="Path to database file (default: todoit.db)"
    )
    
    parser.add_argument(
        "--backup",
        action="store_true", 
        help="Create backup before migration"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be changed without applying"
    )
    
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    print("🔧 TODOIT MCP - Subtask Key Flexibility Migration")
    print("=" * 50)
    
    # Check database status
    if not check_database_status(args.db_path):
        return
    
    # Confirmation prompt
    if not args.force and not args.dry_run:
        print(f"\n⚠️  This will modify your database: {args.db_path}")
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Migration cancelled")
            return
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        create_backup(args.db_path)
    
    # Run migration
    success = run_migration(args.db_path, args.dry_run)
    
    if success and not args.dry_run:
        print(f"\n🏁 Migration completed successfully!")
        print(f"   Database: {args.db_path}")
        print(f"   You can now use duplicate subtask keys across different parents!")
    

if __name__ == "__main__":
    main()