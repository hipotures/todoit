# Changelog

All notable changes to TODOIT MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.12.0] - 2025-08-19

### 🧹 MAJOR: Technical Debt Cleanup - Legacy CLI Removal

#### ✨ **Removed**
- **Legacy CLI Files**: Removed 2,309 lines of duplicate legacy code
  - Deleted `interfaces/cli_original.py` (2,238 lines) - Legacy monolithic CLI
  - Deleted `interfaces/cli_modular.py` (71 lines) - Transitional implementation
- **Code Duplication**: Eliminated maintenance burden of keeping multiple CLI implementations synchronized

#### ✅ **Enhanced**
- **CLI Architecture**: Single source of truth - only modular `interfaces/cli.py` remains
- **Feature Completeness**: All legacy functionality preserved in modular structure
  - `add-subtask` → `add --subitem` (unified command approach)
  - `subtasks` → `list` with item filtering (more flexible)
  - `move-to-subtask` → `move-to-subitem` (updated naming)
- **Additional Features**: Modular CLI includes new commands not in legacy version
  - `archive`/`unarchive` list management
  - `rename` for lists and items  
  - `find-subitems` advanced search
  - `reports` and analytics
  - Enhanced `tag` management

#### 🔧 **Technical Benefits**
- **Reduced Complexity**: Eliminated duplicate code maintenance
- **Better Organization**: Functionality properly separated into focused modules
- **Package Size**: Cleaner distribution without legacy files
- **Maintainability**: Future changes only need to be made in one place

#### 📊 **Impact**
- **Codebase Size**: Reduced by 2,309 lines of duplicate code
- **Architecture**: Clean 3-layer design preserved with no functional loss
- **Development**: Simplified workflow with single CLI implementation
- **Production**: No impact - package already used modular CLI

---

## [2.11.1] - 2025-08-18

### 🐛 HOTFIX: CLI Display Natural Sorting

#### ✅ **Fixed**
- **CLI Display**: Fixed CLI re-sorting items by `position` after natural sorting
- **Hierarchical Numbering**: Updated table numbering to reflect natural sort order  
- **Live Display**: Fixed live mode to preserve natural sorting from manager
- **Visual Consistency**: CLI now correctly shows `scene_0020` before `scene_0021`

#### 🔧 **Technical Details**
- **Removed re-sorting** in `_organize_items_by_hierarchy()` function
- **Removed re-sorting** in `_create_live_items_table()` function  
- **Updated hierarchical numbering** to use natural sort order index instead of position
- **Preserved natural sorting** from database layer throughout display pipeline

#### 📊 **Impact**
- CLI now fully respects natural sorting implemented in v2.11.0
- Consistent behavior between MCP tools and CLI commands
- Eliminates user confusion from mixed sorting approaches

---

## [2.11.0] - 2025-08-18

### 🚀 MAJOR: Natural Sorting Implementation

#### ✨ **New Features**
- **NATURAL SORTING**: Lists and items now sort naturally by their keys
  - `scene_0020` comes before `scene_0021` (not after)  
  - `test_2` comes before `test_10` (not after)
  - `0014_jane` comes before `0037_wuthering` (correct numeric order)
- **IMPROVED UX**: Eliminates confusing alphabetic sorting of numeric sequences
- **AUTOMATIC**: No configuration needed - all sorting is now natural by default

#### 🔧 **Technical Implementation**
- **Added `natural_sort_key()` function** in `Database` class using regex pattern `([0-9]+)`
- **Updated all sorting methods** to use natural sorting instead of position-based
- **Maintained hierarchical structure**: Main items first, then subitems grouped by parent
- **Performance optimized**: Sorting done in Python after database query

#### 📊 **Impact**
- **Lists**: `todo_list_all` now returns naturally sorted lists
- **Items**: `todo_get_list_items` returns naturally sorted items within each list
- **All database queries** updated to use natural sorting consistently
- **MCP & CLI**: Both interfaces benefit from improved sorting

#### 🔄 **Breaking Change**
- **Position field**: No longer primary sort criterion (still exists for compatibility)
- **New sort order**: Items now sorted by `item_key` with natural number handling

---

## [2.10.2] - 2025-08-17

### 🐛 BUGFIX: Property Commands ID Resolution

#### ✅ **Fixed CLI Property Commands**
- **FIXED**: Property commands now support numeric list IDs (e.g., `--list 126`)
- **CONSISTENT**: All property commands now work like `list show` command
- **RESOLVED**: `todoit item property list --list 126` no longer fails with "List '126' not found"
- **ADDED**: `resolve_list_key()` helper function for ID-to-key conversion

#### 🔧 **Technical Details**
- **Added ID resolution logic** to all property commands in `property_commands.py`
- **Maintains existing validation** that prevents list keys from being only digits
- **Consistent behavior** with other CLI commands that accept numeric IDs
- **No breaking changes** - existing functionality preserved

#### 📝 **Documentation Updates**
- **Updated CLI_GUIDE.md** with examples showing numeric ID usage
- **Added notes** to property command sections about ID/key support

## [2.10.2] - 2025-08-17

### 🎯 PATCH: Comprehensive Data Reduction for ALL Response Types

#### ⚡ **Complete MCP Data Optimization**
- **EXTENDED**: Data reduction to property, tag, and assignment responses
- **COMPREHENSIVE**: All 5 response types now consistently optimized
- **VERIFIED**: Real-world user testing confirms reductions across all operations

#### 📊 **Complete Data Reduction Metrics**
- **Item responses**: 13 fields → 5 fields (62% reduction)
- **List responses**: 8+ fields → 4 fields (50% reduction)  
- **Property responses**: 6 fields → 2 fields (67% reduction)
- **Tag responses**: 4 fields → 2 fields (50% reduction)
- **Assignment responses**: 4 fields → 3 fields (25% reduction)

#### 🔧 **Additional Functions Optimized**
- **todo_set_item_property** - clean property responses (6→2 fields)
- **todo_set_list_property** - clean property responses (6→2 fields)
- **todo_create_tag** - clean tag responses (4→2 fields)
- **todo_add_list_tag** - clean assignment responses (4→3 fields)
- **All list operations** - clean embedded tag arrays (4→2 fields per tag)

#### 🎯 **Real-World Examples**
- **Property example**: User's 6-field response with timestamps → 2 essential fields
- **Tag example**: User's 4-field response with id/timestamp → 2 essential fields
- **Consistent clean data** across all MCP tool responses

## [2.10.1] - 2025-08-17

### 🎯 PATCH: Complete MCP Data Reduction Implementation

#### ⚡ **Complete MCP Response Optimization**
- **FIXED**: Applied data reduction to ALL MCP tools (missed functions in initial release)
- **VERIFIED**: Real-world user testing confirms 62-67% data reduction across all operations
- **COMPREHENSIVE**: Every item and list response now uses optimized format
- **CONSISTENT**: Uniform clean data structure across all 51 MCP tools

#### 📊 **Detailed Data Reduction Metrics**
- **Item responses**: 13 fields → 5 fields (62% reduction)
  - **Removed**: `id`, `list_id`, `created_at`, `updated_at`, `started_at`, `completed_at`, `completion_states`, `metadata`, `parent_item_id`
  - **Retained**: `item_key`, `title`, `status`, `position`, `is_subtask`
- **List responses**: 8+ fields → 4 fields (~50% reduction)
  - **Removed**: `id`, `created_at`, `updated_at`, `status`, `metadata`, internal fields
  - **Retained**: `list_key`, `title`, `description`, `list_type`

#### 🔧 **Functions Completed**
- **todo_rename_item** - now returns clean item data
- **todo_add_item** (all variants) - clean item/subitem responses
- **todo_get_item** (all modes) - clean item/subitem data
- **todo_get_list_items** - clean items with optimized fields
- **todo_get_list** - clean list data structure
- **All smart workflow tools** - clean next item recommendations
- **All dependency tools** - clean blocked/blocker item data
- **Import/export tools** - clean list data in responses

## [2.10.0] - 2025-08-17

### 🚀 MAJOR: MCP Data Optimization & Tool Cleanup

#### ⚡ **MCP Response Data Reduction**
- **REDUCED**: Item responses by ~67% - removed timestamps, metadata, completion_states, internal IDs
- **ESSENTIAL**: Only `item_key`, `title`, `status`, `position` + `is_subtask` indicator retained
- **OPTIMIZED**: List responses - removed timestamps, kept only essential fields
- **PERFORMANCE**: Significantly faster MCP responses with lower token usage in Claude Code
- **READABILITY**: Cleaner, more focused data for better user experience

#### 🧹 **Tool Consolidation**
- **REMOVED**: `todo_update_item_content` MCP tool (redundant functionality)
- **UNIFIED**: `todo_rename_item` now handles both key and title updates (replaces removed tool)
- **TOTAL**: Reduced from 52 to 51 MCP tools
- **MINIMAL**: 9 tools (reduced from 10)
- **STANDARD**: 23 tools (reduced from 24)
- **MAX**: 51 tools (reduced from 52)

#### 📚 **Documentation Updates**
- **UPDATED**: MCP_TOOLS.md with new tool counts and data optimization section
- **ENHANCED**: Performance impact metrics updated for optimized responses
- **DOCUMENTED**: Complete data reduction strategy and benefits

#### 🧪 **Test Coverage**
- **UPDATED**: All test suites for reduced tool count
- **VERIFIED**: E2E tests use `todo_rename_item` for content updates
- **PASSING**: All 700+ tests pass with optimized data structures

#### 🎯 **Performance Benefits**
- **TOKEN USAGE**: Reduced context size in Claude Code interactions
- **RESPONSE SPEED**: Faster MCP tool responses with minimal data transfer
- **FOCUS**: Users see only actionable data, reducing cognitive load

## [2.9.0] - 2025-08-17

### 🚀 MAJOR FEATURE: Complete Rename Functionality

#### ✨ **New Rename Operations**
- **NEW**: `todo_rename_item` MCP tool - Rename item keys and/or titles with subitem support
- **NEW**: `todo_rename_list` MCP tool - Rename list keys and/or titles  
- **NEW**: `todoit item rename` CLI command - Complete item renaming functionality
- **ENHANCED**: Full subitem rename support via `subitem_key` parameter

#### 🔧 **Database & Core Enhancements**
- **ADDED**: `rename_item()` method in Database layer with key/content updates
- **ADDED**: `rename_item()` method in TodoManager with validation and history
- **ENHANCED**: Cross-list uniqueness validation for item keys
- **ROBUST**: Complete error handling for all rename edge cases

#### 🎯 **MCP API Consistency Improvements**  
- **STANDARDIZED**: All MCP tools now use `title` parameter instead of `content` for external APIs
- **MAPPING**: Automatic internal `content` ↔ external `title` field mapping
- **CONSISTENT**: Unified naming convention across all 52 MCP tools
- **BACKWARDS**: Maintains internal database `content` field structure

#### 🧪 **Comprehensive Testing**
- **ADDED**: 29 unit tests for rename functionality (18 item + 11 list)
- **ADDED**: 11 integration tests for MCP rename tools  
- **FIXED**: Updated all existing tests for new `title` parameter convention
- **COVERAGE**: Complete test coverage for all rename scenarios and edge cases

#### 📊 **Updated Tool Counts**
- **TOTAL**: 52 MCP tools (increased from 50)
- **MINIMAL**: 12 tools (includes essential rename operations)
- **STANDARD**: 24 tools (includes both rename tools)  
- **MAX**: 52 tools (complete feature set)

#### 📚 **Documentation Updates**
- **UPDATED**: MCP_TOOLS.md with new tool descriptions and counts
- **ENHANCED**: Tool level configuration tables and performance metrics
- **DETAILED**: Complete rename functionality documentation

#### 🔒 **Validation & Security**
- **STRICT**: Key format validation (alphanumeric + underscore/dash)
- **SAFE**: Circular dependency prevention in rename operations
- **AUDIT**: Complete history recording for all rename operations
- **UNIQUE**: Cross-context uniqueness enforcement

## [2.8.3] - 2025-08-17

### 🐛 CRITICAL BUG FIX - CLI find-subitems Compatibility

#### ✅ **Fixed CLI Error After API Changes**
- **FIXED**: `'dict' object has no attribute 'item_key'` error in `todoit item find-subitems` command
- **CAUSE**: Breaking changes in v2.7.0 changed API response structure but CLI wasn't updated
- **SOLUTION**: Added defensive compatibility code to handle both object and dict formats
- **BACKWARDS COMPATIBLE**: CLI now works with current and future API changes

#### 🔄 **Enhanced Error Handling**
- **ROBUST**: CLI now gracefully handles data structure variations
- **DEFENSIVE**: Compatible with both `TodoItem` objects and dictionary responses
- **FUTURE-PROOF**: Will work regardless of internal data format changes

#### 📚 **Documentation Updates**
- **ADDED**: Complete `find-subitems` command documentation in CLI_GUIDE.md
- **EXAMPLES**: Real-world workflow automation examples
- **OUTPUT**: Sample command output formatting

## [2.8.2] - 2025-08-17

### 🔧 TEST FIXES - Complete Test Suite Compatibility

#### ✅ **All 653 Tests Now Passing**
- **FIXED**: Updated all test files to use new `update_item_status` function signature
- **COMPLETED**: Comprehensive test suite compatibility after v2.8.1 breaking changes
- **VERIFIED**: Full test coverage maintained with zero regressions

#### 🔄 **Test Conversions Applied**
- **PATTERN 1**: `update_item_status("list", "item", "status")` → `update_item_status("list", "item", status="status")`
- **PATTERN 2**: `update_item_status("list", "sub", "status", parent_item_key="parent")` → `update_item_status("list", "parent", subitem_key="sub", status="status")`
- **CLI MOCKS**: Updated mock assertions to match new function signature

#### 📁 **Test Files Updated (16 files)**
- `tests/test_status_synchronization.py` - Status propagation tests (15 calls)
- `tests/unit/test_*_validation.py` - Archive and validation tests (4 files)
- `tests/integration/test_*_api.py` - API integration tests (6 files)
- `tests/edge_cases/test_edge_cases_limits.py` - Edge case scenarios
- `tests/unit/test_cli_error_handling.py` - CLI mock expectations

#### 📊 **Test Results**
- **BEFORE**: 634 passed, 9 failed, 10 errors
- **AFTER**: 653 passed, 0 failed, 0 errors
- **IMPROVEMENT**: 100% test success rate achieved

## [2.8.1] - 2025-08-17

### 🐛 CRITICAL BUG FIX - Subitem Disambiguation

#### ❌ **Bug Fixed**: Wrong Subitem Updates
- **PROBLEM**: `todo_update_item_status` was updating wrong subitem when multiple subitems had same name across different parents
- **EXAMPLE**: Updating `scene_0007/image_dwn` incorrectly updated `scene_0001/image_dwn` instead
- **ROOT CAUSE**: Backward compatibility between old `parent_item_key` and new `subitem_key` parameters created confusing routing logic

#### ✅ **Solution Implemented**:
- **REMOVED**: All backward compatibility - `parent_item_key` completely eliminated from `update_item_status`
- **UNIFIED**: Parameter naming - now uses `subitem_key` consistently across MCP and Manager layers  
- **SIMPLIFIED**: MCP routing - direct pass-through of parameters without translation logic
- **UPDATED**: All test files and documentation converted to new syntax

#### 🔧 **New Required Syntax**:
```python
# OLD (now forbidden):
update_item_status("list", "subitem", "status", parent_item_key="parent")

# NEW (required):
update_item_status("list", "parent", subitem_key="subitem", status="status")
```

#### 📖 **Updated Documentation**:
- **FIXED**: All examples in `docs/MCP_TOOLS.md`, `docs/api.md`, and `CHANGELOG.md`
- **VERIFIED**: CLI commands now use correct syntax
- **TESTED**: Both MCP and Manager layers properly target correct subitems

#### ⚠️ **Breaking Change**:
- **IMPACT**: Code using old `parent_item_key` parameter will now get `TypeError`
- **BENEFIT**: Zero ambiguity - always updates the correct subitem
- **MIGRATION**: Replace `parent_item_key="parent"` with proper `item_key="parent", subitem_key="subitem"` syntax

## [2.8.0] - 2025-08-16

### 🚀 MAJOR API CLEANUP - Enhanced Subitem Support

#### ✨ **BREAKING CHANGE**: MCP Function Consolidation
- **REMOVED**: `todo_start_item` - Redundant convenience function eliminated
- **REMOVED**: `todo_mark_completed` - Redundant convenience function eliminated  
- **ENHANCED**: `todo_update_item_status` now supports `subitem_key: Optional[str] = None` parameter
- **UNIFIED**: Single function handles both item and subitem status updates

#### 🎯 **API Improvements**
- **OLD APPROACH**: Separate functions for convenience (but couldn't handle subitems)
- **NEW APPROACH**: One universal function with optional subitem support
- **SUBITEM UPDATES**: `todo_update_item_status(list_key, parent_key, subitem_key=subitem, status=status)`
- **ITEM UPDATES**: `todo_update_item_status(list_key, item_key, status=status)` (unchanged)

#### 📖 **Updated Documentation**
- **UPDATED**: MCP_TOOLS.md with new subitem_key parameter examples
- **REDUCED**: Tool count from 54 to 50 (removed redundant functions)
- **ENHANCED**: Clear examples of item vs subitem status updates

#### ⚠️ **Breaking Change Notice**
- **IMPACT**: Code using `todo_start_item` or `todo_mark_completed` must migrate to `todo_update_item_status`
- **MIGRATION**: Replace with `todo_update_item_status(list_key, item_key, status="in_progress")` or `todo_update_item_status(list_key, item_key, status="completed")`
- **BENEFIT**: Now supports subitems: `todo_update_item_status(list_key, parent_key, subitem_key=subitem, status=status)`

## [2.7.0] - 2025-08-16

### 🚀 MAJOR ENHANCEMENT - Improved JSON Structure for `todo_find_subitems_by_status`

#### ✨ **BREAKING CHANGE**: New Grouped Response Format
- **CHANGED**: `todo_find_subitems_by_status` now returns grouped matches with full parent context
- **NEW STRUCTURE**: Returns `{"matches": [...], "matches_count": N}` instead of flat `{"items": [...], "count": N}`
- **ENHANCEMENT**: Each match includes complete parent item + matching subitems in logical groups
- **IMPROVEMENT**: Limit now applies to parent groups, not individual subitems (prevents fragmented results)

#### 🎯 **API Improvements**
- **OLD RESPONSE**: Flat list of subitems without parent context
- **NEW RESPONSE**: Hierarchical structure with parent + grouped subitems
- **BENEFIT**: One API call replaces two - no need for separate parent context retrieval
- **PERFORMANCE**: More logical grouping reduces need for additional queries

#### 📖 **Updated Documentation**
- **UPDATED**: MCP_TOOLS.md with new response structure examples
- **ADDED**: Migration guide showing old vs new JSON format
- **ENHANCED**: Clear examples of grouped matches with parent context

#### ⚠️ **Breaking Change Notice**
- **IMPACT**: Code using `result["items"]` must change to `result["matches"][0]["matching_subitems"]`
- **MIGRATION**: Update client code to handle new grouped structure
- **VERSION**: This is a major version bump due to breaking API changes

## [2.6.0] - 2025-08-16

### 🔧 IMPROVEMENT - Environment Variable Centralization and CLI Consistency

#### ✨ Centralized Environment Variable Handling
- **REFACTORED**: Environment variable handling moved to `TodoManager` constructor
- **UNIFIED**: Both CLI and MCP now use `TODOIT_DB_PATH` consistently (removed `TODOIT_DATABASE`)
- **ENHANCED**: `TODOIT_FORCE_TAGS` support added to MCP server through `TodoManager`
- **IMPROVED**: Single source of truth for environment configuration across all interfaces

#### ✨ Standardized List Parameter Naming
- **CHANGED**: `todoit list rename --current` parameter renamed to `--list` for consistency
- **IMPROVED**: All list commands now use uniform `--list` parameter naming convention
- **ENHANCED**: Better CLI consistency across all list management operations

#### 🧪 Testing Coverage
- **ADDED**: Comprehensive unit tests for environment variable handling in `TodoManager`
- **FIXED**: MCP integration tests updated to use unified environment variables
- **VERIFIED**: All 653 tests pass with new centralized configuration

## [2.5.9] - 2025-08-16

### 🔧 BUGFIX - Critical Test Suite Fixes and Subitem Disambiguation

#### ✨ Fixed Subitem Disambiguation Bug
- **FIXED**: CLI commands now correctly target subitems when duplicate names exist across different parent items
- **ENHANCED**: Added `parent_item_key` parameter to core manager functions for proper subitem identification
- **SOLVED**: Commands like `item status --subitem image_gen` now work correctly when multiple parents have subitems with same names
- **IMPROVED**: All CLI item commands now properly handle parent-child relationships

#### 🧪 Test Suite Overhaul
- **FIXED**: Property filtering integration tests - corrected create_list parameters and mock object attributes
- **ENHANCED**: Subtask positioning tests - fixed fixture issues, CLI parsing, and assertion formats  
- **SOLVED**: Unit test mock objects now have proper position and parent_item_id attributes for sorting
- **IMPROVED**: CLI subprocess tests now properly add required tags for environment filtering

#### 🏷️ Environment Tag Filtering Compatibility
- **FIXED**: CLI tests now work correctly with TODOIT_FILTER_TAGS environment variable
- **ENHANCED**: Test lists automatically receive appropriate tags for visibility in filtered environments
- **MAINTAINED**: Force tags functionality preserved - environment isolation working as designed

#### 📊 Test Results
- **100% Test Coverage**: All 644 tests now pass successfully
- **Regression Prevention**: Added comprehensive unit tests for subitem disambiguation scenarios
- **Integration Stability**: CLI subprocess tests handle real-world environment configurations

## [2.5.8] - 2025-08-16

### 🔧 BUGFIX - Complete Hierarchy Display in Properties

#### ✨ Fixed Missing Parent Items
- **FIXED**: Property display now shows ALL items in hierarchy, even those without properties
- **ENHANCED**: Parent items without properties display with placeholder `—` to maintain hierarchy context
- **SOLVED**: Users can now see which subitems belong to which parent items
- **IMPROVED**: Complete hierarchical structure is always visible

#### 📊 Display Example

**Before (Missing Context):**
```
Key                │ Property Key    │ Value
  scene_gen        │ thread_id       │ 12345
  image_dwn        │ dwn_pathfile    │ /path/file.png
  scene_gen        │ thread_id       │ 67890
```

**After (Clear Hierarchy):**
```
Key                │ Property Key    │ Value
scene_0001         │ —               │ —
  scene_gen        │ thread_id       │ 12345
  image_dwn        │ dwn_pathfile    │ /path/file.png
scene_0002         │ —               │ —
  scene_gen        │ thread_id       │ 67890
```

#### 🎯 Problem Solved
- **Before**: Only items with properties were shown, breaking hierarchy context
- **After**: All items shown with placeholders for items without properties
- **Benefit**: Clear parent-child relationships always visible

#### 🔧 Technical Enhancement
- **Manager API**: Enhanced `get_all_items_properties()` to include placeholder entries
- **Display Logic**: Items without properties get `—` placeholder to maintain hierarchy
- **Sorting Preserved**: Hierarchical sorting still works correctly with placeholders

## [2.5.7] - 2025-08-16

### 🎨 IMPROVEMENT - Simplified Property Display

#### ✨ Clean Visual Hierarchy
- **REMOVED**: Unnecessary "#" column with hierarchical numbering
- **SIMPLIFIED**: Display now shows only Key, Property Key, and Value columns
- **MAINTAINED**: Hierarchical indentation in Key column with `  ` prefix for subitems
- **CLEANER**: More focused table layout without redundant numbering information

#### 📊 Display Example

**Simplified Clean Format:**
```
Key                │ Property Key    │ Value
scene_0001         │ priority        │ high
  scene_gen        │ thread_id       │ 12345
scene_0002         │ status          │ in_progress
  audio_sync       │ format          │ wav
```

#### 🎯 Problem Solved
- **Before**: Redundant "#" column with numbering that wasn't referenced elsewhere
- **After**: Clean 3-column layout with only essential information
- **Benefit**: Less visual clutter, focus on actual property data

## [2.5.6] - 2025-08-16

### 🎨 ENHANCEMENT - Hierarchical Numbering in Property Display

#### ✨ Visual Hierarchy Improvements
- **REPLACED**: "Type" column with text labels (`📝 Item`, `└─ Subitem`) with hierarchical numbering
- **NEW**: Hierarchical numbering system using `#` column showing `1`, `1.1`, `1.2`, `2`, `2.1` etc.
- **ENHANCED**: Proper indentation for subitems in Key column with `  ` prefix
- **IMPROVED**: Display matches item list hierarchy format for consistent user experience

#### 📊 Display Examples

**Enhanced Table Format:**
```
#        │ Key           │ Property Key    │ Value
1        │ scene_0001    │ priority        │ high
1.1      │   scene_gen   │ thread_id       │ 12345
2        │ scene_0002    │ status          │ in_progress
2.1      │   audio_sync  │ format          │ wav
```

**Tree Format (Unchanged):**
```
📋 All Item Properties
├── 📝 scene_0001
│   ├── priority: high
│   └── └─ scene_gen
│       └── thread_id: 12345
└── 📝 scene_0002
    ├── status: in_progress
    └── └─ audio_sync
        └── format: wav
```

#### 🔧 Technical Enhancements
- **Numbering Algorithm**: Smart hierarchical numbering with parent-child relationship tracking
- **Display Logic**: Enhanced `_display_item_properties_table()` function with proper sorting
- **Key Indentation**: Visual hierarchy through indented subitem keys
- **Consistent Layout**: Unified format matching item list display standards

#### 🎯 Problem Solved
- **Before**: Confusing text labels (`📝 Item`, `└─ Subitem`) in Type column
- **After**: Clear hierarchical numbering (`1`, `1.1`, `1.2`) with indented keys
- **User Feedback**: Addressed user preference for numerical hierarchy like item list display

#### ✅ Backward Compatibility
- Tree format display unchanged
- All existing commands work unchanged
- No breaking changes to API or CLI interface

## [2.5.5] - 2025-08-16

### 🎨 ENHANCEMENT - Property Display Hierarchy

#### ✨ Visual Hierarchy Improvements
- **NEW**: Added "Type" column to property list display showing `📝 Item` vs `└─ Subitem`
- **ENHANCED**: Hierarchical sorting - main items first, followed by their subitems
- **IMPROVED**: Tree view with proper parent-child relationships for complex structures

#### 📊 Display Examples

**Table Format (Enhanced):**
```
Type         │ Item Key   │ Property Key    │ Value
📝 Item      │ feature1   │ priority        │ high
└─ Subitem   │ backend    │ difficulty      │ medium
└─ Subitem   │ frontend   │ framework       │ react
```

**Tree Format (Enhanced):**
```
📋 All Item Properties
├── 📝 feature1
│   ├── priority: high
│   ├── └─ backend
│   │   └── difficulty: medium
│   └── └─ frontend
│       └── framework: react
```

#### 🔧 Technical Enhancements
- **Manager API**: Added `parent_item_id` and `parent_item_key` to `get_all_items_properties()`
- **Sorting Algorithm**: Hierarchical sorting with proper parent-child grouping
- **CLI Display**: Enhanced both table and tree formats with clear visual hierarchy

#### 🎯 Problem Solved
- **Before**: Confusing duplicate item keys without context
- **After**: Clear visual distinction between main items and subitems
- **Benefit**: Eliminates confusion in complex hierarchical property structures

#### 📚 Documentation Updates
- **Updated**: CLI Guide with new hierarchy display examples
- **Added**: Visual examples for both table and tree formats

#### ✅ Backward Compatibility
- All existing commands work unchanged
- Enhanced display is automatically applied
- No breaking changes to API or CLI interface

## [2.5.4] - 2025-08-16

### 🔧 BUGFIX - CLI Parameter Consistency

#### ✨ CLI Standardization
- **FIXED**: Inconsistent parameter naming in `list delete` command
- **CHANGED**: `--lists` parameter renamed to `--list` for consistency across all CLI commands
- **MAINTAINED**: Full backward functionality - comma-separated values still supported

#### 📋 Usage Examples
```bash
# Single list deletion
todoit list delete --list "project1"

# Multiple lists deletion (comma-separated)
todoit list delete --list "project1,project2,project3"

# With force flag
todoit list delete --list "old-project" --force
```

#### 🔍 Technical Changes
- **File Changed**: `interfaces/cli_modules/list_commands.py` - standardized parameter name
- **Tests Updated**: Updated unit and e2e tests to use consistent parameter naming
- **Documentation**: Already consistent, no changes needed

#### 🎯 Benefits
- **Consistent UX**: All CLI commands now use predictable `--list` parameter
- **Better DX**: Developers can expect uniform command structure
- **Maintained Functionality**: Multi-list operations work exactly as before

## [2.5.3] - 2025-08-16

### 🆕 NEW FEATURE - Subitem Property Support

#### ✨ CLI Enhancements
- **ADDED**: `--subitem` option to all item property commands
- **NEW**: `todoit item property set --list "project" --item "task1" --subitem "subtask1" --key "difficulty" --value "medium"`
- **NEW**: `todoit item property get --list "project" --item "task1" --subitem "subtask1" --key "difficulty"`
- **NEW**: `todoit item property list --list "project" --item "task1" --subitem "subtask1"`
- **NEW**: `todoit item property delete --list "project" --item "task1" --subitem "subtask1" --key "difficulty"`

#### 🔧 Manager API Enhancements
- **ENHANCED**: `set_item_property()` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `get_item_property()` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `get_item_properties()` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `delete_item_property()` - Added optional `parent_item_key` parameter for subitem support

#### 🌐 MCP Tools Enhancements
- **ENHANCED**: `todo_set_item_property` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `todo_get_item_property` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `todo_get_item_properties` - Added optional `parent_item_key` parameter for subitem support
- **ENHANCED**: `todo_delete_item_property` - Added optional `parent_item_key` parameter for subitem support

#### 📚 Documentation Updates
- **UPDATED**: CLI Guide with subitem property examples
- **UPDATED**: MCP Tools documentation with subitem property usage
- **ADDED**: Comprehensive examples for both CLI and MCP interfaces

#### 🔍 Bug Fixed
- **FIXED**: Property listing now correctly shows both main item and subitem properties in unified view
- **FIXED**: `todoit item property list --list "project"` now displays all properties including subitems

#### Technical Implementation
- **File Changed**: `core/manager.py` - Extended property methods with parent_item_key support
- **File Changed**: `interfaces/cli_modules/property_commands.py` - Added --subitem option to all commands
- **File Changed**: `interfaces/mcp_server.py` - Enhanced MCP tools with subitem support
- **Backward Compatibility**: All existing property commands continue to work unchanged

## [2.5.2] - 2025-08-16

### 🔧 BUGFIX - Environment Variable Expansion
- **FIXED**: `$HOME` and other environment variables not expanded in `TODOIT_DB_PATH`
- **ADDED**: Automatic expansion of environment variables in database path
- **ENHANCED**: Better database path validation and error handling
- **IMPROVED**: SQLite connection error messages with helpful suggestions

#### Technical Details:
- **File Changed**: `core/manager.py` - added `os.path.expandvars()` for environment variable expansion
- **Root Cause**: `python-dotenv` doesn't expand variables like `$HOME` automatically
- **Solution**: Explicit expansion before database initialization

#### Now Works:
- `TODOIT_DB_PATH=$HOME/.todoit/todoit.db` ✅
- `TODOIT_DB_PATH=/home/user/.todoit/todoit.db` ✅
- `TODOIT_DB_PATH=/tmp/todoit.db` ✅

#### Error Handling:
- Directory creation with permission validation
- Clear error messages for common SQLite issues
- Helpful suggestions for path and permission problems

## [2.5.1] - 2025-08-16

### 🎨 UX IMPROVEMENT - Better Error Messages
- **IMPROVED**: Beautiful, helpful error message when database path is missing
- **ENHANCED**: Rich formatting with colors and clear instructions
- **ADDED**: Quick fix examples and migration guide link
- **REPLACED**: Raw ValueError with user-friendly SystemExit

#### Technical Details:
- **File Changed**: `core/manager.py` - enhanced error handling in TodoManager.__init__()
- **User Experience**: Clear guidance instead of cryptic traceback
- **Migration Help**: Direct links to v2.5.0 migration guide

#### Error Message Includes:
- ❌ Clear problem description
- 💡 Quick fix examples (`export TODOIT_DB_PATH=...`)
- 🔗 Parameter alternative (`--db-path`)
- 📖 Link to migration documentation

## [2.5.0] - 2025-08-16

### 🔥 BREAKING CHANGE - Database Path Management
- **REMOVED**: Default database location `~/.todoit/todoit.db`
- **ADDED**: Required database path specification via `--db-path` or `TODOIT_DB_PATH`
- **RENAMED**: Environment variable from `TODOIT_DATABASE` to `TODOIT_DB_PATH`
- **RENAMED**: CLI parameter from `--db` to `--db-path`
- **ENHANCED**: Explicit database path requirement prevents accidental production access
- **IMPROVED**: Clear priority: `--db-path` > `TODOIT_DB_PATH` > error

#### Migration Guide:
- **Before**: `todoit list all` (used `~/.todoit/todoit.db`)
- **After**: `TODOIT_DB_PATH=/path/to/db todoit list all` or `todoit --db-path /path/to/db list all`

#### Technical Details:
- **Files Changed**: 
  - `core/manager.py` - removed default path logic, added environment variable check
  - `interfaces/cli.py` - renamed parameter, removed default handling
- **Documentation Updated**: All references to default database path removed
- **Environment**: Added `.env` files with `TODOIT_DB_PATH=/tmp/test_todoit.db`

#### Benefits:
- **Security**: No accidental production database access
- **Explicit**: Clear database path requirement
- **Flexible**: Environment variable or parameter support
- **Consistent**: Uniform naming convention across CLI and env vars

## [2.4.2] - 2025-08-16

### 🔧 CLI IMPROVEMENT - Command Redundancy Fix
- **FIXED**: Redundant command syntax in property management
- **RENAMED**: `todoit list property list` → `todoit list property show`
- **IMPROVED**: Cleaner command structure eliminates confusion
- **ENHANCED**: Better CLI ergonomics for property operations

#### Technical Details:
- **File Changed**: `interfaces/cli_modules/property_commands.py` line 68
- **Before**: `@list_property_group.command("list")`
- **After**: `@list_property_group.command("show")`
- **Impact**: Property commands now have consistent, non-redundant naming

#### Benefits:
- **Clarity**: Eliminates confusing double "list" in command syntax
- **Consistency**: Aligns with other CLI patterns using "show" for display operations
- **Usability**: Reduces cognitive load when using property commands
- **Professional**: More polished command interface

## [2.4.1] - 2025-08-16

### 🎨 UI IMPROVEMENT - Enhanced Table Formatting
- **IMPROVED**: Cleaner subtask display in list show command
- **REMOVED**: Tree symbols (└─) from task titles for better readability
- **ENHANCED**: Consistent indentation in both Key and Task columns
- **SIMPLIFIED**: Visual hierarchy without cluttered symbols

#### Visual Changes:
- **Key Column**: Subtasks now use clean indentation instead of tree symbols
- **Task Column**: Removed unnecessary tree prefixes, improved alignment
- **Hierarchy**: Maintained clear parent-child relationships with simple spacing
- **Readability**: Significantly improved table clarity and visual appeal

#### Technical Details:
- **File Changed**: `interfaces/cli_modules/display.py` lines 463, 514-515
- **Impact**: All `list show` commands now display with improved formatting
- **Compatibility**: Fully backward compatible, only visual improvements

### Benefits:
- **Cleaner Look**: Reduced visual noise in table output
- **Better Scanning**: Easier to read hierarchical task structures
- **Professional Appearance**: More polished CLI interface
- **Consistency**: Uniform indentation across all columns

## [2.4.0] - 2025-08-16

### 🔧 BUGFIX - MCP Server Environment Variable Support
- **FIXED**: Critical bug in MCP server where `TODOIT_DATABASE` environment variable was ignored
- **UPDATED**: `init_manager()` function now properly respects environment variable settings
- **RESOLVED**: MCP validation errors caused by using wrong database with old 'linked' types
- **ENHANCED**: MCP server now works correctly in isolated test environments

#### Technical Details:
- **File Changed**: `interfaces/mcp_server.py` lines 19-28
- **Root Cause**: MCP server always used default `~/.todoit/todoit.db` regardless of environment
- **Solution**: Check `TODOIT_DATABASE` environment variable before creating TodoManager instance
- **Impact**: All 54 MCP tools now work correctly in test environments

### 🧪 TESTING IMPROVEMENTS
- **ADDED**: Comprehensive E2E test for MCP server (`test_e2e_mcp_comprehensive.py`)
- **TESTED**: All 54 discovered MCP tools systematically
- **VERIFIED**: Complete MCP workflow including dependencies, properties, tags, and advanced operations
- **ACHIEVED**: Robust testing coverage for entire MCP interface

#### New Test Coverage:
- **Project Lifecycle**: Full workflow from list creation to archive
- **System Robustness**: Error handling and edge cases
- **Data Consistency**: Business logic validation and automatic status synchronization
- **Tool Count**: 54 MCP tools discovered and tested (exceeded expected 52)

### Benefits:
- **Reliable MCP Testing**: Environment isolation now works correctly
- **Comprehensive Coverage**: All MCP functionality thoroughly tested
- **Future-Proof**: Robust test suite prevents regressions
- **Claude Code Integration**: MCP server works properly with custom database paths

## [2.3.0] - 2025-08-16

### 🔥 BREAKING CHANGES - Complete Test Suite Fix (100% Pass Rate)
- **FIXED**: All remaining test failures after parallel/hierarchical/linked removal
- **UPDATED**: 80+ test files to work with simplified sequential-only architecture
- **REMOVED**: Obsolete tests for removed functionality (sync_add, list relations)
- **ACHIEVED**: Perfect 612/612 tests passing (100% success rate)

#### Test Fixes Applied:
- **Models Tests**: Removed RelationType enum references
- **MCP Tools**: Updated expected tool count from 56 to 52 tools
- **Schema Tests**: Updated to expect 4 categories instead of 5
- **Archive Tests**: Fixed parent_list_id AttributeError issues
- **E2E Workflow**: Removed --tree option usage throughout
- **Dependency Graph**: Updated to return empty results for removed functionality
- **Emoji Mapping**: Removed type column (🔀) references from expectations
- **Integration Tests**: Converted all --tree usage to standard list view
- **Subtask Positioning**: Fixed hierarchy display testing

#### Core System Improvements:
- **Simplified Manager**: Removed get_cross_list_progress and get_dependency_graph complexity
- **Clean MCP Interface**: All 52 tools working perfectly with sequential lists
- **Stable Database**: No more parent_list_id or relation table dependencies
- **Reliable CLI**: All commands work without tree/hierarchy options

### Benefits:
- **Development Confidence**: 100% test pass rate ensures system reliability
- **Simplified Codebase**: Easier maintenance without complex relation logic
- **Clean Architecture**: Focus on core functionality without unused features
- **Future-Proof**: Solid foundation for new feature development

## [2.2.0] - 2025-08-16

### ✨ Feature Enhancement - CLI Simplification
- **REMOVED**: `--type` option from `list create` command (auto-set to sequential)
- **REMOVED**: Type column from `list all` table display (🔀 column)
- **REMOVED**: Type information from list creation success messages
- **REMOVED**: Type from list rename command output
- **UPDATED**: Schema command no longer shows obsolete relation types
- **SIMPLIFIED**: CLI interface is now cleaner and more focused

Since only sequential list type exists, displaying type information was redundant.
The CLI now focuses on actual functionality rather than implementation details.

## [2.1.1] - 2025-08-16

### 🐛 Bug Fixes
- **FIXED**: Import errors after removing list relations functionality
  - Remove orphaned imports: `ListRelation`, `RelationType` from database.py
  - Fix indentation errors in `list_commands.py` after removing tree/hierarchical code blocks
- **VERIFIED**: All CLI functionality works correctly with sequential-only list type
- **TESTED**: Complete test suite on clean database confirms stability

## [2.1.0] - 2025-08-16

### 🗑️ BREAKING CHANGES - Feature Removal

#### Removed List Types and Relations
- **REMOVED**: Parallel, hierarchical, and linked list types functionality 
- **REMOVED**: `list_relations` table and all related database operations
- **REMOVED**: `parent_list_id` column from `todo_lists` table
- **REMOVED**: MCP tools: `todo_link_list_1to1`, `todo_create_list_relation`, `todo_get_list_items_hierarchical`
- **REMOVED**: CLI command: `todoit list link`
- **REMOVED**: CLI options: `--tree` flag from list commands
- **SIMPLIFIED**: Only sequential list type is now supported
- **MIGRATION**: Database migration 005 removes deprecated schema elements

#### Code Cleanup
- **REMOVED**: All related model classes: `ListRelation`, `ListRelationCreate`, `RelationType` enum
- **REMOVED**: Database methods: `create_list_relation()`, `get_list_relations()`, `delete_list_relations()`
- **REMOVED**: Manager methods: `link_list_1to1()`, `create_list_relation()`, `get_lists_by_relation()`
- **REMOVED**: Dedicated test files for removed functionality
- **UPDATED**: Documentation to reflect simplified feature set

### 📖 Documentation Updates
- **UPDATED**: MCP tools documentation (MCP_TOOLS.md) - removed deprecated tools
- **UPDATED**: CLI guide (CLI_GUIDE.md) - removed link command documentation  
- **UPDATED**: API documentation (api.md) - simplified list type options
- **UPDATED**: Database schema documentation (database.md) - removed list_relations table
- **UPDATED**: README.md - removed hierarchical tasks from feature list

## [2.0.0] - 2025-08-16

### 🔄 BREAKING CHANGES - CLI Complete Refactoring

#### Major CLI Syntax Changes
- **NEW SYNTAX**: ALL CLI commands now use explicit switches instead of positional arguments
  - **Item Commands**: `todoit item status --list "list" --item "item" --status completed`
  - **List Commands**: `todoit list create --list "project" --title "My Project"`
  - **Dependency Commands**: `todoit dep add --dependent "frontend:ui" --required "backend:api"`
  - **Property Commands**: `todoit property set --list "project" --key "priority" --value "high"`
  - **Stats Commands**: `todoit stats progress --list "project"`
  - **I/O Commands**: `todoit io export --list "project" --file "export.md"`
  - **Tag Commands**: `todoit tag create --name "urgent" --color "red"`

#### Terminology Standardization
- **BREAKING**: Replaced all "task/subtask" terminology with "item/subitem" throughout CLI interface
- **Parameter Change**: `--content` parameter renamed to `--title` for better user experience
- **Command Updates**: All help text, error messages, and examples updated to new terminology

#### Smart Command Logic
- **Unified Commands**: Single commands now handle both items and subitems automatically
  - `item add` - Smart add based on `--subitem` parameter presence
  - `item status` - Smart status update for items or subitems
  - `item edit` - Smart edit with context detection
  - `item delete` - Smart delete with unified interface
- **Context Detection**: Commands automatically determine whether to operate on items or subitems

#### Manager API Updates
- **BREAKING**: Renamed core manager methods:
  - `add_subtask()` → `add_subitem()`
  - `get_subtasks()` → `get_subitems()`
  - `move_to_subtask()` → `move_to_subitem()`
- **Updated Documentation**: All docstrings and method descriptions use new terminology

#### Documentation Complete Overhaul
- **New Reference**: Created comprehensive `docs/REF-20250816.md` with migration guide
- **Updated CLI Guide**: All examples in `docs/CLI_GUIDE.md` converted to new syntax
- **No Backward Compatibility**: Clean break approach - old syntax no longer supported

#### Example New Syntax
```bash
# Item commands
todoit item add --list "project" --item "feature1" --title "Implement login"
todoit item add --list "project" --item "feature1" --subitem "step1" --title "Design UI"
todoit item status --list "project" --item "feature1" --status completed
todoit item list --list "project"

# List commands  
todoit list create --list "project" --title "My Project"
todoit list delete --list "old-project" --force
todoit list live --list "project" --refresh 5

# Dependencies
todoit dep add --dependent "frontend:component" --required "backend:api"
todoit dep show --item "frontend:component"

# Properties
todoit property set --list "project" --key "priority" --value "high"
todoit property list --list "project"

# Stats and I/O
todoit stats progress --list "project" --detailed
todoit io export --list "project" --file "/path/export.md"

# Tags
todoit tag create --name "urgent" --color "red"
todoit list tag add --list "project" --tag "urgent"
```

### Benefits
- **Explicit and Clear**: All parameters use descriptive switches
- **Unified Interface**: Fewer commands, more consistency
- **Better Discoverability**: Clear parameter names eliminate ambiguity
- **Consistent Terminology**: item/subitem throughout entire system
- **Smart Context**: Commands adapt based on provided parameters

### Migration Required
⚠️ **NO BACKWARD COMPATIBILITY** - All scripts and workflows must be updated to new syntax

## [1.25.3] - 2025-08-15

### Added
- **🔄 Duplicate Subtask Keys**: Enhanced subtask flexibility by allowing the same key across different parents
  - **Feature**: Subtasks can now use identical keys (e.g., `image_gen`, `image_dwn`) for different parent tasks
  - **Use Case**: Enables standardized workflows where multiple scenes/items share common subtask patterns
  - **Example**: `scene_0019` and `scene_0020` can both have `image_gen` and `image_dwn` subtasks
  - **Search Enhancement**: `todo_find_subitems_by_status` now works with generic keys like `{"image_gen":"completed","image_dwn":"pending"}`

### Technical
- **Database Schema**: Modified unique constraint from `(list_id, item_key)` to `(list_id, parent_item_id, item_key)`
- **New Function**: Added `get_item_by_key_and_parent()` for precise subtask lookup with parent context
- **Validation Logic**: Updated `add_subtask()` to check uniqueness only among siblings (same parent)
- **Backward Compatibility**: Main task keys remain unique within each list as before
- **Test Coverage**: 5 comprehensive tests covering duplicate keys, constraint validation, and search functionality

### Benefits
- **Workflow Standardization**: Common subtask patterns can be reused across different parent tasks
- **MCP Integration**: Claude Code can now use generic subtask keys in `todo_find_subitems_by_status`
- **Reduced Naming Complexity**: No need for unique prefixes like `scene_0019_image_gen`
- **Data Integrity**: Maintains all existing constraints while providing new flexibility

## [1.25.2] - 2025-08-15

### Fixed
- **📋 Property List Hierarchical Sorting**: Fixed `todoit item property list` to display properties in hierarchical order
  - **Issue**: Properties were sorted alphabetically by item_key instead of following list hierarchy
  - **Root Cause**: `get_all_items_properties()` used alphabetical sorting instead of hierarchical position
  - **Solution**: Added `item_order` tracking to maintain hierarchical sequence from `get_list_items()`
  - **Result**: Properties now display in logical task order (1,2,3...) matching list structure

### Technical
- **Enhanced Sorting Logic**: Modified `get_all_items_properties()` to use `(item_order, property_key)` for sorting
- **Maintained Structure**: Preserved alphabetical sorting of properties within each item
- **Test Coverage**: 5 new unit tests for hierarchical property sorting scenarios
- **Performance**: No performance impact - leverages existing hierarchical ordering from database

## [1.25.1] - 2025-08-15

### Fixed
- **🔢 Hierarchical Task Positioning**: Fixed sequential numbering for main tasks and subtasks
  - **Issue**: Main tasks displayed non-sequential positions (1, 9, 17, 25...) due to interleaved positioning with subtasks
  - **Root Cause**: Single global position counter caused main tasks and subtasks to compete for sequential positions
  - **Solution**: Implemented separate positioning logic - main tasks get positions 1,2,3... and subtasks get positions 1,2,3... within each parent
  - **Result**: Clean hierarchical display with main tasks numbered 1,2,3 and subtasks numbered 1.1,1.2,2.1,2.2 etc.

### Technical
- **Database Enhancement**: Enhanced `get_next_position()` to accept `parent_item_id` parameter for hierarchical positioning
- **Query Optimization**: Updated `get_list_items()` and `get_items_by_status()` with hierarchical ordering (main tasks first, then subtasks by parent)
- **Test Coverage**: 6 new unit tests + updated existing tests for new positioning behavior
- **Performance**: Independent position counters eliminate position conflicts and improve scalability

## [1.25.0] - 2025-08-15

### Fixed
- **🔧 Subtask Position Conflicts**: Fixed critical position conflicts in subtask creation
  - **Issue**: Database position conflicts caused by inconsistent positioning logic in `add_subtask()`
  - **Root Cause**: First subtask used `parent.position + 1` with shifting, subsequent subtasks used `max(subtask_positions) + 1` without shifting
  - **Solution**: Simplified positioning to always use `get_next_position()` for all subtasks
  - **Result**: Sequential positions without conflicts, reliable subtask creation and display

### Technical
- **Database Fix**: Eliminated position conflicts that could cause data integrity issues
- **Code Simplification**: Reduced complex positioning logic from 13 lines to 1 line
- **Test Coverage**: 6 new unit tests + 4 integration tests for position conflict scenarios
- **Performance**: Removed unnecessary `get_item_children()` and `shift_positions()` calls

## [1.24.0] - 2025-08-15

### Fixed
- **🔢 Hierarchical Numbering**: Fixed subtask numbering to reset per parent task
  - **Issue**: Subtasks had continuous numbering (1.2, 1.3, ..., 9.10, 9.11) instead of parent-relative (1.1, 1.2, 1.3, 9.1, 9.2)
  - **Root Cause**: Display logic used global `item.position` instead of sibling index within parent
  - **Solution**: Modified `add_item_to_table()` in `display.py` to use enumerated sibling index for subtasks
  - **Result**: Correct hierarchical numbering (Task 1: 1.1, 1.2, 1.3; Task 3: 3.1, 3.2; Task 6: 6.1)

### Technical
- **Code Changes**: Enhanced `_render_table_view()` with proper parent-relative indexing
- **Test Coverage**: 4 new unit tests + 3 integration tests for hierarchical numbering
- **Backward Compatible**: No API changes, only display logic improvement

## [1.23.0] - 2025-08-15

### Added
- **🏷️ List Rename Functionality**: Complete CLI command for renaming list keys and titles
  - **New CLI Command**: `todoit list rename <current_key> --key <new_key> --title "New Title"`
  - **Flexible Options**: Rename key only, title only, or both simultaneously
  - **Safe Operation**: Validation for unique keys, proper format, and confirmation prompts
  - **History Tracking**: Full audit trail of rename operations
  - **FORCE_TAGS Integration**: Respects environment isolation settings
  - **Rich UI**: Preview changes in tables with success confirmation

### Technical
- **New Method**: `TodoManager.rename_list()` with comprehensive validation
- **Database Update**: Uses existing `update_list()` with proper foreign key preservation
- **Test Coverage**: 11 unit tests + 13 integration tests for CLI functionality
- **Error Handling**: Comprehensive validation for all edge cases

## [1.22.0] - 2025-08-15

### Enhanced
- **🚀 CLI JSON Output**: Fixed `todoit list show` to return single unified JSON instead of multiple separate JSONs in JSON mode
  - **Unified Structure**: Combined `list_info`, `items`, and `properties` sections in one JSON response  
  - **Backward Compatible**: Table, YAML, and XML formats remain unchanged
  - **Improved Integration**: Better support for automation and API consumption

- **⚡ Enhanced MCP `todo_get_list`**: Extended with optional parameters for complete data retrieval
  - **New Parameters**: `include_items` and `include_properties` (both default to `True`)
  - **Single Call Efficiency**: Get list, items, and properties in one MCP call instead of three
  - **Flexible Usage**: Can retrieve only specific data sections as needed
  - **Backward Compatible**: Default behavior includes everything, maintaining existing workflows

### Configuration
- **🛡️ MCP Tools Reorganization**: Moved archive management tools from STANDARD to MAX level
  - **Enhanced Security**: `todo_archive_list` and `todo_unarchive_list` now require MAX level
  - **Updated Counts**: STANDARD level now has 24 tools (down from 25), MAX level has 58 tools (up from 57)
  - **Better Token Efficiency**: STANDARD level now provides 59% token savings (improved from 55%)

### Documentation
- **📚 Updated MCP Tools Documentation**: Complete documentation update for enhanced `todo_get_list`
  - **New Usage Examples**: Comprehensive examples showing all parameter combinations
  - **Updated Tool Counts**: Corrected all tool level counts and performance metrics
  - **Enhanced Clarity**: Better organization and more detailed explanations

### Testing
- **🧪 Comprehensive Test Coverage**: Added robust test suites for all new functionality
  - **JSON Output Tests**: 9 test scenarios covering CLI and MCP JSON output fixes
  - **Enhanced MCP Tests**: Complete coverage of new `todo_get_list` parameter combinations
  - **Backward Compatibility**: Verified no breaking changes in existing functionality

## [1.21.0] - 2025-08-15

### Added
- **🔍 Advanced Subitem Search**: New `find_subitems_by_status()` function for workflow automation
  - **Sibling Status Conditions**: Find subitems based on status of their siblings within the same parent group
  - **Perfect for Workflows**: Automate sequential processes (e.g., find downloads when generation complete)
  - **Multiple Conditions**: All conditions must be satisfied within sibling groups (AND logic)
  - **Optimized Performance**: Single database queries with proper sorting by position
  - **Complete Integration**: Available in API, MCP tools (`todo_find_subitems_by_status`), and CLI (`todoit item find-subitems`)

### Technical Implementation
- **Database Layer**: Added `find_subitems_by_status()` method with efficient parent grouping
- **Manager Layer**: Full validation and error handling with Pydantic model conversion
- **CLI Interface**: Rich JSON parsing with comprehensive error messages and formatted output
- **MCP Interface**: Standard tool with complete metadata in responses
- **Testing**: 13 comprehensive test scenarios covering edge cases and performance

### Usage Examples
```bash
# CLI: Find downloads ready to process
todoit item find-subitems images --conditions '{"generate":"completed","download":"pending"}' --limit 5

# Python API: Development workflow automation
ready_tests = manager.find_subitems_by_status(
    "features", 
    {"design": "completed", "code": "completed", "test": "pending"},
    limit=10
)
```

## [1.20.0] - 2025-08-14

### Added
- **🔄 Automatic Status Synchronization**: Revolutionary parent-child status management system
  - **Smart Status Calculation**: Parent status automatically calculated from children (failed > all_pending > all_completed > in_progress)
  - **Manual Change Blocking**: Tasks with subtasks cannot have manually changed status - prevents inconsistencies
  - **Real-time Propagation**: Status changes propagate recursively through entire hierarchy instantly
  - **Transaction Safety**: All synchronization happens in atomic database transactions

### Technical
- **Performance Optimized**: Single SQL query per hierarchy level with covering indexes
- **Database Schema**: Added `idx_todo_items_parent_status` index for O(1) child status aggregation
- **New Methods**: `has_subtasks()`, `get_children_status_summary()`, `_sync_parent_status()`
- **Circular Protection**: Visited-set mechanism prevents infinite recursion (max 10 levels)
- **MCP Integration**: Enhanced error messages for blocked operations with `status_sync_blocked` type

### Breaking Changes
- **Status Lock**: Tasks with subtasks can no longer have manually changed status - use subtask status changes instead
- **Behavior Change**: Adding first subtask to completed task changes parent to pending automatically

### Tests
- **Comprehensive Coverage**: 10 new test scenarios covering all synchronization edge cases
- **Performance Tested**: Verified with 100+ subtasks, completes in <5 seconds
- **Integration Updated**: All existing tests adapted to new status synchronization behavior

## [1.19.4] - 2025-08-13

### Added 
- **🎯 Readable JSON Field Names**: Emoji symbols in CLI headers now map to human-readable field names in JSON/YAML/XML output
  - **Better API Usability**: `🏷️` → `tags`, `📋` → `pending_count`, `✅` → `completed_count`, etc.
  - **Script-Friendly**: JSON output now parseable without dealing with emoji characters
  - **Backward Compatible**: Table output still uses emoji for visual appeal

### Technical
- **Emoji Mapping System**: Added `EMOJI_TO_NAME_MAPPING` in display module
- **Unified Serialization**: Enhanced `_prepare_data_for_serialization()` to map emoji keys
- **Test Coverage**: Added comprehensive integration tests for emoji mapping functionality
- **Property Command Fix**: Standardized JSON output format for `item property list` command

## [1.19.3] - 2025-08-13

### Added
- **🆕 Item Limit Parameter**: Added optional `limit` parameter to `todo_get_all_items_properties`
  - **Performance Optimization**: Limit number of items processed for large lists
  - **Flexible Querying**: Works with status filters - limit applies to items, not properties
  - **Backward Compatible**: Optional parameter - existing code continues to work unchanged

### Technical
- **Core Manager Enhancement**: Updated `get_all_items_properties()` to accept `limit` parameter
- **MCP Interface Update**: Added `limit` parameter to MCP tool `todo_get_all_items_properties`
- **Test Coverage**: Added comprehensive unit and integration tests for limit functionality

## [1.19.2] - 2025-08-13

### Changed
- **🔧 Unified JSON Format**: Fixed MCP `todo_get_all_items_properties` to match CLI JSON format
  - **Consistent Output**: MCP now returns same grouped format as CLI: `{"item_key": {"prop": "value"}}`
  - **Clean Response**: Removed wrapper metadata, returns direct property data
  - **Better Integration**: MCP and CLI now provide identical JSON structure for property data

### Technical
- **MCP Server Enhancement**: Updated `todo_get_all_items_properties` to group properties by item_key
- **Simplified Response**: MCP returns grouped data directly without success/count metadata wrapper

## [1.19.1] - 2025-08-13

### Changed
- **🔧 Enhanced JSON Output Format**: Improved `todoit item property list` JSON output for better usability
  - **Grouped Format**: JSON now groups properties by item_key: `{"item_key": {"prop": "value"}}`
  - **Cleaner Structure**: Eliminates verbose table-style format in JSON output
  - **Better Integration**: Simplified structure ideal for external tool integration and scripting
  - **Backward Compatibility**: Table, tree, YAML, and XML formats remain unchanged
  - **Comprehensive Testing**: 7 integration tests covering all output formats and edge cases

### Technical
- **Enhanced CLI Logic**: Added output format detection to property list command
- **Improved User Experience**: JSON output now directly usable without data transformation
- **Test Coverage**: Added comprehensive test suite for new JSON format behavior

### Use Cases
- **API Integration**: Direct consumption of item properties without parsing table structures
- **Scripting**: Simplified property access for automation scripts
- **Data Export**: Clean JSON format for external processing tools

## [1.19.0] - 2025-08-13

### Added
- **📊 Bulk Property Analysis**: New comprehensive tool for retrieving all properties across items with status filtering
  - **Core Function**: `get_all_items_properties(list_key, status=None)` with optional status filter (`pending`, `in_progress`, `completed`, `failed`)
  - **MCP Tool**: `todo_get_all_items_properties` added to **STANDARD** tool set (25 tools total)
  - **Enhanced Response**: Includes property data with status, count, and unique items metadata
  - **Multi-Criteria Filtering**: Enables complex property analysis that single-property search cannot handle
  - **Status-Based Filtering**: Filter properties by item status for targeted analysis
  - **Comprehensive Testing**: 10 integration tests covering all scenarios and edge cases

### Technical
- **Database Optimization**: Leverages existing indexes for efficient property queries
- **Tool Count Update**: STANDARD level now includes 25 tools (was 24), MAX level 57 tools total
- **Documentation**: Updated MCP_TOOLS.md with new tool examples and usage patterns
- **Test Coverage**: Added comprehensive integration test suite for new functionality

### Use Cases
- **Complex Property Analysis**: Find items matching multiple property criteria (e.g., `image_downloaded=pending` AND `image_generated=completed`)
- **Status-Based Property Retrieval**: Get properties only for items in specific status states
- **Bulk Data Export**: Retrieve all properties for external processing and analysis
- **Multi-Property Workflows**: Enable sophisticated filtering logic in client applications

## [1.18.1] - 2025-08-12

### Changed
- **🔧 API Simplification**: Removed redundant `todo_find_item_by_property` MCP tool
  - **Unified Interface**: Use `todo_find_items_by_property` with `limit=1` for single results
  - **Better Design**: One function with optional parameters > multiple functions
  - **Cleaner API**: Reduced from 57 to 56 total MCP tools
  - **Updated Examples**: Documentation shows `limit=1` usage instead of separate function
  - **Backward Compatibility**: All functionality preserved with cleaner interface

### Technical
- **Code Reduction**: Removed ~126 lines of redundant code
- **Test Updates**: Integrated tests now use unified approach
- **Documentation**: Updated MCP_TOOLS.md with simplified examples

## [1.18.0] - 2025-08-12

### Added
- **🔍 Property-Based Item Search**: New comprehensive search functionality for finding items by custom properties
  - **Database Layer**: `find_items_by_property()` function with optimized SQL JOIN queries and optional LIMIT support
  - **Core Manager**: `find_items_by_property()` business logic function
  - **CLI Command**: `todoit item find` with options: `--property`, `--value`, `--limit`, `--first`
  - **MCP Tools**: `todo_find_items_by_property` for external integration
  - **Standard MCP Integration**: Added `todo_find_items_by_property` to basic MCP tool set (~20 essential tools)
  - **Performance Optimization**: Added composite database index `idx_item_properties_key_value` for fast property searches
  - **JSON Output Support**: Full support for `TODOIT_OUTPUT_FORMAT` environment variable (JSON/YAML/XML)
  - **Comprehensive Testing**: 29 unit and integration tests covering all search scenarios and edge cases

### Performance
- **Database Indexing**: Added optimized composite index on `item_properties(property_key, property_value)` for efficient search queries
- **Query Optimization**: SQL JOIN implementation with position-based ordering and configurable result limits

## [1.17.0] - 2025-08-12

### Added
- **🚀 Complete JSON Output Support**: All CLI commands now support unified output formats
  - **New Format Support**: Added JSON, YAML, XML output formats to all remaining commands
  - **Commands Updated**: `item tree`, `dep show`, `schema`, `dep graph` now support `TODOIT_OUTPUT_FORMAT`
  - **Unified Display System**: Migrated all commands to consistent display system for better format support
  - **Rich Documentation**: Added comprehensive output format documentation to README.md

### Fixed
- **🔧 Advanced Command JSON Output**: Enhanced JSON support for complex display commands
  - **Item Tree**: `todoit item tree` - Hierarchical task display with proper JSON serialization
  - **Dependency Show**: `todoit dep show` - Structured dependency analysis in all formats
  - **System Schema**: `todoit schema` - System information with categorized output
  - **Dependency Graph**: `todoit dep graph` - Project dependency visualization
  - **Enhanced Testing**: Added 41 comprehensive integration tests for all new JSON output features
  - **Backward Compatible**: All existing table format behavior preserved

### Changed
- **📋 Display System Improvements**: Enhanced unified display architecture
  - **Consistent Structure**: All commands now use standardized data formatting
  - **Format Detection**: Automatic format switching based on `TODOIT_OUTPUT_FORMAT` environment variable
  - **Error Handling**: Improved error handling for malformed references and edge cases

## [1.16.6] - 2025-08-12

### Fixed
- **🔧 JSON Output Support for Property Commands**: Fixed `TODOIT_OUTPUT_FORMAT=json` support for property list commands
  - **List Properties**: `todoit list property list` now properly supports JSON, YAML, XML output formats
  - **Item Properties**: `todoit item property list` (both single item and all items) now supports all output formats
  - **Unified Display**: Migrated property commands to use unified display system for consistent formatting
  - **Comprehensive Testing**: Added 7 integration tests covering all property command scenarios and output formats
  - **Backward Compatible**: Table format (default) remains unchanged and fully functional

## [1.16.4] - 2025-08-10

### Changed
- **🎨 Improved Tag Colors**: Updated tag color palette for better visual comfort
  - **Dimmed Primary Colors**: Changed first 5 colors to `dim red`, `dim green`, `dim blue`, `dim yellow`, `dim white` for subtler appearance
  - **Balanced Final Colors**: Changed last 2 colors from `bright_green`, `bright_red` to standard `green`, `red`
  - **Enhanced Readability**: More consistent and less aggressive color scheme across all tag displays

## [1.16.3] - 2025-08-10

### Added
- **📄 List Items Pagination**: Added `limit` parameter to `todo_get_list_items` MCP tool for pagination support
  - **Enhanced Response**: Added `more_available` and `total_count` fields for pagination metadata
  - **Hierarchical Support**: Limit works with both flat and hierarchical task structures
  - **Status Filtering**: Limit parameter works in combination with status filtering
  - **Comprehensive Testing**: 17 unit tests covering all edge cases and scenarios

## [1.16.0] - 2025-08-10

### Added
- **🏷️ 12-Color Tag System**: Complete visual tag system with automatic color assignment
  - **12 Distinct Colors**: `red`, `green`, `blue`, `yellow`, `orange`, `purple`, `cyan`, `magenta`, `pink`, `grey`, `bright_green`, `bright_red`
  - **Automatic Color Assignment**: New tags automatically receive next available color in sequence (index-based)
  - **Tag Limit Enforcement**: System prevents creation of more than 12 tags to maintain visual clarity
  - **Error Messaging**: Clear error message when attempting to create 13th tag: "Maximum number of tags reached (12). Cannot create more tags with distinct colors."

### Changed
- **🎨 Enhanced CLI Display**: Added tags column (🏷️) to `list all` commands showing colored dots
  - **Tags Legend**: Automatic legend displays below tables showing all used tags with colors
  - **Visual Recognition**: Tags appear as colored dots (●) for immediate identification
  - **Consistent Ordering**: Tags displayed alphabetically for predictable organization
- **🔧 Improved Tag Creation**: Default tag creation now uses automatic color assignment instead of always defaulting to blue
  - **CLI**: `todoit tag create <name>` automatically assigns next available color
  - **MCP**: `todo_create_tag` with no color parameter uses automatic assignment
  - **Override**: Explicit color specification still available and overrides auto-assignment

### Fixed
- **🐛 Rich Color Display**: Fixed colored tag dots not displaying correctly in CLI
  - **Issue**: Tags showed as plain text "● blue" instead of colored dots
  - **Solution**: Removed special case handling for blue color, added underscore support to color validation regex
  - **Result**: All 12 colors now display properly with Rich formatting
- **✅ Test Compatibility**: Updated integration tests to handle new table format with tags column
  - **Issue**: Archive CLI tests failing due to changed table structure after adding 🏷️ column
  - **Solution**: Modified test assertions to handle multi-line table entries and truncated names
  - **Coverage**: All archive workflow tests now pass with new display format

### Technical Details
- **Model Validation**: Updated `ListTag` color field regex to accept underscores for `bright_green`/`bright_red`
- **Automatic Color Logic**: Implemented index-based color assignment in `_get_next_available_color()` method
- **Display System**: Added tag retrieval and formatting logic to list display components
- **Database**: No schema changes required - existing tag system extended with color management
- **Performance**: O(1) color assignment based on tag count, efficient legend generation

### Developer Impact
- **11 New Unit Tests**: Comprehensive test suite for tag color system including edge cases
- **Documentation Updated**: MCP_TOOLS.md includes new tag system documentation with examples
- **Backward Compatibility**: Existing tags retain their colors, no migration needed
- **API Consistency**: All MCP tools include color information in tag responses

### User Benefits
- **Visual Clarity**: Easy tag identification with 12 distinct, visually optimized colors
- **Zero Configuration**: Automatic color management requires no user intervention  
- **Predictable Workflow**: Consistent color assignment and display across all interfaces
- **Professional Appearance**: Clean, organized tag display with legend support

## [1.15.2] - 2025-08-10

### Changed
- **📋 Improved List Sorting**: Changed default list sorting from ID to alphabetical by list key
  - **CLI Tables**: All `todoit list all` commands now show lists sorted alphabetically by list key
  - **MCP Tools**: `todo_list_all` and related MCP tools return lists in alphabetical order by key
  - **Tree View**: Hierarchical list displays also use alphabetical sorting
  - **Consistency**: Both CLI and MCP interfaces now use the same predictable sorting order

### Technical Details
- **Database Layer**: Modified `get_all_lists()` and `get_lists_by_tags()` to use `ORDER BY list_key ASC`
- **CLI Layer**: Updated sorting logic from `key=lambda x: x.id` to `key=lambda x: x.list_key`
- **Display Layer**: Tree views and all list displays now consistently use alphabetical sorting
- **Backward Compatibility**: No breaking changes, only improved user experience

### User Impact
- **Before**: Lists displayed in creation order (ID-based): `zebra`, `alpha`, `beta` (IDs: 1, 2, 3)
- **After**: Lists displayed alphabetically: `alpha`, `beta`, `zebra` (more intuitive ordering)
- **Benefit**: Easier to find lists in large projects with many lists

## [1.15.1] - 2025-08-10

### Fixed
- **🐛 Critical Fix: List deletion with tags** - Fixed FOREIGN KEY constraint error when deleting lists with tags
  - **Issue**: `todoit list delete` command failed with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`
  - **Root Cause**: Missing cleanup of `ListTagAssignmentDB` records before list deletion
  - **Solution**: Added proper tag assignment cleanup in `delete_list()` method
  - **Impact**: All lists with tags can now be deleted successfully via CLI and MCP tools

### Added
- **🧪 Comprehensive Test Coverage**: New unit tests for list deletion scenarios with tags
  - `tests/unit/test_delete_list_with_tags.py` - 5 test cases covering all tag deletion scenarios
  - Tests single tag, multiple tags, complex data combinations, and CLI reproduction scenarios
  - Ensures future regression prevention for tag-related list operations

### Technical Details
- **File Modified**: `core/manager.py:193` - Added `ListTagAssignmentDB` cleanup
- **Test Coverage**: 393 tests passing (5 new tests added)
- **Backward Compatibility**: No breaking changes, existing functionality preserved

## [1.15.0] - 2025-08-10

### Added
- **🎛️ MCP Tools Level Configuration System**: New 3-level system to optimize token usage and performance
  - **MINIMAL** (10 tools): Essential operations only, 82% token savings
  - **STANDARD** (23 tools): Balanced functionality, 58% token savings (new default)
  - **MAX** (55 tools): Complete feature set (previous behavior)
- **Environment Variable Configuration**: `TODOIT_MCP_TOOLS_LEVEL` controls available tools
- **Conditional Tool Registration**: New `@conditional_tool` decorator for dynamic tool loading
- **Security Benefits**: MINIMAL and STANDARD levels exclude destructive operations (`delete_list`, `delete_item`)
- **Comprehensive Documentation**: Updated MCP_TOOLS.md with detailed level breakdowns and performance metrics

### Changed
- **Default MCP Level**: Changed from MAX (55 tools) to STANDARD (23 tools) for better performance
- **MCP Server Architecture**: Reorganized tools by level categories for better maintainability
- **Test Coverage**: Added comprehensive unit tests for all tool levels

### Fixed
- **List Linking CLI**: Fixed issue where linked lists weren't visible due to tag filtering
- **Test Environment Isolation**: Fixed integration tests failing due to FORCE_TAGS conflicts
- **MCP Tools Count Test**: Updated to work with new conditional tool system

### Technical Details
- **Token Context Reduction**: 58-82% reduction in MCP context tokens depending on level
- **Performance Impact**: ~500-1000 tokens (MINIMAL) vs 3000+ tokens (MAX)
- **Backward Compatibility**: Existing configurations work unchanged (defaults to STANDARD)
- **Tool Categories**: Organized into Basic Operations, Advanced, Subtasks, Dependencies, Smart Algorithms, Tags, Reports

### Migration Guide
- **No action required**: Existing setups automatically get STANDARD level (23 tools)
- **For maximum features**: Set `TODOIT_MCP_TOOLS_LEVEL=MAX` (previous behavior)
- **For minimal setup**: Set `TODOIT_MCP_TOOLS_LEVEL=MINIMAL` (10 essential tools)

## [1.14.3] - 2025-08-09

### Added
- Complete comprehensive environment isolation with FORCE_TAGS across all CLI commands

### Fixed
- FORCE_TAGS environment isolation for all list and item commands
- Unit tests for flag_value status command solution

## [1.14.2] - 2025-08-09

### Fixed  
- FORCE_TAGS environment isolation for all item commands
- Add FORCE_TAGS environment isolation to all list commands

## [1.14.1] - Previous releases

### Features
- 55 comprehensive MCP tools for Claude Code integration
- Smart task selection algorithms with subtask prioritization  
- Cross-list dependency management
- Hierarchical task organization with subtasks
- List linking with 1:1 task mapping
- Archive management with completion validation
- Tag-based organization and filtering
- Comprehensive progress tracking and analytics
- Import/export functionality (Markdown support)
- Advanced properties system for lists and items
- Real-time monitoring and live updates
- Comprehensive error reporting and analytics

[1.15.0]: https://github.com/todoit/todoit-mcp/compare/v1.14.3...v1.15.0
[1.14.3]: https://github.com/todoit/todoit-mcp/compare/v1.14.2...v1.14.3
[1.14.2]: https://github.com/todoit/todoit-mcp/compare/v1.14.1...v1.14.2