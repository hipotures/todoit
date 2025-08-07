-- Migration: Add status column to todo_lists table
-- Date: 2025-08-08
-- Description: Add status column to support list archiving functionality

-- Add status column with default 'active'
ALTER TABLE todo_lists ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Update existing records to have 'active' status
UPDATE todo_lists SET status = 'active' WHERE status IS NULL;

-- Add index on status column for performance
CREATE INDEX idx_todo_lists_status ON todo_lists(status);

-- Add combined index for filtering by status and other common queries
CREATE INDEX idx_todo_lists_status_created ON todo_lists(status, created_at);