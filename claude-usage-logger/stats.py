#!/usr/bin/env python3
"""
Claude Code Usage Stats - Phase 2 (SQLite)
Enhanced usage statistics with filtering and export capabilities.
"""

import csv
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class UsageStatsSQL:
    """Enhanced analyzer for Claude Code usage patterns using SQLite."""

    def __init__(self, db_file: str = None):
        """
        Initialize the stats analyzer.

        Args:
            db_file: Path to the SQLite database. Defaults to ~/.claude_usage.db
        """
        if db_file is None:
            db_file = os.path.expanduser("~/.claude_usage.db")

        self.db_file = Path(db_file)

        if not self.db_file.exists():
            print(f"Database not found: {self.db_file}")
            print("Run migration first: python3 ~/claude-usage-logger/migrate.py")
            sys.exit(1)

        self.conn = sqlite3.connect(str(self.db_file))
        self.conn.row_factory = sqlite3.Row

    def __del__(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()

    def get_total_entries(self) -> int:
        """Get total number of log entries."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_log")
        return cursor.fetchone()[0]

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the date range of logged data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM usage_log")
        row = cursor.fetchone()
        return (row[0], row[1])

    def get_tool_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        tool_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tool usage statistics with optional filters."""
        query = """
            SELECT
                tool_name,
                COUNT(*) as invocations,
                COUNT(DISTINCT session_id) as sessions_used
            FROM usage_log
            WHERE 1=1
        """
        params = []

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        if tool_filter:
            query += " AND tool_name = ?"
            params.append(tool_filter)

        query += " GROUP BY tool_name ORDER BY invocations DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_skill_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get skill usage statistics."""
        query = """
            SELECT
                skill_name,
                COUNT(*) as invocations,
                COUNT(DISTINCT session_id) as sessions_used
            FROM usage_log
            WHERE skill_name IS NOT NULL
        """
        params = []

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        query += " GROUP BY skill_name ORDER BY invocations DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_subagent_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get subagent usage statistics."""
        query = """
            SELECT
                subagent_name,
                COUNT(*) as invocations,
                COUNT(DISTINCT session_id) as sessions_used
            FROM usage_log
            WHERE subagent_name IS NOT NULL
        """
        params = []

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        query += " GROUP BY subagent_name ORDER BY invocations DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_session_stats(
        self,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get session statistics."""
        if session_id:
            query = """
                SELECT
                    session_id,
                    session_name,
                    COUNT(*) as total_invocations,
                    COUNT(DISTINCT tool_name) as unique_tools,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM usage_log
                WHERE session_id = ?
                GROUP BY session_id, session_name
            """
            params = [session_id]
        else:
            query = """
                SELECT
                    session_id,
                    session_name,
                    COUNT(*) as total_invocations,
                    COUNT(DISTINCT tool_name) as unique_tools,
                    MIN(timestamp) as first_event,
                    MAX(timestamp) as last_event
                FROM usage_log
                GROUP BY session_id, session_name
                ORDER BY last_event DESC
                LIMIT ?
            """
            params = [limit]

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_session_tool_breakdown(self, session_id: str) -> List[Dict[str, Any]]:
        """Get tool breakdown for a specific session."""
        query = """
            SELECT
                tool_name,
                COUNT(*) as invocations
            FROM usage_log
            WHERE session_id = ?
            GROUP BY tool_name
            ORDER BY invocations DESC
        """

        cursor = self.conn.cursor()
        cursor.execute(query, [session_id])

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_entries(
        self,
        limit: int = 10,
        tool_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        query = """
            SELECT
                id, timestamp, tool_name, session_id, session_name,
                skill_name, subagent_name, metadata
            FROM usage_log
        """
        params = []

        if tool_filter:
            query += " WHERE tool_name = ?"
            params.append(tool_filter)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def get_time_series_data(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        tool_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get time-series data for export."""
        query = """
            SELECT
                date(timestamp) as date,
                tool_name,
                COUNT(*) as invocations
            FROM usage_log
            WHERE 1=1
        """
        params = []

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        if tool_filter:
            query += " AND tool_name = ?"
            params.append(tool_filter)

        query += " GROUP BY date(timestamp), tool_name ORDER BY date, tool_name"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(
        self,
        output_file: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        tool_filter: Optional[str] = None
    ):
        """Export time-series data to CSV."""
        data = self.get_time_series_data(from_date, to_date, tool_filter)

        if not data:
            print("No data to export")
            return

        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "tool_name", "invocations"])
            writer.writeheader()
            writer.writerows(data)

        print(f"✓ Exported {len(data)} rows to {output_file}")

    def display_stats(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        session_filter: Optional[str] = None,
        tool_filter: Optional[str] = None
    ):
        """Display comprehensive usage statistics."""
        print("=" * 70)
        print("CLAUDE CODE USAGE STATISTICS (SQLite)")
        print("=" * 70)
        print(f"Database: {self.db_file}")

        total_entries = self.get_total_entries()
        date_range = self.get_date_range()

        print(f"Total entries: {total_entries}")
        if date_range[0] and date_range[1]:
            print(f"Date range: {date_range[0]} to {date_range[1]}")

        # Display filters if active
        if from_date or to_date or tool_filter or session_filter:
            print()
            print("Active filters:")
            if from_date:
                print(f"  From: {from_date}")
            if to_date:
                print(f"  To: {to_date}")
            if tool_filter:
                print(f"  Tool: {tool_filter}")
            if session_filter:
                print(f"  Session: {session_filter}")

        print()

        # Session-specific view
        if session_filter:
            self._display_session_details(session_filter)
            return

        # Tool statistics
        print("-" * 70)
        print("TOOL USAGE STATISTICS")
        print("-" * 70)

        tool_stats = self.get_tool_stats(from_date, to_date, tool_filter)
        if tool_stats:
            max_tool_len = max(len(t["tool_name"]) for t in tool_stats)
            for stat in tool_stats:
                print(
                    f"  {stat['tool_name']:<{max_tool_len}}  "
                    f"{stat['invocations']:>5} invocations  "
                    f"({stat['sessions_used']} sessions)"
                )
        else:
            print("  No data")

        print()

        # Skills
        print("-" * 70)
        print("SKILLS USAGE")
        print("-" * 70)

        skill_stats = self.get_skill_stats(from_date, to_date)
        if skill_stats:
            max_skill_len = max(len(s["skill_name"]) for s in skill_stats)
            for stat in skill_stats:
                print(
                    f"  {stat['skill_name']:<{max_skill_len}}  "
                    f"{stat['invocations']:>5} invocations  "
                    f"({stat['sessions_used']} sessions)"
                )
        else:
            print("  No skill data")

        print()

        # Subagents
        print("-" * 70)
        print("SUBAGENT USAGE")
        print("-" * 70)

        subagent_stats = self.get_subagent_stats(from_date, to_date)
        if subagent_stats:
            max_subagent_len = max(len(s["subagent_name"]) for s in subagent_stats)
            for stat in subagent_stats:
                print(
                    f"  {stat['subagent_name']:<{max_subagent_len}}  "
                    f"{stat['invocations']:>5} invocations  "
                    f"({stat['sessions_used']} sessions)"
                )
        else:
            print("  No subagent data")

        print()

        # Recent sessions
        print("-" * 70)
        print("RECENT SESSIONS")
        print("-" * 70)

        session_stats = self.get_session_stats(limit=10)
        if session_stats:
            for i, session in enumerate(session_stats, 1):
                session_name = session["session_name"] or "unknown"
                print(f"  {i:2d}. Session: {session['session_id']} ({session_name})")
                print(f"      Total invocations: {session['total_invocations']}")
                print(f"      Unique tools: {session['unique_tools']}")
                print(f"      First event: {session['first_event']}")
                print(f"      Last event: {session['last_event']}")
                print()
        else:
            print("  No session data")

        print("=" * 70)

    def _display_session_details(self, session_id: str):
        """Display detailed statistics for a specific session."""
        print("-" * 70)
        print(f"SESSION DETAILS: {session_id}")
        print("-" * 70)

        session_stats = self.get_session_stats(session_id=session_id)
        if not session_stats:
            print("Session not found")
            return

        session = session_stats[0]
        print(f"Session name: {session['session_name'] or 'unknown'}")
        print(f"Total invocations: {session['total_invocations']}")
        print(f"Unique tools: {session['unique_tools']}")
        print(f"First event: {session['first_event']}")
        print(f"Last event: {session['last_event']}")
        print()

        print("Tool breakdown:")
        tool_breakdown = self.get_session_tool_breakdown(session_id)
        if tool_breakdown:
            max_tool_len = max(len(t["tool_name"]) for t in tool_breakdown)
            for tool in tool_breakdown:
                print(f"  {tool['tool_name']:<{max_tool_len}}  {tool['invocations']:>5} invocations")
        else:
            print("  No data")

        print()


def parse_date_shortcut(shortcut: str) -> Optional[str]:
    """Parse date shortcuts like 'today', 'yesterday', 'last-week'."""
    now = datetime.utcnow()

    if shortcut == "today":
        return now.date().isoformat()
    elif shortcut == "yesterday":
        return (now - timedelta(days=1)).date().isoformat()
    elif shortcut == "last-week":
        return (now - timedelta(weeks=1)).date().isoformat()
    elif shortcut == "last-month":
        return (now - timedelta(days=30)).date().isoformat()

    # Try to parse as ISO date
    try:
        datetime.fromisoformat(shortcut)
        return shortcut
    except ValueError:
        return None


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Display Claude Code usage statistics (Phase 2 - SQLite)"
    )
    parser.add_argument(
        "--db-file",
        help="Path to SQLite database (default: ~/.claude_usage.db)",
        default=None
    )
    parser.add_argument(
        "--from",
        dest="from_date",
        help="Filter from date (YYYY-MM-DD or today/yesterday/last-week/last-month)",
        default=None
    )
    parser.add_argument(
        "--to",
        dest="to_date",
        help="Filter to date (YYYY-MM-DD or today/yesterday)",
        default=None
    )
    parser.add_argument(
        "--session",
        help="Filter by session ID",
        default=None
    )
    parser.add_argument(
        "--tool",
        help="Filter by tool name",
        default=None
    )
    parser.add_argument(
        "--export-csv",
        help="Export time-series data to CSV file",
        default=None
    )

    args = parser.parse_args()

    # Parse date shortcuts
    from_date = parse_date_shortcut(args.from_date) if args.from_date else None
    to_date = parse_date_shortcut(args.to_date) if args.to_date else None

    stats = UsageStatsSQL(args.db_file)

    if args.export_csv:
        stats.export_to_csv(
            args.export_csv,
            from_date=from_date,
            to_date=to_date,
            tool_filter=args.tool
        )
    else:
        stats.display_stats(
            from_date=from_date,
            to_date=to_date,
            session_filter=args.session,
            tool_filter=args.tool
        )


if __name__ == "__main__":
    main()
