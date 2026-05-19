#需求池管理系统（Hermes 实现版）

轻量级需求池管理工具，支持评审流程、驳回类型、版本对比、导出和 AI 总结。

## 快速启动

```bash
cd /Users/fox/Claude Code/projects/requirement-pool-hermes

# 安装依赖（如尚未安装）
/Users/fox/Hermes/.venv/bin/pip install -r requirements.txt

# 启动服务（默认端口 8000）
bash scripts/start.sh

# 或手动启动
/Users/fox/Hermes/.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问：http://localhost:8000

## 生产部署

```bash
# 使用 systemd（Linux）
sudo cp scripts/requirement-pool.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable requirement-pool
sudo systemctl start requirement-pool

# 使用 supervisor（Linux）
# 参考 scripts/supervisor.conf
```

## 架构

| 模块 | 文件 | 职责 |
|------|------|------|
| 后端 API | `app/main.py` | FastAPI 应用入口，自动初始化数据库 |
| 数据模型 | `app/models.py` | SQLAlchemy 模型定义 |
| 数据库 | `app/database.py` | 数据库连接管理 |
| 路由 | `app/routers/` | 各业务模块 API |
| 前端 | `app/static/index.html` | 单页应用 |
| 脚本 | `scripts/` | 工具脚本 |

## 技术栈

- **后端**：Python 3.10+ / FastAPI / SQLAlchemy / SQLite
- **前端**：HTML5 + Vanilla JavaScript + ECharts (CDN)
- **Excel 导出**：openpyxl

## 数据模型

- `requirement` — 需求主表
- `requirement_review` — 评审扩展表
- `status_log` — 状态流转记录
- `review_session` — 评审会话

## 状态设计

| 字段 | 来源 | 说明 |
|------|------|------|
| demand_status | CSV 导入，只读 | active / closed |
| plan_status | 系统内部 | 正常 / 未来规划 |
| is_closed | 派生 | demand_status="closed" 时为 1 |