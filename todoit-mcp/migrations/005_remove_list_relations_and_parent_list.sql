-- Migration 005: Remove list relations and parent_list_id functionality
-- This migration removes support for parallel, hierarchical, and linked list types
-- Date: 2024-XX-XX

-- Drop list_relations table entirely
DROP TABLE IF EXISTS list_relations;

-- Remove parent_list_id column from todo_lists table
-- Note: This is a destructive operation that will lose hierarchical list data
ALTER TABLE todo_lists DROP COLUMN IF EXISTS parent_list_id;

-- Drop related indexes
DROP INDEX IF EXISTS idx_todo_lists_parent;
DROP INDEX IF EXISTS idx_list_relations_source;
DROP INDEX IF EXISTS idx_list_relations_target;
DROP INDEX IF EXISTS idx_list_relations_unique;

-- Update any lists that have non-sequential types to sequential
UPDATE todo_lists 
SET list_type = 'sequential' 
WHERE list_type IN ('parallel', 'hierarchical', 'linked');