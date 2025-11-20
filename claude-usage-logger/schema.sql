-- Claude Code Usage Pattern Logger - SQLite Schema
-- Phase 2: Database schema for usage tracking

CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    session_id TEXT,
    session_name TEXT,
    skill_name TEXT,
    subagent_name TEXT,
    metadata TEXT,  -- JSON blob for additional context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_tool ON usage_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_session ON usage_log(session_id);
CREATE INDEX IF NOT EXISTS idx_skill ON usage_log(skill_name);
CREATE INDEX IF NOT EXISTS idx_subagent ON usage_log(subagent_name);
CREATE INDEX IF NOT EXISTS idx_created_at ON usage_log(created_at);

-- View for quick session summaries
CREATE VIEW IF NOT EXISTS session_summary AS
SELECT
    session_id,
    session_name,
    COUNT(*) as total_invocations,
    COUNT(DISTINCT tool_name) as unique_tools,
    MIN(timestamp) as first_event,
    MAX(timestamp) as last_event
FROM usage_log
GROUP BY session_id, session_name
ORDER BY last_event DESC;

-- View for tool popularity
CREATE VIEW IF NOT EXISTS tool_popularity AS
SELECT
    tool_name,
    COUNT(*) as invocations,
    COUNT(DISTINCT session_id) as sessions_used
FROM usage_log
GROUP BY tool_name
ORDER BY invocations DESC;

-- View for skill usage
CREATE VIEW IF NOT EXISTS skill_usage AS
SELECT
    skill_name,
    COUNT(*) as invocations,
    COUNT(DISTINCT session_id) as sessions_used
FROM usage_log
WHERE skill_name IS NOT NULL
GROUP BY skill_name
ORDER BY invocations DESC;

-- View for subagent usage
CREATE VIEW IF NOT EXISTS subagent_usage AS
SELECT
    subagent_name,
    COUNT(*) as invocations,
    COUNT(DISTINCT session_id) as sessions_used
FROM usage_log
WHERE subagent_name IS NOT NULL
GROUP BY subagent_name
ORDER BY invocations DESC;
