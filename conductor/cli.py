"""CLI interface for Claude Code Conductor."""

import click
import sys
import os
from pathlib import Path
import pyperclip
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
import json

from .db import Database
from .templates import PromptTemplate
from .context import ContextManager
from .state import ProjectState
from .registry import Registry
from .monitor import ProgressMonitor
from .sync import Sync


console = Console()


def get_db():
    """Get database instance."""
    db_path = os.environ.get('CONDUCTOR_DB_PATH')
    return Database(db_path)


def get_default_project():
    """Get default project from environment or config."""
    return os.environ.get('CONDUCTOR_PROJECT')


def format_output(data, output_format='human'):
    """Format output based on format preference.

    Args:
        data: Data to output
        output_format: 'human' or 'json'
    """
    if output_format == 'json':
        console.print_json(json.dumps(data, indent=2))
    else:
        return data  # Let caller handle human-readable format


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Claude Code Conductor - Orchestrate and enhance Claude Code sessions."""
    pass


@cli.command()
@click.argument('project_name')
@click.option('--scope', required=True, help='Project scope description')
def init(project_name, scope):
    """Initialize a new project."""
    db = get_db()

    try:
        project_id = db.create_project(project_name, scope)
        console.print(f"✓ Project '[bold green]{project_name}[/]' initialized", style="green")
        console.print(f"  ID: {project_id}")
        console.print(f"  Scope: {scope}")

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('task_description')
@click.option('-p', '--project', help='Project name')
@click.option('--force', is_flag=True, help='Force add even if scope creep detected')
def add_task(task_description, project, force):
    """Add a new task to a project."""
    db = get_db()

    project_name = project or get_default_project()
    if not project_name:
        console.print("✗ Error: No project specified. Use -p or set CONDUCTOR_PROJECT", style="red")
        sys.exit(1)

    proj = db.get_project(name=project_name)
    if not proj:
        console.print(f"✗ Error: Project '{project_name}' not found", style="red")
        sys.exit(1)

    # Check for scope creep
    state = ProjectState(proj['id'], db)
    is_creep, reason = state.check_scope_creep(task_description)

    if is_creep and not force:
        console.print(f"⚠️  Warning: Task appears to be out of scope", style="yellow")
        console.print(f"  Reason: {reason}")

        if not click.confirm("Add anyway?", default=False):
            console.print("✗ Task not added", style="red")
            sys.exit(1)

    task_id = db.add_task(proj['id'], task_description, is_scope_creep=is_creep)

    if is_creep:
        console.print(f"✓ Task added (marked as scope creep)", style="yellow")
    else:
        console.print(f"✓ Task added (within scope)", style="green")

    console.print(f"  ID: {task_id}")


@cli.command()
@click.argument('task_id', type=int)
@click.option('-p', '--project', help='Project name')
def complete(task_id, project):
    """Mark a task as completed."""
    db = get_db()

    try:
        db.update_task(task_id, status='completed')
        console.print(f"✓ Task {task_id} marked as completed", style="green")

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('-p', '--project', help='Project name')
@click.option('--format', type=click.Choice(['human', 'json']), default='human')
def status(project, format):
    """Show project status."""
    db = get_db()

    if project:
        projects = [db.get_project(name=project)]
        if not projects[0]:
            console.print(f"✗ Error: Project '{project}' not found", style="red")
            sys.exit(1)
    else:
        projects = db.get_all_projects()

    if not projects:
        console.print("No projects found. Create one with: conductor init <name> --scope \"...\"")
        return

    for proj in projects:
        if not proj:
            continue

        stats = db.get_task_stats(proj['id'])

        # Create status display
        if format == 'json':
            data = {
                'name': proj['name'],
                'scope': proj['scope'],
                'stats': stats,
                'created_at': proj['created_at']
            }
            console.print_json(json.dumps(data, indent=2))
        else:
            # Human-readable format
            progress = int(stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0

            console.print(f"\n[bold]{proj['name']}[/] [dim]({_format_age(proj['created_at'])})[/]")
            console.print(f"  Scope: {proj['scope']}")
            console.print(f"  Progress: {progress}% ({stats['completed']}/{stats['total']} tasks)")

            # Show task breakdown
            tasks = db.get_tasks(proj['id'])

            if tasks:
                console.print()

                for task in tasks:
                    if task['status'] == 'completed':
                        icon = "✓"
                        style = "dim green"
                    elif task['status'] == 'in_progress':
                        icon = "⟳"
                        style = "bold cyan"
                    elif task['status'] == 'blocked':
                        icon = "🚫"
                        style = "red"
                    else:
                        icon = "○"
                        style = "white"

                    desc = task['description']
                    if len(desc) > 70:
                        desc = desc[:67] + "..."

                    console.print(f"  {icon} {desc}", style=style)

                    if task['status'] == 'in_progress':
                        console.print(f"     [dim](in progress)[/]", style="cyan")
                    elif task['status'] == 'blocked' and task.get('blocked_reason'):
                        console.print(f"     [dim]Blocked: {task['blocked_reason']}[/]", style="red")


@cli.command()
@click.argument('template_name')
@click.option('-p', '--project', help='Project name')
@click.option('-v', '--var', multiple=True, help='Variable in format key=value')
@click.option('--no-copy', is_flag=True, help='Do not copy to clipboard')
@click.option('--output', type=click.Path(), help='Write to file instead of clipboard')
def prompt(template_name, project, var, no_copy, output):
    """Generate an expanded prompt from a template."""
    db = get_db()

    # Parse variables
    variables = {}
    for v in var:
        if '=' not in v:
            console.print(f"✗ Error: Invalid variable format '{v}'. Use key=value", style="red")
            sys.exit(1)

        key, value = v.split('=', 1)
        variables[key] = value

    # Get project context if specified
    project_name = project or get_default_project()
    project_id = None

    if project_name:
        proj = db.get_project(name=project_name)
        if proj:
            project_id = proj['id']

            # Build context
            ctx_mgr = ContextManager(db)
            context = ctx_mgr.format_context_for_llm(project_id)
            variables['context'] = context

    # Expand template
    templates = PromptTemplate(db)

    try:
        expanded = templates.expand(template_name, variables, variables.get('context'))

        # Output
        if output:
            Path(output).write_text(expanded)
            console.print(f"✓ Prompt written to {output}", style="green")
        elif not no_copy:
            pyperclip.copy(expanded)
            console.print(f"✓ Prompt copied to clipboard ({len(expanded)} chars)", style="green")
        else:
            console.print(expanded)

        if project_name:
            console.print(f"  [dim]With context from project: {project_name}[/]")

    except ValueError as e:
        console.print(f"✗ Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('task_description')
@click.option('-p', '--project', required=True, help='Project name')
def scope_check(task_description, project):
    """Check if a task is within project scope."""
    db = get_db()

    proj = db.get_project(name=project)
    if not proj:
        console.print(f"✗ Error: Project '{project}' not found", style="red")
        sys.exit(1)

    state = ProjectState(proj['id'], db)
    is_creep, reason = state.check_scope_creep(task_description)

    if is_creep:
        console.print("⚠️  [bold yellow]Outside scope[/]", style="yellow")
        console.print(f"  Reason: {reason}")
        sys.exit(1)
    else:
        console.print("✓ [bold green]Within scope[/]", style="green")
        console.print(f"  {reason}")


@cli.command()
@click.option('-p', '--project', help='Project name')
@click.option('--category', help='Filter by category')
def tools(project, category):
    """List relevant tools for current project/task."""
    db = get_db()

    project_name = project or get_default_project()

    # Get context
    context = ""
    if project_name:
        proj = db.get_project(name=project_name)
        if proj:
            # Build context from current tasks
            tasks = db.get_tasks(proj['id'], status='in_progress')
            if tasks:
                context = " ".join(t['description'] for t in tasks)

    registry = Registry()
    all_tools = registry.get_all_tools(context, category)

    # Display MCP servers
    if all_tools['mcp_servers']:
        console.print("\n[bold]MCP Servers:[/]")

        table = Table(show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Category")
        table.add_column("Description")
        table.add_column("Relevance", justify="right")

        for server in all_tools['mcp_servers']:
            relevance = server.get('relevance', 0)
            rel_display = f"{relevance:.2f}" if context else "-"

            table.add_row(
                server['name'],
                server.get('category', ''),
                server.get('description', ''),
                rel_display
            )

        console.print(table)

    # Display skills
    if all_tools['skills']:
        console.print("\n[bold]Skills:[/]")

        table = Table(show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Category")
        table.add_column("When to use")

        for skill in all_tools['skills'][:10]:  # Limit to top 10
            table.add_row(
                skill['name'],
                skill.get('category', ''),
                skill.get('when', '')
            )

        console.print(table)

    # Display subagents
    if all_tools['subagents']:
        console.print("\n[bold]Subagents:[/]")

        table = Table(show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Triggers")
        table.add_column("Description")

        for agent in all_tools['subagents'][:5]:  # Limit to top 5
            table.add_row(
                agent['name'],
                agent.get('trigger', ''),
                agent.get('description', '')
            )

        console.print(table)


@cli.command()
@click.option('--push', is_flag=True, help='Push local state to remote')
@click.option('--pull', is_flag=True, help='Pull remote state to local')
def sync(push, pull):
    """Synchronize state across machines."""
    syncer = Sync()

    if not push and not pull:
        # Show status
        status = syncer.get_sync_status()

        console.print(f"[bold]Sync Status[/]")
        console.print(f"  Method: {status['method']}")
        console.print(f"  Has local changes: {status['has_local_changes']}")

        if status.get('last_sync'):
            console.print(f"  Last sync: {status['last_sync']}")

        console.print(f"  Sync count: {status['sync_count']}")

        return

    if push:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Pushing state...", total=None)

            result = syncer.push_state()

        if result['success']:
            console.print(f"✓ State pushed ({result['method']})", style="green")
            syncer.mark_synced()
        else:
            console.print(f"✗ Push failed: {result.get('error', 'Unknown error')}", style="red")
            sys.exit(1)

    if pull:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Pulling state...", total=None)

            result = syncer.pull_state()

        if result['success']:
            console.print(f"✓ State pulled ({result['method']})", style="green")
        else:
            console.print(f"✗ Pull failed: {result.get('error', 'Unknown error')}", style="red")
            sys.exit(1)


@cli.command()
@click.argument('action', type=click.Choice(['start', 'end']))
@click.option('-p', '--project', required=True, help='Project name')
def session(action, project):
    """Start or end a work session."""
    db = get_db()

    proj = db.get_project(name=project)
    if not proj:
        console.print(f"✗ Error: Project '{project}' not found", style="red")
        sys.exit(1)

    if action == 'start':
        session_id = db.start_session(proj['id'])
        console.print(f"✓ Session {session_id[:8]} started for {project}", style="green")
        console.print(f"  Use 'conductor session end -p {project}' to end this session")

    elif action == 'end':
        # Find active session
        active = db.get_active_sessions(proj['id'])

        if not active:
            console.print(f"✗ No active session for project '{project}'", style="red")
            sys.exit(1)

        session_id = active[0]['id']
        db.end_session(session_id)

        console.print(f"✓ Session {session_id[:8]} ended", style="green")

        # Show session summary
        monitor = ProgressMonitor(db)
        analysis = monitor.analyze_session(session_id)

        console.print(f"  Duration: {analysis['duration_hours']:.1f} hours")
        console.print(f"  Tasks completed: {analysis['tasks_completed']}")


@cli.command()
@click.option('-p', '--project', help='Project name')
def report(project):
    """Generate productivity report."""
    db = get_db()

    project_name = project or get_default_project()
    if not project_name:
        console.print("✗ Error: No project specified", style="red")
        sys.exit(1)

    proj = db.get_project(name=project_name)
    if not proj:
        console.print(f"✗ Error: Project '{project_name}' not found", style="red")
        sys.exit(1)

    monitor = ProgressMonitor(db)
    report_data = monitor.get_productivity_report(proj['id'])

    # Display report
    console.print(f"\n[bold]Productivity Report: {report_data['project']['name']}[/]\n")

    # Completion
    console.print("[bold]Completion:[/]")
    console.print(f"  Progress: {report_data['completion']['percentage']}%")
    console.print(f"  Completed: {report_data['completion']['completed']}/{report_data['completion']['total']}")
    console.print(f"  Remaining: {report_data['completion']['remaining']}")

    # Health
    health = report_data['health']
    health_color = {
        'healthy': 'green',
        'needs_attention': 'yellow',
        'at_risk': 'orange',
        'critical': 'red'
    }[health['status']]

    console.print(f"\n[bold]Health:[/]")
    console.print(f"  Score: [{health_color}]{health['score']}/100[/]")
    console.print(f"  Status: [{health_color}]{health['status']}[/]")

    if health['issues']:
        console.print("  Issues:")
        for issue in health['issues']:
            console.print(f"    - {issue}")

    # Velocity
    velocity = report_data['velocity']
    console.print(f"\n[bold]Velocity:[/]")
    console.print(f"  Tasks per day: {velocity['tasks_per_day']}")

    if velocity['estimated_days_to_completion']:
        console.print(f"  Est. completion: {velocity['estimated_days_to_completion']} days")

    # Recommendations
    recommendations = monitor.get_recommendations(proj['id'])
    if recommendations:
        console.print(f"\n[bold]Recommendations:[/]")
        for rec in recommendations:
            console.print(f"  • {rec}")


@cli.command()
def templates():
    """List available templates."""
    db = get_db()
    tmpl = PromptTemplate(db)

    all_templates = tmpl.list_templates()

    table = Table(show_header=True, title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Variables")
    table.add_column("Usage", justify="right")

    for t in all_templates:
        variables = ", ".join(t.get('variables', []))
        usage = str(t.get('usage_count', 0))

        table.add_row(
            t['name'],
            t['type'],
            variables,
            usage
        )

    console.print(table)


def _format_age(timestamp):
    """Format timestamp as age string."""
    from datetime import datetime

    dt = datetime.fromisoformat(timestamp)
    age = datetime.now() - dt

    if age.days > 0:
        return f"{age.days} days old"
    elif age.seconds > 3600:
        return f"{age.seconds // 3600} hours old"
    else:
        return f"{age.seconds // 60} minutes old"


if __name__ == '__main__':
    cli()
