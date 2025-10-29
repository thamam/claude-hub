# Claude Hub - Custom Addons Repository

This repository contains custom Claude Code extensions including slash commands, hooks, agents, skills, and MCP servers.

## Directory Structure

```
.claude/
├── commands/       # Custom slash commands
├── hooks/          # Event hooks (pre/post tool execution)
├── agents/         # Custom agent definitions
├── skills/         # Reusable skill modules
└── mcp/            # Model Context Protocol servers
```

## Available Commands

### thh3:bug:log

**Location**: `.claude/commands/thh3:bug:log.md`

**Purpose**: Document bugs comprehensively for backlog management and autonomous agent investigation.

**Usage**:
```bash
/thh3:bug:log
```

**What it does**:
- Guides you through documenting a bug systematically
- Gathers reproduction steps, error messages, and context
- Analyzes the codebase to identify likely root causes
- Creates a self-contained markdown report that includes:
  - Formal bug description with observed vs expected behavior
  - Step-by-step reproduction instructions (visual and programmatic)
  - Root cause investigation with ranked hypotheses
  - Complete diagnostic scripts
  - Success criteria and test cases
  - Phased fix strategy
  - Code locations and file modifications needed

**Output**: Comprehensive bug report saved to `temp/debug/` or custom location

**Key Features**:
- **Self-contained**: Background agents can work from the report alone
- **Actionable**: Specific files, lines, and changes identified
- **Testable**: Clear success criteria provided
- **Tool-ready**: Includes runnable diagnostic scripts

**Use Cases**:
1. Document bugs for backlog when you can't fix them immediately
2. Hand off investigations to other developers
3. Enable background agents (Codex, Cursor) to autonomously investigate and submit PRs
4. Create detailed bug reports for team collaboration

**Example**:
```bash
# User observes an issue
User: "All feature matches are marked as outliers except when comparing baseline to itself"

# Run the command
/thh3:bug:log

# Agent guides through documentation process
# - Gathers context and reproduction steps
# - Investigates codebase
# - Creates comprehensive report

# Output: temp/debug/all-matches-outliers-bug.md
# - 650+ lines of investigation guidance
# - Runnable diagnostic scripts
# - 5 ranked root cause hypotheses
# - Complete fix strategy
```

## Installation

### For Project-Specific Use

Copy the `.claude/` directory to your project root:

```bash
cp -r ./.claude /path/to/your/project/
```

### For Global Use

Symlink or copy to your home directory's `.claude/` folder:

```bash
# Option 1: Symlink (changes reflect automatically)
ln -s /home/thh3/personal/claude-hub/.claude/commands/thh3:bug:log.md ~/.claude/commands/

# Option 2: Copy (static snapshot)
cp /home/thh3/personal/claude-hub/.claude/commands/thh3:bug:log.md ~/.claude/commands/
```

## Creating New Commands

Custom slash commands follow the format: `<user>:<category>:<command-name>`

Example: `thh3:bug:log`
- **user**: `thh3` (your identifier)
- **category**: `bug` (functional grouping)
- **command-name**: `log` (specific action)

### Command File Structure

```markdown
---
description: Brief description of what the command does
---

# Command Title

[Agent instructions and behavior]
```

### Command File Location

Save to: `.claude/commands/<user>:<category>:<command-name>.md`

## Contributing

This is a personal repository for custom Claude Code extensions. Feel free to use and adapt these commands for your own projects.

## License

MIT License - See LICENSE file for details

## Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Slash Commands Guide](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Agent Development](https://docs.claude.com/en/docs/claude-code/agents)
