---
name: sql-generation
description: MySQL SQL 查询生成与优化技能，专注用友 YonBIP / iUAP 合同系统数据字典。触发词：SQL查询、数据库查询、生成SQL、表结构分析、合同系统、用友SQL、Navicat数据字典。
---

# SQL 生成 Skill

## 能力范围

- 基于数据字典生成 SELECT / INSERT / UPDATE / DELETE 语句
- 关联查询（JOIN）优化与多表关联逻辑
- 聚合统计（GROUP BY、HAVING、子查询）
- 复杂业务查询构建（如合同金额汇总、部门权限过滤）
- SQL 性能优化建议（索引使用、EXPLAIN 分析）
- 分页查询与条件筛选

## 数据字典参考

### 数据源位置

- `/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/合同系统数据字典/`

### 已接入数据库

| 数据库 | 来源 | 服务器 |
|--------|------|--------|
| `iuap_apdoc_coredoc` | 春秋测试环境 | 192.168.210.176:3307（MySQL 8.4） |
| `yonbip_clm_contract` | 春秋测试环境 | 192.168.210.176:3307（MySQL 8.4） |

> **说明**：SQL 文件为 Navicat 导出的建表脚本（.sql），可使用文件头部注释确认表名和字段说明。

## 生成流程

### Step 1：理解业务需求

向用户确认：

1. 目标表（from 哪个表？）
2. 筛选条件（where 条件？）
3. 输出字段（select 哪些列？）
4. 聚合需求（是否需要 group by？）
5. 排序与分页

### Step 2：读取数据字典

使用 `read_file` 读取对应 .sql 文件头部（`head -200`），理解表结构和字段含义。

```bash
# 示例：读取 iuap_apdoc_coredoc 表结构
head -200 "/Users/fox/Documents/Obsidian Vault/自动笔记/05-数据资产/01-数据治理/合同系统数据字典/iuap_apdoc_coredoc.sql"
```

### Step 3：生成 SQL

遵循以下规范：

- 表别名使用 AS（可读性）
- WHERE 条件加注释说明业务含义
- 金额字段注意单位（分 vs 元）
- 日期字段注意格式（DATE vs DATETIME）
- LIMIT 默认 1000 条，防止全表扫描

### Step 4：优化建议

- 是否缺少索引（主键、外键字段）
- 是否可用覆盖索引减少回表
- 子查询是否可改为 JOIN（性能差异）
- 百万级数据分页建议（游标分页 vs 深度分页）

## 示例场景

### 场景 1：合同金额汇总

```sql
SELECT
    dept_id,
    COUNT(*) AS contract_count,
    SUM(contract_amount) AS total_amount
FROM yonbip_clm_contract
WHERE contract_status = 'APPROVED'
  AND contract_date >= '2025-01-01'
GROUP BY dept_id
HAVING SUM(contract_amount) > 1000000
ORDER BY total_amount DESC;
```

### 场景 2：跨库关联查询

```sql
SELECT
    c.contract_code,
    c.contract_name,
    d.doc_title,
    c.creator,
    c.create_time
FROM yonbip_clm_contract c
LEFT JOIN iuap_apdoc_coredoc d ON c.id = d.doc_id
WHERE c.contract_status = 'PENDING'
LIMIT 100;
```

## 注意事项

- 敏感字段（密码、内部ID）不直接暴露，生成时用 `/* sensitive */` 占位
- 批量更新/删除必须包含 WHERE 条件并建议附上备份查询
- 涉及金额计算时，明确单位（元/分）避免精度问题
