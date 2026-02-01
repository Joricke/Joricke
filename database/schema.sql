-- Research Chat System — Database Schema
-- This file documents the database structure.
-- The schema is automatically created by database.py on first run.

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     TEXT NOT NULL,           -- UUID grouping messages in one conversation
    student_id  TEXT NOT NULL,           -- Pseudonymised student identifier (e.g. S001)
    task_id     TEXT DEFAULT '',         -- Optional task/assignment identifier
    role        TEXT NOT NULL            -- 'user', 'assistant', or 'system'
                CHECK (role IN ('user', 'assistant', 'system')),
    message     TEXT NOT NULL,           -- The message content
    model       TEXT DEFAULT '',         -- LLM model used (e.g. claude-sonnet-4-20250514)
    provider    TEXT DEFAULT '',         -- LLM provider (openai / anthropic)
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indices for common query patterns
CREATE INDEX IF NOT EXISTS idx_messages_chat_id    ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_student_id ON messages(student_id);
CREATE INDEX IF NOT EXISTS idx_messages_task_id    ON messages(task_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp  ON messages(timestamp);
