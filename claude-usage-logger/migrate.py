#!/usr/bin/env python3
"""
Migration script: JSONL to SQLite
Migrates usage data from JSONL format to SQLite database.
"""

import json
import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class UsageMigrator:
    """Migrator for moving JSONL data to SQLite."""

    def __init__(
        self,
        jsonl_file: str = None,
        db_file: str = None,
        schema_file: str = None
    ):
        """
        Initialize the migrator.

        Args:
            jsonl_file: Path to JSONL log file (default: ~/.claude_usage_log.jsonl)
            db_file: Path to SQLite database (default: ~/.claude_usage.db)
            schema_file: Path to SQL schema file
        """
        if jsonl_file is None:
            jsonl_file = os.path.expanduser("~/.claude_usage_log.jsonl")

        if db_file is None:
            db_file = os.path.expanduser("~/.claude_usage.db")

        if schema_file is None:
            # Try to find schema file in same directory as this script
            script_dir = Path(__file__).parent
            schema_file = script_dir / "schema.sql"

        self.jsonl_file = Path(jsonl_file)
        self.db_file = Path(db_file)
        self.schema_file = Path(schema_file)

    def create_database(self):
        """Create the SQLite database with schema."""
        print(f"Creating database: {self.db_file}")

        if not self.schema_file.exists():
            print(f"Error: Schema file not found: {self.schema_file}")
            return False

        # Read schema
        with open(self.schema_file, "r") as f:
            schema = f.read()

        # Create database
        conn = sqlite3.connect(self.db_file)
        try:
            conn.executescript(schema)
            conn.commit()
            print("✓ Database schema created successfully")
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
        finally:
            conn.close()

    def migrate_jsonl_to_sqlite(self):
        """Migrate data from JSONL to SQLite."""
        if not self.jsonl_file.exists():
            print(f"Error: JSONL file not found: {self.jsonl_file}")
            return False

        print(f"Reading entries from: {self.jsonl_file}")

        # Read all entries
        entries = []
        with open(self.jsonl_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed entry at line {line_num}: {e}")

        print(f"Found {len(entries)} entries to migrate")

        if not entries:
            print("No entries to migrate")
            return True

        # Insert into database
        conn = sqlite3.connect(self.db_file)
        try:
            cursor = conn.cursor()

            for entry in entries:
                # Extract fields
                timestamp = entry.get("timestamp")
                tool_name = entry.get("tool", "unknown")
                session_id = entry.get("session_id")
                session_name = entry.get("session_name")
                skill_name = entry.get("skill_name")
                subagent_name = entry.get("subagent_name")

                # Store remaining fields as metadata JSON
                metadata_fields = {
                    k: v for k, v in entry.items()
                    if k not in [
                        "timestamp", "tool", "session_id", "session_name",
                        "skill_name", "subagent_name"
                    ]
                }
                metadata = json.dumps(metadata_fields) if metadata_fields else None

                # Insert
                cursor.execute(
                    """
                    INSERT INTO usage_log (
                        timestamp, tool_name, session_id, session_name,
                        skill_name, subagent_name, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp, tool_name, session_id, session_name,
                        skill_name, subagent_name, metadata
                    )
                )

            conn.commit()
            print(f"✓ Migrated {len(entries)} entries successfully")
            return True

        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def backup_jsonl(self):
        """Create a backup of the JSONL file."""
        if not self.jsonl_file.exists():
            return True

        backup_file = Path(str(self.jsonl_file) + ".backup")
        print(f"Creating backup: {backup_file}")

        try:
            shutil.copy2(self.jsonl_file, backup_file)
            print(f"✓ Backup created successfully")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def verify_migration(self):
        """Verify the migration was successful."""
        print("Verifying migration...")

        # Count entries in JSONL
        jsonl_count = 0
        if self.jsonl_file.exists():
            with open(self.jsonl_file, "r") as f:
                for line in f:
                    if line.strip():
                        jsonl_count += 1

        # Count entries in SQLite
        conn = sqlite3.connect(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usage_log")
            db_count = cursor.fetchone()[0]
        finally:
            conn.close()

        print(f"JSONL entries: {jsonl_count}")
        print(f"SQLite entries: {db_count}")

        if jsonl_count == db_count:
            print("✓ Migration verified successfully")
            return True
        else:
            print("⚠ Warning: Entry counts don't match")
            return False

    def run_migration(self):
        """Run the complete migration process."""
        print("=" * 70)
        print("CLAUDE CODE USAGE LOGGER - MIGRATION TO SQLITE")
        print("=" * 70)
        print()

        # Step 1: Backup JSONL
        if not self.backup_jsonl():
            print("Migration aborted: Could not create backup")
            return False

        # Step 2: Create database
        if not self.create_database():
            print("Migration aborted: Could not create database")
            return False

        # Step 3: Migrate data
        if not self.migrate_jsonl_to_sqlite():
            print("Migration aborted: Could not migrate data")
            return False

        # Step 4: Verify
        if not self.verify_migration():
            print("Warning: Verification failed, but data was migrated")

        print()
        print("=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        print()
        print("Database file:", self.db_file)
        print("Backup file:", str(self.jsonl_file) + ".backup")
        print()
        print("Next steps:")
        print("1. Test the database with: claude-usage-stats")
        print("2. The logger will now use SQLite instead of JSONL")
        print()

        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Claude Code usage data from JSONL to SQLite"
    )
    parser.add_argument(
        "--jsonl-file",
        help="Path to JSONL file (default: ~/.claude_usage_log.jsonl)",
        default=None
    )
    parser.add_argument(
        "--db-file",
        help="Path to SQLite database (default: ~/.claude_usage.db)",
        default=None
    )
    parser.add_argument(
        "--schema-file",
        help="Path to SQL schema file",
        default=None
    )

    args = parser.parse_args()

    migrator = UsageMigrator(
        jsonl_file=args.jsonl_file,
        db_file=args.db_file,
        schema_file=args.schema_file
    )

    success = migrator.run_migration()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
