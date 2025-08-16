#!/usr/bin/env python3
"""
Script to fix duplicated parameters that were introduced by the previous fix script.
"""

import os
import re

def fix_duplicated_params(filepath):
    """Fix duplicated --list and --item parameters"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix duplicated --list parameters
    content = re.sub(r'--list",\s*"--list"', '--list"', content)
    content = re.sub(r'"--list",\s*"--list",', '"--list",', content)
    
    # Fix duplicated --item parameters  
    content = re.sub(r'--item",\s*"--item"', '--item"', content)
    content = re.sub(r'"--item",\s*"--item",', '"--item",', content)
    
    # Fix patterns like: "--list", "--list", "--item", "listname", "--title", "--item", "itemname", "--title"
    content = re.sub(
        r'"--list",\s*"--list",\s*"--item",\s*"([^"]+)",\s*"--title",\s*"--item",\s*"([^"]+)",\s*"--title"',
        r'"--list", "\1", "--item", "\2", "--title"',
        content
    )
    
    # Fix patterns where we have extra --title parameters
    content = re.sub(r'"--title",\s*"--title"', '"--title"', content)
    
    # Fix patterns like: "item", "add", "--list", "listname", "--item", "parent", "--title", "child", "content"
    # This should be a subitem addition pattern
    content = re.sub(
        r'"item",\s*"add",\s*"--list",\s*"([^"]+)",\s*"--item",\s*"([^"]+)",\s*"--title",\s*"([^"]+)",\s*"([^"]+)"',
        r'"item", "add", "--list", "\1", "--item", "\2", "--subitem", "\3", "--title", "\4"',
        content
    )
    
    return content, content != original_content

def main():
    """Fix duplicated parameters"""
    test_files = [
        'tests/integration/test_integration.py',
        'tests/integration/test_emoji_mapping_json.py',
        'tests/integration/test_item_next_json_output.py',
        'tests/integration/test_stats_progress_json_output.py',
        'tests/integration/test_property_json_output.py'
    ]
    
    fixed_files = 0
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"Fixing {filepath}...")
            content, changed = fix_duplicated_params(filepath)
            if changed:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  - Fixed duplicated parameters")
                fixed_files += 1
            else:
                print(f"  - No changes needed")
    
    print(f"\nFixed duplicated parameters in {fixed_files} files")

if __name__ == "__main__":
    main()