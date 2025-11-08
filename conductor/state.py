"""Project state management and scope checking."""

from typing import List, Dict, Tuple, Optional
from datetime import datetime
import re


class ProjectState:
    """Manages project state and tracks scope compliance."""

    def __init__(self, project_id: str, db):
        """Initialize project state manager.

        Args:
            project_id: Project ID
            db: Database instance
        """
        self.project_id = project_id
        self.db = db

    def check_scope_creep(self, task_description: str) -> Tuple[bool, str]:
        """Determine if task is within original scope.

        Args:
            task_description: Description of proposed task

        Returns:
            Tuple of (is_scope_creep, reason)
        """
        project = self.db.get_project(project_id=self.project_id)
        if not project:
            return False, "Project not found"

        original_scope = project['scope']

        # Check for explicitly excluded items
        is_excluded, reason = self.is_explicitly_excluded(
            task_description,
            original_scope
        )
        if is_excluded:
            return True, reason

        # Calculate similarity score
        scope_keywords = self.extract_keywords(original_scope)
        task_keywords = self.extract_keywords(task_description)

        similarity = self.calculate_similarity(scope_keywords, task_keywords)

        # Threshold for scope creep (adjustable)
        if similarity < 0.3:
            return True, f"Low relevance to original scope (similarity: {similarity:.2f})"

        return False, f"Within scope (similarity: {similarity:.2f})"

    def is_explicitly_excluded(
        self,
        task_description: str,
        scope: str
    ) -> Tuple[bool, str]:
        """Check if task matches explicit exclusions.

        Args:
            task_description: Task description
            scope: Project scope

        Returns:
            Tuple of (is_excluded, reason)
        """
        # Extract exclusions from scope
        exclusion_patterns = [
            (r'no\s+(\w+)', 'Explicitly excluded: no {}'),
            (r'without\s+(\w+)', 'Explicitly excluded: without {}'),
            (r"don't\s+(\w+)", "Explicitly excluded: don't {}"),
            (r'exclude\s+(\w+)', 'Explicitly excluded: exclude {}'),
            (r'not\s+including\s+(\w+)', 'Explicitly excluded: not including {}'),
        ]

        task_lower = task_description.lower()

        for pattern, message_template in exclusion_patterns:
            matches = re.findall(pattern, scope.lower())
            for match in matches:
                # Check if excluded item appears in task
                if match in task_lower or match in task_description.lower():
                    return True, message_template.format(match)

        return False, ""

    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text.

        Args:
            text: Text to extract from

        Returns:
            List of keywords
        """
        # Common stop words to ignore
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'this', 'but',
            'they', 'have', 'had', 'what', 'when', 'where', 'who', 'which',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just',
            'should', 'now'
        }

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter stop words and short words
        keywords = [
            w for w in words
            if w not in stop_words and len(w) > 2
        ]

        return keywords

    def calculate_similarity(
        self,
        keywords1: List[str],
        keywords2: List[str]
    ) -> float:
        """Calculate similarity between keyword sets.

        Uses Jaccard similarity coefficient.

        Args:
            keywords1: First keyword set
            keywords2: Second keyword set

        Returns:
            Similarity score (0-1)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def get_completion_path(self) -> List[Dict]:
        """Generate optimal path to project completion.

        Returns:
            Ordered list of tasks to complete
        """
        # Get all pending and in-progress tasks
        pending = self.db.get_tasks(self.project_id, status='pending')
        in_progress = self.db.get_tasks(self.project_id, status='in_progress')

        # Priority: in_progress first, then pending
        path = []

        # Add in-progress (highest priority)
        for task in in_progress:
            path.append({
                'task_id': task['id'],
                'description': task['description'],
                'status': task['status'],
                'priority': 'high',
                'reason': 'Already in progress'
            })

        # Add pending tasks
        for task in pending:
            path.append({
                'task_id': task['id'],
                'description': task['description'],
                'status': task['status'],
                'priority': 'normal',
                'reason': 'Pending'
            })

        return path

    def get_blockers(self) -> List[Dict]:
        """Get all blocked tasks and their reasons.

        Returns:
            List of blocked task dicts
        """
        return self.db.get_tasks(self.project_id, status='blocked')

    def get_progress_percentage(self) -> int:
        """Calculate overall progress percentage.

        Returns:
            Progress percentage (0-100)
        """
        stats = self.db.get_task_stats(self.project_id)

        if stats['total'] == 0:
            return 0

        return int((stats['completed'] / stats['total']) * 100)

    def get_estimated_remaining_tasks(self) -> int:
        """Get count of remaining tasks.

        Returns:
            Number of incomplete tasks
        """
        stats = self.db.get_task_stats(self.project_id)
        return stats['pending'] + stats['in_progress'] + stats['blocked']

    def suggest_next_action(self) -> Optional[Dict]:
        """Suggest the next concrete action to take.

        Returns:
            Dict with suggestion or None
        """
        # Check for in-progress tasks first
        in_progress = self.db.get_tasks(self.project_id, status='in_progress')
        if in_progress:
            task = in_progress[0]
            return {
                'action': 'continue',
                'task_id': task['id'],
                'description': task['description'],
                'reason': 'Complete in-progress task before starting new work'
            }

        # Check for blocked tasks - maybe they can be unblocked
        blocked = self.db.get_tasks(self.project_id, status='blocked')
        if blocked:
            task = blocked[0]
            return {
                'action': 'unblock',
                'task_id': task['id'],
                'description': task['description'],
                'reason': f"Blocked: {task.get('blocked_reason', 'Unknown')}"
            }

        # Start next pending task
        pending = self.db.get_tasks(self.project_id, status='pending')
        if pending:
            task = pending[0]
            return {
                'action': 'start',
                'task_id': task['id'],
                'description': task['description'],
                'reason': 'Next task in queue'
            }

        # Nothing to do
        return {
            'action': 'none',
            'reason': 'All tasks completed! 🎉'
        }

    def mark_task_complete(self, task_id: int, session_id: str = None):
        """Mark a task as completed.

        Args:
            task_id: Task ID
            session_id: Session ID (to increment counter)
        """
        self.db.update_task(task_id, status='completed')

        if session_id:
            self.db.increment_session_tasks(session_id)

    def mark_task_blocked(self, task_id: int, reason: str):
        """Mark a task as blocked.

        Args:
            task_id: Task ID
            reason: Reason for blocking
        """
        self.db.update_task(task_id, status='blocked', blocked_reason=reason)

    def mark_task_in_progress(self, task_id: int):
        """Mark a task as in progress.

        Args:
            task_id: Task ID
        """
        self.db.update_task(task_id, status='in_progress')

    def get_state_summary(self) -> Dict:
        """Get complete state summary.

        Returns:
            Dict with state information
        """
        project = self.db.get_project(project_id=self.project_id)
        stats = self.db.get_task_stats(self.project_id)
        next_action = self.suggest_next_action()
        blockers = self.get_blockers()

        return {
            'project': project,
            'stats': stats,
            'progress': self.get_progress_percentage(),
            'remaining_tasks': self.get_estimated_remaining_tasks(),
            'next_action': next_action,
            'blocker_count': len(blockers),
            'blockers': blockers
        }

    def get_scope_compliance_report(self) -> Dict:
        """Generate scope compliance report.

        Returns:
            Dict with compliance metrics
        """
        all_tasks = self.db.get_tasks(
            self.project_id,
            include_scope_creep=True
        )

        scope_creep_tasks = [t for t in all_tasks if t['is_scope_creep']]

        completed_tasks = [t for t in all_tasks if t['status'] == 'completed']
        completed_scope_creep = [
            t for t in completed_tasks if t['is_scope_creep']
        ]

        return {
            'total_tasks': len(all_tasks),
            'scope_creep_tasks': len(scope_creep_tasks),
            'scope_creep_percentage': (
                len(scope_creep_tasks) / len(all_tasks) * 100
                if all_tasks else 0
            ),
            'completed_scope_creep': len(completed_scope_creep),
            'compliance_score': (
                (len(all_tasks) - len(scope_creep_tasks)) / len(all_tasks) * 100
                if all_tasks else 100
            )
        }

    def get_velocity_metrics(self) -> Dict:
        """Calculate velocity metrics.

        Returns:
            Dict with velocity information
        """
        completed = self.db.get_tasks(self.project_id, status='completed')

        if not completed:
            return {
                'completed_count': 0,
                'avg_completion_time': None,
                'estimated_completion_date': None
            }

        # Calculate average time to complete (if we have timestamps)
        completion_times = []
        for task in completed:
            if task.get('completed_at') and task.get('created_at'):
                created = datetime.fromisoformat(task['created_at'])
                completed_at = datetime.fromisoformat(task['completed_at'])
                delta = (completed_at - created).total_seconds() / 3600  # hours
                completion_times.append(delta)

        avg_time = sum(completion_times) / len(completion_times) if completion_times else None

        # Estimate completion
        remaining = self.get_estimated_remaining_tasks()
        estimated_completion = None

        if avg_time and remaining:
            hours_remaining = avg_time * remaining
            estimated_completion = datetime.now().timestamp() + (hours_remaining * 3600)

        return {
            'completed_count': len(completed),
            'avg_completion_time_hours': avg_time,
            'estimated_completion_timestamp': estimated_completion,
            'remaining_tasks': remaining
        }
