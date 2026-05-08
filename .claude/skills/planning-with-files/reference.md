# Planning with Files - Reference

## Core Philosophy

```
Context Window = RAM (volatile, limited)
Filesystem = Disk (persistent, unlimited)

→ Anything important gets written to disk.
```

## File Purposes

| File | Purpose | When to Update |
|------|---------|----------------|
| `task_plan.md` | Phases, progress, decisions | After each phase |
| `findings.md` | Research, discoveries | After ANY discovery |
| `progress.md` | Session log, test results | Throughout session |

## Critical Rules

### 1. Create Plan First
Never start a complex task without `task_plan.md`. Non-negotiable.

### 2. The 2-Action Rule
> "After every 2 view/browser/search operations, IMMEDIATELY save key findings to text files."

### 3. Update After Every Phase
Mark phases complete, log what happened, note any issues.

### 4. Log All Errors
Prevent repetition by documenting failures and resolutions.

### 5. Never Repeat Failed Actions
If something fails, mutate your approach instead of retrying blindly.

## Status Values

- `pending` — Not started yet
- `in_progress` — Currently working on this
- `complete` — Finished this phase

## When to Use Planning Mode

### Automatic Activation
- Multi-step tasks (3+ steps)
- Research tasks
- Complex projects spanning multiple tool calls

### Manual Activation
```
/planning-with-files
```

### Natural Language
"Use planning mode for this task"
"Create task_plan.md and start development"

## Hooks

### UserPromptSubmit
Reads planning files into context when they exist.

### PreToolUse
Reminds you of current plan before tool execution.

### PostToolUse
Prompts you to update progress after Write/Edit operations.

### Stop
Checks if task is truly complete before finishing.

## Session Recovery

After `/clear` or context reset:

```bash
# macOS/Linux
$(command -v python3 || command -v python) .cursor/skills/planning-with-files/scripts/session-catchup.py "$(pwd)"
```

This script:
1. Detects unsynced context
2. Shows git diff summary
3. Reads current planning files
4. Suggests updates based on changes

## Best Practices

### Task Planning
- Break into 3-7 phases
- Each phase should be completable
- Include a "Delivery" phase

### Findings
- Be specific, not vague
- Include sources
- Note implications

### Progress Logging
- Timestamp entries
- Note success/failure
- Document blockers

### Decision Making
- Always include rationale
- Consider alternatives
- Document trade-offs

## Anti-Patterns

❌ **Don't**: Keep everything in context
✅ **Do**: Write to files immediately

❌ **Don't**: Skip error logging
✅ **Do**: Document every failure

❌ **Don't**: Repeat failed approaches
✅ **Do**: Mutate strategy based on errors

❌ **Don't**: Let plans go stale
✅ **Do**: Update status after every phase

## Template Usage

Copy templates from `.cursor/skills/planning-with-files/templates/` to your project directory:

```bash
cp .cursor/skills/planning-with-files/templates/task_plan.md ./task_plan.md
cp .cursor/skills/planning-with-files/templates/findings.md ./findings.md
cp .cursor/skills/planning-with-files/templates/progress.md ./progress.md
```

Then customize for your specific task.
