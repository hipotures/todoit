#!/usr/bin/env python3
"""
Script to fix remaining CLI syntax issues that were missed in the first pass.
"""

import os
import re
import glob

def fix_remaining_cli_patterns(filepath):
    """Fix remaining CLI patterns that were missed"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern: "list", "create", "listname", "--title" -> "list", "create", "--list", "listname", "--title"
    content = re.sub(
        r'"list",\s*"create",\s*"([^"]+)",\s*"--title"',
        r'"list", "create", "--list", "\1", "--title"',
        content
    )
    
    # Pattern: "list", "show", "listname" -> "list", "show", "--list", "listname"
    content = re.sub(
        r'"list",\s*"show",\s*"([^"]+)"(?!\s*[,\]])',
        r'"list", "show", "--list", "\1"',
        content
    )
    
    # Pattern: "list", "show", "listname", "--tree" -> "list", "show", "--list", "listname", "--tree"
    content = re.sub(
        r'"list",\s*"show",\s*"([^"]+)",\s*"--tree"',
        r'"list", "show", "--list", "\1", "--tree"',
        content
    )
    
    # Pattern: "item", "add", "list", "item", "content" -> "item", "add", "--list", "list", "--item", "item", "--title", "content"
    content = re.sub(
        r'"item",\s*"add",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"',
        r'"item", "add", "--list", "\1", "--item", "\2", "--title", "\3"',
        content
    )
    
    # Pattern: "item", "status", "list", "item", "--status" -> "item", "status", "--list", "list", "--item", "item", "--status"
    content = re.sub(
        r'"item",\s*"status",\s*"([^"]+)",\s*"([^"]+)",\s*"--status"',
        r'"item", "status", "--list", "\1", "--item", "\2", "--status"',
        content
    )
    
    # Pattern: "item", "next", "list" -> "item", "next", "--list", "list"
    content = re.sub(
        r'"item",\s*"next",\s*"([^"]+)"(?!\s*[,\]])',
        r'"item", "next", "--list", "\1"',
        content
    )
    
    # Pattern: "item", "next-smart", "list" -> "item", "next-smart", "--list", "list"
    content = re.sub(
        r'"item",\s*"next-smart",\s*"([^"]+)"(?!\s*[,\]])',
        r'"item", "next-smart", "--list", "\1"',
        content
    )
    
    # Pattern: ["list", "create", "name"] -> ["list", "create", "--list", "name"]
    content = re.sub(
        r'\["list",\s*"create",\s*"([^"]+)"\]',
        r'["list", "create", "--list", "\1"]',
        content
    )
    
    # Fix multiline array patterns
    # Pattern with line breaks: [\n    "list",\n    "create",\n    "name",\n    "--title" -> add --list
    content = re.sub(
        r'(\[\s*"list",\s*"create",\s*")([^"]+)(",\s*"--title")',
        r'\1--list", "\2\3',
        content,
        flags=re.MULTILINE
    )
    
    # Fix more complex invoke patterns that span multiple lines
    # This handles cases where the array is split across multiple lines
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for "list", "create", followed by a name on next lines
        if '"list",' in line and i + 1 < len(lines) and '"create",' in lines[i + 1]:
            # Check if the next few lines have the old pattern
            if i + 2 < len(lines) and re.search(r'"([^"]+)",', lines[i + 2]) and '--title' not in lines[i + 2]:
                # This looks like: "list", "create", "name", "--title"
                name_match = re.search(r'"([^"]+)",', lines[i + 2])
                if name_match and i + 3 < len(lines) and '"--title"' in lines[i + 3]:
                    # Fix the pattern
                    new_lines.append(line)  # "list",
                    new_lines.append(lines[i + 1])  # "create",
                    new_lines.append(f'            "--list",')
                    new_lines.append(f'            "{name_match.group(1)}",')
                    new_lines.append(lines[i + 3])  # "--title",
                    i += 4
                    continue
        
        # Look for "item", "add" patterns
        if '"item",' in line and i + 1 < len(lines) and '"add",' in lines[i + 1]:
            # Check for old 3-argument pattern: item, add, list, item, content
            if (i + 4 < len(lines) and 
                re.search(r'"([^"]+)",', lines[i + 2]) and 
                re.search(r'"([^"]+)",', lines[i + 3]) and
                re.search(r'"([^"]+)",', lines[i + 4]) and
                '--list' not in lines[i + 2]):
                
                list_match = re.search(r'"([^"]+)",', lines[i + 2])
                item_match = re.search(r'"([^"]+)",', lines[i + 3])
                content_match = re.search(r'"([^"]+)",', lines[i + 4])
                
                if list_match and item_match and content_match:
                    new_lines.append(line)  # "item",
                    new_lines.append(lines[i + 1])  # "add",
                    new_lines.append(f'            "--list",')
                    new_lines.append(f'            "{list_match.group(1)}",')
                    new_lines.append(f'            "--item",')
                    new_lines.append(f'            "{item_match.group(1)}",')
                    new_lines.append(f'            "--title",')
                    new_lines.append(f'            "{content_match.group(1)}",')
                    i += 5
                    continue
        
        new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    return content, content != original_content

def main():
    """Fix remaining CLI syntax issues"""
    test_files = [
        'tests/integration/test_integration.py',
        'tests/integration/test_emoji_mapping_json.py',
        'tests/integration/test_item_next_json_output.py',
        'tests/integration/test_stats_progress_json_output.py',
        'tests/integration/test_property_search_integration.py',
        'tests/integration/test_rename_cli.py',
        'tests/integration/test_property_json_output.py',
        'tests/integration/test_tag_list_json_output.py'
    ]
    
    fixed_files = 0
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"Fixing {filepath}...")
            content, changed = fix_remaining_cli_patterns(filepath)
            if changed:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  - Fixed remaining CLI patterns")
                fixed_files += 1
            else:
                print(f"  - No changes needed")
    
    print(f"\nFixed remaining patterns in {fixed_files} files")

if __name__ == "__main__":
    main()