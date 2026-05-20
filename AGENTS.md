---
title: AGENTS.md
lastUpdated: 2026-05-10
version: 1.1
---

# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, OpenCode, Hermes, Antigravity, etc.) when working with code in this repository.

---

## Repository Overview

A collection of skills for senior software engineers. Skills are packaged instructions that extend AI agents capabilities across the full development lifecycle — from idea to production.

**Workspace**: `/Users/fox/Claude Code/`

---

## Supported Platforms

| Platform | How It Reads This File | Notes |
|----------|----------------------|-------|
| Claude Code | Native (`AGENTS.md` in repo root) | Primary platform |
| Cursor | `.cursor/rules/` or project instructions | Copy relevant sections |
| Copilot | `.github/copilot-instructions.md` | See Copilot setup in `docs/` |
| OpenCode | Skill-driven via `skill` tool | See `docs/opencode-setup.md` |
| Hermes | Project instructions | Configure in Hermes settings |
| Antigravity | Via agent-skills plugin | See antigravity.ai |
| Gemini CLI | Via `skills` tool | `gemini skills install ./skills/` |

> **Platform-specific setup guides** are in `docs/`:
> - `cursor-setup.md` · `copilot-setup.md` · `opencode-setup.md`
> - `gemini-cli-setup.md` · `windsurf-setup.md` · `getting-started.md`

---

## Skill Organization

Skills are organized in two layers:

```
skills/
├── engineering/          # 22 工程技能（Addy Osmani 体系）
│   ├── using-agent-skills.md
│   ├── idea-refine.md
│   ├── spec-driven-development.md
│   ├── planning-and-task-breakdown.md
│   ├── incremental-implementation.md
│   ├── context-engineering.md
│   ├── api-and-interface-design.md
│   ├── test-driven-development.md
│   ├── browser-testing-with-devtools.md
│   ├── debugging-and-error-recovery.md
│   ├── code-review-and-quality.md
│   ├── security-and-hardening.md
│   ├── performance-optimization.md
│   ├── code-simplification.md
│   ├── doubt-driven-development.md       # 质疑驱动开发
│   ├── git-workflow-and-versioning.md
│   ├── ci-cd-and-automation.md
│   ├── deprecation-and-migration.md
│   ├── documentation-and-adrs.md
│   ├── shipping-and-launch.md
│   └── source-driven-development.md
│
└── domain/              # 2 领域技能（企业定制）
    ├── data-analysis.md          # 通用数据分析流程（含ML建模+财务分析）
    └── sql-generation.md        # SQL生成（合同/税务/共享/资金）
```

---

## Skill Discovery Rules

### Core Rule

**If a task matches a skill, you MUST invoke it. Never implement directly if a skill applies.**

### Intent → Skill Mapping

Map the user's intent to the appropriate skill(s):

**工程技能（Engineering）**

| Intent | Primary Skill | Fallback |
|--------|--------------|----------|
| Feature / new functionality | `spec-driven-development` | → `incremental-implementation` → `test-driven-development` |
| Planning / task breakdown | `planning-and-task-breakdown` | — |
| Bug / failure / error | `debugging-and-error-recovery` | — |
| Code review | `code-review-and-quality` | — |
| Refactoring / simplification | `code-simplification` | — |
| API or interface design | `api-and-interface-design` | — |
| UI work | `frontend-ui-engineering` | — |
| Security review | `security-and-hardening` | — |
| Performance issues | `performance-optimization` | — |
| Shipping / deployment | `shipping-and-launch` | → `git-workflow-and-versioning` + `ci-cd-and-automation` |
| Deprecation / migration | `deprecation-and-migration` | — |
| Writing docs / ADRs | `documentation-and-adrs` | — |
| Source verification | `source-driven-development` | — |
| High-stakes decision | `doubt-driven-development` | — |
| Vague idea / needs refinement | `idea-refine` | — |

**领域技能（Domain — 财务/数据专用）**

| Intent | Skill |
|--------|-------|
| 分析财务数据 / 报表解读 / 供应商分析 | `data-analysis` |
| 生成 / 优化 SQL 查询 | `sql-generation` |
| 通用数据分析流程（清洗→EDA→建模→可视化，含ML/深度学习/运筹优化） | `data-analysis` |

---

## Development Lifecycle

Follow this lifecycle for all non-trivial work:

```
DEFINE（定义） → PLAN（规划） → BUILD（构建） → VERIFY（验证） → REVIEW（审查） → SHIP（交付）
```

| Phase | Skill | Claude Code Command |
|-------|-------|-------------------|
| DEFINE | `idea-refine` + `spec-driven-development` | `/spec` |
| PLAN | `planning-and-task-breakdown` | `/plan` |
| BUILD | `incremental-implementation` + `test-driven-development` | `/build` |
| VERIFY | `debugging-and-error-recovery` + `browser-testing-with-devtools` | `/test` |
| REVIEW | `code-review-and-quality` + `security-and-hardening` + `performance-optimization` | `/review` |
| SHIP | `shipping-and-launch` + `git-workflow-and-versioning` + `ci-cd-and-automation` | `/ship` |

> **Claude Code users**: Use the 7 slash commands (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/code-simplify`, `/ship`) as workflow entry points. Each command activates the appropriate skill automatically.

---

## Orchestration: Three Layers

This workspace has three composable layers. They have different jobs:

- **Skills** (`skills/engineering/<name>/SKILL.md`, `skills/domain/<name>/SKILL.md`) — workflows with steps and exit criteria. The *how*. Mandatory when an intent matches.
- **Personas** (`agents/personas/<role>.md`) — roles with a perspective and output format. The *who*.
- **Slash commands** (`.claude/commands/*.md`) — user-facing entry points. The *when*. The orchestration layer.

### Composition Rules

1. **The user (or a slash command) is the orchestrator.**
2. **Personas do not invoke other personas.** A persona may invoke skills.
3. **Parallel fan-out with merge** is the only endorsed multi-persona pattern — used by `/ship` to run `code-reviewer`, `security-auditor`, and `test-engineer` concurrently, then synthesize their reports.
4. **Do not build a "router" persona** that decides which other persona to call. That's the job of slash commands and intent mapping.

See `agents/README.md` for the decision matrix and `references/orchestration-patterns.md` for the full pattern catalog.

---

## Creating a New Skill

### Directory Structure

For **engineering skills**:
```
skills/engineering/
  {skill-name}/
    SKILL.md              # Required: skill definition (kebab-case dir name)
```

For **domain skills**:
```
skills/domain/
  {skill-name}/
    SKILL.md              # Required: skill definition
```

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Skill directory | `kebab-case` | `my-new-skill` |
| SKILL.md | Always uppercase, exact filename | `SKILL.md` |
| Frontmatter `name` | `kebab-case` | `my-new-skill` |
| Frontmatter `description` | One sentence, include trigger phrases | "Use when..."

### SKILL.md Frontmatter (Required)

```markdown
---
name: {skill-name}
description: {One sentence describing when to use this skill. Include trigger phrases like "Deploy my app", "Check logs", etc.}
---

# {Skill Title}
```

> ⚠️ The frontmatter `name` field is required. This is how the skill is discovered by the `skill` tool.

### Best Practices

- **Keep SKILL.md under 500 lines** — put detailed reference material in separate files
- **Write specific descriptions** — helps the agent know exactly when to activate
- **Use progressive disclosure** — reference supporting files that are read only when needed
- **Frontmatter `name` must match directory name** — this is how the skill tool discovers skills

### End-User Installation

**Claude Code:**
```bash
cp -r skills/engineering/{skill-name} ~/.claude/skills/
# Or for domain skills:
cp -r skills/domain/{skill-name} ~/.claude/skills/
```

**Claude.ai:**
Paste the `SKILL.md` content into project knowledge or conversation.

**Other platforms:**
Copy `SKILL.md` to the platform's skill/rules directory. See platform-specific guides in `docs/`.

---

## Anti-Rationalization

The following thoughts are incorrect and must be ignored:

- "This is too small for a skill"
- "I can just quickly implement this"
- "I'll gather context first"

Correct behavior: **Always check for and use skills first.**

---

## Reference Documents

| File | Purpose |
|------|---------|
| `agents/README.md` | Persona roster and decision matrix |
| `references/orchestration-patterns.md` | Full orchestration pattern catalog |
| `references/testing-patterns.md` | Testing patterns reference |
| `references/security-checklist.md` | Security checklist |
| `references/performance-checklist.md` | Performance checklist |
| `references/accessibility-checklist.md` | Accessibility checklist |
| `docs/skill-anatomy.md` | Anatomy of a well-formed skill |

---

*Last updated: 2026-05-10 | Version 1.1*
