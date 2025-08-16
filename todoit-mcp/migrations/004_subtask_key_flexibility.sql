-- TODOIT MCP v1.25.3: Enable duplicate subtask keys across different parent tasks
-- This migration allows subtasks to use identical keys for different parent tasks
-- while maintaining uniqueness constraint within each parent

-- Step 1: Drop the old unique constraint on (list_id, item_key)
DROP INDEX IF EXISTS idx_todo_items_unique_key;

-- Step 2: Create new unique constraint on (list_id, parent_item_id, item_key)
-- This allows:
-- - Same subtask keys for different parents: scene_0019/image_gen, scene_0020/image_gen
-- - Maintains uniqueness for main tasks (where parent_item_id IS NULL)
-- - Maintains uniqueness for subtasks within the same parent
CREATE UNIQUE INDEX idx_todo_items_unique_key_hierarchical 
ON todo_items (list_id, parent_item_id, item_key);

-- Step 3: Add index on parent_item_id status for performance (if not exists)
CREATE INDEX IF NOT EXISTS idx_todo_items_parent_status 
ON todo_items (parent_item_id, status);

-- Migration completed successfully
-- Benefits:
-- - Enables standardized subtask workflows (scene_gen, image_gen, image_dwn)
-- - Allows generic MCP searches with find_subitems_by_status
-- - Reduces naming complexity (no need for scene_0019_image_gen prefixes)
-- - Maintains full backward compatibility for main task uniqueness