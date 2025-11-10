"""Prompt template engine for Claude Code Conductor."""

from typing import Dict, List, Optional
import re
from pathlib import Path


class PromptTemplate:
    """Manages prompt templates with variable substitution and context injection."""

    BUILTIN_TEMPLATES = {
        "debug": """Find and fix the bug systematically:
1. Reproduce the issue
2. Form hypotheses about the cause
3. Test each hypothesis with minimal changes
4. Verify the fix doesn't break other functionality
5. Add a test to prevent regression

Current context: {context}
Specific issue: {issue}""",

        "implement": """Implement {feature} following these principles:
- Follow existing code patterns in the project
- YAGNI: Only implement what's explicitly requested
- Include appropriate error handling
- Add docstrings for new functions/classes
- Write unit tests for new functionality

Project context: {context}
Existing patterns to follow: {patterns}""",

        "refactor": """Refactor code for {principle}:
- Maintain ALL existing functionality
- Improve {metric} without sacrificing readability
- Add/update tests to ensure no regression
- Document significant changes

Current implementation: {current}
Target improvement: {target}""",

        "continue": """Continue working on {project}:

Progress so far:
{completed_tasks}

Currently working on:
{current_task}

Next steps:
{next_steps}

Project scope: {scope}
Stay within scope - do not add: {out_of_scope}""",

        "review": """Review code for:
1. Security vulnerabilities
2. Performance issues
3. Logic errors
4. Missing edge cases
5. Code quality issues

Be critical and specific. Provide actionable feedback.
Context: {context}""",

        "test": """Write comprehensive tests for {feature}:
- Unit tests for individual functions/methods
- Integration tests for component interaction
- Edge cases and error handling
- Mock external dependencies appropriately

Code to test:
{code}

Follow testing patterns from: {patterns}""",

        "optimize": """Optimize {target} for {metric}:
- Profile to identify bottlenecks
- Apply appropriate optimizations
- Measure impact with benchmarks
- Ensure correctness is maintained

Current implementation: {current}
Performance requirements: {requirements}""",

        "document": """Document {feature}:
- Clear description of purpose and behavior
- Usage examples with common scenarios
- Parameter and return value documentation
- Note any important limitations or gotchas

Code to document:
{code}""",

        "plan": """Create an implementation plan for {feature}:
- Break down into concrete, actionable steps
- Identify dependencies and order of operations
- List files that need to be created/modified
- Note any potential challenges

Requirements:
{requirements}

Existing codebase context:
{context}""",

        "fix-scope": """This task appears to be outside the original project scope.

Original scope: {scope}

Proposed task: {task}

Please either:
1. Explain how this task IS within scope
2. Adjust the project scope explicitly to include this
3. Create a separate project for this feature

Remember: Scope creep kills projects. Stay focused.""",
    }

    def __init__(self, db):
        """Initialize template engine.

        Args:
            db: Database instance for loading custom templates
        """
        self.db = db

    def list_templates(self) -> List[Dict]:
        """List all available templates (builtin + custom).

        Returns:
            List of dicts with template info
        """
        templates = []

        # Add builtin templates
        for name in self.BUILTIN_TEMPLATES:
            variables = self._extract_variables(self.BUILTIN_TEMPLATES[name])
            templates.append({
                'name': name,
                'type': 'builtin',
                'variables': variables,
                'usage_count': 0
            })

        # Add custom templates
        custom = self.db.get_all_templates()
        for tmpl in custom:
            tmpl['type'] = 'custom'
            templates.append(tmpl)

        return templates

    def get_template(self, name: str) -> Optional[str]:
        """Get template content by name.

        Args:
            name: Template name

        Returns:
            Template content or None
        """
        # Check custom templates first
        custom = self.db.get_template(name)
        if custom:
            return custom['content']

        # Fall back to builtin
        return self.BUILTIN_TEMPLATES.get(name)

    def expand(
        self,
        template_name: str,
        variables: Dict[str, str] = None,
        project_context: str = None
    ) -> str:
        """Expand a template with variables and context.

        Args:
            template_name: Name of template to expand
            variables: Dict of variable replacements
            project_context: Project context to inject

        Returns:
            Expanded prompt string
        """
        template_content = self.get_template(template_name)
        if not template_content:
            raise ValueError(f"Template '{template_name}' not found")

        # Increment usage count if it's a custom template
        if template_name not in self.BUILTIN_TEMPLATES:
            self.db.increment_template_usage(template_name)

        variables = variables or {}

        # Add project context if provided and not already in variables
        if project_context and 'context' not in variables:
            variables['context'] = project_context

        # Find all required variables
        required_vars = self._extract_variables(template_content)

        # Substitute variables
        result = template_content
        for var in required_vars:
            placeholder = f"{{{var}}}"
            if var in variables:
                result = result.replace(placeholder, str(variables[var]))
            # Leave placeholder if no value provided (user can fill in)

        return result

    def create_template(
        self,
        name: str,
        content: str,
        variables: List[str] = None
    ):
        """Create a custom template.

        Args:
            name: Template name
            content: Template content with {variable} placeholders
            variables: List of variable names (auto-detected if not provided)
        """
        if name in self.BUILTIN_TEMPLATES:
            raise ValueError(f"Cannot override builtin template '{name}'")

        if variables is None:
            variables = self._extract_variables(content)

        self.db.add_template(name, content, variables)

    def _extract_variables(self, template: str) -> List[str]:
        """Extract variable names from template.

        Args:
            template: Template content

        Returns:
            List of variable names
        """
        # Find all {variable} patterns
        pattern = r'\{(\w+)\}'
        matches = re.findall(pattern, template)
        return sorted(set(matches))

    def render_with_context(
        self,
        template_name: str,
        variables: Dict[str, str],
        project_id: str = None,
        include_scope: bool = True,
        include_progress: bool = True,
        include_learnings: bool = True
    ) -> str:
        """Render template with full project context.

        Args:
            template_name: Template name
            variables: Variable values
            project_id: Project to get context from
            include_scope: Include project scope
            include_progress: Include task progress
            include_learnings: Include relevant learnings

        Returns:
            Fully expanded prompt
        """
        variables = variables.copy()

        if project_id:
            # Build rich context
            context_parts = []

            if include_scope:
                project = self.db.get_project(project_id=project_id)
                if project:
                    context_parts.append(f"Project: {project['name']}")
                    context_parts.append(f"Scope: {project['scope']}")

            if include_progress:
                stats = self.db.get_task_stats(project_id)
                if stats['total'] > 0:
                    completed_pct = int(stats['completed'] / stats['total'] * 100)
                    context_parts.append(
                        f"Progress: {completed_pct}% "
                        f"({stats['completed']}/{stats['total']} tasks)"
                    )

                # Add current tasks
                in_progress = self.db.get_tasks(project_id, status='in_progress')
                if in_progress:
                    context_parts.append("\nIn progress:")
                    for task in in_progress:
                        context_parts.append(f"  - {task['description']}")

                pending = self.db.get_tasks(project_id, status='pending')
                if pending:
                    context_parts.append("\nPending tasks:")
                    for task in pending[:5]:  # Show first 5
                        context_parts.append(f"  - {task['description']}")
                    if len(pending) > 5:
                        context_parts.append(f"  ... and {len(pending) - 5} more")

            if include_learnings:
                learnings = self.db.get_learnings(project_id=project_id, limit=5)
                if learnings:
                    context_parts.append("\nRecent learnings:")
                    for learning in learnings:
                        context_parts.append(f"  - {learning['pattern']}")

            if 'context' not in variables:
                variables['context'] = "\n".join(context_parts)

        return self.expand(template_name, variables, variables.get('context'))

    def save_template_to_file(self, name: str, file_path: str):
        """Save a template to a file.

        Args:
            name: Template name
            file_path: Path to save to
        """
        template = self.db.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template['content'])

    def load_template_from_file(self, name: str, file_path: str):
        """Load a template from a file.

        Args:
            name: Template name to create
            file_path: Path to load from
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {file_path}")

        content = path.read_text()
        self.create_template(name, content)
