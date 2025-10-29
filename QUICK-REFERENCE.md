# Claude Hub - Quick Reference

## Installation

```bash
# Project-specific
cp -r .claude /path/to/your/project/

# Global (with auto-updates)
ln -s $(pwd)/.claude/commands/thh3:bug:log.md ~/.claude/commands/

# Global (static copy)
cp .claude/commands/thh3:bug:log.md ~/.claude/commands/
```

## Available Commands

### /thh3:bug:log

**One-liner**: Document bugs comprehensively for backlog and autonomous agent investigation

**When to use**:
- You find a bug but can't fix it immediately
- Want to hand off investigation to another developer
- Need background agent to autonomously investigate and PR
- Want systematic bug documentation with reproduction steps

**What it creates**:
- 500-700 line markdown report
- Formal bug description with impact assessment
- Step-by-step reproduction (visual + programmatic)
- Ranked root cause hypotheses
- Runnable diagnostic scripts
- Success criteria and test cases
- Phased fix strategy
- Code locations and modifications needed

**Output location**: `temp/debug/[bug-name]-[date].md` (configurable)

**Example**:
```bash
/thh3:bug:log

# Agent asks: "What behavior are you observing?"
# You describe the bug
# Agent investigates codebase
# Agent creates comprehensive report
# ✓ Bug documented and ready for handoff
```

## Command Format

All commands follow: `<user>:<category>:<command-name>`

- **user**: `thh3` (your identifier)
- **category**: Functional grouping (e.g., `bug`, `test`, `docs`)
- **command-name**: Specific action (e.g., `log`, `fix`, `generate`)

## Directory Structure

```
.claude/
├── commands/       # Slash commands (*.md)
├── hooks/          # Event hooks (planned)
├── agents/         # Custom agents (planned)
├── skills/         # Reusable skills (planned)
└── mcp/            # MCP servers (planned)
```

## Creating New Commands

1. Create file: `.claude/commands/<user>:<category>:<name>.md`
2. Add frontmatter:
   ```markdown
   ---
   description: Brief command description
   ---
   ```
3. Write agent instructions in markdown
4. Use in Claude Code: `/<user>:<category>:<name>`

## Background Agent Handoff

Once you have a bug report from `/thh3:bug:log`:

```bash
# In another Claude Code session, Cursor, or Codex:
"Please investigate temp/debug/[bug-name].md, implement the fix,
test it against success criteria, and submit a PR"
```

The agent can work autonomously because the report includes:
- Complete reproduction steps
- Runnable diagnostic scripts
- Phased fix strategy
- Specific file locations
- Measurable success criteria

## Common Workflows

### Bug Workflow

```bash
# 1. Document bug
/thh3:bug:log
# → Creates temp/debug/bug-report.md

# 2. Backlog it
mv temp/debug/bug-report.md docs/bugs/

# 3. Later, hand to agent
"Fix the bug in docs/bugs/bug-report.md"
```

### Team Collaboration

```bash
# 1. Document bug
/thh3:bug:log

# 2. Commit to repo
git add temp/debug/bug-report.md
git commit -m "docs: document RANSAC outlier bug"
git push

# 3. Teammate pulls and investigates
# All context is in the markdown file
```

## Tips

- **Document early**: Capture bugs while context is fresh
- **Be specific**: Include file paths, line numbers, error messages
- **Run diagnostics**: Let agent search codebase and read files
- **Trust the process**: Agent will create comprehensive reports
- **Customize**: Edit command files to match your workflow

## Files

- `README.md` - Main documentation
- `.claude/README.md` - Detailed command documentation
- `.claude/commands/EXAMPLE-USAGE.md` - Complete workflow example
- `.claude/commands/thh3:bug:log.md` - Bug documentation command

## Resources

- [Claude Code Docs](https://docs.claude.com/en/docs/claude-code)
- [Slash Commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Custom Commands](https://docs.claude.com/en/docs/claude-code/slash-commands/custom-commands)

---

**Quick Help**:
- Installation: See "Installation" section above
- Usage: Just type `/thh3:bug:log` in Claude Code
- Examples: See `.claude/commands/EXAMPLE-USAGE.md`
- Details: See `README.md` or `.claude/README.md`
