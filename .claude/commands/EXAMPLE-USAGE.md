# Example Usage: /thh3:bug:log Command

This document shows an example workflow of using the bug documentation command.

## Scenario

You're working on a camera shift detection system and notice that all feature matches are being marked as outliers (red arrows) except when comparing the baseline image to itself.

## Workflow

### 1. Invoke the Command

```bash
/thh3:bug:log
```

### 2. Agent Asks Clarifying Questions

The agent will guide you through documentation:

```
Agent: "I'll help you document this bug comprehensively. Let me gather some information:

1. What behavior are you observing?
2. What did you expect to happen instead?
3. Which component or module is affected?
4. Can you provide any error messages or logs?
```

### 3. You Provide Context

```
User: "I'm using Mode B (Baseline Correspondence Tool) with diagnostic mode enabled.
When I compare baseline to itself, all matches show as green (inliers).
But when I compare baseline to any other frame, ALL matches are red (outliers).

I expected 50-90% inlier ratio for legitimate camera movements, but I'm getting 0%.

Component: src/movement_detector.py - the RANSAC homography estimation
No error messages, just all matches marked as outliers."
```

### 4. Agent Investigates

The agent will:
- Search for relevant code using Glob/Grep
- Read the movement detection implementation
- Analyze RANSAC parameters
- Identify likely root causes

```
Agent: "Let me search for the movement detection code..."
[Searches codebase]

Agent: "I found the detect_movement() method. Let me analyze the RANSAC parameters..."
[Reads files]

Agent: "I've identified 5 potential root causes, with RANSAC threshold being most likely..."
```

### 5. Agent Creates Comprehensive Report

```
Agent: "I've created a comprehensive bug report at:
temp/debug/all-matches-outliers-bug.md

The report includes:
- Formal bug description and impact assessment
- Two reproduction methods (visual and programmatic)
- 5 ranked root cause hypotheses with evidence collection
- Complete diagnostic script (tools/validation/diagnose_outliers.py)
- Success criteria and test cases
- Phased fix strategy
- Specific code locations to modify

This report is self-contained - a background agent can use it to investigate
and implement a fix without needing our conversation context."
```

### 6. Output File Structure

The generated file (`temp/debug/all-matches-outliers-bug.md`) contains:

```markdown
# Bug Report: All Feature Matches Marked as Outliers

**Date**: 2025-10-29
**Severity**: High
**Component**: Movement Detection / Homography Estimation

## Executive Summary
[Concise problem description]

## Bug Description
### Observed Behavior
[Detailed with examples]

### Expected Behavior
[What should happen]

## Impact Assessment
- Confidence calculation affected
- Displacement accuracy compromised
- False positives possible

## How to Reproduce

### Method 1: Visual Verification
```bash
.venv/bin/python tools/validation/baseline_correspondence_tool.py \
    --input-dir sample_images/of_jerusalem \
    --config config.json
```

### Method 2: Programmatic
```python
#!/usr/bin/env python3
# Complete reproduction script
...
```

## Root Cause Investigation

### 1. RANSAC Threshold Too Strict ⭐ (Most Likely)
**Location**: src/movement_detector.py:165-180
**Theory**: ransacReprojThreshold set too low...
**Test**: Try thresholds [1.0, 3.0, 5.0, 10.0]...

### 2. Wrong Transformation Model
...

### Complete Diagnostic Script
```python
#!/usr/bin/env python3
"""Complete, runnable diagnostic script"""
# 200+ lines of diagnostic code
```

## Success Criteria
- Minimum: >10% inlier ratio
- Optimal: 50-90% inlier ratio
- Test cases provided

## Proposed Fix Strategy
- Phase 1: Diagnosis
- Phase 2: Parameter Tuning
- Phase 3: Configuration
- Phase 4: Testing

## Code Locations
Files to modify:
- src/movement_detector.py:165-180
- config.json (add ransac_threshold)
```

## Next Steps

### Option 1: Backlog for Later

```bash
mv temp/debug/all-matches-outliers-bug.md docs/bugs/
git add docs/bugs/all-matches-outliers-bug.md
git commit -m "docs: document all-matches-outliers bug for backlog"
```

### Option 2: Hand to Developer

```
"Hey @teammate, I documented a bug with the RANSAC outlier detection.
See docs/bugs/all-matches-outliers-bug.md - it has complete reproduction
steps, diagnostic scripts, and fix strategy. Can you take a look?"
```

### Option 3: Background Agent Investigation

In another Claude Code session or with Cursor/Codex:

```
"Please investigate the bug documented in temp/debug/all-matches-outliers-bug.md.

Run the diagnostic script, identify the root cause, implement the fix following
the proposed strategy, test against the success criteria, and submit a PR with
the changes."
```

The agent can work autonomously because:
- All context is in the markdown file
- Reproduction steps are complete and runnable
- Diagnostic scripts are provided
- Fix strategy is phased and detailed
- Success criteria are measurable
- Code locations are specific

## Benefits

1. **Immediate**: Document while context is fresh
2. **Complete**: Nothing forgotten, all details captured
3. **Actionable**: Another agent can implement fix without asking questions
4. **Backlogable**: Can defer investigation without losing information
5. **Collaborative**: Easy to hand off to teammates
6. **Systematic**: Structured investigation prevents overlooking causes

## Customization

You can customize the agent's behavior by editing `.claude/commands/thh3:bug:log.md`:

- Change default save location
- Add project-specific sections
- Modify investigation checklist
- Adjust diagnostic script templates
- Customize fix strategy phases

## Tips

1. **Run command early**: Document bugs when you first notice them
2. **Include screenshots**: If using visual tools, mention screenshot paths
3. **Provide logs**: Copy/paste error messages and stack traces
4. **Share theories**: If you have hunches, share them - agent will investigate
5. **Be specific**: File paths, line numbers, exact commands used
