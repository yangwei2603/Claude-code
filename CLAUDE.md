# CLAUDE.md
<!-- Last updated: 2026-05-07 -->
<!-- Version: 1.3 -->

This file provides guidance to Claude Code when working with code in this repository.

## Workspace Structure

```
Claude Code/
├── CLAUDE.md                          # This file — global configuration
├── .claude/
│   ├── commands/                      # Slash commands (/spec /plan /build /test /review /ship)
│   └── hooks/                         # Session lifecycle hooks (auto-injected on startup)
├── skills/                            # Skills layer: engineering + domain skills
│   ├── engineering/                   # 21 engineering skills (spec-driven, code-review, etc.)
│   └── domain/                        # Domain skills
│       ├── data-analysis/            # 通用数据分析流程（清洗→EDA→建模→可视化→报告）
│       ├── financial-analysis/       # 春秋财务部通用分析（供应商、成本多维、报表发布、竞争情报）
│       └── sql-generation/           # SQL生成：YonBIP全业务域（合同/税务/共享/资金）
├── agents/                            # Agents layer: personas + orchestration framework
│   ├── personas/                     # Reusable personas: code-reviewer, test-engineer, security-auditor
│   └── orchestration/               # Python multi-agent framework (9 agents + llm_client)
│       ├── llm_client.py           # MiniMax + DeepSeek unified LLM client
│       ├── agents/                 # 9 agents: pm/task/dev/test/fix/review/git/deploy/monitor
│       ├── config/settings.yaml    # LLM config (provider switching: minimax / deepseek)
│       └── workflows/
├── projects/                          # Projects layer: product implementations
│   ├── file-organizer/              # Intelligent file classification agent (Python/macOS)
│   └── fin-product-forecast/        # Financial product forecasting system (Python/sklearn/SQLite)
├── AI-Factory/                       # Read-only reference source (sync from root skills/agents/hooks)
│   ├── agent-skills/                # Origin — do not edit, synced to root
│   ├── file-organizer-agent/        # [Migrated → projects/file-organizer/]
│   └── fin-product-forecast/        # [Migrated → projects/fin-product-forecast/]
├── 参考文件/                           # Architecture reference documents (Chinese)
├── data-analysis-local/              # 本地数据分析工作区（Local data analysis workspace）
│   └── <topic>-<YYYYMMDD>/          # Per-task analysis folder (SQL, reports, charts)
```

> **技能路径 (Skill Path):** Engineering skills are at `skills/engineering/<name>/SKILL.md`.
> Domain skills are at `skills/domain/<name>/SKILL.md`.

## Getting Started

### Required Configuration

| Config | Purpose |
|--------|---------|
| `.claude/settings.local.json` | API keys, LLM providers (MiniMax/DeepSeek) |
| `.claude/commands/*.md` | 7 slash commands (spec, plan, build, test, review, code-simplify, ship) |

### Verification

Run `/help` to confirm slash commands are loaded. If commands are missing, check that `.claude/commands/` contains all 7 command files.

### Hooks

Session lifecycle hooks in `.claude/hooks/` and `hooks/`:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | On session start | Initialize workspace context |
| `sdd-cache-pre.sh` | Before SDD skill | Cache preparation |
| `sdd-cache-post.sh` | After SDD skill | Cache refresh |
| `simplify-ignore.sh` | During simplify | Ignore patterns for refactoring |

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
    │   ├── UI work? ──────────────────────→ frontend-ui-engineering + frontend-design
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
    ├── Deploying / launching? ─────────────→ shipping-and-launch
    │
    │   ── 数据分析 / 自动化场景 (Data Analysis & Automation) ──
    ├── 分析财务数据 / 报表解读? ──────────→ financial-analysis (domain)
    ├── 生成/优化 SQL 查询? ────────────────→ sql-generation (domain)
    ├── 通用数据分析流程? ──────────────────→ data-analysis (domain)
    │   └── 航司财务专项? ─────────────────→ financial-analysis (domain)
    ├── 流程自动化 / RPA / 定时任务? ───────→ ci-cd-and-automation
    └── 技术文档优化 / ADR? ────────────────→ documentation-and-adrs
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
| UI work | `frontend-ui-engineering` + `frontend-design` (aesthetics) |
| Security review | `security-and-hardening` |
| Performance issues | `performance-optimization` |
| Shipping / deployment | `shipping-and-launch` |
| **通用数据分析流程** | `data-analysis` (domain) |
| **财务数据 / 报表解读 / 供应商分析** | `financial-analysis` (domain) |
| **SQL 生成 / 数据查询** | `sql-generation` (domain) |
| **流程自动化 / RPA / 定时任务** | `ci-cd-and-automation` |
| **文档优化 / ADR / 技术写作** | `documentation-and-adrs` |
| **系统设计 / 架构规划** | `spec-driven-development` → `api-and-interface-design` |

### All Available Skills

Skills are located at `skills/engineering/<skill-name>/SKILL.md`.
Domain skills are located at `skills/domain/<skill-name>/SKILL.md`.

| Phase | Skill | Path | Summary |
|-------|-------|------|---------|
| **Define** | `idea-refine` | engineering | Refine vague ideas through structured thinking |
| **Define** | `spec-driven-development` | engineering | Requirements and acceptance criteria before code |
| **Plan** | `planning-and-task-breakdown` | engineering | Decompose into small, verifiable tasks |
| **Build** | `incremental-implementation` | engineering | Thin vertical slices, test each before expanding |
| **Build** | `source-driven-development` | engineering | Verify against official docs before implementing |
| **Build** | `context-engineering` | engineering | Right context at the right time |
| **Build** | `frontend-ui-engineering` | engineering | Production-quality UI (component architecture, responsive CSS) |
| **Build** | `frontend-design` | plugin (claude-plugins-official) | Distinctive aesthetics (typography, color, motion, visual details) |
| **Build** | `api-and-interface-design` | engineering | Stable interfaces with clear contracts |
| **Verify** | `test-driven-development` | engineering | Failing test first, then make it pass |
| **Verify** | `browser-testing-with-devtools` | engineering | Chrome DevTools MCP for runtime verification |
| **Verify** | `debugging-and-error-recovery` | engineering | Reproduce → localize → fix → guard |
| **Review** | `code-review-and-quality` | engineering | Five-axis review with quality gates |
| **Review** | `security-and-hardening` | engineering | OWASP prevention, input validation, least privilege |
| **Review** | `performance-optimization` | engineering | Measure first, optimize only what matters |
| **Review** | `code-simplification` | engineering | Eliminate complexity that doesn't earn its keep |
| **Ship** | `git-workflow-and-versioning` | engineering | Atomic commits, clean history |
| **Ship** | `ci-cd-and-automation` | engineering | Automated quality gates on every change |
| **Ship** | `deprecation-and-migration` | engineering | Safe removal of old code and APIs |
| **Ship** | `documentation-and-adrs` | engineering | Document the why, not just the what |
| **Ship** | `shipping-and-launch` | engineering | Pre-launch checklist, monitoring, rollback plan |
| **Meta** | `using-agent-skills` | engineering | Meta-skill: discover and invoke the right skill |
| **数据分析** | `data-analysis` | domain | 通用数据分析流程：数据获取→清洗→EDA→建模→可视化→报告 |
| **数据分析** | `financial-analysis` | domain | 春秋财务部通用分析：供应商评估、成本多维钻取、报表发布清单、竞争情报 |
| **数据分析** | `sql-generation` | domain | SQL生成：根据/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/数据字典（合同/税务/共享/资金）|

### Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order. Do not skip verification steps.
3. **Multiple skills can apply.** Sequence them: `spec` → `planning` → `impl` → `test` → `review` → `ship`.
4. **When in doubt, start with a spec.** If the task is non-trivial and there's no spec, begin with `spec-driven-development`.
5. **Mandatory workflow for ALL code changes.** Every code change — new feature, bug fix, refactor — MUST follow the closed-loop workflow: `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`. `spec-driven-development` and `incremental-implementation` are MANDATORY for any non-trivial change. Skipping steps is not allowed.
5. **Mandatory workflow for ALL code changes.** Every code change — new feature, bug fix, refactor — MUST follow the closed-loop workflow: `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`. `spec-driven-development` and `incremental-implementation` are MANDATORY for any non-trivial change. Skipping steps is not allowed.

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

### New Project Setup (Mandatory)

When creating a new project under `projects/`:

1. **Create `CLAUDE.md` first** — Before any code, write the project-level `CLAUDE.md`
2. **Follow Development Workflow** — All projects MUST go through: `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`
3. **Enforce Karpathy Guidelines** — All code must follow the Karpathy Coding Guidelines below (Think Before Coding → Simplicity First → Surgical Changes → Goal-Driven Execution)
4. **Use spec-driven-development skill** — Non-trivial projects must start with a spec

### Root vs Project CLAUDE.md Division

| Scope | File | Responsibility |
|-------|------|----------------|
| **Global** | `/CLAUDE.md` | Workspace navigation, Skill routing, Agent system, Development workflow, Karpathy guidelines |
| **Project** | `projects/<name>/CLAUDE.md` | Project overview, quick commands, architecture, known issues, code conventions, testing strategy |

**Rule**: Project `CLAUDE.md` inherits all global rules (Karpathy guidelines, Core Operating Behaviors) by default. Project-specific overrides must be explicitly stated.

## Core Operating Behaviors

These apply at all times, regardless of which skill is active:

1. **Surface assumptions** — Before implementing anything non-trivial, state your assumptions explicitly and ask for confirmation.
2. **Manage confusion actively** — When you encounter inconsistencies, STOP. Name the confusion. Ask. Don't guess.
3. **Push back when warranted** — Point out problems directly with concrete downsides. Sycophancy is a failure mode.
4. **Enforce simplicity** — Prefer boring, obvious solutions. Cleverness is expensive.
5. **Maintain scope discipline** — Touch only what you're asked to touch. No unsolicited renovation.
6. **Verify, don't assume** — A task is not complete until verification passes. "Seems right" is never sufficient.

---

## Karpathy Coding Guidelines (Mandatory Constraint)

> Source: [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)
> These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

**The test:** Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Projects

### file-organizer
- **Path**: `projects/file-organizer/`
- **Tech**: Python, macOS
- **Purpose**: Intelligent file classification and organization agent
- **Note**: v5.0 版本，旧版 `file-organizer-agent` 已迁移至此

### fin-product-forecast (Financial Product Forecasting System)
- **Path**: `projects/fin-product-forecast/`
- **Tech**: Python, native HTTP, scikit-learn, SQLite
- **Purpose**: Price forecasting and risk alerting for financial products (primarily FX), supporting trading decisions
- **Core modules**: fx_system (forecasting engine), tools/fx_quant_strategy.py (quant backtesting), docs/ (documentation)
- **Doc entry**: `projects/fin-product-forecast/docs/GUIDE.md`

### Project CLAUDE.md Template

When creating a new project, use this template for `projects/<name>/CLAUDE.md`:

```markdown
# CLAUDE.md — {项目名}

## 项目概述
1句话描述项目目标和核心价值。

## 快速命令
```bash
# 常用CLI命令
```

## 架构
| 模块 | 文件 | 职责 |
|------|------|------|
| | | |

## 已知问题
- 来自 SPEC.md 的已知技术债务

## 代码规范
- 项目特有的编码约定（继承全局 Karpathy 指南）

## 测试策略
- 测试框架、覆盖率目标、关键测试场景

## 与全局 Skill 的关联
| 场景 | 使用的 Skill |
|------|-------------|
| 新功能开发 | spec-driven-development → incremental-implementation |
| Bug 修复 | debugging-and-error-recovery |
| 代码审查 | code-review-and-quality |
| 部署发布 | shipping-and-launch |
```

## Data Analysis Knowledge Base

### SQL Table Schema

| File | Size | Purpose |
|------|------|---------|
| `v_clm_contract_dw.sql` | ~12 KB | 合同数据宽表视图（已验证，推荐优先使用） |
| `iuap_apdoc_coredoc.sql` | 1.4 GB | Core document table schema |
| `yonbip_clm_contract.sql` | 76 MB | Contract module table schema |

**Path**: `data-analysis-local/`
**Use**: Extract contract and supplier data for data analysis. See `skills/domain/sql-generation/SKILL.md`.

## Data Analysis Workflow (Mandatory — Hard Constraint)

All data analysis tasks involving internal/private/financial data **must** follow this workflow. No exceptions.

### 1. Local Model Requirement (Strict)

**Trigger keywords** (any of): 本地模型、本地数据、内部数据、私有化、涉密、财务数据、航班收益、供应商、成本、合同

When any trigger keyword appears:
- **MUST** call `llm.chat(prompt, model="local")` via `agents/orchestration/llm_client.py`
- **FORBIDDEN**: Hardcoding analysis text, insights, conclusions, or recommendations
- Internal financial data **MUST** use local model, **never** cloud APIs

**Required import**:
```python
from agents.orchestration.llm_client import llm
response = llm.chat(prompt, model="local")
```

**Strict prohibition**: Analysis content (摘要、发现、风险、建议等) must be generated by the local model — never write it manually or copy-paste previous reports.

### 2. Output Location
- Fixed pattern: `data-analysis-local/<主题>-<YYYYMMDD>/`
- Always create new folder per analysis task; never reuse old folders

### 3. Report Output Format
- **ASK user** before generating: Markdown / PDF / Word
- Report must include header:
  ```
  作者：数字化办公室-AI
  日期：YYYY-MM-DD
  数据来源：
  分析模型：Qwen3-VL-235B-A22B-Instruct-AWQ（本地私有化大模型）
  ```

### 4. Workflow Sequence
```
1. Detect trigger keyword → mandatory local model call
2. Output dir: data-analysis-local/<topic>-<YYYYMMDD>/
3. Ask user for report format (Markdown/PDF/Word)
4. Data analysis → call llm.chat(prompt, model="local") for all analysis content
5. Generate report → save to output folder
```

### 5. Memory System

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

- Engineering skills: `skills/engineering/<name>/SKILL.md`
- Domain skills: `skills/domain/data-analysis/` | `skills/domain/financial-analysis/` | `skills/domain/sql-generation/`
- Data analysis workspace: `data-analysis-local/<topic>-<YYYYMMDD>/`
- Slash commands: `/spec` `/plan` `/build` `/test` `/review` `/code-simplify` `/ship`
- Agent personas: `agents/personas/`
- Multi-agent system: `agents/orchestration/main.py`
- LLM client: `agents/orchestration/llm_client.py` (MiniMax + DeepSeek)
- Edit this file to customize Claude Code behavior

---

## Document Optimization Guide

When optimizing technical documents, follow these principles:

### 1. Structure First
- Use clear hierarchy: H1 → H2 → H3
- Table of contents for documents > 1000 words
- Consistent formatting throughout

### 2. Content Quality
- One idea per paragraph
- Bullet points for lists (max 7 items)
- Tables for comparisons and specifications
- Code blocks for technical examples

### 3. Cross-References
- Link to related skills and documents
- Use relative paths for internal links
- Version references for external dependencies

### 4. Maintenance
- Update date in header
- Changelog for significant revisions
- Deprecated content marked with ~~strikethrough~~

### 5. Review Checklist
- [ ] Technical accuracy verified
- [ ] All links working
- [ ] Code examples tested
- [ ] Consistent terminology
- [ ] Accessible language (avoid unnecessary jargon)
