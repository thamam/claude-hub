"""Progress monitoring and productivity analytics."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ProgressMonitor:
    """Monitors project progress and session productivity."""

    def __init__(self, db):
        """Initialize progress monitor.

        Args:
            db: Database instance
        """
        self.db = db

    def analyze_session(self, session_id: str) -> Dict:
        """Analyze session productivity.

        Args:
            session_id: Session ID

        Returns:
            Dict with session metrics
        """
        session = self.db.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}

        # Calculate duration
        started = datetime.fromisoformat(session['started_at'])

        if session.get('ended_at'):
            ended = datetime.fromisoformat(session['ended_at'])
            duration = (ended - started).total_seconds() / 3600  # hours
            is_active = False
        else:
            ended = datetime.now()
            duration = (ended - started).total_seconds() / 3600  # hours
            is_active = True

        # Get tasks completed in this session
        tasks_completed = session['tasks_completed']

        # Calculate productivity metrics
        tasks_per_hour = tasks_completed / duration if duration > 0 else 0

        return {
            'session_id': session_id,
            'project_id': session['project_id'],
            'machine_id': session['machine_id'],
            'started_at': session['started_at'],
            'ended_at': session.get('ended_at'),
            'duration_hours': round(duration, 2),
            'tasks_completed': tasks_completed,
            'tasks_per_hour': round(tasks_per_hour, 2),
            'is_active': is_active
        }

    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """Get all sessions for a project with analytics.

        Args:
            project_id: Project ID

        Returns:
            List of session analytics
        """
        # Get all sessions (active and ended)
        active_sessions = self.db.get_active_sessions(project_id)

        # Get ended sessions (need custom query)
        cursor = self.db.conn.cursor()
        cursor.execute(
            """SELECT * FROM sessions
               WHERE project_id = ? AND ended_at IS NOT NULL
               ORDER BY started_at DESC""",
            (project_id,)
        )
        ended_sessions = [dict(row) for row in cursor.fetchall()]

        all_sessions = active_sessions + ended_sessions

        # Analyze each session
        analytics = []
        for session in all_sessions:
            session_data = self.analyze_session(session['id'])
            analytics.append(session_data)

        return analytics

    def suggest_next_action(self, project_id: str) -> Dict:
        """Suggest concrete next action.

        Args:
            project_id: Project ID

        Returns:
            Dict with suggestion
        """
        from .state import ProjectState

        state = ProjectState(project_id, self.db)
        return state.suggest_next_action()

    def detect_stuck_patterns(self, project_id: str) -> List[Dict]:
        """Detect if project is stuck.

        Args:
            project_id: Project ID

        Returns:
            List of stuck indicators
        """
        indicators = []

        # Check for long-running in-progress tasks
        in_progress = self.db.get_tasks(project_id, status='in_progress')

        for task in in_progress:
            created = datetime.fromisoformat(task['created_at'])
            age_hours = (datetime.now() - created).total_seconds() / 3600

            if age_hours > 24:  # Task in progress for more than 24 hours
                indicators.append({
                    'type': 'long_running_task',
                    'severity': 'high',
                    'task_id': task['id'],
                    'description': task['description'],
                    'age_hours': round(age_hours, 1),
                    'suggestion': 'Consider breaking this task into smaller pieces or marking as blocked'
                })

        # Check for many blocked tasks
        blocked = self.db.get_tasks(project_id, status='blocked')
        if len(blocked) > 3:
            indicators.append({
                'type': 'many_blocked_tasks',
                'severity': 'high',
                'count': len(blocked),
                'suggestion': 'Focus on unblocking tasks before adding new work'
            })

        # Check for no recent progress
        stats = self.db.get_task_stats(project_id)
        if stats['completed'] == 0 and stats['total'] > 0:
            project = self.db.get_project(project_id=project_id)
            created = datetime.fromisoformat(project['created_at'])
            age_days = (datetime.now() - created).days

            if age_days > 1:
                indicators.append({
                    'type': 'no_completed_tasks',
                    'severity': 'medium',
                    'age_days': age_days,
                    'suggestion': 'Complete at least one task to build momentum'
                })

        # Check for scope creep
        all_tasks = self.db.get_tasks(project_id, include_scope_creep=True)
        scope_creep_tasks = [t for t in all_tasks if t['is_scope_creep']]

        if scope_creep_tasks:
            indicators.append({
                'type': 'scope_creep',
                'severity': 'medium',
                'count': len(scope_creep_tasks),
                'percentage': round(len(scope_creep_tasks) / len(all_tasks) * 100, 1),
                'suggestion': 'Review scope and remove out-of-scope tasks'
            })

        return indicators

    def get_velocity(self, project_id: str, days: int = 7) -> Dict:
        """Calculate project velocity.

        Args:
            project_id: Project ID
            days: Number of days to analyze

        Returns:
            Dict with velocity metrics
        """
        # Get completed tasks in time window
        completed = self.db.get_tasks(project_id, status='completed')

        cutoff = datetime.now() - timedelta(days=days)

        recent_completed = [
            t for t in completed
            if t.get('completed_at') and
            datetime.fromisoformat(t['completed_at']) >= cutoff
        ]

        # Calculate velocity
        tasks_per_day = len(recent_completed) / days if days > 0 else 0

        # Estimate remaining time
        stats = self.db.get_task_stats(project_id)
        remaining = stats['pending'] + stats['in_progress']

        if tasks_per_day > 0:
            estimated_days = remaining / tasks_per_day
        else:
            estimated_days = None

        return {
            'period_days': days,
            'tasks_completed': len(recent_completed),
            'tasks_per_day': round(tasks_per_day, 2),
            'remaining_tasks': remaining,
            'estimated_days_to_completion': (
                round(estimated_days, 1) if estimated_days else None
            )
        }

    def get_project_health(self, project_id: str) -> Dict:
        """Get overall project health score.

        Args:
            project_id: Project ID

        Returns:
            Dict with health metrics
        """
        health = {
            'score': 100,
            'status': 'healthy',
            'issues': []
        }

        # Check various health indicators
        stats = self.db.get_task_stats(project_id)

        # Penalize for blocked tasks
        if stats['blocked'] > 0:
            blocked_ratio = stats['blocked'] / stats['total'] if stats['total'] > 0 else 0
            penalty = int(blocked_ratio * 30)
            health['score'] -= penalty
            health['issues'].append(f"{stats['blocked']} blocked tasks")

        # Penalize for stuck patterns
        stuck_patterns = self.detect_stuck_patterns(project_id)
        if stuck_patterns:
            high_severity = sum(1 for p in stuck_patterns if p['severity'] == 'high')
            penalty = high_severity * 15 + (len(stuck_patterns) - high_severity) * 5
            health['score'] -= penalty
            health['issues'].append(f"{len(stuck_patterns)} stuck indicators")

        # Check velocity
        velocity = self.get_velocity(project_id)
        if velocity['tasks_per_day'] < 0.5:  # Less than 1 task per 2 days
            health['score'] -= 10
            health['issues'].append("Low velocity")

        # Check scope compliance
        all_tasks = self.db.get_tasks(project_id, include_scope_creep=True)
        scope_creep = [t for t in all_tasks if t['is_scope_creep']]

        if scope_creep:
            creep_ratio = len(scope_creep) / len(all_tasks)
            if creep_ratio > 0.2:  # More than 20% scope creep
                penalty = int(creep_ratio * 20)
                health['score'] -= penalty
                health['issues'].append(f"{len(scope_creep)} scope creep tasks")

        # Ensure score is in valid range
        health['score'] = max(0, min(100, health['score']))

        # Determine status
        if health['score'] >= 80:
            health['status'] = 'healthy'
        elif health['score'] >= 60:
            health['status'] = 'needs_attention'
        elif health['score'] >= 40:
            health['status'] = 'at_risk'
        else:
            health['status'] = 'critical'

        return health

    def get_productivity_report(self, project_id: str) -> Dict:
        """Generate comprehensive productivity report.

        Args:
            project_id: Project ID

        Returns:
            Dict with full report
        """
        project = self.db.get_project(project_id=project_id)
        if not project:
            return {'error': 'Project not found'}

        stats = self.db.get_task_stats(project_id)
        velocity = self.get_velocity(project_id)
        health = self.get_project_health(project_id)
        stuck_patterns = self.detect_stuck_patterns(project_id)
        sessions = self.get_project_sessions(project_id)

        # Calculate total time spent
        total_hours = sum(s['duration_hours'] for s in sessions)

        # Calculate completion percentage
        completion_pct = (
            int(stats['completed'] / stats['total'] * 100)
            if stats['total'] > 0 else 0
        )

        return {
            'project': {
                'id': project_id,
                'name': project['name'],
                'scope': project['scope'],
                'created_at': project['created_at'],
                'updated_at': project['updated_at']
            },
            'completion': {
                'percentage': completion_pct,
                'completed': stats['completed'],
                'total': stats['total'],
                'remaining': stats['pending'] + stats['in_progress']
            },
            'health': health,
            'velocity': velocity,
            'stuck_patterns': stuck_patterns,
            'time': {
                'total_hours': round(total_hours, 2),
                'session_count': len(sessions),
                'avg_session_hours': (
                    round(total_hours / len(sessions), 2)
                    if sessions else 0
                )
            },
            'status_breakdown': {
                'pending': stats['pending'],
                'in_progress': stats['in_progress'],
                'completed': stats['completed'],
                'blocked': stats['blocked']
            }
        }

    def get_recommendations(self, project_id: str) -> List[str]:
        """Get actionable recommendations.

        Args:
            project_id: Project ID

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get health metrics
        health = self.get_project_health(project_id)
        stats = self.db.get_task_stats(project_id)
        stuck_patterns = self.detect_stuck_patterns(project_id)
        velocity = self.get_velocity(project_id)

        # Based on health score
        if health['score'] < 60:
            recommendations.append(
                "⚠️  Project health is concerning. Address blocking issues immediately."
            )

        # Based on stuck patterns
        for pattern in stuck_patterns:
            if pattern['type'] == 'long_running_task':
                recommendations.append(
                    f"Consider breaking down or reassessing: {pattern['description'][:50]}..."
                )
            elif pattern['type'] == 'many_blocked_tasks':
                recommendations.append(
                    "Focus on unblocking tasks before starting new work"
                )

        # Based on velocity
        if velocity['tasks_per_day'] < 0.5:
            recommendations.append(
                "Velocity is low. Break tasks into smaller, achievable chunks."
            )

        # Based on task status
        if stats['in_progress'] > 2:
            recommendations.append(
                "Multiple tasks in progress. Focus on completing one before starting another."
            )

        if stats['blocked'] > 0:
            recommendations.append(
                f"You have {stats['blocked']} blocked tasks. Work on unblocking them."
            )

        # Scope compliance
        all_tasks = self.db.get_tasks(project_id, include_scope_creep=True)
        scope_creep = [t for t in all_tasks if t['is_scope_creep']]

        if scope_creep:
            recommendations.append(
                f"Review {len(scope_creep)} scope creep tasks - remove or adjust scope."
            )

        # If healthy and progressing well
        if health['score'] >= 80 and velocity['tasks_per_day'] >= 1.0:
            recommendations.append(
                "✓ Project is progressing well. Keep up the momentum!"
            )

        # If nothing else, suggest next action
        if not recommendations:
            from .state import ProjectState
            state = ProjectState(project_id, self.db)
            next_action = state.suggest_next_action()

            if next_action:
                recommendations.append(
                    f"Next: {next_action.get('action', 'continue').title()} - "
                    f"{next_action.get('description', '')[:50]}..."
                )

        return recommendations
