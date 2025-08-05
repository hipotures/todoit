-- TODOIT MCP Database Schema
-- SQLite database schema for TODO list management system

-- Main table for TODO lists
CREATE TABLE todo_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_key TEXT UNIQUE NOT NULL,  -- e.g., "project_alpha", "shopping_weekly"
    title TEXT NOT NULL,
    description TEXT,
    list_type TEXT DEFAULT 'sequential',  -- 'sequential', 'parallel', 'hierarchical'
    parent_list_id INTEGER REFERENCES todo_lists(id),
    metadata JSON DEFAULT '{}',  -- additional data like project_id, tags, priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual tasks/items
CREATE TABLE todo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL REFERENCES todo_lists(id) ON DELETE CASCADE,
    item_key TEXT NOT NULL,  -- local key within the list
    content TEXT NOT NULL,
    position INTEGER NOT NULL,  -- order in the list
    status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    completion_states JSON DEFAULT '{}',  -- for multi-state like {"tested": true, "deployed": false}
    parent_item_id INTEGER REFERENCES todo_items(id),
    metadata JSON DEFAULT '{}',  -- e.g., assignee, due_date, priority, tags
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(list_id, item_key)
);

-- Relations between lists
CREATE TABLE list_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_list_id INTEGER NOT NULL REFERENCES todo_lists(id) ON DELETE CASCADE,
    target_list_id INTEGER NOT NULL REFERENCES todo_lists(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,  -- 'dependency', 'parent', 'related'
    relation_key TEXT,  -- e.g., project_id, sprint_id
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_list_id, target_list_id, relation_type)
);

-- Change history (audit log)
CREATE TABLE todo_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES todo_items(id) ON DELETE CASCADE,
    list_id INTEGER REFERENCES todo_lists(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- 'created', 'updated', 'completed', 'failed'
    old_value JSON,
    new_value JSON,
    user_context TEXT DEFAULT 'system',  -- e.g., 'claude_code', 'manual', 'automation'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_todo_lists_list_key ON todo_lists(list_key);
CREATE INDEX idx_todo_lists_parent ON todo_lists(parent_list_id);
CREATE INDEX idx_todo_items_list_id ON todo_items(list_id);
CREATE INDEX idx_todo_items_status ON todo_items(status);
CREATE INDEX idx_todo_items_position ON todo_items(list_id, position);
CREATE INDEX idx_todo_items_parent ON todo_items(parent_item_id);
CREATE INDEX idx_list_relations_source ON list_relations(source_list_id);
CREATE INDEX idx_list_relations_target ON list_relations(target_list_id);
CREATE INDEX idx_todo_history_item ON todo_history(item_id);
CREATE INDEX idx_todo_history_list ON todo_history(list_id);
CREATE INDEX idx_todo_history_timestamp ON todo_history(timestamp);

-- Triggers for updated_at timestamps
CREATE TRIGGER update_todo_lists_timestamp 
    AFTER UPDATE ON todo_lists
    FOR EACH ROW
    BEGIN
        UPDATE todo_lists SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_todo_items_timestamp 
    AFTER UPDATE ON todo_items
    FOR EACH ROW
    BEGIN
        UPDATE todo_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Table: list_properties (key-value storage for lists)
CREATE TABLE list_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    property_key TEXT NOT NULL,
    property_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (list_id) REFERENCES todo_lists (id) ON DELETE CASCADE,
    UNIQUE(list_id, property_key)
);

-- Index for faster property lookups
CREATE INDEX idx_list_properties_list_id ON list_properties(list_id);
CREATE INDEX idx_list_properties_key ON list_properties(property_key);

-- Trigger to update timestamp on list_properties changes
CREATE TRIGGER update_list_properties_timestamp 
    AFTER UPDATE ON list_properties
    FOR EACH ROW
    BEGIN
        UPDATE list_properties SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;