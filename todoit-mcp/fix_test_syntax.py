#!/usr/bin/env python3
"""
Script to fix CLI syntax in all test files.
Updates old CLI syntax to new format across the entire test suite.
"""

import os
import re
import glob

def fix_cli_syntax_in_file(filepath):
    """Fix CLI syntax in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: list create name --title "Title" -> list create --list name --title "Title"
    content = re.sub(
        r'list create ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 --title',
        r'list create --list \1\2\1 --title',
        content
    )
    
    # Pattern 2: list create name "Title" -> list create --list name --title "Title"
    content = re.sub(
        r'list create ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"][^\'"]*.+?[\'"])',
        r'list create --list \1\2\1 --title \3',
        content
    )
    
    # Pattern 3: item add list_name item_name "content" -> item add --list list_name --item item_name --title "content"
    content = re.sub(
        r'item add ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3 ([\'"][^\'"]*.+?[\'"])',
        r'item add --list \1\2\1 --item \3\4\3 --title \5',
        content
    )
    
    # Pattern 4: item add list_name item_name --content "content" -> item add --list list_name --item item_name --title "content"
    content = re.sub(
        r'item add ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3 --content',
        r'item add --list \1\2\1 --item \3\4\3 --title',
        content
    )
    
    # Pattern 5: item add-subtask list parent sub "content" -> item add --list list --item parent --subitem sub --title "content"
    content = re.sub(
        r'item add-subtask ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\5 ([\'"][^\'"]*.+?[\'"])',
        r'item add --list \1\2\1 --item \3\4\3 --subitem \5\6\5 --title \7',
        content
    )
    
    # Pattern 6: item status list item status -> item status --list list --item item --status status
    content = re.sub(
        r'item status ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3 ([a-zA-Z_][a-zA-Z0-9_]*)',
        r'item status --list \1\2\1 --item \3\4\3 --status \5',
        content
    )
    
    # Pattern 7: item next list -> item next --list list
    content = re.sub(
        r'item next ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1(?!\s*--)',
        r'item next --list \1\2\1',
        content
    )
    
    # Pattern 8: list show list -> list show --list list
    content = re.sub(
        r'list show ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1(?!\s*--)',
        r'list show --list \1\2\1',
        content
    )
    
    # Pattern 9: list archive list -> list archive --list list
    content = re.sub(
        r'list archive ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1(?!\s*--)',
        r'list archive --list \1\2\1',
        content
    )
    
    # Pattern 10: list progress list -> list stats --list list (command changed)
    content = re.sub(
        r'list progress ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1(?!\s*--)',
        r'list stats --list \1\2\1',
        content
    )
    
    # Pattern 11: item subtasks list item -> item list --list list --item item
    content = re.sub(
        r'item subtasks ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3',
        r'item list --list \1\2\1 --item \3\4\3',
        content
    )
    
    # Pattern 12: item tree list item -> item list --list list --item item
    content = re.sub(
        r'item tree ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3',
        r'item list --list \1\2\1 --item \3\4\3',
        content
    )
    
    # Pattern 13: dep add dependent:item requires required:item -> dep add --dependent dependent:item --required required:item
    content = re.sub(
        r'dep add ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_]*)\1 requires ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_]*)\3',
        r'dep add --dependent \1\2\1 --required \3\4\3',
        content
    )
    
    # Pattern 14: dep show item -> dep show --item item
    content = re.sub(
        r'dep show ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_]*)\1(?!\s*--)',
        r'dep show --item \1\2\1',
        content
    )
    
    # Pattern 15: item move-to-subtask list item parent -> item move-to-subitem --list list --item item --parent parent
    content = re.sub(
        r'item move-to-subtask ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\1 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\3 ([\'"]?)([a-zA-Z_][a-zA-Z0-9_]*)\5',
        r'item move-to-subitem --list \1\2\1 --item \3\4\3 --parent \5\6\5',
        content
    )
    
    # Fix CLI runner invoke patterns (for Click tests)
    # Pattern: ["list", "create", "name", "--title", "title"] -> ["list", "create", "--list", "name", "--title", "title"]
    content = re.sub(
        r'\["list", "create", "([^"]+)", "--title"',
        r'["list", "create", "--list", "\1", "--title"',
        content
    )
    
    # Pattern: ["item", "add", "list", "item", "content"] -> ["item", "add", "--list", "list", "--item", "item", "--title", "content"]
    content = re.sub(
        r'\["item", "add", "([^"]+)", "([^"]+)", "([^"]+)"\]',
        r'["item", "add", "--list", "\1", "--item", "\2", "--title", "\3"]',
        content
    )
    
    # Pattern: ["item", "add-subtask", "list", "item", "sub", "content"] -> ["item", "add", "--list", "list", "--item", "item", "--subitem", "sub", "--title", "content"]
    content = re.sub(
        r'\["item", "add-subtask", "([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)"\]',
        r'["item", "add", "--list", "\1", "--item", "\2", "--subitem", "\3", "--title", "\4"]',
        content
    )
    
    # Pattern: ["item", "status", "list", "item", "--status", "status"] -> ["item", "status", "--list", "list", "--item", "item", "--status", "status"]
    content = re.sub(
        r'\["item", "status", "([^"]+)", "([^"]+)", "--status"',
        r'["item", "status", "--list", "\1", "--item", "\2", "--status"',
        content
    )
    
    # Fix more complex invoke patterns with line breaks
    content = re.sub(
        r'\[\s*"list",\s*"create",\s*"([^"]+)",\s*"--title"',
        r'[\n                    "list",\n                    "create",\n                    "--list",\n                    "\1",\n                    "--title"',
        content
    )
    
    # Fix remaining progress -> stats
    content = re.sub(r'"progress"', '"stats"', content)
    
    # Fix error message checks
    content = re.sub(r'"add-subtask"', '"add"', content)
    content = re.sub(r'"move-to-subtask"', '"move-to-subitem"', content)
    content = re.sub(r'"tree"', '"list"', content)
    
    return content, content != original_content

def fix_api_methods_in_file(filepath):
    """Fix API method renames in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # API method renames
    content = re.sub(r'\.add_subitem\(', '.add_subitem(', content)
    content = re.sub(r'\.get_subitems\(', '.get_subitems(', content)
    content = re.sub(r'\.move_to_subitem\(', '.move_to_subitem(', content)
    
    return content, content != original_content

def fix_terminology_in_file(filepath):
    """Fix terminology changes in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix terminology in strings and comments (be careful not to change variable names)
    # Only change in quoted strings and comments
    content = re.sub(r'"([^"]*\b)task(\b[^"]*)"', r'"\1item\2"', content)
    content = re.sub(r'"([^"]*\b)subtask(\b[^"]*)"', r'"\1subitem\2"', content)
    content = re.sub(r'"([^"]*\b)Task(\b[^"]*)"', r'"\1Item\2"', content)
    content = re.sub(r'"([^"]*\b)Subtask(\b[^"]*)"', r'"\1Subitem\2"', content)
    
    # Fix in assert messages
    content = re.sub(r'assert "([^"]*\b)task(\b[^"]*)" in', r'assert "\1item\2" in', content)
    content = re.sub(r'assert "([^"]*\b)subtask(\b[^"]*)" in', r'assert "\1subitem\2" in', content)
    content = re.sub(r'assert "([^"]*\b)Task(\b[^"]*)" in', r'assert "\1Item\2" in', content)
    content = re.sub(r'assert "([^"]*\b)Subtask(\b[^"]*)" in', r'assert "\1Subitem\2" in', content)
    
    return content, content != original_content

def main():
    """Main function to fix all test files"""
    test_dirs = [
        'tests/unit/',
        'tests/integration/',
        'tests/e2e/',
        'tests/edge_cases/',
        'tests/'
    ]
    
    total_files_modified = 0
    cli_fixes = 0
    api_fixes = 0
    terminology_fixes = 0
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            # Find all Python test files
            pattern = os.path.join(test_dir, '*.py')
            files = glob.glob(pattern)
            
            for filepath in files:
                if os.path.basename(filepath).startswith('test_') or 'test' in os.path.basename(filepath):
                    print(f"Processing {filepath}...")
                    
                    # Fix CLI syntax
                    content, cli_changed = fix_cli_syntax_in_file(filepath)
                    if cli_changed:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        cli_fixes += 1
                        print(f"  - Fixed CLI syntax")
                    
                    # Fix API methods
                    content, api_changed = fix_api_methods_in_file(filepath)
                    if api_changed:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        api_fixes += 1
                        print(f"  - Fixed API methods")
                    
                    # Fix terminology
                    content, term_changed = fix_terminology_in_file(filepath)
                    if term_changed:
                        with open(filepath, 'w') as f:
                            f.write(content)
                        terminology_fixes += 1
                        print(f"  - Fixed terminology")
                    
                    if cli_changed or api_changed or term_changed:
                        total_files_modified += 1
    
    print(f"\nSummary:")
    print(f"Total files modified: {total_files_modified}")
    print(f"CLI syntax fixes: {cli_fixes}")
    print(f"API method fixes: {api_fixes}")
    print(f"Terminology fixes: {terminology_fixes}")

if __name__ == "__main__":
    main()