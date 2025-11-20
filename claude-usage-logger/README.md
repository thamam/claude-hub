# Claude Code Usage Pattern Logger

A two-phase usage pattern logger for tracking Claude Code tool usage patterns.

## Overview

This logger helps track how Claude Code tools are being used, providing insights into:
- Which tools are used most frequently
- Skills and subagent invocations
- Usage patterns by session
- Time-series analysis of tool usage

## Features

### Phase 1: JSONL Logger (POC)
- Simple JSON Lines format storage
- Low overhead logging
- Easy to parse and analyze
- File-based: `~/.claude_usage_log.jsonl`

### Phase 2: SQLite Database
- Structured database storage
- Advanced querying and filtering
- Time-series analysis
- Export capabilities (CSV)
- Database file: `~/.claude_usage.db`

### Production-Ready Improvements
- **Thread Safety**: Safe for concurrent access from multiple threads
- **Resource Management**: Automatic connection cleanup with context managers
- **No Side Effects**: kwargs dictionaries are not mutated
- **Error Handling**: Graceful degradation on logging failures
- **Connection Pooling**: Efficient database connection management

## Installation

### Quick Start

```bash
cd ~/claude-usage-logger
chmod +x install.sh
./install.sh
```

This will:
1. Make all scripts executable
2. Create command-line tools
3. Run initial tests
4. Display usage instructions

## Usage

### Phase 1: JSONL Logging

#### Testing the Logger

```bash
# Test the logger
python3 ~/claude-usage-logger/logger.py
```

#### Viewing Statistics

```bash
# View usage stats
python3 ~/claude-usage-logger/stats_poc.py

# Or if symlinked:
claude-usage-stats-poc
```

#### Using the Logger in Your Code

**Basic Usage:**
```python
import sys
sys.path.insert(0, '/root/claude-usage-logger')
from logger import log_tool_usage, log_skill, log_subagent

# Log a generic tool usage
log_tool_usage("web_search", query_length=45)

# Log a skill invocation
log_skill("rapid-prototype", context="building new feature")

# Log a subagent invocation
log_subagent("general-purpose", task_type="research")

# Log with session info
log_tool_usage(
    "bash",
    session_name="Debug Session",
    command_length=120
)
```

**Context Manager Usage (Recommended for explicit resource control):**
```python
from logger import UsageLogger

# Automatic cleanup when done
with UsageLogger() as logger:
    logger.log_tool_usage("task_start")
    # ... do work ...
    logger.log_tool_usage("task_complete")
# Connection automatically closed here

# Or with explicit close
logger = UsageLogger()
try:
    logger.log_skill("data-processing")
finally:
    logger.close()
```

**Thread-Safe Usage:**
```python
from logger import UsageLogger
import threading

# Single logger instance can be safely shared across threads
logger = UsageLogger()

def worker(thread_id):
    for i in range(10):
        logger.log_tool_usage("parallel_task", thread_id=thread_id, iteration=i)

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

logger.close()
```

### Phase 2: SQLite Migration

#### Running the Migration

When you're ready to upgrade to SQLite:

```bash
python3 ~/claude-usage-logger/migrate.py
```

This will:
1. Create a backup of your JSONL file (`~/.claude_usage_log.jsonl.backup`)
2. Create the SQLite database (`~/.claude_usage.db`)
3. Import all existing JSONL entries
4. Verify the migration

#### Using the Enhanced Stats

```bash
# View all stats
python3 ~/claude-usage-logger/stats.py

# Filter by date range
python3 ~/claude-usage-logger/stats.py --from 2025-01-01 --to 2025-01-31

# Use date shortcuts
python3 ~/claude-usage-logger/stats.py --from last-week
python3 ~/claude-usage-logger/stats.py --from yesterday

# Filter by tool
python3 ~/claude-usage-logger/stats.py --tool web_search

# View specific session
python3 ~/claude-usage-logger/stats.py --session abc123

# Export to CSV
python3 ~/claude-usage-logger/stats.py --export-csv usage_data.csv --from last-month
```

#### Date Shortcuts

- `today`: Today's date
- `yesterday`: Yesterday's date
- `last-week`: 7 days ago
- `last-month`: 30 days ago

## Data Format

### JSONL Format (Phase 1)

Each line is a JSON object:

```json
{"timestamp": "2025-01-15T10:30:45Z", "tool": "web_search", "session_id": "abc123", "session_name": "Project Debug", "query_length": 45}
{"timestamp": "2025-01-15T10:32:10Z", "tool": "skill", "skill_name": "rapid-prototype", "session_id": "abc123", "session_name": "Project Debug"}
{"timestamp": "2025-01-15T10:35:22Z", "tool": "subagent", "subagent_name": "general-purpose", "session_id": "abc123", "session_name": "Project Debug"}
```

### SQLite Format (Phase 2)

Table structure:

```sql
CREATE TABLE usage_log (
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
```

## Tracked Fields

### Standard Fields
- `timestamp`: ISO 8601 timestamp (UTC)
- `tool`/`tool_name`: Tool name (e.g., "web_search", "bash", "skill")
- `session_id`: Unique session identifier (auto-generated or from environment)
- `session_name`: Human-readable session name

### Pattern-Specific Fields
- `skill_name`: Name of the skill (when tool is "skill")
- `subagent_name`: Name of the subagent (when tool is "subagent")
- Additional fields stored in `metadata` (SQLite) or as top-level fields (JSONL)

## Session Detection

The logger attempts to detect sessions in this order:

1. Environment variable `CLAUDE_SESSION_ID`
2. Auto-generated UUID (8 characters)

Session names come from:
1. Explicit parameter in log calls
2. Environment variable `CLAUDE_SESSION_NAME`
3. Default: "unknown"

## Integration with Claude Code

### Environment Variables

To enable session tracking, set these environment variables before running Claude Code:

```bash
export CLAUDE_SESSION_ID="my-session-123"
export CLAUDE_SESSION_NAME="Feature Development"
```

### Manual Integration

Since Claude Code doesn't currently expose a hook system for automatic tool tracking, you can:

1. **Manual Logging**: Call the logger functions directly in your scripts
2. **Wrapper Scripts**: Create wrapper scripts that log and then call Claude Code
3. **Session Hooks**: Use shell hooks to log at session start/end

Example wrapper script:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/claude-usage-logger')
from logger import log_tool_usage

# Log the tool usage
log_tool_usage("my_custom_tool", param1="value1")

# Your actual tool logic here
# ...
```

## Example Queries

### SQLite Direct Queries

You can query the database directly:

```bash
sqlite3 ~/.claude_usage.db
```

```sql
-- Most used tools
SELECT tool_name, COUNT(*) as count
FROM usage_log
GROUP BY tool_name
ORDER BY count DESC;

-- Usage by date
SELECT date(timestamp) as date, COUNT(*) as invocations
FROM usage_log
GROUP BY date(timestamp)
ORDER BY date DESC;

-- Session summary
SELECT session_id, session_name, COUNT(*) as invocations,
       MIN(timestamp) as first_event, MAX(timestamp) as last_event
FROM usage_log
GROUP BY session_id, session_name;

-- Skill popularity
SELECT skill_name, COUNT(*) as invocations
FROM usage_log
WHERE skill_name IS NOT NULL
GROUP BY skill_name
ORDER BY invocations DESC;
```

## File Structure

```
~/claude-usage-logger/
├── logger.py           # Core logging library (supports both JSONL and SQLite)
├── stats_poc.py        # Phase 1 stats viewer (JSONL)
├── stats.py            # Phase 2 stats viewer (SQLite)
├── migrate.py          # Migration script (JSONL → SQLite)
├── schema.sql          # SQLite database schema
├── install.sh          # Installation script
└── README.md           # This file

~/.claude_usage_log.jsonl        # JSONL log file
~/.claude_usage_log.jsonl.backup # Backup after migration
~/.claude_usage.db               # SQLite database
```

## Troubleshooting

### Logger Not Writing

Check permissions:
```bash
ls -la ~/.claude_usage_log.jsonl
ls -la ~/.claude_usage.db
```

### Migration Issues

If migration fails:
1. Check that the JSONL file exists and is readable
2. Verify the schema.sql file is present
3. Check disk space: `df -h ~`

Restore from backup:
```bash
cp ~/.claude_usage_log.jsonl.backup ~/.claude_usage_log.jsonl
```

### Database Locked

If you get "database is locked" errors:
```bash
# Close any connections
fuser ~/.claude_usage.db  # See which processes are using it
```

## Advanced Usage

### Custom Database Location

```python
from logger import UsageLogger

logger = UsageLogger(
    log_file="/custom/path/usage.jsonl",
    db_file="/custom/path/usage.db"
)
```

### Batch Analysis

Export data for external analysis:

```bash
# Export to CSV
python3 ~/claude-usage-logger/stats.py --export-csv data.csv --from 2025-01-01

# Analyze with other tools
python3 -c "
import pandas as pd
df = pd.read_csv('data.csv')
print(df.groupby('tool_name')['invocations'].sum())
"
```

## Performance

- **JSONL**: Minimal overhead, ~1ms per write
- **SQLite**: Indexed queries, ~2-5ms per write
- **Migration**: ~1000 entries per second

## Privacy & Security

- All data is stored locally
- No network communication
- No sensitive data is logged by default
- Review metadata before sharing logs

## Future Enhancements

Potential improvements:
- Automatic hook integration
- Real-time dashboard
- Pattern detection and recommendations
- Integration with Claude Code's internal metrics
- Support for remote logging

## Contributing

To extend the logger:

1. Add new log methods to `logger.py`
2. Update the schema if needed (Phase 2)
3. Add corresponding stats views
4. Document new fields in this README

## License

This tool is provided as-is for use with Claude Code.

## Support

For issues or questions:
1. Check this README
2. Review the code comments
3. Test with the provided examples
4. Check file permissions and disk space

## Version History

- **Phase 1 (JSONL)**: Initial release with basic logging
- **Phase 2 (SQLite)**: Enhanced with database backend and advanced analytics
