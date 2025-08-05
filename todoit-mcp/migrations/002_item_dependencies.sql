-- TODOIT MCP - Phase 2: Cross-List Dependencies Migration
-- Create item_dependencies table for cross-list task dependencies

-- Cross-list item dependencies table
CREATE TABLE item_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dependent_item_id INTEGER NOT NULL REFERENCES todo_items(id) ON DELETE CASCADE,
    required_item_id INTEGER NOT NULL REFERENCES todo_items(id) ON DELETE CASCADE,
    dependency_type TEXT DEFAULT 'blocks',  -- 'blocks', 'requires', 'related'
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dependent_item_id, required_item_id)
);

-- Indexes for performance
CREATE INDEX idx_item_deps_dependent ON item_dependencies(dependent_item_id);
CREATE INDEX idx_item_deps_required ON item_dependencies(required_item_id);
CREATE INDEX idx_item_deps_type ON item_dependencies(dependency_type);

-- Prevent circular dependencies constraint (will be handled in application layer)
-- SQLite doesn't support complex constraints, so we'll validate in Python