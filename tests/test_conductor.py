"""Comprehensive tests for Claude Code Conductor."""

import unittest
import tempfile
import os
from pathlib import Path

from conductor.db import Database
from conductor.templates import PromptTemplate
from conductor.context import ContextManager
from conductor.state import ProjectState
from conductor.registry import Registry
from conductor.monitor import ProgressMonitor


class TestDatabase(unittest.TestCase):
    """Test database operations."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = Database(self.temp_db.name)

    def tearDown(self):
        """Clean up test database."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_create_project(self):
        """Test project creation."""
        project_id = self.db.create_project("test-project", "Test scope")
        self.assertIsNotNone(project_id)

        project = self.db.get_project(name="test-project")
        self.assertEqual(project['name'], "test-project")
        self.assertEqual(project['scope'], "Test scope")

    def test_add_task(self):
        """Test task creation."""
        project_id = self.db.create_project("test-project", "Test scope")

        task_id = self.db.add_task(project_id, "Test task")
        self.assertIsNotNone(task_id)

        tasks = self.db.get_tasks(project_id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['description'], "Test task")

    def test_task_status_updates(self):
        """Test task status transitions."""
        project_id = self.db.create_project("test-project", "Test scope")
        task_id = self.db.add_task(project_id, "Test task")

        # Test in_progress
        self.db.update_task(task_id, status='in_progress')
        tasks = self.db.get_tasks(project_id, status='in_progress')
        self.assertEqual(len(tasks), 1)

        # Test completed
        self.db.update_task(task_id, status='completed')
        tasks = self.db.get_tasks(project_id, status='completed')
        self.assertEqual(len(tasks), 1)
        self.assertIsNotNone(tasks[0]['completed_at'])

    def test_task_stats(self):
        """Test task statistics."""
        project_id = self.db.create_project("test-project", "Test scope")

        self.db.add_task(project_id, "Task 1", status='pending')
        self.db.add_task(project_id, "Task 2", status='in_progress')
        self.db.add_task(project_id, "Task 3", status='completed')

        stats = self.db.get_task_stats(project_id)

        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['in_progress'], 1)
        self.assertEqual(stats['completed'], 1)

    def test_sessions(self):
        """Test session management."""
        project_id = self.db.create_project("test-project", "Test scope")

        session_id = self.db.start_session(project_id, "test-machine")
        self.assertIsNotNone(session_id)

        active = self.db.get_active_sessions(project_id)
        self.assertEqual(len(active), 1)

        self.db.end_session(session_id)

        active = self.db.get_active_sessions(project_id)
        self.assertEqual(len(active), 0)


class TestTemplates(unittest.TestCase):
    """Test template engine."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = Database(self.temp_db.name)
        self.templates = PromptTemplate(self.db)

    def tearDown(self):
        """Clean up."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_builtin_templates(self):
        """Test builtin templates exist."""
        templates = self.templates.list_templates()

        builtin_names = [t['name'] for t in templates if t['type'] == 'builtin']

        self.assertIn('debug', builtin_names)
        self.assertIn('implement', builtin_names)
        self.assertIn('refactor', builtin_names)

    def test_template_expansion(self):
        """Test template variable expansion."""
        expanded = self.templates.expand(
            'debug',
            variables={
                'context': 'Test context',
                'issue': 'Test issue'
            }
        )

        self.assertIn('Test context', expanded)
        self.assertIn('Test issue', expanded)

    def test_custom_template(self):
        """Test custom template creation."""
        self.templates.create_template(
            'custom-test',
            'This is a {variable} template',
            ['variable']
        )

        expanded = self.templates.expand(
            'custom-test',
            {'variable': 'custom'}
        )

        self.assertIn('custom', expanded)


class TestScopeChecking(unittest.TestCase):
    """Test scope creep detection."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = Database(self.temp_db.name)

    def tearDown(self):
        """Clean up."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_within_scope(self):
        """Test task within scope."""
        project_id = self.db.create_project(
            "rag-pipeline",
            "Build document RAG pipeline using PostgreSQL vectors. No UI."
        )

        state = ProjectState(project_id, self.db)

        is_creep, reason = state.check_scope_creep(
            "Implement vector embeddings with PostgreSQL"
        )

        self.assertFalse(is_creep)

    def test_explicit_exclusion(self):
        """Test explicitly excluded task."""
        project_id = self.db.create_project(
            "rag-pipeline",
            "Build document RAG pipeline. No UI. No authentication."
        )

        state = ProjectState(project_id, self.db)

        is_creep, reason = state.check_scope_creep(
            "Add user authentication system"
        )

        self.assertTrue(is_creep)
        self.assertIn('authentication', reason.lower())

    def test_low_similarity(self):
        """Test task with low similarity to scope."""
        project_id = self.db.create_project(
            "rag-pipeline",
            "Build document RAG pipeline using PostgreSQL"
        )

        state = ProjectState(project_id, self.db)

        is_creep, reason = state.check_scope_creep(
            "Create mobile app for iOS and Android"
        )

        self.assertTrue(is_creep)


class TestContextManager(unittest.TestCase):
    """Test context management."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = Database(self.temp_db.name)
        self.ctx = ContextManager(self.db, max_context_size=1000)

    def tearDown(self):
        """Clean up."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_context_optimization(self):
        """Test context stays under limit."""
        project_id = self.db.create_project(
            "test-project",
            "Test scope " * 100  # Long scope
        )

        # Add many tasks
        for i in range(20):
            self.db.add_task(project_id, f"Task {i} with description " * 10)

        context = self.ctx.format_context_for_llm(project_id)

        self.assertLessEqual(len(context), self.ctx.max_context_size)

    def test_keyword_extraction(self):
        """Test keyword extraction."""
        project_id = self.db.create_project(
            "test-project",
            "Build a web application using Python and PostgreSQL"
        )

        keywords = self.ctx.get_scope_keywords(project_id)

        self.assertIn('web', keywords)
        self.assertIn('application', keywords)
        self.assertIn('python', keywords)
        self.assertIn('postgresql', keywords)


class TestRegistry(unittest.TestCase):
    """Test tool registry."""

    def setUp(self):
        """Set up test registry."""
        self.temp_registry = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.yaml',
            mode='w'
        )
        self.temp_registry.close()
        self.registry = Registry(self.temp_registry.name)

    def tearDown(self):
        """Clean up."""
        os.unlink(self.temp_registry.name)

    def test_relevant_mcp_servers(self):
        """Test MCP server relevance matching."""
        servers = self.registry.get_relevant_mcp_servers(
            "Need to store data in PostgreSQL database"
        )

        # Should find postgres server
        names = [s['name'] for s in servers]
        self.assertIn('postgres', names)

    def test_relevant_subagents(self):
        """Test subagent matching."""
        agents = self.registry.get_relevant_subagents(
            "Fix a bug in the authentication system"
        )

        # Should find debugger
        names = [a['name'] for a in agents]
        self.assertIn('debugger', names)


class TestProgressMonitor(unittest.TestCase):
    """Test progress monitoring."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db = Database(self.temp_db.name)
        self.monitor = ProgressMonitor(self.db)

    def tearDown(self):
        """Clean up."""
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_velocity_calculation(self):
        """Test velocity calculation."""
        project_id = self.db.create_project("test-project", "Test scope")

        # Add completed tasks
        for i in range(5):
            task_id = self.db.add_task(project_id, f"Task {i}")
            self.db.update_task(task_id, status='completed')

        velocity = self.monitor.get_velocity(project_id, days=7)

        self.assertGreater(velocity['tasks_per_day'], 0)

    def test_health_score(self):
        """Test health score calculation."""
        project_id = self.db.create_project("test-project", "Test scope")

        # Add some completed tasks (healthy)
        for i in range(5):
            task_id = self.db.add_task(project_id, f"Task {i}")
            self.db.update_task(task_id, status='completed')

        health = self.monitor.get_project_health(project_id)

        self.assertGreaterEqual(health['score'], 0)
        self.assertLessEqual(health['score'], 100)

    def test_stuck_detection(self):
        """Test stuck pattern detection."""
        project_id = self.db.create_project("test-project", "Test scope")

        # Add many blocked tasks
        for i in range(5):
            task_id = self.db.add_task(project_id, f"Blocked task {i}")
            self.db.update_task(task_id, status='blocked', blocked_reason='Waiting')

        stuck = self.monitor.detect_stuck_patterns(project_id)

        # Should detect many blocked tasks
        types = [s['type'] for s in stuck]
        self.assertIn('many_blocked_tasks', types)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == '__main__':
    run_tests()
