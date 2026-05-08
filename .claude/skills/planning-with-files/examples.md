# Examples

## Example 1: Building a REST API

### User Request
"Create a Python REST API for a todo app with CRUD operations"

### What Claude Does

1. **Creates task_plan.md**:
```markdown
## Goal
Create a Python REST API for a todo app with CRUD operations

## Current Phase
Phase 1

## Phases
### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [ ] Identify constraints
- [ ] Document findings
- **Status:** in_progress

### Phase 2: Planning & Structure
- [ ] Define technical approach
- [ ] Create project structure
- **Status:** pending
...
```

2. **Creates findings.md** for research:
```markdown
## Discoveries
### Framework Choice
- **Finding**: FastAPI is best for this use case
- **Rationale**: Built-in validation, async support, auto-docs
```

3. **Updates progress.md** throughout:
```markdown
## What Was Done
### 14:32 - Created project structure
- **What**: Set up FastAPI project with proper structure
- **Result**: Success
- **Notes**: Used uv for dependency management
```

## Example 2: Research Task

### User Request
"Research the best database for a real-time analytics system"

### What Claude Does

1. **Creates task_plan.md** with research phases
2. **Extensively uses findings.md** to store:
   - Comparison of different databases
   - Performance benchmarks
   - Use case analysis
3. **Updates progress.md** after each source reviewed

## Key Patterns

### The 2-Action Rule
After every 2 view/browser/search operations, IMMEDIATELY save key findings to findings.md.

### Decision Logging
Always document WHY you chose something:
```markdown
| Decision | Rationale |
|----------|-----------|
| Use PostgreSQL | ACID compliance, JSON support, proven at scale |
```

### Error Logging
Never repeat a failed action - log it:
```markdown
| Error | Attempt | Resolution |
|-------|---------|------------|
| ImportError | 1 | Installed missing package |
```
