# Changelog

All notable changes to the Claude Code Usage Pattern Logger.

## [1.1.0] - Code Review Improvements

### Added
- **Thread Safety**: Added threading locks to ensure safe concurrent access
  - Both JSONL and SQLite backends now support multi-threaded logging
  - Tested with 10 concurrent threads logging simultaneously

- **Context Manager Support**: Logger now supports `with` statement
  ```python
  with UsageLogger() as logger:
      logger.log_tool_usage("task")
  # Connection automatically closed
  ```

- **Resource Management**: Automatic cleanup of database connections
  - `__enter__` and `__exit__` methods for context manager protocol
  - `__del__` method for cleanup on object deletion
  - `atexit` registration for cleanup on program exit
  - Explicit `close()` method for manual cleanup

- **Test Suite**: Comprehensive test coverage for improvements
  - Context manager functionality
  - Thread safety verification
  - Resource cleanup testing
  - kwargs immutability verification
  - Concurrent access patterns

### Fixed
- **kwargs Mutation**: Changed from `kwargs.pop()` to `kwargs.get()`
  - Prevents unexpected side effects on caller's dictionaries
  - Preserves original kwargs for caller inspection

- **Connection Leak**: SQLite connections now properly closed
  - Automatic cleanup on context exit
  - Cleanup on object deletion
  - Protection against multiple close calls

- **Thread Safety Issues**: Added locks around critical sections
  - File writes protected with lock
  - Database operations protected with lock
  - Prevents race conditions and data corruption

### Changed
- **SQLite Connection**: Added connection parameters for better reliability
  - `check_same_thread=False`: Allow cross-thread usage
  - `timeout=10.0`: Wait up to 10 seconds if database locked

- **Error Handling**: Added connection state validation
  - Raises `RuntimeError` if attempting to use closed connection
  - Better error messages for debugging

### Technical Details

**Before (Issues):**
```python
# Issue 1: Connection never closed
logger = UsageLogger()
logger.log_tool_usage("tool")
# Connection leaked!

# Issue 2: kwargs mutated
metadata = {"skill_name": "test", "custom": "value"}
logger.log_tool_usage("tool", **metadata)
# metadata was modified by pop()!

# Issue 3: Not thread-safe
# Multiple threads could corrupt data
```

**After (Fixed):**
```python
# Fix 1: Proper cleanup
with UsageLogger() as logger:
    logger.log_tool_usage("tool")
# Connection automatically closed

# Fix 2: kwargs preserved
metadata = {"skill_name": "test", "custom": "value"}
logger.log_tool_usage("tool", **metadata)
# metadata unchanged!

# Fix 3: Thread-safe
logger = UsageLogger()
# Safe to use from multiple threads
threads = [Thread(target=logger.log_tool_usage, args=("tool",)) for _ in range(10)]
```

### Testing
All improvements verified with test suite:
```bash
python3 test_improvements.py
```

Results:
- ✓ Context manager support
- ✓ Resource cleanup (including double-close safety)
- ✓ kwargs immutability
- ✓ Thread safety (10 threads, 50 concurrent operations)
- ✓ Concurrent access (5 workers, 50 operations)

## [1.0.0] - Initial Release

### Added
- Phase 1: JSONL logging backend
- Phase 2: SQLite logging backend
- Automatic backend switching
- Migration tool (JSONL → SQLite)
- Stats viewers (both JSONL and SQLite)
- Session tracking
- Skill and subagent logging
- Metadata support
- Command-line tools
- Comprehensive documentation
- Usage examples

### Features
- Dual backend support
- Date range filtering
- CSV export
- Session-based analysis
- Tool usage statistics
- Skills and subagent tracking
- Low-overhead logging
- Graceful error handling
