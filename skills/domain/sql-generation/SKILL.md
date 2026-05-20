---
name: sql-generation
description: >
  SQL 查询生成与优化。覆盖用友 YonBIP 各业务域：
  合同管理（clm_contract）、税务系统（tax）、财务共享（FSS）、
  资金系统（cms）、总账（gl）、应付（ap）、应收（ar）。
  当用户问及：SQL 查询、数据字典、指标取数、合同数据分析、
  税务数据提取、共享作业查询、资金流水分析时触发。
triggers:
  - SQL 查询
  - 数据字典
  - 指标取数
  - 合同数据
  - 税务数据
  - 共享作业
  - 资金流水
  - 财务分析取数
  - 用友 YonBIP
agent_created: true
version: 1.0
created: 2026-05-07
---

# SQL 生成 Skill

## 能力范围

生成覆盖用友 YonBIP 全业务域的 SQL 查询语句，优先使用已验证的视图（如 `v_clm_contract_dw`），复杂查询直接构建 JOIN。

---

## 一、已验证的视图

### 1.1 合同数据宽表

**视图名**: `v_clm_contract_dw`
**数据库**: `yonbip_clm_contract`
**状态**: ✅ 已验证，字段完整

```sql
-- 基础查询模板
SELECT
    contract_code,       -- 合同编号
    contract_title,      -- 合同名称
    vendor_name,          -- 供应商名称
    vendor_supply_type,   -- 供应类型
    contract_amount,      -- 合同金额（本币）
    paid_amount,          -- 已付款金额
    invoice_amount,       -- 收票金额
    contract_status,      -- 合同状态
    sign_date,            -- 签订日期
    effective_date,       -- 生效日期
    expiry_date           -- 失效日期
FROM v_clm_contract_dw
WHERE dr = 0
  -- AND sign_date BETWEEN '2025-01-01' AND '2025-12-31'
  -- AND vendor_supply_type IN ('非关联方', '关联方')
;
```

---

## 二、业务域 SQL 模板

### 2.1 合同域（clm_contract）

**核心取数场景**

| 场景 | SQL 重点 | 关键字段 |
|------|----------|----------|
| 合同执行进度 | 已付/合同金额比 | paid_amount / contract_amount |
| 供应商排名 | 按金额分组 | vendor_name / contract_amount |
| 关联方识别 | supply_type | vendor_supply_type |
| 合同变更追踪 | change_times | change_contract_id |
| 履约保证金 | margin字段 | margin_amount / return_bond |
| 质保金管理 | retention字段 | retention_amount / retention_paid |

**常用字段速查**
```sql
-- 合同金额字段
contract_amount     -- 合同金额（本币）
have_tax_mny        -- 含税金额
no_tax_mny          -- 无税金额
tax_amount          -- 税额

-- 执行金额字段
paid_amount         -- 已付款
prepay_amount       -- 预付款
ap_amount           -- 应付未付
invoice_amount      -- 收票金额
service_confirm_amount -- 服务确认金额

-- 供应商字段
vendor_name         -- 供应商名称
vendor_supply_type  -- 供应类型（关联方/非关联方）
vendor_industry     -- 供应商行业
vendor_company_type -- 供应商企业类型

-- 状态字段
contract_status     -- 合同状态
finalize_status     -- 定稿状态
stamp_status        -- 用印状态
```

**示例查询：按供应商类型统计合同执行率**
```sql
SELECT
    CASE
        WHEN vendor_supply_type = '非关联方' THEN '非关联方'
        WHEN vendor_supply_type = '关联方' THEN '关联方'
        ELSE '未知'
    END AS supplier_category,
    COUNT(*) AS contract_count,
    SUM(contract_amount) AS total_amount,
    SUM(paid_amount) AS total_paid,
    ROUND(SUM(paid_amount) / NULLIF(SUM(contract_amount), 0) * 100, 2) AS payment_rate
FROM v_clm_contract_dw
WHERE dr = 0
  AND sign_date >= '2025-01-01'
GROUP BY
    CASE
        WHEN vendor_supply_type = '非关联方' THEN '非关联方'
        WHEN vendor_supply_type = '关联方' THEN '关联方'
        ELSE '未知'
    END
ORDER BY total_amount DESC;
```

**示例查询：欠票预警（收票金额 < 合同金额）**
```sql
SELECT
    contract_code,
    contract_title,
    vendor_name,
    contract_amount,
    paid_amount,
    invoice_amount,
    ROUND((contract_amount - invoice_amount) / NULLIF(contract_amount, 0) * 100, 2) AS invoice_gap_rate,
    expiry_date
FROM v_clm_contract_dw
WHERE dr = 0
  AND (contract_amount - invoice_amount) > 0
  AND contract_status IN ('EXECUTING', 'COMPLETED')
ORDER BY invoice_gap_rate DESC;
```

---

### 2.2 税务域（待接入）

**规划视图**: `v_tax_transaction_dw`

| 字段 | 说明 |
|------|------|
| tax_type | 税种（增值税/所得税/个税等）|
| tax_rate | 税率 |
| tax_amount | 税额 |
| invoice_type | 发票类型（专票/普票）|
| invoice_date | 开票日期 |
| supplier_id | 供应商ID |

**待实现查询**:
```sql
-- 按税种统计进项税额
SELECT
    tax_type,
    SUM(tax_amount) AS total_tax,
    COUNT(*) AS invoice_count
FROM v_tax_transaction_dw
WHERE invoice_date BETWEEN :start_date AND :end_date
GROUP BY tax_type;
```

---

### 2.3 财务共享域（待接入）

**规划视图**: `v_fss_dw`

| 场景 | 字段 |
|------|------|
| 单据审批时效 | submit_time / approve_time |
| 费用分摊 | cost_center / department |
| 影像补扫率 | image_status |
| 退单原因 | reject_reason |

**待实现查询**:
```sql
-- 共享作业时效分析
SELECT
    biz_type,
    COUNT(*) AS bill_count,
    AVG(TIMESTAMPDIFF(HOUR, submit_time, approve_time)) AS avg_hours,
    SUM(CASE WHEN reject_flag = 1 THEN 1 ELSE 0 END) AS reject_count,
    ROUND(SUM(CASE WHEN reject_flag = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS reject_rate
FROM v_fss_dw
WHERE submit_date >= :start_date
GROUP BY biz_type;
```

---

### 2.4 资金域（待接入）

**规划视图**: `v_cms_cashflow_dw`

| 字段 | 说明 |
|------|------|
| cash_type | 收支类型 |
| bank_account | 银行账户 |
| amount_cny | 金额（本币）|
| transaction_date | 交易日期 |
| counterparty | 交易对手 |

**待实现查询**:
```sql
-- 月度资金流水汇总
SELECT
    DATE_FORMAT(transaction_date, '%Y-%m') AS month,
    cash_type,
    SUM(amount_cny) AS total_amount,
    COUNT(*) AS transaction_count
FROM v_cms_cashflow_dw
WHERE transaction_date >= :start_date
GROUP BY DATE_FORMAT(transaction_date, '%Y-%m'), cash_type
ORDER BY month DESC, cash_type;
```

---

## 三、跨域关联查询（高阶）

### 3.1 合同-付款-发票关联

```sql
-- 合同执行全景（合同→付款→收票）
SELECT
    c.contract_code,
    c.contract_title,
    c.vendor_name,
    c.contract_amount,
    c.paid_amount,
    c.invoice_amount,
    ROUND(c.paid_amount / NULLIF(c.contract_amount, 0) * 100, 2) AS payment_progress_pct,
    ROUND(c.invoice_amount / NULLIF(c.contract_amount, 0) * 100, 2) AS invoice_progress_pct,
    c.expiry_date,
    c.contract_status
FROM v_clm_contract_dw c
WHERE c.dr = 0
  AND c.sign_date >= '2024-01-01'
ORDER BY c.contract_amount DESC;
```

---

## 四、SQL 编写规范

### 4.1 命名规范
- 视图命名：`v_<业务域>_<用途>_dw`
- 字段别名：snake_case + 中文注释
- 变量占位：用 `:param_name`（非 `@` 或 `?`）

### 4.2 性能规范
- 避免 `SELECT *`，明确字段
- WHERE 条件含 `dr = 0`（逻辑删除过滤）
- 大表加日期范围条件
- 关联超过3表时拆分为子查询

### 4.3 字段映射模板（新增域时使用）
```sql
-- 新域字段映射模板
SELECT
    t.id AS primary_key,
    t.code AS business_code,
    t.name AS business_name,
    t.org_id AS org_id,
    t.dept_id AS dept_id,
    t.amount AS amount,
    t.status AS status,
    t.create_time AS create_time,
    t.dr AS is_deleted
FROM <database>.<table> t
WHERE t.dr = 0;
```

---

## 五、数据字典位置

**Obsidian Vault**（优先参考）：
```
/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/
├── 合同系统数据字典/
├── 税务系统数据字典/
├── 财务共享数据字典/
└── 资金系统数据字典/
```

---

## 六、相关 Skill

| Skill | 用途 |
|-------|------|
| `data-analysis` | 数据分析 + 报告生成 |
| `neodata-financial-search` | 自然语言财务数据查询 |
| `xlsx` | SQL 导出数据的 Excel 处理 |
