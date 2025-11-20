#!/usr/bin/env python3
"""
Claude Code Usage Pattern Logger
Logs tool usage patterns to JSONL or SQLite for analysis.
Automatically uses SQLite if database exists, otherwise uses JSONL.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid


class UsageLogger:
    """Logger for Claude Code tool usage patterns."""

    def __init__(self, log_file: Optional[str] = None, db_file: Optional[str] = None):
        """
        Initialize the usage logger.
        Automatically uses SQLite if database exists, otherwise uses JSONL.

        Args:
            log_file: Path to the log file. Defaults to ~/.claude_usage_log.jsonl
            db_file: Path to the SQLite database. Defaults to ~/.claude_usage.db
        """
        if log_file is None:
            log_file = os.path.expanduser("~/.claude_usage_log.jsonl")
        if db_file is None:
            db_file = os.path.expanduser("~/.claude_usage.db")

        self.log_file = Path(log_file)
        self.db_file = Path(db_file)

        # Determine which backend to use
        self.use_sqlite = self.db_file.exists()

        if self.use_sqlite:
            self.conn = sqlite3.connect(str(self.db_file))
        else:
            self._ensure_log_file_exists()

        self._session_id = self._get_or_create_session_id()

    def _ensure_log_file_exists(self):
        """Ensure the log file exists, create if it doesn't."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.touch()
        except Exception as e:
            print(f"Warning: Could not create log file: {e}", file=sys.stderr)

    def _get_or_create_session_id(self) -> str:
        """
        Get or create a session ID.
        Uses environment variable if available, otherwise generates a UUID.
        """
        # Try to get from environment
        session_id = os.environ.get("CLAUDE_SESSION_ID")
        if session_id:
            return session_id

        # Generate a new session ID
        return str(uuid.uuid4())[:8]

    def log_tool_usage(
        self,
        tool_name: str,
        session_name: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Log a tool usage event.

        Args:
            tool_name: Name of the tool being used
            session_name: Optional session name
            **kwargs: Additional metadata to log

        Returns:
            bool: True if logging succeeded, False otherwise
        """
        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            session_name = session_name or os.environ.get("CLAUDE_SESSION_NAME", "unknown")

            if self.use_sqlite:
                return self._log_to_sqlite(
                    timestamp, tool_name, session_name, **kwargs
                )
            else:
                return self._log_to_jsonl(
                    timestamp, tool_name, session_name, **kwargs
                )

        except Exception as e:
            # Logging failures should not break tool execution
            print(f"Warning: Failed to log tool usage: {e}", file=sys.stderr)
            return False

    def _log_to_jsonl(
        self,
        timestamp: str,
        tool_name: str,
        session_name: str,
        **kwargs
    ) -> bool:
        """Log to JSONL file."""
        log_entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "session_id": self._session_id,
            "session_name": session_name,
        }

        # Add any additional metadata
        log_entry.update(kwargs)

        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return True

    def _log_to_sqlite(
        self,
        timestamp: str,
        tool_name: str,
        session_name: str,
        **kwargs
    ) -> bool:
        """Log to SQLite database."""
        # Extract known fields
        skill_name = kwargs.pop("skill_name", None)
        subagent_name = kwargs.pop("subagent_name", None)

        # Store remaining fields as metadata
        metadata = json.dumps(kwargs) if kwargs else None

        # Insert into database
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO usage_log (
                timestamp, tool_name, session_id, session_name,
                skill_name, subagent_name, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp, tool_name, self._session_id, session_name,
                skill_name, subagent_name, metadata
            )
        )
        self.conn.commit()

        return True

    def log_skill(self, skill_name: str, session_name: Optional[str] = None, **kwargs):
        """Log a skill invocation."""
        return self.log_tool_usage(
            tool_name="skill",
            skill_name=skill_name,
            session_name=session_name,
            **kwargs
        )

    def log_subagent(self, subagent_name: str, session_name: Optional[str] = None, **kwargs):
        """Log a subagent invocation."""
        return self.log_tool_usage(
            tool_name="subagent",
            subagent_name=subagent_name,
            session_name=session_name,
            **kwargs
        )

    def log_web_search(self, query: str, session_name: Optional[str] = None, **kwargs):
        """Log a web search."""
        return self.log_tool_usage(
            tool_name="web_search",
            query_length=len(query),
            session_name=session_name,
            **kwargs
        )

    def log_bash(self, command: str, session_name: Optional[str] = None, **kwargs):
        """Log a bash command execution."""
        return self.log_tool_usage(
            tool_name="bash",
            command_length=len(command),
            session_name=session_name,
            **kwargs
        )

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        session_name: Optional[str] = None,
        **kwargs
    ):
        """Log a file operation (read, write, edit)."""
        return self.log_tool_usage(
            tool_name=f"file_{operation}",
            file_path=file_path,
            session_name=session_name,
            **kwargs
        )

    def log_web_fetch(self, url: str, session_name: Optional[str] = None, **kwargs):
        """Log a web fetch operation."""
        return self.log_tool_usage(
            tool_name="web_fetch",
            url=url,
            session_name=session_name,
            **kwargs
        )


# Global logger instance
_logger = None


def get_logger() -> UsageLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = UsageLogger()
    return _logger


# Convenience functions for direct use
def log_tool_usage(tool_name: str, **kwargs):
    """Log a tool usage event."""
    return get_logger().log_tool_usage(tool_name, **kwargs)


def log_skill(skill_name: str, **kwargs):
    """Log a skill invocation."""
    return get_logger().log_skill(skill_name, **kwargs)


def log_subagent(subagent_name: str, **kwargs):
    """Log a subagent invocation."""
    return get_logger().log_subagent(subagent_name, **kwargs)


def log_web_search(query: str, **kwargs):
    """Log a web search."""
    return get_logger().log_web_search(query, **kwargs)


def log_bash(command: str, **kwargs):
    """Log a bash command execution."""
    return get_logger().log_bash(command, **kwargs)


def log_file_operation(operation: str, file_path: str, **kwargs):
    """Log a file operation."""
    return get_logger().log_file_operation(operation, file_path, **kwargs)


def log_web_fetch(url: str, **kwargs):
    """Log a web fetch operation."""
    return get_logger().log_web_fetch(url, **kwargs)


if __name__ == "__main__":
    # Test the logger
    logger = UsageLogger()

    print("Testing usage logger...")
    print(f"Backend: {'SQLite' if logger.use_sqlite else 'JSONL'}")
    print(f"Session ID: {logger._session_id}")
    print()

    # Test various log types
    logger.log_tool_usage("test_tool", test_param="value")
    logger.log_skill("rapid-prototype")
    logger.log_subagent("general-purpose")
    logger.log_web_search("test query")
    logger.log_bash("ls -la")
    logger.log_file_operation("read", "/path/to/file.py")

    if logger.use_sqlite:
        print(f"✓ Test logs written to {logger.db_file}")
    else:
        print(f"✓ Test logs written to {logger.log_file}")
    print()
    print("Run the stats viewer to see the logs:")
    if logger.use_sqlite:
        print("  python3 ~/claude-usage-logger/stats.py")
    else:
        print("  python3 ~/claude-usage-logger/stats_poc.py")
