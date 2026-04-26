# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

```
Claude Code/
├── GitHub/                    # GitHub repositories
│   └── openclaw-home-pc/      # Multi-agent desktop automation system
└── .claude/                   # Claude Code configuration
    ├── plans/                 # Implementation plans
    └── memory/                # Persistent memory
```

## Development Capabilities

### Skill System

Available skills for different development domains:

| Skill | Purpose |
|-------|---------|
| `/init` | Initialize new CLAUDE.md for projects |
| `/review` | Code review and PR review |
| `/security-review` | Security vulnerability scanning |
| `/simplify` | Code optimization and refactoring |
| `/loop` | Recurring task automation |
| `/claude-api` | Claude API and Anthropic SDK development |

### Agent System

| Agent | Use Case |
|-------|----------|
| `Explore` | Codebase research, architecture analysis, finding code patterns |
| `Plan` | Implementation planning, design validation |
| `general-purpose` | Complex multi-step tasks, research |

### Development Workflow

**闭环开发流程**: Plan → Explore → Implement → Review → Simplify

| Phase | Command | Description |
|-------|---------|-------------|
| Plan | `/plan` | Design and confirm complex task implementation |
| Explore | Explore Agent | Codebase research, architecture analysis |
| Implement | Direct editing | Feature and code implementation |
| Review | `/review` | Code review, PR review |
| Simplify | `/simplify` | Code optimization, refactoring |

### Automation

- **Scheduled tasks**: `/loop <interval> <command>` - e.g., `/loop 10m /babysit-prs`
- **Cron jobs**: `/cron "<cron>" <command>` - e.g., `/cron "0 9 * * 1-5" /code-audit`

## Capability Domains

### Frontend Development
- React, Vue, Svelte component design
- Responsive design and CSS architecture
- Performance optimization
- State management patterns

### Backend Development
- RESTful and GraphQL API design
- Database design and optimization
- Microservices architecture
- Authentication and authorization

### DevOps & Cloud
- CI/CD pipeline design
- Docker and Kubernetes
- Cloud deployment (AWS, GCP, Azure)
- Infrastructure as code

### AI/ML Engineering
- Claude API integration
- Prompt engineering and optimization
- Model fine-tuning
- Data pipeline processing

### System Architecture
- Distributed systems design
- Security best practices
- Scalability patterns
- Observability and monitoring

## Data Analysis Knowledge Base

### SQL表结构知识库
路径：`/Users/fox/知识库/sql 代码/`

| 文件 | 大小 | 用途 |
|------|------|------|
| iuap_apdoc_coredoc.sql | 1.4GB | 核心文档表结构 |
| yonbip_clm_contract.sql | 76MB | 合同模块表结构 |

**用途**：提取合同、供应商数据进行数据分析

## Memory System

Persists information across sessions:
- **User**: User role, preferences, knowledge
- **Feedback**: Guidance on approach, what to avoid
- **Project**: Current work, goals, deadlines
- **Reference**: External systems, resources

## Quick Reference

- Edit this file to customize Claude Code behavior
- Skills are invoked with `/skill-name`
- Agents are launched via the `Agent` tool
- Memory is stored in `.claude/memory/`