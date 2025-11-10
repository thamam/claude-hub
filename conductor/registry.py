"""Tool and resource registry for Claude Code Conductor."""

from typing import List, Dict, Optional
from pathlib import Path
import yaml
import re


class Registry:
    """Manages registry of MCP servers, skills, and subagents."""

    def __init__(self, registry_path: str = None):
        """Initialize registry.

        Args:
            registry_path: Path to registry YAML file
        """
        if registry_path is None:
            registry_path = Path.home() / ".conductor" / "registry.yaml"
        else:
            registry_path = Path(registry_path)

        self.registry_path = registry_path
        self.registry = self._load_or_create_registry()

    def _load_or_create_registry(self) -> Dict:
        """Load registry from file or create default."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return yaml.safe_load(f) or self._default_registry()
        else:
            registry = self._default_registry()
            self._save_registry(registry)
            return registry

    def _default_registry(self) -> Dict:
        """Get default registry structure."""
        return {
            'mcp_servers': {
                'always_active': [
                    {
                        'name': 'memory',
                        'description': 'Context retention across sessions',
                        'config_path': '~/.claude/mcp_config.json'
                    }
                ],
                'databases': [
                    {
                        'name': 'postgres',
                        'when': 'SQL, relational data, vector storage',
                        'description': 'PostgreSQL database operations'
                    },
                    {
                        'name': 'mongodb',
                        'when': 'Document store, flexible schema',
                        'description': 'MongoDB document database'
                    },
                    {
                        'name': 'redis',
                        'when': 'Caching, pub/sub, real-time',
                        'description': 'Redis in-memory data store'
                    }
                ],
                'productivity': [
                    {
                        'name': 'notion',
                        'when': 'Documentation, notes, knowledge base',
                        'description': 'Notion workspace integration'
                    },
                    {
                        'name': 'linear',
                        'when': 'Issue tracking, project management',
                        'description': 'Linear issue tracker'
                    },
                    {
                        'name': 'github',
                        'when': 'Repository operations, PR management',
                        'description': 'GitHub integration'
                    }
                ],
                'web': [
                    {
                        'name': 'puppeteer',
                        'when': 'Web scraping, browser automation',
                        'description': 'Browser automation with Puppeteer'
                    },
                    {
                        'name': 'fetch',
                        'when': 'HTTP requests, API calls',
                        'description': 'Web content fetching'
                    }
                ]
            },
            'skills': {
                'documents': [
                    {
                        'name': 'docx',
                        'path': '/mnt/skills/public/docx/SKILL.md',
                        'when': 'Creating Word documents',
                        'description': 'Microsoft Word document creation'
                    },
                    {
                        'name': 'pdf',
                        'path': '/mnt/skills/public/pdf/SKILL.md',
                        'when': 'PDF manipulation',
                        'description': 'PDF generation and editing'
                    },
                    {
                        'name': 'xlsx',
                        'path': '/mnt/skills/public/xlsx/SKILL.md',
                        'when': 'Excel spreadsheets',
                        'description': 'Excel file operations'
                    }
                ],
                'development': [
                    {
                        'name': 'mcp-builder',
                        'path': '/mnt/skills/examples/mcp-builder/SKILL.md',
                        'when': 'Creating new MCP servers',
                        'description': 'MCP server scaffolding'
                    }
                ]
            },
            'subagents': [
                {
                    'name': 'github_specialist',
                    'trigger': 'git, repository, PR, commit, branch',
                    'instructions': 'Handle all git and GitHub operations',
                    'description': 'Git and GitHub expert'
                },
                {
                    'name': 'test_generator',
                    'trigger': 'test, testing, TDD, unit test, integration test',
                    'instructions': 'Generate comprehensive test suites',
                    'description': 'Test generation specialist'
                },
                {
                    'name': 'debugger',
                    'trigger': 'bug, error, issue, problem, crash, exception',
                    'instructions': 'Systematic debugging approach',
                    'description': 'Debugging expert'
                },
                {
                    'name': 'optimizer',
                    'trigger': 'optimize, performance, speed, slow, memory',
                    'instructions': 'Performance optimization and profiling',
                    'description': 'Performance optimization specialist'
                },
                {
                    'name': 'documenter',
                    'trigger': 'document, documentation, readme, comments',
                    'instructions': 'Create comprehensive documentation',
                    'description': 'Documentation specialist'
                }
            ]
        }

    def _save_registry(self, registry: Dict):
        """Save registry to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

    def get_relevant_mcp_servers(
        self,
        context: str,
        category: str = None
    ) -> List[Dict]:
        """Get MCP servers relevant to context.

        Args:
            context: Context description (task, keywords, etc.)
            category: Optional category filter

        Returns:
            List of relevant MCP server dicts
        """
        results = []

        # Always include always_active servers
        for server in self.registry['mcp_servers'].get('always_active', []):
            results.append({**server, 'category': 'always_active', 'relevance': 1.0})

        context_lower = context.lower()

        # Search through categories
        for cat_name, servers in self.registry['mcp_servers'].items():
            if cat_name == 'always_active':
                continue

            if category and category != cat_name:
                continue

            for server in servers:
                when = server.get('when', '').lower()
                if when:
                    # Calculate relevance based on keyword matching
                    when_keywords = when.split(',')
                    when_keywords = [k.strip() for k in when_keywords]

                    relevance = 0.0
                    for keyword in when_keywords:
                        if keyword in context_lower:
                            relevance += 1.0

                    if relevance > 0:
                        normalized_relevance = min(relevance / len(when_keywords), 1.0)
                        results.append({
                            **server,
                            'category': cat_name,
                            'relevance': normalized_relevance
                        })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return results

    def get_relevant_skills(self, context: str, category: str = None) -> List[Dict]:
        """Get skills relevant to context.

        Args:
            context: Context description
            category: Optional category filter

        Returns:
            List of relevant skill dicts
        """
        results = []
        context_lower = context.lower()

        for cat_name, skills in self.registry['skills'].items():
            if category and category != cat_name:
                continue

            for skill in skills:
                when = skill.get('when', '').lower()
                name = skill.get('name', '').lower()

                # Check if skill is relevant
                relevance = 0.0

                if when and any(keyword in context_lower for keyword in when.split()):
                    relevance += 0.5

                if name in context_lower:
                    relevance += 0.5

                if relevance > 0:
                    results.append({
                        **skill,
                        'category': cat_name,
                        'relevance': relevance
                    })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return results

    def get_relevant_subagents(self, context: str) -> List[Dict]:
        """Get subagents relevant to context.

        Args:
            context: Context description

        Returns:
            List of relevant subagent dicts
        """
        results = []
        context_lower = context.lower()

        for agent in self.registry.get('subagents', []):
            trigger = agent.get('trigger', '')
            if not trigger:
                continue

            # Split triggers by comma
            triggers = [t.strip() for t in trigger.split(',')]

            # Calculate relevance
            relevance = 0.0
            matched_triggers = []

            for trig in triggers:
                if trig.lower() in context_lower:
                    relevance += 1.0
                    matched_triggers.append(trig)

            if relevance > 0:
                normalized_relevance = min(relevance / len(triggers), 1.0)
                results.append({
                    **agent,
                    'relevance': normalized_relevance,
                    'matched_triggers': matched_triggers
                })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return results

    def get_all_tools(
        self,
        context: str = None,
        category: str = None
    ) -> Dict[str, List[Dict]]:
        """Get all relevant tools.

        Args:
            context: Context description (optional)
            category: Category filter (optional)

        Returns:
            Dict with mcp_servers, skills, and subagents
        """
        if context:
            return {
                'mcp_servers': self.get_relevant_mcp_servers(context, category),
                'skills': self.get_relevant_skills(context, category),
                'subagents': self.get_relevant_subagents(context)
            }
        else:
            # Return all without filtering
            return {
                'mcp_servers': self._get_all_mcp_servers(category),
                'skills': self._get_all_skills(category),
                'subagents': self.registry.get('subagents', [])
            }

    def _get_all_mcp_servers(self, category: str = None) -> List[Dict]:
        """Get all MCP servers."""
        results = []

        for cat_name, servers in self.registry['mcp_servers'].items():
            if category and category != cat_name:
                continue

            for server in servers:
                results.append({**server, 'category': cat_name})

        return results

    def _get_all_skills(self, category: str = None) -> List[Dict]:
        """Get all skills."""
        results = []

        for cat_name, skills in self.registry['skills'].items():
            if category and category != cat_name:
                continue

            for skill in skills:
                results.append({**skill, 'category': cat_name})

        return results

    def add_mcp_server(
        self,
        name: str,
        category: str,
        when: str,
        description: str,
        config_path: str = None
    ):
        """Add a new MCP server to registry.

        Args:
            name: Server name
            category: Category (databases, productivity, etc.)
            when: When to use (keywords)
            description: Description
            config_path: Optional config path
        """
        if category not in self.registry['mcp_servers']:
            self.registry['mcp_servers'][category] = []

        server = {
            'name': name,
            'when': when,
            'description': description
        }

        if config_path:
            server['config_path'] = config_path

        self.registry['mcp_servers'][category].append(server)
        self._save_registry(self.registry)

    def add_skill(
        self,
        name: str,
        category: str,
        path: str,
        when: str,
        description: str
    ):
        """Add a new skill to registry.

        Args:
            name: Skill name
            category: Category (documents, development, etc.)
            path: Path to skill file
            when: When to use
            description: Description
        """
        if category not in self.registry['skills']:
            self.registry['skills'][category] = []

        skill = {
            'name': name,
            'path': path,
            'when': when,
            'description': description
        }

        self.registry['skills'][category].append(skill)
        self._save_registry(self.registry)

    def add_subagent(
        self,
        name: str,
        trigger: str,
        instructions: str,
        description: str
    ):
        """Add a new subagent to registry.

        Args:
            name: Agent name
            trigger: Trigger keywords (comma-separated)
            instructions: Instructions for agent
            description: Description
        """
        agent = {
            'name': name,
            'trigger': trigger,
            'instructions': instructions,
            'description': description
        }

        if 'subagents' not in self.registry:
            self.registry['subagents'] = []

        self.registry['subagents'].append(agent)
        self._save_registry(self.registry)

    def remove_tool(self, tool_type: str, name: str, category: str = None):
        """Remove a tool from registry.

        Args:
            tool_type: Type (mcp_server, skill, subagent)
            name: Tool name
            category: Category (for MCP servers and skills)
        """
        if tool_type == 'subagent':
            self.registry['subagents'] = [
                a for a in self.registry.get('subagents', [])
                if a['name'] != name
            ]
        elif tool_type in ['mcp_server', 'skill']:
            registry_key = 'mcp_servers' if tool_type == 'mcp_server' else 'skills'

            for cat_name in self.registry[registry_key]:
                if category and cat_name != category:
                    continue

                self.registry[registry_key][cat_name] = [
                    item for item in self.registry[registry_key][cat_name]
                    if item['name'] != name
                ]

        self._save_registry(self.registry)

    def export_registry(self, output_path: str):
        """Export registry to file.

        Args:
            output_path: Output file path
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w') as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False)

    def import_registry(self, input_path: str, merge: bool = False):
        """Import registry from file.

        Args:
            input_path: Input file path
            merge: If True, merge with existing. If False, replace.
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Registry file not found: {input_path}")

        with open(input_file, 'r') as f:
            imported = yaml.safe_load(f)

        if merge:
            # Merge registries (simple approach - can be enhanced)
            for key in imported:
                if key not in self.registry:
                    self.registry[key] = imported[key]
                elif isinstance(imported[key], dict):
                    self.registry[key].update(imported[key])
                elif isinstance(imported[key], list):
                    self.registry[key].extend(imported[key])
        else:
            self.registry = imported

        self._save_registry(self.registry)
