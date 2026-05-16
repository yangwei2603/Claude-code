# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace

```
Claude Code/
├── .claude/commands/          # 7 slash commands: /spec /plan /build /test /review /code-simplify /ship
├── .claude/hooks/             # Session lifecycle hooks (session-start.sh 等)
├── skills/
│   ├── engineering/           # 21 工程技能（技能名/SKILL.md）
│   └── domain/                 # 4 领域技能：data-analysis, financial-analysis, sql-generation, machine-learning
├── agents/
│   ├── personas/             # code-reviewer, security-auditor, test-engineer
│   └── orchestration/        # Python 多 Agent 框架（9 agents + llm_client）
│       ├── llm_client.py      # MiniMax / DeepSeek / 本地大模型 统一客户端
│       ├── main.py            # 入口
│       └── agents/           # pm/task/dev/test/fix/review/git/deploy/monitor
├── projects/                  # 各项目含独立 CLAUDE.md
│   ├── file-organizer/        # 智能文件分类 Agent（Python/macOS）
│   ├── fin-product-forecast/  # 金融产品价格预测（Python/sklearn/SQLite）
│   ├── futures-signal/        # 期货信号系统（Python）
│   └── 内控二期/              # 内控系统二期
├── data-analysis-local/       # 本地数据分析工作区（详见其 CLAUDE.md）
│   └── <主题>-<YYYYMMDD>/    # 每次分析任务独立目录
└── hooks/                     # 完整钩子集（SDD-cache, simplify-ignore, git-hooks）
```

## Skill System

**技能路径**：`skills/engineering/<name>/SKILL.md` 或 `skills/domain/<name>/SKILL.md`

### 何时使用技能（Intent → Skill）

| 场景 | 技能 |
|------|------|
| 新功能 / 需求定义 | `spec-driven-development` → `incremental-implementation` |
| 任务分解 | `planning-and-task-breakdown` |
| 写测试 / TDD | `test-driven-development` |
| Bug 修复 | `debugging-and-error-recovery` |
| 代码审查 | `code-review-and-quality` |
| 重构 / 简化 | `code-simplification` |
| UI 开发 | `frontend-ui-engineering` |
| API 设计 | `api-and-interface-design` |
| 安全审查 | `security-and-hardening` |
| 性能优化 | `performance-optimization` |
| CI/CD / 自动化 | `ci-cd-and-automation` |
| 文档 / ADR | `documentation-and-adrs` |
| 部署发布 | `shipping-and-launch` |
| **数据分析流程** | `data-analysis`（domain）|
| **财务数据 / 报表** | `financial-analysis`（domain）|
| **SQL 生成** | `sql-generation`（domain）|

**规则**：任务匹配技能时，**必须**调用该技能，不直接实现。技能是工作流，不是建议。

## Development Workflow

所有代码变更（功能 / Bug 修复 / 重构）必须经过：

```
/spec → /plan → /build → /test → /review → /ship
```

非平凡项目必须从 `/spec` 开始。新项目在 `projects/` 下创建，先写项目级 `CLAUDE.md`。

## Agent System

| 组件 | 用途 |
|------|------|
| `agents/personas/` | 可复用角色：code-reviewer, security-auditor, test-engineer |
| `agents/orchestration/` | Python 多 Agent 框架，9 个专业化 Agent |
| `agents/orchestration/llm_client.py` | MiniMax + DeepSeek + 本地大模型统一客户端 |

调用方式：
```python
from agents.orchestration.llm_client import llm
resp = llm.chat(prompt, model="local")  # 本地模型（涉密数据）
resp = llm.chat(prompt, model="deepseek")  # DeepSeek
```

## 本地模型约束（硬约束）

触发词：本地数据、内部数据、私有化、涉密、财务数据、航班收益、供应商、成本、合同

→ 强制使用 `model="local"`，本地模型不可达时**直接终止**，不得回退到云端。

## Data Analysis

`data-analysis-local/CLAUDE.md` 包含：
- 本地 SQLite 数据库路径（`/Users/fox/DB/analysis.db` / `external_data.db`）
- 报告输出规范（格式选择、Obsidian 同步）
- SQL 数据字典位置

## Karpathy Coding Guidelines（必须遵守）

1. **Think Before Coding** — 明确假设，不确定则提问，多种解释则列出
2. **Simplicity First** — 只写解决问题所需的最小代码，不做投机性抽象
3. **Surgical Changes** — 只改必须改的，不改善相邻代码
4. **Goal-Driven Execution** — 定义可验证的成功标准，循环验证

## Core Operating Behaviors

1. **Surface assumptions** — 非平凡实现前显式声明假设并确认
2. **Manage confusion actively** — 遇不一致立即停止，说清问题，不猜测
3. **Push back when warranted** — 有具体问题时直接指出
4. **Enforce simplicity** — 倾向显而易见方案，复杂有代价
5. **Scope discipline** — 只改被要求改的，不主动翻新
6. **Verify, don't assume** — 验证通过才算完成

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
│       └── sql-generation/           # SQL生成：公司内部系统全业务域（合同/税务/共享/资金）
├── agents/                            # Agents layer: personas + orchestration framework
│   ├── personas/                     # Reusable personas: code-reviewer, test-engineer, security-auditor
│   └── orchestration/               # Python multi-agent framework (9 agents + llm_client)
│       ├── llm_client.py           # MiniMax + DeepSeek + 本地大模型 统一 LLM 客户端
│       ├── agents/                 # 9 agents: pm/task/dev/test/fix/review/git/deploy/monitor
│       ├── config/settings.yaml    # LLM config (provider switching: minimax / deepseek)
│       └── workflows/
├── projects/                          # Projects layer: 各项目独立目录
│   └── <project-name>/              # 每个项目含独立 CLAUDE.md，项目会持续增加
├── AI-Factory/                       # Read-only origin — sync from here to skills/agents/hooks on demand
│   └── agent-skills/                # Reference source, do not edit directly
├── 参考文件/                           # Architecture reference documents (Chinese)
├── data-analysis-local/              # 本地数据分析工作区（详见该目录 CLAUDE.md）
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

Hooks 分布在两个目录：`.claude/hooks/`（轻量启动钩子）和 `hooks/`（完整钩子集）。

| Hook | 目录 | Trigger | Purpose |
|------|------|---------|----------|
| `session-start.sh` | `.claude/hooks/` + `hooks/` | On session start | Initialize workspace context |
| `sdd-cache-pre.sh` | `hooks/` | Before SDD skill | Cache preparation |
| `sdd-cache-post.sh` | `hooks/` | After SDD skill | Cache refresh |
| `simplify-ignore.sh` | `hooks/` | During simplify | Ignore patterns for refactoring |
| `simplify-ignore-test.sh` | `hooks/` | During simplify | Ignore patterns (test mode) |
| `git-hooks/` | `hooks/` | Git events | Git lifecycle hooks |
| `SDD-CACHE.md` / `SIMPLIFY-IGNORE.md` | `hooks/` | — | Hook 配置文档 |
| `hooks.json` | 两个目录各一份 | — | Hook 注册配置 |

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
| **数据分析** | `sql-generation` | domain | SQL生成：根据数据字典生成查询（合同/税务/共享/资金），字典路径见 `data-analysis-local/CLAUDE.md` |

### Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.
2. **Skills are workflows, not suggestions.** Follow the steps in order. Do not skip verification steps.
3. **Multiple skills can apply.** Sequence them: `spec` → `planning` → `impl` → `test` → `review` → `ship`.
4. **When in doubt, start with a spec.** If the task is non-trivial and there's no spec, begin with `spec-driven-development`.
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

各项目位于 `projects/` 下，每个项目含独立 `CLAUDE.md`。项目会持续增加，不在此逐一列举。

当前项目目录：
- `projects/file-organizer/` — 智能文件分类 Agent（Python/macOS）
- `projects/fin-product-forecast/` — 金融产品价格预测系统（Python/sklearn/SQLite）
- `projects/futures-signal/` — 期货信号系统（Python）

> 项目详情（架构、模块、已知问题等）见各项目目录下的 `CLAUDE.md`。

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

## Data Analysis

数据分析工作的详细约束（本地模型要求、输出规范、报告格式等）见 `data-analysis-local/CLAUDE.md`。

相关 Skills：`data-analysis` / `financial-analysis` / `sql-generation`（均在 `skills/domain/` 下）。

## Capability Domains

> 详细技术能力见各项目 CLAUDE.md，本工作区不预判具体技术栈。

## Quick Reference

- Engineering skills: `skills/engineering/<name>/SKILL.md`
- Domain skills: `skills/domain/data-analysis/` | `skills/domain/financial-analysis/` | `skills/domain/sql-generation/`
- Slash commands: `/spec` `/plan` `/build` `/test` `/review` `/code-simplify` `/ship`
- Agent personas: `agents/personas/`
- Multi-agent system: `agents/orchestration/main.py`
- LLM client: `agents/orchestration/llm_client.py` (MiniMax + DeepSeek + 本地模型)
- Edit this file to customize Claude Code behavior

---

## Document Optimization Guide

文档规范参考：`skills/engineering/documentation-and-adrs/SKILL.md`。

---

## Hermes Agent 协作

Hermes Agent (v0.13.0) 已安装在独立虚拟环境中，可作为上下文数据源和 MCP Server 为 Claude Code 提供跨工作空间信息整合。

### Hermes 工作空间

| 项目 | 路径 |
|------|------|
| 工作空间 | `/Users/fox/Hermes` |
| 虚拟环境 | `/Users/fox/Hermes/.venv` |
| 命令 | `~/.local/bin/hermes` |
| 配置 | `~/.hermes/config.yaml` |

### 已索引数据源

| 数据源 | 路径 | 索引位置 |
|--------|------|----------|
| Obsidian Vault | `/Users/fox/Documents/Obsidian Vault` | `/Users/fox/Hermes/context/obsidian_index.json` (162 篇笔记) |
| 个人数据库 | `/Users/fox/DB/analysis.db` | `/Users/fox/Hermes/context/database_index.json` (9 表, 2,556,370 行) |
| 个人数据库(临时) | `/Users/fox/DB/analysis_temp.db` | 同上 (1 表, 232,495 行) |

### 通过 Hermes 查询数据

```bash
# 搜索 Obsidian 笔记内容
rg -i "关键词" "/Users/fox/Documents/Obsidian Vault/"

# 查询个人数据库
sqlite3 /Users/fox/DB/analysis.db "SELECT * FROM table_name LIMIT 10;"

# 通过索引检索笔记元数据
python3 -c "import json; idx=json.load(open('/Users/fox/Hermes/context/obsidian_index.json')); [print(n['title'], n['relative_path']) for n in idx['notes'] if '关键词' in n.get('tags',[])]"
```

### Hermes MCP Server

Hermes 已配置为 Claude Code 的 MCP Server（见 `.claude/mcp.json`）：

```bash
# 启动 Hermes MCP Server
hermes mcp serve
```

### 更新索引

```bash
python3 /Users/fox/Hermes/scripts/index_obsidian.py   # 更新 Obsidian 索引
python3 /Users/fox/Hermes/scripts/index_database.py   # 更新数据库索引
```
