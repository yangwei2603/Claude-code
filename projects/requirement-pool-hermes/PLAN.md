# PLAN — 需求池管理系统 v2 实现计划

> 生成时间：2026-05-28
> 状态：✅ 已完成

---

## 需求梳理

### Dashboard 首页（Batch 4 上）
根据 SPEC.md 3.3 节，需补充：

| 模块 | 现状 | 需求 |
|------|------|------|
| 本月评审统计 | 5 个 KPI 卡片（已实现） | 补充：待评审数 badge、评审率趋势（CSS） |
| 当月评审统计 | `monthly-review-stats` 已挂载（后端 API 缺失） | 需新增 `/reviews/monthly-review-stats` 后端 API |
| 业务线汇总 | `business-tbody` 已挂载 | `business/summary` API 需存在，当前可能 404 |
| 创建人分布 | `chart-creator` 已挂载 | `requirements/distribution?group_by=creator` 需存在 |

### 生命周期页（Batch 4 下）
根据 SPEC.md 3.5 节：

| 功能 | 现状 | 需求 |
|------|------|------|
| 4 Tab 结构 | 已实现 Tab 切换 | 需确认后端 API 支持按 stage 过滤 |
| 快速立项 | 仅有按钮，无逻辑 | 需新增 `PUT /requirements/{id}/stage` + 前端关联项目弹窗 |
| 标记上线 | 仅有按钮，无逻辑 | 需新增 `PUT /requirements/{id}/online` + 日期录入 |
| 标记关闭 | 仅有按钮，无逻辑 | 需新增 `PUT /requirements/{id}/close` + 日期+原因录入 |
| 无归属需求区 | 无 | 需新增独立区域 + 快速创建项目逻辑 |

---

## 文件变更清单

### 新增后端 API
- `app/routers/reviews.py`
  - `GET /reviews/monthly-review-stats` — 本月评审统计

### 修改后端 API
- `app/routers/requirements.py`
  - `PUT /requirements/{demand_id}/stage` — 标记立项（关联项目）
  - `PUT /requirements/{demand_id}/online` — 标记上线
  - `PUT /requirements/{demand_id}/close` — 标记关闭

### 前端修改
- `app/static/index.html`
  - Dashboard：月份统计 API 容错、创建人图表样式
  - 生命周期页：4 Tab 联动后端、快速立项/标记上线/标记关闭弹窗
  - 新增 `initCreatorChart()` 函数
  - 新增项目关联弹窗 HTML

### 路由注册
- `app/main.py` 或 `app/routers/__init__.py` — 确认 `reviews` 路由已注册

---

## 实施顺序

### Phase 1：后端 API 补全（build-1）
1. 新增 `GET /reviews/monthly-review-stats`
2. 新增 `PUT /requirements/{demand_id}/stage`（立项）
3. 新增 `PUT /requirements/{demand_id}/online`（上线）
4. 新增 `PUT /requirements/{demand_id}/close`（关闭）

### Phase 2：前端生命周期页补全（build-2）
1. 重构 `loadLifecycle()` 按 Tab 调用正确 API
2. 新增"关联项目"弹窗（立项用）
3. 新增"标记上线"弹窗（日期选择）
4. 新增"标记关闭"弹窗（日期 + 原因）
5. 新增无归属需求独立展示区

### Phase 3：Dashboard 收尾（build-3）
1. 修复 `initCreatorChart()` 函数
2. 确认各 API 容错逻辑
3. 页面刷新验证

---

## API 规格

### GET /reviews/monthly-review-stats
**响应：**
```json
{
  "data": {
    "passed": 5,      // 本月通过数
    "rejected": 2,     // 本月驳回数
    "future": 1,      // 本月未来规划数
    "total": 8        // 本月已评审总数
  }
}
```

### PUT /requirements/{demand_id}/stage
**请求：**
```json
{ "project_id": "P001" }
```
**响应：** `{ "message": "ok" }`

### PUT /requirements/{demand_id}/online
**请求：**
```json
{ "actual_launch_date": "2026-06-01" }
```
**响应：** `{ "message": "ok" }`

### PUT /requirements/{demand_id}/close
**请求：**
```json
{ "close_date": "2026-06-10", "close_reason": "需求变更" }
```
**响应：** `{ "message": "ok" }`

---

## 风险项
- `/reviews/monthly-review-stats` 后端尚未实现，需新建
- `/business/summary` API 可能不存在，需确认
- 生命周期 4 Tab 的后端过滤字段是 `stage` 还是其他，需确认数据模型