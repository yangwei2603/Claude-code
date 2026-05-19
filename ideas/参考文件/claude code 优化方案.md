# Agent Skill 工作流程（企业级标准版）

Agent Skill 的本质不是“一个 Prompt”，而是：

> 一套可持续运行的
> **任务拆解 → 执行 → 测试 → 修复 → Review → 提交 → 反馈优化**
> 的完整闭环系统

尤其适合你现在做的：

* AI Coding
* RPA 自动化
* 财务数字化
* 多 Agent 协作
* 自动 PRD + 自动测试 + 自动修复

---

# 一、标准 Agent Skill 全流程图

```text
需求输入（PRD / 用户一句话）
        ↓
产品经理 Agent（需求分析）
        ↓
任务拆解 Agent（拆成子任务）
        ↓
开发 Agent（Claude Code 写代码）
        ↓
测试 Agent（自动测试）
        ↓
Bug 修复 Agent（自动修Bug）
        ↓
Code Review Agent（质量检查）
        ↓
Git Agent（提交PR）
        ↓
部署 Agent（发布上线）
        ↓
监控 Agent（日志反馈）
        ↓
持续优化（再次进入循环）
```

这就是完整闭环。

不是单点 AI。

而是系统。

---

# 二、核心 Agent 分工（建议必须有）

---

## 1️⃣ 产品经理 Agent（PM Agent）

### 输入

```text
用户需求 / PRD
```

### 输出

```json
{
  "modules": [
    "登录模块",
    "权限模块",
    "报表模块"
  ],
  "priority": "P1",
  "risk": "中"
}
```

### 职责

* 理解需求
* 输出 PRD
* 拆业务模块
* 排优先级

---

## 2️⃣ Task Agent（任务拆解）

### 输入

```text
PRD
```

### 输出

```json
[
  {
    "task": "创建用户表",
    "owner": "Backend Agent"
  }
]
```

### 职责

* 任务颗粒度标准化
* 分配执行对象

---

## 3️⃣ Dev Agent（开发 Agent）

推荐：

Claude Code
Cursor
Visual Studio Code

### 职责

* 写代码
* 重构
* 自动生成接口
* 自动生成数据库设计

---

## 4️⃣ Test Agent（测试 Agent）

### 职责

* 自动生成 pytest
* 自动运行测试
* 输出错误日志

这是最重要的。

没有测试 = AI胡写。

---

## 5️⃣ Fix Agent（修复 Agent）

### 输入

```text
测试失败日志
```

### 输出

```text
修复后的代码
```

### 职责

* 自动修Bug
* 回归验证

---

## 6️⃣ Review Agent（审查 Agent）

### 职责

* 安全检查
* 性能检查
* SQL 风险
* 权限问题
* 代码规范

企业必须有。

---

## 7️⃣ Git Agent

### 职责

* 自动 commit
* 自动 push
* 自动 PR

---

## 8️⃣ Deploy Agent（部署）

### 职责

* 自动发版
* 自动回滚
* 环境校验

---

## 9️⃣ Monitor Agent（监控）

### 职责

* 日志分析
* 告警处理
* 自动生成优化建议

这是高级玩法。

---

# 三、真正可执行的目录结构（推荐）

```text
agent-skill-system/
│
├── agents/
│   ├── pm_agent.py
│   ├── task_agent.py
│   ├── dev_agent.py
│   ├── test_agent.py
│   ├── fix_agent.py
│   ├── review_agent.py
│   ├── git_agent.py
│   └── deploy_agent.py
│
├── prompts/
│   ├── pm_prompt.md
│   ├── review_prompt.md
│   └── fix_prompt.md
│
├── workflows/
│   └── main_flow.py
│
├── config/
│   └── settings.yaml
│
├── tasks/
│   └── prd.txt
│
└── main.py
```

这是生产级结构。

不是 demo。

---

# 四、核心工作流（最关键）

## main.py 思路

```text
读取 PRD
→ PM Agent 分析
→ Task Agent 拆任务
→ Claude 写代码
→ Test Agent 测试
→ 如果失败：
      Fix Agent 修复
→ Review Agent 检查
→ Git 提交
→ Deploy 发布
```

这才是真正的 Agent Skill。

---

# 五、和 QClaw / Workbuddy 的关系（重点）

推荐架构：

```text
QClaw（调度）
      ↓
Main Controller
      ↓
多个 Agent
      ↓
Claude Code
      ↓
GitHub PR
```

即：

### QClaw 不负责写代码

### Claude 不负责调度

### Python 主控负责闭环

这是最稳定的方案。

---

# 六、你最应该做的升级（非常重要）

不是：

❌ 再多加几个 Prompt

而是：

## 建立：

### 可复用 Skill Library（技能库）

例如：

```text
skills/
├── mysql_design_skill
├── api_design_skill
├── test_generation_skill
├── code_review_skill
├── financial_report_skill
```

以后：

任何项目都能复用。

这才是真正的企业级。

---

# 七、你下一步应该直接做

建议立刻搭：

## 第一阶段 MVP

只做：

* PM Agent
* Dev Agent
* Test Agent
* Fix Agent
* Git Agent

就够了。

别一开始全做。

容易死。

---

# 八、真正的高手路线

不是：

“用 AI 写代码”

而是：

## 让 AI 自己管理 AI 写代码

这才是 Agent Skill。

这才是壁垒。

---