"""Database interface for Claude Code Conductor."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import uuid


class Database:
    """SQLite database interface for managing projects, tasks, sessions, and learnings."""

    def __init__(self, db_path: str = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to data/conductor.db
        """
        if db_path is None:
            db_path = Path.home() / ".conductor" / "conductor.db"
        else:
            db_path = Path(db_path)

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                scope TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked')) DEFAULT 'pending',
                is_scope_creep BOOLEAN DEFAULT 0,
                blocked_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                tasks_completed INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Learnings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                session_id TEXT,
                pattern TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # Templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                name TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                variables TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_learnings_project ON learnings(project_id)")

        self.conn.commit()

    # Project operations

    def create_project(self, name: str, scope: str) -> str:
        """Create a new project.

        Args:
            name: Project name (must be unique)
            scope: Project scope description

        Returns:
            Project ID
        """
        project_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO projects (id, name, scope) VALUES (?, ?, ?)",
            (project_id, name, scope)
        )
        self.conn.commit()
        return project_id

    def get_project(self, name: str = None, project_id: str = None) -> Optional[Dict]:
        """Get project by name or ID.

        Args:
            name: Project name
            project_id: Project ID

        Returns:
            Project dict or None
        """
        cursor = self.conn.cursor()
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        elif name:
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_projects(self) -> List[Dict]:
        """Get all projects ordered by most recently updated."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def update_project(self, project_id: str, **kwargs):
        """Update project fields.

        Args:
            project_id: Project ID
            **kwargs: Fields to update (scope, etc.)
        """
        if not kwargs:
            return

        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [project_id]

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE projects SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        self.conn.commit()

    def delete_project(self, project_id: str):
        """Delete a project and all associated data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()

    # Task operations

    def add_task(
        self,
        project_id: str,
        description: str,
        is_scope_creep: bool = False,
        status: str = "pending"
    ) -> int:
        """Add a new task to a project.

        Args:
            project_id: Project ID
            description: Task description
            is_scope_creep: Whether task is outside scope
            status: Initial status (default: pending)

        Returns:
            Task ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO tasks (project_id, description, status, is_scope_creep)
               VALUES (?, ?, ?, ?)""",
            (project_id, description, status, is_scope_creep)
        )
        self.conn.commit()

        # Update project timestamp
        self._touch_project(project_id)

        return cursor.lastrowid

    def get_tasks(
        self,
        project_id: str,
        status: str = None,
        include_scope_creep: bool = True
    ) -> List[Dict]:
        """Get tasks for a project.

        Args:
            project_id: Project ID
            status: Filter by status (optional)
            include_scope_creep: Include scope creep tasks

        Returns:
            List of task dicts
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM tasks WHERE project_id = ?"
        params = [project_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        if not include_scope_creep:
            query += " AND is_scope_creep = 0"

        query += " ORDER BY created_at ASC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: int, **kwargs):
        """Update task fields.

        Args:
            task_id: Task ID
            **kwargs: Fields to update (status, description, etc.)
        """
        if not kwargs:
            return

        # Auto-set completed_at when status changes to completed
        if kwargs.get('status') == 'completed' and 'completed_at' not in kwargs:
            kwargs['completed_at'] = datetime.now().isoformat()

        fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
        values = list(kwargs.values()) + [task_id]

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE tasks SET {fields} WHERE id = ?", values)
        self.conn.commit()

        # Update project timestamp
        cursor.execute("SELECT project_id FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            self._touch_project(row[0])

    def delete_task(self, task_id: int):
        """Delete a task."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def get_task_stats(self, project_id: str) -> Dict[str, int]:
        """Get task statistics for a project.

        Returns:
            Dict with counts by status
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT status, COUNT(*) as count
               FROM tasks
               WHERE project_id = ?
               GROUP BY status""",
            (project_id,)
        )

        stats = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'blocked': 0,
            'total': 0
        }

        for row in cursor.fetchall():
            stats[row['status']] = row['count']
            stats['total'] += row['count']

        return stats

    # Session operations

    def start_session(self, project_id: str, machine_id: str = None) -> str:
        """Start a new session.

        Args:
            project_id: Project ID
            machine_id: Machine identifier (default: hostname)

        Returns:
            Session ID
        """
        if machine_id is None:
            import socket
            machine_id = socket.gethostname()

        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, project_id, machine_id) VALUES (?, ?, ?)",
            (session_id, project_id, machine_id)
        )
        self.conn.commit()
        return session_id

    def end_session(self, session_id: str):
        """End a session.

        Args:
            session_id: Session ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET ended_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_active_sessions(self, project_id: str = None) -> List[Dict]:
        """Get active (not ended) sessions.

        Args:
            project_id: Filter by project (optional)
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM sessions WHERE ended_at IS NULL"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY started_at DESC"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def increment_session_tasks(self, session_id: str):
        """Increment completed tasks counter for session."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET tasks_completed = tasks_completed + 1 WHERE id = ?",
            (session_id,)
        )
        self.conn.commit()

    # Learning operations

    def add_learning(
        self,
        pattern: str,
        context: str = None,
        project_id: str = None,
        session_id: str = None
    ) -> int:
        """Add a learning/pattern.

        Args:
            pattern: The learning pattern
            context: Additional context
            project_id: Associated project (optional)
            session_id: Associated session (optional)

        Returns:
            Learning ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO learnings (pattern, context, project_id, session_id)
               VALUES (?, ?, ?, ?)""",
            (pattern, context, project_id, session_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_learnings(
        self,
        project_id: str = None,
        session_id: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get learnings.

        Args:
            project_id: Filter by project (optional)
            session_id: Filter by session (optional)
            limit: Max number to return

        Returns:
            List of learning dicts
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM learnings WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # Template operations

    def add_template(self, name: str, content: str, variables: List[str] = None):
        """Add or update a template.

        Args:
            name: Template name
            content: Template content
            variables: List of variable names
        """
        cursor = self.conn.cursor()
        variables_json = json.dumps(variables) if variables else None

        cursor.execute(
            """INSERT OR REPLACE INTO templates (name, content, variables)
               VALUES (?, ?, ?)""",
            (name, content, variables_json)
        )
        self.conn.commit()

    def get_template(self, name: str) -> Optional[Dict]:
        """Get template by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM templates WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            if result.get('variables'):
                result['variables'] = json.loads(result['variables'])
            return result
        return None

    def get_all_templates(self) -> List[Dict]:
        """Get all templates."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY usage_count DESC, name ASC")

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('variables'):
                result['variables'] = json.loads(result['variables'])
            results.append(result)

        return results

    def increment_template_usage(self, name: str):
        """Increment template usage counter."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE templates SET usage_count = usage_count + 1 WHERE name = ?",
            (name,)
        )
        self.conn.commit()

    # Helper methods

    def _touch_project(self, project_id: str):
        """Update project's updated_at timestamp."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,)
        )
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
