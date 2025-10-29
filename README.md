# Claude Hub

A repository for custom Claude Code extensions including slash commands, hooks, agents, skills, and MCP servers.

## Quick Start

```bash
# Use a command in your project
cp -r .claude /path/to/your/project/

# Or install globally
ln -s $(pwd)/.claude/commands/* ~/.claude/commands/
```

## Available Extensions

### Slash Commands

#### `/thh3:bug:log` - Bug Documentation Agent

Comprehensive bug documentation tool that creates self-contained reports for backlog management and autonomous agent investigation.

**Features**:
- Guided bug documentation workflow
- Automatic codebase analysis and root cause investigation
- Generates runnable diagnostic scripts
- Creates phased fix strategies with success criteria
- Enables background agents to autonomously investigate and submit PRs

**Output**: Detailed markdown report (typically 500-700 lines) with:
- Formal bug description and impact assessment
- Step-by-step reproduction instructions
- Ranked root cause hypotheses with evidence collection plans
- Complete diagnostic scripts
- Success criteria and test cases
- Code locations and modification guidance

See [.claude/README.md](.claude/README.md) for detailed documentation.

## Directory Structure

```
.claude/
├── README.md          # Detailed documentation
├── commands/          # Custom slash commands
│   └── thh3:bug:log.md
├── hooks/             # Event hooks (planned)
├── agents/            # Custom agents (planned)
├── skills/            # Reusable skills (planned)
└── mcp/              # MCP servers (planned)
```

## Installation

### Project-Specific Installation

```bash
# Clone this repository
git clone https://github.com/yourusername/claude-hub.git

# Copy to your project
cp -r claude-hub/.claude /path/to/your/project/
```

### Global Installation

```bash
# Create global .claude directory if it doesn't exist
mkdir -p ~/.claude/commands

# Symlink commands for automatic updates
ln -s $(pwd)/.claude/commands/* ~/.claude/commands/

# Or copy for static version
cp .claude/commands/* ~/.claude/commands/
```

## Usage Examples

### Bug Documentation Workflow

```bash
# In your project with claude-code
/thh3:bug:log

# Agent will guide you through:
# 1. Gathering bug details and context
# 2. Analyzing your codebase
# 3. Identifying root causes
# 4. Creating comprehensive report

# Output saved to: temp/debug/[bug-name]-[date].md
```

### Background Agent Handoff

Once you have the bug report, you can:

1. **Backlog it**: Store in `docs/bugs/` for future work
2. **Hand to developer**: Self-contained for team collaboration
3. **Background agent**: Give to Codex/Cursor for autonomous fix:
   ```
   "Please investigate the bug documented in temp/debug/all-matches-outliers-bug.md,
    implement the fix, test it, and submit a PR"
   ```

## Creating Custom Commands

Commands follow the format: `<user>:<category>:<command-name>.md`

```bash
# Create new command
touch .claude/commands/thh3:newcategory:mycommand.md

# Edit with your agent instructions
# See existing commands for examples
```

## Contributing

This is a personal repository for custom extensions. Feel free to fork and adapt for your needs.

## License

MIT License - See LICENSE file

## Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Slash Commands Guide](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Creating Custom Commands](https://docs.claude.com/en/docs/claude-code/slash-commands/custom-commands)
