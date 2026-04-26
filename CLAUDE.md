# CLAUDE.md

This file provides guidance to Claude Code when working in this workspace.

## Workspace Structure

```
Claude Code/
├── CLAUDE.md                          # This file — global configuration
├── .claude/
│   ├── commands/                      # Slash commands (/spec /plan /build /test /review /ship)
│   └── hooks/                         # Session lifecycle hooks (auto-injected on startup)
├── skills/                            # 三层结构：skills（工程+领域技能）
│   ├── engineering/                   # 21个工程 Skill（spec-driven、code-review 等）
│   └── domain/                        # 领域 Skill
│       ├── financial-analysis/       # 航司财务分析（年报、CASK、六大航司对比）
│       └── sql-generation/           # SQL 生成（YonBIP/iuap 合同系统）
├── agents/                            # 三层结构：agents（Persona + 编排框架）
│   ├── personas/                     # 可复用角色：code-reviewer、test-engineer、security-auditor
│   └── orchestration/               # Python 多 Agent 编排框架（9个Agent + llm_client）
│       ├── llm_client.py             # MiniMax + DeepSeek 统一 LLM 客户端
│       ├── agents/                   # 9个Agent：pm/task/dev/test/fix/review/git/deploy/monitor
│       ├── config/settings.yaml      # LLM 配置（provider 切换：minimax / deepseek）
│       └── workflows/
├── projects/                          # 三层结构：projects（具体产品项目）
│   ├── file-organizer/              # 智能文件分类 Agent（Python/macOS）
│   └── fin-product-forecast/         # 金融产品预测预警系统（Python/SQLite/sklearn）
├── AI-Factory/                       # 只读引用源（skills/agents/hooks 仍在原位）
│   ├── agent-skills/                # Skills & Personas 原始位置
│   ├── file-organizer-agent/        # [已迁移 → projects/file-organizer/]
│   └── fin-product-forecast/         # [已迁移 → projects/fin-product-forecast/]
└── 参考文件/                           # 架构参考文档
```

## Skill System

### Skill Discovery Flowchart

When a task arrives, route to the appropriate skill:

```
Task arrives
    │
    ├── Vague idea / need refinement? ──────→ idea-refine
    ├── New project / feature / change? ────→ spec-driven-development
    ├── Have a spec, need tasks? ───────────→ planning-and-task-breakdown
    ├── Implementing code? ─────────────────→ incremental-implementation
    │   ├── UI work? ──────────────────────→ frontend-ui-engineering
    │   ├── API work? ─────────────────────→ api-and-interface-design
    │   ├── Need better context? ───────────→ context-engineering
    │   └── Need doc-verified code? ────────→ source-driven-development
    ├── Writing / running tests? ───────────→ test-driven-development
    │   └── Browser-based? ────────────────→ browser-testing-with-devtools
    ├── Something broke? ───────────────────→ debugging-and-error-recovery
    ├── Reviewing code? ────────────────────→ code-review-and-quality
    │   ├── Security concerns? ────────────→ security-and-hardening
    │   └── Performance concerns? ──────────→ performance-optimization
    ├── Committing / branching? ────────────→ git-workflow-and-versioning
    ├── CI/CD pipeline work? ───────────────→ ci-cd-and-automation
    ├── Writing docs / ADRs? ───────────────→ documentation-and-adrs
    └── Deploying / launching? ─────────────→ shipping-and-launch
```

### Intent → Skill Mapping

| Intent | Skill |
|--------|-------|
| Feature / new functionality | `spec-driven-development` → `incremental-implementation` → `test-driven-development` |
| Planning / task breakdown | `planning-and-task-breakdown` |
| Bug / failure / unexpected behavior | `debugging-and-error-recovery` |
| Code review | `code-review-and-quality` |
| Refactoring / simplification | `code-simplification` |
| API or interface design | `api-and-interface-design` |
| UI work | `frontend-ui-engineering` |
| Security review | `security-and-hardening` |
| Performance issues | `performance-optimization` |
| Shipping / deployment | `shipping-and-launch` |

### All Available Skills

Skills are located at `skills/engineering/<skill-name>/SKILL.md`.

| Phase | Skill | Summary |
|-------|-------|---------|
| **Define** | `idea-refine` | Refine vague ideas through structured thinking |
| **Define** | `spec-driven-development` | Requirements and acceptance criteria before code |
| **Plan** | `planning-and-task-breakdown` | Decompose into small, verifiable tasks |
| **Build** | `incremental-implementation` | Thin vertical slices, test each before expanding |
| **Build** | `source-driven-development` | Verify against official docs before implementing |
| **Build** | `context-engineering` | Right context at the right time |
| **Build** | `frontend-ui-engineering` | Production-quality UI with accessibility |
| **Build** | `api-and-interface-design` | Stable interfaces with clear contracts |
| **Verify** | `test-driven-development` | Failing test first, then make it pass |
| **Verify** | `browser-testing-with-devtools` | Chrome DevTools MCP for runtime verification |
| **Verify** | `debugging-and-error-recovery` | Reproduce → localize → fix → guard |
| **Review** | `code-review-and-quality` | Five-axis review with quality gates |
| **Review** | `security-and-hardening` | OWASP prevention, input validation, least privilege |
| **Review** | `performance-optimization` | Measure first, optimize only what matters |
| **Review** | `code-simplification` | Eliminate complexity that doesn't earn its keep |
| **Ship** | `git-workflow-and-versioning` | Atomic commits, clean history |
| **Ship** | `ci-cd-and-automation` | Automated quality gates on every change |
| **Ship** | `deprecation-and-migration` | Safe removal of old code and APIs |
| **Ship** | `documentation-and-adrs` | Document the why, not just the what |
| **Ship** | `shipping-and-launch` | Pre-launch checklist, monitoring, rollback plan |
| **Meta** | `using-agent-skills` | Meta-skill: discover and invoke the right skill |

### Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order. Do not skip verification steps.
3. **Multiple skills can apply.** Sequence them: `spec` → `planning` → `impl` → `test` → `review` → `ship`.
4. **When in doubt, start with a spec.** If the task is non-trivial and there's no spec, begin with `spec-driven-development`.

## Slash Commands

Available after `.claude/commands/` is set up:

| Command | Purpose |
|---------|---------|
| `/spec` | Define requirements and acceptance criteria |
| `/plan` | Break down implementation into tasks |
| `/build` | Incremental implementation with tests |
| `/test` | Test-driven development workflow |
| `/review` | Code review across five quality axes |
| `/code-simplify` | Identify and remove unnecessary complexity |
| `/ship` | Parallel fan-out review (code + security + test) then launch |

## Agent System

### Reusable Personas

Located at `agents/personas/`:

| Persona | Use Case |
|---------|----------|
| `code-reviewer` | Code quality review, PR review |
| `security-auditor` | Security vulnerability scanning |
| `test-engineer` | Test strategy, test coverage analysis |

### Orchestration Rules

- **Single perspective** → Call a persona directly
- **Multi-perspective parallel** → `/ship` command (fan-out: code-reviewer + security-auditor + test-engineer → merge)
- **Full pipeline automation** → `agents/orchestration/main.py` (9-agent Python framework)

### Multi-Agent Orchestration (agents/orchestration)

Located at `agents/orchestration/`. A Python-based orchestration framework with 9 specialized agents:

| Agent | Role |
|-------|------|
| PM Agent | Requirement analysis, module decomposition |
| Architect Agent | System design, technology selection |
| Task Agent | Task planning and scheduling |
| Dev Agent | Code generation and implementation |
| Test Agent | Test case generation |
| Fix Agent | Bug analysis and repair |
| Review Agent | Code review |
| Deploy Agent | Deployment and release |
| Monitor Agent | System monitoring and alerting |

**Entry point**: `agents/orchestration/main.py`

## Development Workflow

**Closed-loop development**: Plan → Explore → Implement → Review → Simplify

| Phase | Command / Skill | Description |
|-------|-----------------|-------------|
| Define | `/spec` | Requirements, acceptance criteria |
| Plan | `/plan` | Task breakdown and sequencing |
| Explore | Explore Agent | Codebase research, architecture analysis |
| Build | `/build` | Incremental implementation |
| Test | `/test` | Test-driven verification |
| Review | `/review` | Code quality review |
| Simplify | `/code-simplify` | Remove unnecessary complexity |
| Ship | `/ship` | Parallel review + launch |

## Core Operating Behaviors

These apply at all times, regardless of which skill is active:

1. **Surface assumptions** — Before implementing anything non-trivial, state your assumptions explicitly and ask for confirmation.
2. **Manage confusion actively** — When you encounter inconsistencies, STOP. Name the confusion. Ask. Don't guess.
3. **Push back when warranted** — Point out problems directly with concrete downsides. Sycophancy is a failure mode.
4. **Enforce simplicity** — Prefer boring, obvious solutions. Cleverness is expensive.
5. **Maintain scope discipline** — Touch only what you're asked to touch. No unsolicited renovation.
6. **Verify, don't assume** — A task is not complete until verification passes. "Seems right" is never sufficient.

## Projects

### file-organizer-agent
- **Path**: `projects/file-organizer/`
- **Tech**: Python, macOS
- **Purpose**: Intelligent file classification and organization agent

### fin-product-forecast（金融产品预测预警系统）
- **Path**: `projects/fin-product-forecast/`
- **Tech**: Python, 原生 HTTP, scikit-learn, SQLite
- **Purpose**: 金融产品（汇率为主）的价格预测与风险预警，为交易决策提供科学依据
- **核心模块**：fx_system（预测引擎）、tools/fx_quant_strategy.py（量化回测）、docs/（文档体系）
- **文档入口**：`projects/fin-product-forecast/docs/GUIDE.md`

## Data Analysis Knowledge Base

### SQL Table Schema

| File | Size | Purpose |
|------|------|---------|
| `iuap_apdoc_coredoc.sql` | 1.4 GB | Core document table schema |
| `yonbip_clm_contract.sql` | 76 MB | Contract module table schema |

**Path**: `/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/合同系统数据字典/`
**Use**: Extract contract and supplier data for data analysis. See `skills/domain/sql-generation/SKILL.md`.

## Memory System

Persists information across sessions via `.claude/memory/`:

- **User**: Role, preferences, knowledge
- **Feedback**: Guidance on approach, what to avoid
- **Project**: Current work, goals, deadlines
- **Reference**: External systems, resources

## Capability Domains

### Frontend Development
- React, Vue, Svelte component design
- Responsive design and CSS architecture
- Performance optimization, state management patterns

### Backend Development
- RESTful and GraphQL API design
- Database design and optimization
- Microservices architecture, authentication and authorization

### DevOps & Cloud
- CI/CD pipeline design
- Docker and Kubernetes
- Cloud deployment (AWS, GCP, Azure), Infrastructure as code

### AI/ML Engineering
- Claude API integration
- Prompt engineering and optimization
- Model fine-tuning, data pipeline processing

### System Architecture
- Distributed systems design
- Security best practices
- Scalability patterns, observability and monitoring

## Quick Reference

- Skills are at `skills/engineering/<name>/SKILL.md`
- Domain skills: `skills/domain/financial-analysis/` | `skills/domain/sql-generation/`
- Slash commands: `/spec` `/plan` `/build` `/test` `/review` `/code-simplify` `/ship`
- Agent personas: `agents/personas/`
- Multi-agent system: `agents/orchestration/main.py`
- LLM client: `agents/orchestration/llm_client.py` (MiniMax + DeepSeek)
- Edit this file to customize Claude Code behavior
