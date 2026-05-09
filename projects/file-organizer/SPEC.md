# SPEC: file-organizer 需求说明书

## 1. Objective

**项目目标：** 为数字化转型办公室提供自动化文件分类整理工具，将散落的业务文件按规则归档到标准目录结构中，支持 CLI 和 Web UI 双模式运行。

**目标用户：** 数字化转型办公室内部人员

**核心价值：**
- 减少人工文件整理工作量
- 通过规则引擎保证分类一致性
- 支持多维度分类（文件名/内容/扩展名）
- 完整的操作日志和回滚能力保障数据安全

**现状能力（v4.0）：**
- 四级优先级分类：关键词 → LLM语义 → 内容分析 → 扩展名兜底（v5.0新顺序）
- 支持 19 种文件格式内容提取（docx/pdf/xlsx/pptx等）
- 文件名智能解析（日期/项目编号/版本号）
- 重复文件检测、守护模式、回滚机制
- Web 管理界面（Flask）
- LLM 分类引擎（v5.0 新增）：支持 MiniMax / DeepSeek / OpenAI，按置信度阈值过滤

**重构目标（新优先级顺序）：**
1. **优先级1：关键词规则** — 文件名关键词精确匹配（最快、最准）
2. **优先级2：LLM 智能分类** — 大模型语义理解，兜底关键词匹配不到的文件
3. **优先级3：内容分析** — 文件内容关键词提取（docx/pdf/xlsx等）
4. **优先级4：扩展名兜底** — 按文件类型归档

> **设计理由**：关键词最快但覆盖有限，LLM 可理解语义但有延迟/成本，内容分析补充大文件，扩展名保底。

**v5.0 新增功能：LLM 智能分类引擎**
- 支持 MiniMax / DeepSeek / OpenAI 多模型切换
- Prompt 缓存 + 并发批量请求优化延迟
- 分类置信度阈值过滤，避免低质量结果
- 规则优先，LLM 仅处理关键词未命中的文件
- 按文件大小/类型智能分流（大文件走内容分析，文本走 LLM）

**已知待改进项（来自代码审查）：**
- `organizer.py` 1475 行过大，违反单一职责
- `DEFAULT_RULES` 在代码中硬编码，与 config.json/template JSON 三重冗余
- 路径硬编码 `\\`，macOS 不兼容
- `_classify_by_content` 裸 `except:` 静默吞异常
- `rglob` 全量加载大目录

---

## 2. Tech Stack

| 组件 | 技术 | 备注 |
|------|------|------|
| 语言 | Python 3 | 最低 3.8 |
| CLI 框架 | argparse | 标准库 |
| Web 框架 | Flask + flask-cors | |
| 内容提取 | python-docx, PyPDF2, openpyxl, pptx, striprtf | 可选库，缺库时优雅降级 |
| 配置格式 | JSON | config.json |
| 规则格式 | JSON | templates/*.json |
| 状态存储 | JSON 文件 | state/*.json |

---

## 3. Commands

```bash
# 预览整理（不移动文件）
python run.py --preview

# 执行整理
python run.py --execute

# 全量整理
python run.py --execute --full

# 指定天数增量
python run.py --execute --days 3

# 初始化目录结构
python run.py --setup
python run.py --setup --execute

# 守护模式（持续轮询）
python run.py --watch

# 回滚
python run.py --rollback

# 重复文件处理
python run.py --duplicates
python run.py --duplicates --execute

# Web 管理界面
python run.py --web
python run.py --web --port 5001

# 指定配置/模板
python run.py --config other.json
python run.py --template digital-office

# 指定规则 JSON
python run.py --execute --rules '{"keyword_rules":[{"keywords":["合同"],"target":"07-商务与采购\\00-合同协议"}]}'

# 保留原文件（复制模式）
python run.py --execute --keep-original
```

---

## 4. Project Structure

```
file-organizer/
├── organizer.py          # 核心引擎（1475行，需拆分）
├── main.py               # CLI 入口（argparse）
├── task_manager.py       # 任务管理（CRUD + 模板）
├── web.py                # Flask Web API（~610行）
├── scheduler.py         # 守护调度器
├── run.py                # 统一 CLI 入口
├── config.json           # 主配置文件
├── config.yaml           # YAML 格式配置（备用）
├── requirements.txt      # 依赖
├── templates/            # 规则模板
│   └── digital-office.json
├── tasks/                # 任务配置（JSON）
├── state/                # 状态文件
│   └── organizer_state.json
├── logs/                 # 会话日志（session_*.json）
├── utils/                # 工具模块
├── rules/                # 规则目录（预留）
├── organizer/            # organzier.py 源码（Python package）
├── llm/                  # LLM 相关（预留）
├── web/                  # Web 前端资源
├── build.sh / build.ps1  # 构建脚本
└── SPEC.md               # 本文档
```

**重构后目标结构（organizer.py 拆分）：**
```
organizer/
├── __init__.py
├── organizer.py       # 编排层（~400行）
├── rules.py           # 规则数据与 I/O（~400行）
├── classifier.py     # 分类决策逻辑（~300行）
├── content_analyzer.py # 内容提取（~260行）
├── state.py           # 状态管理（~280行）
├── constants.py       # 魔法数字常量
└── exceptions.py       # 自定义异常
```

---

## 5. Code Style

### 命名规范
- 类名：`PascalCase`（如 `DocumentOrganizer`, `ContentExtractor`）
- 函数/方法：`snake_case`（如 `scan_and_organize`, `_classify_by_content`）
- 常量：`UPPER_SNAKE_CASE`（如 `MAX_EXTRACTED_TEXT_CHARS`）
- 私有成员：前缀 `_`（如 `_classify`, `_move_file`）

### 路径处理
- 统一使用 `pathlib.Path`，禁止硬编码 `/` 或 `\\`
- 跨平台路径用 `Path / "subdir"` 或 `os.sep`
- 绝对路径用 `.is_absolute()` 判断

### 异常处理
- 禁止裸 `except:`，必须指定具体异常类型
- 外部库导入失败用 `try/except ImportError` 降级
- 所有异常必须记录日志

### 类型注解
- 函数参数和返回值标注类型（`filepath: Path`, `-> ClassificationResult`）
- dataclass 用于数据结构（`ClassificationResult`）

### 示例片段
```python
from pathlib import Path
from typing import Optional

def classify_file(filepath: Path, rules: dict) -> ClassificationResult:
    """四级优先级分类决策"""
    ext = filepath.suffix.lower()

    # 优先级1：业务领域
    for rule in rules.get("business_domain_rules", []):
        if match_keywords(filepath.name, rule["keywords"]):
            return ClassificationResult(
                target_path=rule["target"],
                rule_name=f"业务领域[{rule['keywords'][0]}]",
                priority=1,
                confidence=0.9,
                analysis_method="filename"
            )

    # 优先级4：扩展名兜底
    if ext in rules.get("extension_rules", {}):
        return ClassificationResult(...)

    return ClassificationResult(target_path="99-归档/01-临时文件", ...)
```

---

## 6. Testing Strategy

**当前状态：** 无测试框架

**目标：**
- 框架：`pytest`
- 测试目录：`tests/`
- 测试文件：`test_classifier.py`, `test_content_analyzer.py`, `test_organizer.py`

**测试分层：**
| 层级 | 测试内容 | 示例 |
|------|---------|------|
| 单元测试 | 纯函数（classifier.py 分类逻辑） | `test_classify_priority_1()` |
| 集成测试 | 文件操作（move/copy/rollback） | `test_rollback_last_session()` |
| 端到端测试 | CLI 完整流程 | `test_preview_mode()` |

**验收标准：**
- 分类逻辑 100% 覆盖
- 每个新功能必须附测试
- CI 每次 push 运行测试

---

## 7. Boundaries

### Always（必须遵守）
- CLI 新增参数必须同步更新 `--help`
- 新增依赖库必须更新 `requirements.txt` 并说明用途
- 路径处理统一用 `pathlib.Path`，禁止字符串拼接
- 异常必须记录日志，禁止静默吞掉
- 所有公开函数/类必须有 docstring

### Ask First（需确认后再做）
- 修改分类优先级逻辑
- 更改目录结构（移动或重命名已有目录）
- 添加新的文件格式支持（涉及 ContentExtractor 改动）
- 修改状态文件格式（影响已有回滚功能）
- 增加数据库或外部存储依赖

### Never（禁止）
- 在 `organizer.py` 中继续追加代码（已拆分）
- 在 `DEFAULT_RULES` 中硬编码路径用 `\\`
- 提交包含真实文件路径或敏感信息的代码
- 修改标准目录结构中已有的目录名称（用户已有数据依赖）

---

## 8. Open Questions

1. **Web UI 重构**：当前 web.py 与业务逻辑耦合，是否需要 Vue/React 重构前端？
2. **规则引擎可视化**：是否需要 Web 界面编辑规则（当前只支持 JSON 模板）？
3. **多用户支持**：当前 Web UI 无权限控制，是否需要？
4. **LLM 增强分类**：是否引入 LLM 做文件名语义分类（当前纯关键词）？
5. **文件监控**：是否从轮询改为 inotify/FSEvents 事件驱动？

---

## 9. Success Criteria（完成标志）

### v5.0 → v6.0 模块化迁移（当前迭代）

#### 功能完整性
- [ ] 回滚功能使用新引擎（移除 `run.py` 旧引擎硬依赖）
- [ ] 重复文件检测使用新引擎
- [ ] `python run.py --preview` / `--execute` / `--web` / `--watch` 全部正常
- [ ] Web UI 回滚/重复检测端点切换到新引擎

#### 架构清理
- [ ] `organizer.py` 精简为兼容 shim（≤150 行），不再包含业务逻辑
- [ ] `organizer/__init__.py` 不再动态加载旧模块
- [ ] `llm/claude_classifier.py` 删除（`llm/llm_classifier.py` 已覆盖其功能）
- [ ] 新模块架构：`organizer/` + `rules/` + `llm/` + `utils/` 各司其职

#### 代码质量
- [ ] 无裸 `except:`（当前 8 处全部在 `organizer.py`）
- [ ] 无硬编码 `\\` 路径（`rules/classifier.py` 7处 + `rules/rule_loader.py` 多处）
- [ ] 魔法数字提取为 `organizer/constants.py`
- [ ] 所有公开函数/方法有类型注解

#### CI/CD
- [ ] `.github/workflows/ci.yml` 存在且通过

#### 测试
- [ ] 现有 39 个测试全部通过
- [ ] 新增 `tests/test_content_extractor.py`
- [ ] 新增 `tests/test_rollback.py`
- [ ] 新增 `tests/test_utils.py`
- [ ] 新增 `tests/test_integration.py`（端到端）

#### 构建
- [ ] `build.sh all` 构建成功，生成可执行文件
