# Claude Code Conductor

A lightweight CLI tool that orchestrates and enhances Claude Code sessions by managing context, tools, and project state across all development work.

## What Problem Does This Solve?

Claude Code Conductor addresses common challenges in AI-assisted development:

1. **Scope Creep** - Tracks original project scope and warns when tasks drift
2. **Context Management** - Optimizes prompt context to stay within limits
3. **Multi-Session Continuity** - Maintains state across sessions and machines
4. **Tool Discovery** - Suggests relevant MCP servers, skills, and subagents
5. **Progress Tracking** - Monitors completion vs activity, prevents spinning
6. **Knowledge Sharing** - Captures learnings to improve future sessions

## Installation

```bash
# Clone the repository
git clone https://github.com/thamam/claude-hub.git
cd claude-hub

# Install in development mode
pip install -e .

# Verify installation
conductor --version
```

## Quick Start

### 1. Initialize a Project

```bash
conductor init rag-pipeline --scope "Build document RAG pipeline. No UI. No auth. PostgreSQL vectors."
```

### 2. Add Tasks

```bash
# Add a task within scope
conductor add-task "Set up PostgreSQL with pgvector" -p rag-pipeline
✓ Task added (within scope)

# Try to add something out of scope
conductor add-task "Build user authentication" -p rag-pipeline
⚠️  Warning: Task appears to be out of scope
  Reason: Explicitly excluded: no auth
Add anyway? [y/N]: n
```

### 3. Check Status

```bash
conductor status -p rag-pipeline
```

Output:
```
rag-pipeline (2 days old)
  Scope: Build document RAG pipeline. No UI. No auth. PostgreSQL vectors.
  Progress: 40% (2/5 tasks)

  ✓ Set up PostgreSQL with pgvector
  ✓ Create document loader
  ⟳ Implement vector embeddings (in progress)
  ○ Build search endpoint
  ○ Add relevance ranking
```

### 4. Generate Context-Aware Prompts

```bash
# Generate a prompt from template with project context
conductor prompt implement -p rag-pipeline \
  --var feature="vector search endpoint" \
  --var patterns="FastAPI REST endpoints"

✓ Prompt copied to clipboard (3,247 chars with context)
  With context from project: rag-pipeline
```

The prompt includes:
- Project scope
- Current progress
- Completed tasks
- Recent learnings
- Relevant patterns

### 5. Track Progress

```bash
# Start a work session
conductor session start -p rag-pipeline
✓ Session xyz789 started for rag-pipeline

# Complete tasks
conductor complete 3 -p rag-pipeline
✓ Task 3 marked as completed

# End session
conductor session end -p rag-pipeline
✓ Session xyz789 ended
  Duration: 2.5 hours
  Tasks completed: 1
```

## Core Features

### Scope Creep Detection

Conductor analyzes tasks against your original scope:

```bash
# Check if a task is in scope
conductor scope-check "Add OAuth2 authentication" -p rag-pipeline
⚠️  Outside scope
  Reason: Explicitly excluded: no auth
```

**How it works:**
- Extracts keywords from scope
- Detects explicit exclusions (no X, without Y)
- Calculates similarity score
- Warns when relevance is low

### Template System

Built-in templates for common scenarios:

```bash
# List available templates
conductor templates
```

**Built-in Templates:**
- `debug` - Systematic bug fixing
- `implement` - Feature implementation with YAGNI
- `refactor` - Safe refactoring
- `continue` - Resume work on project
- `review` - Code review
- `test` - Test generation
- `optimize` - Performance optimization
- `document` - Documentation
- `plan` - Implementation planning

**Create custom templates:**

```bash
# Templates use {variable} placeholders
conductor add-template my-feature \
  --content "Implement {feature} using {technology}. Follow {pattern}."
```

### Context Optimization

Automatically builds and optimizes context:

```bash
# View optimized context for project
conductor context -p rag-pipeline
```

Context includes:
- Project scope and status
- Task history and progress
- Recent decisions/learnings
- Blocked tasks and reasons
- Relevant code patterns

**Smart pruning:**
- Stays under token limits (configurable)
- Prioritizes recent and relevant info
- Removes redundancy
- Maintains essential context

### Tool Registry

Discover relevant tools for your task:

```bash
conductor tools -p rag-pipeline
```

Output:
```
MCP Servers:
┌──────────┬────────────┬──────────────────┬───────────┐
│ Name     │ Category   │ Description      │ Relevance │
├──────────┼────────────┼──────────────────┼───────────┤
│ memory   │ always_on  │ Context retention│ 1.00      │
│ postgres │ databases  │ PostgreSQL ops   │ 0.85      │
└──────────┴────────────┴──────────────────┴───────────┘

Subagents:
┌────────────┬──────────────────┬─────────────────────┐
│ Name       │ Triggers         │ Description         │
├────────────┼──────────────────┼─────────────────────┤
│ test_gen   │ test, testing    │ Test generation     │
│ debugger   │ bug, error       │ Debugging expert    │
└────────────┴──────────────────┴─────────────────────┘
```

### Progress Monitoring

Track project health and velocity:

```bash
conductor report -p rag-pipeline
```

Output:
```
Productivity Report: rag-pipeline

Completion:
  Progress: 40%
  Completed: 2/5
  Remaining: 3

Health:
  Score: 75/100
  Status: healthy
  Issues:
    - 1 blocked task

Velocity:
  Tasks per day: 0.67
  Est. completion: 4.5 days

Recommendations:
  • Work on unblocking task #4
  • Velocity is good, keep momentum
```

**Health indicators:**
- Long-running in-progress tasks
- Many blocked tasks
- Low velocity
- Scope creep percentage

### Multi-Machine Sync

Sync state across machines:

```bash
# Check sync status
conductor sync
Sync Status
  Method: git
  Has local changes: true
  Sync count: 5

# Push local changes
conductor sync --push
✓ State pushed (git)

# Pull remote changes (on another machine)
conductor sync --pull
✓ State pulled (git)
```

**Sync methods:**
- **Git** - Automatic if in git repo
- **Dropbox** - If ~/Dropbox exists
- **File** - Manual sync folder at ~/.conductor-sync

## Complete Usage Examples

### Example 1: Starting a New Feature

```bash
# 1. Initialize project
conductor init api-refactor \
  --scope "Refactor authentication API for better performance. No breaking changes to public interface."

# 2. Add initial tasks
conductor add-task "Profile current auth endpoints" -p api-refactor
conductor add-task "Identify bottlenecks" -p api-refactor
conductor add-task "Optimize database queries" -p api-refactor
conductor add-task "Add caching layer" -p api-refactor
conductor add-task "Update tests" -p api-refactor

# 3. Start working
conductor session start -p api-refactor

# 4. Get relevant tools
conductor tools -p api-refactor

# 5. Generate implementation prompt
conductor prompt optimize -p api-refactor \
  --var target="authentication endpoints" \
  --var metric="response time" \
  --var requirements="< 100ms p99"

# (Use Claude Code with the generated prompt)

# 6. Mark progress
conductor complete 1 -p api-refactor
conductor complete 2 -p api-refactor

# 7. Check status
conductor status -p api-refactor

# 8. End session
conductor session end -p api-refactor
```

### Example 2: Continuing Work

```bash
# On a new machine or session
conductor sync --pull

# Generate continuation prompt
conductor prompt continue -p api-refactor

# This includes:
# - What's been completed
# - What's in progress
# - What's next
# - Original scope
```

### Example 3: Handling Scope Creep

```bash
# Someone suggests adding a feature
conductor add-task "Add OAuth2 provider support" -p api-refactor

⚠️  Warning: Task appears to be out of scope
  Reason: Low relevance to original scope (similarity: 0.15)
Add anyway? [y/N]: n

# Check explicitly
conductor scope-check "Add OAuth2 provider support" -p api-refactor
⚠️  Outside scope
  Reason: Low relevance to original scope

# If you decide it's needed, either:
# 1. Create a separate project
conductor init oauth-providers --scope "Add OAuth2 provider support"

# 2. Or explicitly update the original scope
# (Edit scope in database or create new project)
```

## Configuration

Configuration file: `~/.conductor/config.yaml`

```yaml
context:
  max_size: 8000  # Max context characters
  include_patterns: true
  include_learnings: true

sync:
  method: git  # git, dropbox, or file
  auto_sync: false

defaults:
  project: null  # Default project
  verbose: false
  output: human  # human or json

integrations:
  memory_mcp: true
  clipboard: true  # Auto-copy prompts
```

## Environment Variables

```bash
# Set default project
export CONDUCTOR_PROJECT=rag-pipeline

# Custom database location
export CONDUCTOR_DB_PATH=/path/to/conductor.db

# Use commands without -p flag
conductor status  # Uses CONDUCTOR_PROJECT
```

## Command Reference

### Project Management

```bash
conductor init <name> --scope "description"  # Create project
conductor status [-p PROJECT]                 # Show status
conductor context -p PROJECT                  # View context
```

### Task Management

```bash
conductor add-task "description" -p PROJECT   # Add task
conductor complete TASK_ID                    # Mark complete
conductor scope-check "description" -p PROJECT # Check scope
```

### Templates & Prompts

```bash
conductor templates                           # List templates
conductor prompt TEMPLATE -p PROJECT          # Generate prompt
  --var key=value                             # Set variables
  --no-copy                                   # Don't copy
  --output FILE                               # Write to file
```

### Tools & Registry

```bash
conductor tools [-p PROJECT] [--category CAT] # Show tools
```

### Sessions

```bash
conductor session start -p PROJECT            # Start session
conductor session end -p PROJECT              # End session
```

### Sync

```bash
conductor sync                                # Show status
conductor sync --push                         # Push changes
conductor sync --pull                         # Pull changes
```

### Monitoring

```bash
conductor report -p PROJECT                   # Full report
```

## Best Practices

### 1. Start with Clear Scope

Good scope:
```bash
conductor init payment-service \
  --scope "Build payment processing service using Stripe API. Support credit cards only. No crypto. Production-ready with error handling."
```

Bad scope:
```bash
conductor init payment-service --scope "Build payment system"
```

### 2. Use Templates

Templates enforce good practices:

```bash
# Instead of ad-hoc prompts
conductor prompt implement -p PROJECT \
  --var feature="user registration" \
  --var patterns="existing auth module"
```

### 3. Track Sessions

Sessions help measure velocity:

```bash
conductor session start -p PROJECT
# Do work
conductor session end -p PROJECT
```

### 4. Check Health Regularly

```bash
conductor report -p PROJECT
```

Watch for:
- Health score < 60
- Many blocked tasks
- Low velocity
- Scope creep

### 5. Sync Often

```bash
# At end of session
conductor sync --push

# At start of session (new machine)
conductor sync --pull
```

## Architecture

```
conductor/
├── db.py          # SQLite database interface
├── templates.py   # Prompt template engine
├── context.py     # Context optimization
├── state.py       # Project state & scope checking
├── registry.py    # Tool/MCP/skill registry
├── monitor.py     # Progress monitoring
├── sync.py        # Multi-machine sync
└── cli.py         # CLI interface
```

## Performance

Target performance (measured on typical projects):

- Startup time: < 50ms
- Command execution: < 100ms
- Context preparation: < 200ms
- Database queries: < 10ms

## Testing

```bash
# Run test suite
python -m pytest tests/

# Run specific test
python -m pytest tests/test_conductor.py::TestDatabase

# Run with coverage
python -m pytest --cov=conductor tests/
```

## Troubleshooting

### Database Issues

```bash
# Reset database (WARNING: loses all data)
rm ~/.conductor/conductor.db
conductor init test --scope "test"
```

### Sync Issues

```bash
# Check sync status
conductor sync

# Force push
conductor sync --push

# Manual sync (file method)
cp ~/.conductor/conductor.db ~/.conductor-sync/
```

### Context Too Large

Adjust in `~/.conductor/config.yaml`:

```yaml
context:
  max_size: 6000  # Reduce from default 8000
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

## Support

- Issues: https://github.com/thamam/claude-hub/issues
- Discussions: https://github.com/thamam/claude-hub/discussions

## Roadmap

- [ ] Web dashboard for project visualization
- [ ] Integration with Linear/Jira
- [ ] Team collaboration features
- [ ] AI-powered task breakdown
- [ ] Automated learning extraction
- [ ] Plugin system for custom tools
- [ ] VSCode extension

## Credits

Built with:
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [PyYAML](https://pyyaml.org/) - Configuration
- [Pyperclip](https://pypi.org/project/pyperclip/) - Clipboard access

## Philosophy

**YAGNI (You Aren't Gonna Need It)**

Conductor helps you stay focused by:
- Tracking original scope
- Warning about scope creep
- Encouraging completion over activity
- Measuring progress not just effort

**Context is King**

Every prompt includes:
- What you're building (scope)
- What you've done (completed tasks)
- What's next (pending tasks)
- What you've learned (patterns)

**Lightweight Over Feature-Rich**

Conductor does a few things well:
- Fast (< 100ms for most commands)
- Simple (one SQLite file)
- Portable (sync across machines)
- Focused (project orchestration only)
