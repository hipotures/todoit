#!/usr/bin/env python3
"""
Final cleanup script to fix remaining CLI syntax issues.
"""

import os
import re

def final_fix_patterns(filepath):
    """Fix remaining CLI patterns"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix pattern: "--list", "--item", "testlist", "--title", "--item", "task1", "--title"
    content = re.sub(
        r'"--list",\s*"--item",\s*"([^"]+)",\s*"--title",\s*"--item",\s*"([^"]+)",\s*"--title"',
        r'"--list", "\1", "--item", "\2", "--title"',
        content
    )
    
    # Fix other malformed patterns
    content = re.sub(
        r'"item",\s*"add",\s*"--list",\s*"--item",\s*"([^"]+)",\s*"--title",\s*"--item",\s*"([^"]+)",\s*"--title"',
        r'"item", "add", "--list", "\1", "--item", "\2", "--title"',
        content
    )
    
    # Fix "dep", "show", "item" -> "dep", "show", "--item", "item"
    content = re.sub(
        r'"dep",\s*"show",\s*"([^"]+:[^"]+)"(?!\s*,\s*"--)',
        r'"dep", "show", "--item", "\1"',
        content
    )
    
    # Fix "dep", "remove", "item1", "item2" -> "dep", "remove", "--dependent", "item1", "--required", "item2"
    content = re.sub(
        r'"dep",\s*"remove",\s*"([^"]+:[^"]+)",\s*"([^"]+:[^"]+)"',
        r'"dep", "remove", "--dependent", "\1", "--required", "\2"',
        content
    )
    
    # Fix "item", "next", "list" patterns that were missed
    content = re.sub(
        r'"item",\s*"next",\s*"([^"]+)"(?!\s*[,\]])',
        r'"item", "next", "--list", "\1"',
        content
    )
    
    # Fix "item", "next-smart", "list" patterns that were missed  
    content = re.sub(
        r'"item",\s*"next-smart",\s*"([^"]+)"(?!\s*[,\]])',
        r'"item", "next-smart", "--list", "\1"',
        content
    )
    
    # Fix stats command patterns
    content = re.sub(
        r'"stats",\s*"stats",\s*"([^"]+)"',
        r'"stats", "progress", "--list", "\1"',
        content
    )
    
    # Fix item property list commands
    content = re.sub(
        r'"item",\s*"property",\s*"list",\s*"([^"]+)",\s*"([^"]+)"',
        r'"item", "property", "list", "--list", "\1", "--item", "\2"',
        content
    )
    
    content = re.sub(
        r'"item",\s*"property",\s*"list",\s*"([^"]+)"(?!\s*[,\]])',
        r'"item", "property", "list", "--list", "\1"',
        content
    )
    
    return content, content != original_content

def main():
    """Final cleanup of CLI syntax issues"""
    test_files = [
        'tests/integration/test_item_next_json_output.py',
        'tests/integration/test_stats_progress_json_output.py',
        'tests/integration/test_property_json_output.py',
        'tests/integration/test_emoji_mapping_json.py',
        'tests/integration/test_integration.py'
    ]
    
    fixed_files = 0
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"Final cleanup for {filepath}...")
            content, changed = final_fix_patterns(filepath)
            if changed:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  - Applied final fixes")
                fixed_files += 1
            else:
                print(f"  - No changes needed")
    
    print(f"\nApplied final fixes to {fixed_files} files")

if __name__ == "__main__":
    main()