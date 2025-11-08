"""Context manager for optimizing prompt context."""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import re


class ContextManager:
    """Manages and optimizes context for Claude Code prompts."""

    def __init__(self, db, max_context_size: int = 8000):
        """Initialize context manager.

        Args:
            db: Database instance
            max_context_size: Maximum context size in characters
        """
        self.db = db
        self.max_context_size = max_context_size

    def prepare_context(self, project_id: str) -> str:
        """Build optimized context for a project.

        Args:
            project_id: Project ID

        Returns:
            Optimized context string
        """
        context_parts = [
            self.get_project_header(project_id),
            self.get_relevant_history(project_id),
            self.get_recent_decisions(project_id),
            self.get_relevant_patterns(project_id)
        ]

        # Remove None values
        context_parts = [p for p in context_parts if p]

        return self.optimize_context(context_parts)

    def get_project_header(self, project_id: str) -> str:
        """Get project header with scope and status.

        Args:
            project_id: Project ID

        Returns:
            Header string
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return ""

        stats = self.db.get_task_stats(project_id)

        header_parts = [
            f"# Project: {project['name']}",
            f"\n**Scope:** {project['scope']}",
        ]

        if stats['total'] > 0:
            completed_pct = int(stats['completed'] / stats['total'] * 100)
            header_parts.append(
                f"\n**Progress:** {completed_pct}% complete "
                f"({stats['completed']}/{stats['total']} tasks)"
            )

            if stats['blocked'] > 0:
                header_parts.append(f"\n⚠️  {stats['blocked']} blocked tasks")

        return "".join(header_parts)

    def get_relevant_history(self, project_id: str, max_items: int = 10) -> str:
        """Get relevant task history.

        Args:
            project_id: Project ID
            max_items: Maximum number of items to include

        Returns:
            History string
        """
        parts = []

        # Completed tasks (most recent)
        completed = self.db.get_tasks(project_id, status='completed')
        if completed:
            recent_completed = completed[-max_items:]
            parts.append("\n\n## Recently Completed")
            for task in recent_completed:
                parts.append(f"\n- ✓ {task['description']}")

        # In-progress tasks
        in_progress = self.db.get_tasks(project_id, status='in_progress')
        if in_progress:
            parts.append("\n\n## In Progress")
            for task in in_progress:
                parts.append(f"\n- ⟳ {task['description']}")

        # Pending tasks (next few)
        pending = self.db.get_tasks(project_id, status='pending')
        if pending:
            parts.append("\n\n## Next Tasks")
            for task in pending[:5]:
                parts.append(f"\n- ○ {task['description']}")
            if len(pending) > 5:
                parts.append(f"\n- ... and {len(pending) - 5} more")

        # Blocked tasks with reasons
        blocked = self.db.get_tasks(project_id, status='blocked')
        if blocked:
            parts.append("\n\n## Blocked Tasks")
            for task in blocked:
                reason = f" ({task['blocked_reason']})" if task.get('blocked_reason') else ""
                parts.append(f"\n- 🚫 {task['description']}{reason}")

        return "".join(parts) if parts else ""

    def get_recent_decisions(self, project_id: str, limit: int = 5) -> str:
        """Get recent project decisions and learnings.

        Args:
            project_id: Project ID
            limit: Max number of learnings

        Returns:
            Decisions string
        """
        learnings = self.db.get_learnings(project_id=project_id, limit=limit)
        if not learnings:
            return ""

        parts = ["\n\n## Recent Learnings & Decisions"]
        for learning in learnings:
            parts.append(f"\n- {learning['pattern']}")
            if learning.get('context'):
                # Truncate long context
                context = learning['context']
                if len(context) > 100:
                    context = context[:97] + "..."
                parts.append(f"\n  Context: {context}")

        return "".join(parts)

    def get_relevant_patterns(self, project_id: str) -> str:
        """Get relevant code patterns and conventions.

        Args:
            project_id: Project ID

        Returns:
            Patterns string
        """
        # This is a placeholder for future enhancement
        # Could analyze code style, common patterns, etc.
        return ""

    def optimize_context(self, parts: List[str]) -> str:
        """Optimize context to fit within size limit.

        Args:
            parts: List of context parts in priority order

        Returns:
            Optimized context string
        """
        # Join all parts
        full_context = "\n".join(parts)

        # If it fits, return as-is
        if len(full_context) <= self.max_context_size:
            return full_context

        # Need to prune - start from end and work backwards
        result_parts = []
        current_size = 0

        for part in parts:
            part_size = len(part)

            if current_size + part_size <= self.max_context_size:
                result_parts.append(part)
                current_size += part_size
            else:
                # Try to fit a truncated version
                remaining = self.max_context_size - current_size
                if remaining > 100:  # Only if we have meaningful space
                    truncated = part[:remaining - 50] + "\n\n... (truncated)"
                    result_parts.append(truncated)
                break

        return "\n".join(result_parts)

    def get_scope_keywords(self, project_id: str) -> List[str]:
        """Extract keywords from project scope.

        Args:
            project_id: Project ID

        Returns:
            List of keywords
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return []

        scope = project['scope']

        # Extract meaningful words (simple approach)
        # Remove common stop words
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with'
        }

        # Split on word boundaries and filter
        words = re.findall(r'\b\w+\b', scope.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def calculate_relevance_score(
        self,
        task_description: str,
        project_id: str
    ) -> float:
        """Calculate how relevant a task is to project scope.

        Args:
            task_description: Task description
            project_id: Project ID

        Returns:
            Relevance score (0-1)
        """
        scope_keywords = set(self.get_scope_keywords(project_id))
        if not scope_keywords:
            return 0.5  # No data to determine

        # Extract keywords from task
        task_words = re.findall(r'\b\w+\b', task_description.lower())
        task_keywords = set(w for w in task_words if len(w) > 2)

        if not task_keywords:
            return 0.5

        # Calculate Jaccard similarity
        intersection = scope_keywords & task_keywords
        union = scope_keywords | task_keywords

        if not union:
            return 0.5

        return len(intersection) / len(union)

    def get_exclusions(self, project_id: str) -> List[str]:
        """Extract explicit exclusions from project scope.

        Args:
            project_id: Project ID

        Returns:
            List of excluded items
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return []

        scope = project['scope']

        # Look for common exclusion patterns
        exclusion_patterns = [
            r'no\s+(\w+)',
            r'without\s+(\w+)',
            r"don't\s+(\w+)",
            r'exclude\s+(\w+)',
            r'not\s+including\s+(\w+)',
        ]

        exclusions = []
        for pattern in exclusion_patterns:
            matches = re.findall(pattern, scope.lower())
            exclusions.extend(matches)

        return exclusions

    def format_context_for_llm(
        self,
        project_id: str,
        include_sections: Dict[str, bool] = None
    ) -> str:
        """Format complete context optimized for LLM consumption.

        Args:
            project_id: Project ID
            include_sections: Dict of section flags (header, history, etc.)

        Returns:
            Formatted context string
        """
        if include_sections is None:
            include_sections = {
                'header': True,
                'history': True,
                'decisions': True,
                'patterns': True
            }

        parts = []

        if include_sections.get('header', True):
            parts.append(self.get_project_header(project_id))

        if include_sections.get('history', True):
            parts.append(self.get_relevant_history(project_id))

        if include_sections.get('decisions', True):
            parts.append(self.get_recent_decisions(project_id))

        if include_sections.get('patterns', True):
            patterns = self.get_relevant_patterns(project_id)
            if patterns:
                parts.append(patterns)

        # Remove empty parts
        parts = [p for p in parts if p.strip()]

        return self.optimize_context(parts)

    def get_summary(self, project_id: str) -> Dict[str, any]:
        """Get a summary of project context metrics.

        Args:
            project_id: Project ID

        Returns:
            Dict with summary metrics
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return {}

        stats = self.db.get_task_stats(project_id)
        learnings = self.db.get_learnings(project_id=project_id, limit=100)
        active_sessions = self.db.get_active_sessions(project_id)

        context = self.format_context_for_llm(project_id)

        return {
            'project_name': project['name'],
            'scope': project['scope'],
            'task_stats': stats,
            'learning_count': len(learnings),
            'active_sessions': len(active_sessions),
            'context_size': len(context),
            'context_utilization': len(context) / self.max_context_size,
            'created_at': project['created_at'],
            'updated_at': project['updated_at']
        }
