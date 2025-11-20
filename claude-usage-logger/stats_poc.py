#!/usr/bin/env python3
"""
Claude Code Usage Stats - Phase 1 (JSONL POC)
Display usage statistics from the JSONL log file.
"""

import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class UsageStats:
    """Analyzer for Claude Code usage patterns."""

    def __init__(self, log_file: str = None):
        """
        Initialize the stats analyzer.

        Args:
            log_file: Path to the log file. Defaults to ~/.claude_usage_log.jsonl
        """
        if log_file is None:
            log_file = os.path.expanduser("~/.claude_usage_log.jsonl")

        self.log_file = Path(log_file)
        self.entries = []
        self._load_entries()

    def _load_entries(self):
        """Load all log entries from the JSONL file."""
        if not self.log_file.exists():
            print(f"Log file not found: {self.log_file}")
            return

        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.entries.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping malformed entry: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error reading log file: {e}", file=sys.stderr)

    def get_total_invocations(self) -> Dict[str, int]:
        """Get total invocations by tool type."""
        counter = Counter()
        for entry in self.entries:
            tool = entry.get("tool", "unknown")
            counter[tool] += 1
        return dict(counter)

    def get_last_n_invocations(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the last N invocations."""
        return self.entries[-n:] if len(self.entries) >= n else self.entries

    def get_invocations_by_session(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group invocations by session ID."""
        sessions = defaultdict(list)
        for entry in self.entries:
            session_id = entry.get("session_id", "unknown")
            sessions[session_id].append(entry)
        return dict(sessions)

    def get_skills_breakdown(self) -> Dict[str, int]:
        """Get breakdown of skill usage."""
        counter = Counter()
        for entry in self.entries:
            if entry.get("tool") == "skill":
                skill_name = entry.get("skill_name", "unknown")
                counter[skill_name] += 1
        return dict(counter)

    def get_subagents_breakdown(self) -> Dict[str, int]:
        """Get breakdown of subagent usage."""
        counter = Counter()
        for entry in self.entries:
            if entry.get("tool") == "subagent":
                subagent_name = entry.get("subagent_name", "unknown")
                counter[subagent_name] += 1
        return dict(counter)

    def display_stats(self):
        """Display usage statistics in a human-readable format."""
        if not self.entries:
            print("No usage data found.")
            return

        print("=" * 70)
        print("CLAUDE CODE USAGE STATISTICS")
        print("=" * 70)
        print(f"Log file: {self.log_file}")
        print(f"Total entries: {len(self.entries)}")
        print()

        # Total invocations by tool type
        print("-" * 70)
        print("INVOCATIONS BY TOOL TYPE")
        print("-" * 70)
        invocations = self.get_total_invocations()
        if invocations:
            # Sort by count descending
            sorted_invocations = sorted(invocations.items(), key=lambda x: x[1], reverse=True)
            max_tool_len = max(len(tool) for tool, _ in sorted_invocations)

            for tool, count in sorted_invocations:
                print(f"  {tool:<{max_tool_len}}  {count:>5} invocations")
        else:
            print("  No data")
        print()

        # Skills breakdown
        print("-" * 70)
        print("SKILLS USAGE BREAKDOWN")
        print("-" * 70)
        skills = self.get_skills_breakdown()
        if skills:
            sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
            max_skill_len = max(len(skill) for skill, _ in sorted_skills)

            for skill, count in sorted_skills:
                print(f"  {skill:<{max_skill_len}}  {count:>5} invocations")
        else:
            print("  No skill data")
        print()

        # Subagents breakdown
        print("-" * 70)
        print("SUBAGENTS USAGE BREAKDOWN")
        print("-" * 70)
        subagents = self.get_subagents_breakdown()
        if subagents:
            sorted_subagents = sorted(subagents.items(), key=lambda x: x[1], reverse=True)
            max_subagent_len = max(len(subagent) for subagent, _ in sorted_subagents)

            for subagent, count in sorted_subagents:
                print(f"  {subagent:<{max_subagent_len}}  {count:>5} invocations")
        else:
            print("  No subagent data")
        print()

        # Sessions
        print("-" * 70)
        print("INVOCATIONS BY SESSION")
        print("-" * 70)
        sessions = self.get_invocations_by_session()
        if sessions:
            sorted_sessions = sorted(
                sessions.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )

            for session_id, entries in sorted_sessions[:10]:  # Show top 10 sessions
                session_name = entries[0].get("session_name", "unknown")
                print(f"  Session: {session_id} ({session_name})")
                print(f"    Total invocations: {len(entries)}")

                # Show tool breakdown for this session
                tool_counter = Counter()
                for entry in entries:
                    tool_counter[entry.get("tool", "unknown")] += 1

                print(f"    Tools: {dict(tool_counter)}")
                print()
        else:
            print("  No session data")
        print()

        # Last 10 invocations
        print("-" * 70)
        print("LAST 10 INVOCATIONS")
        print("-" * 70)
        last_invocations = self.get_last_n_invocations(10)
        if last_invocations:
            for i, entry in enumerate(last_invocations, 1):
                timestamp = entry.get("timestamp", "unknown")
                tool = entry.get("tool", "unknown")
                session_id = entry.get("session_id", "unknown")

                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    timestamp_str = timestamp

                print(f"  {i:2d}. [{timestamp_str}] {tool} (session: {session_id[:8]})")

                # Show additional details based on tool type
                if tool == "skill":
                    skill_name = entry.get("skill_name", "N/A")
                    print(f"      Skill: {skill_name}")
                elif tool == "subagent":
                    subagent_name = entry.get("subagent_name", "N/A")
                    print(f"      Subagent: {subagent_name}")
                elif tool == "web_search":
                    query_length = entry.get("query_length", "N/A")
                    print(f"      Query length: {query_length}")
        else:
            print("  No data")
        print()

        print("=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Display Claude Code usage statistics (Phase 1 - JSONL POC)"
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file (default: ~/.claude_usage_log.jsonl)",
        default=None
    )

    args = parser.parse_args()

    stats = UsageStats(args.log_file)
    stats.display_stats()


if __name__ == "__main__":
    main()
