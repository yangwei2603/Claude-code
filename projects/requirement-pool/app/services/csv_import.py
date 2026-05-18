import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import ImportMetadata, Requirement, RequirementReview


CSV_HEADER_MAP = {
    # 基础识别
    "编号": "demand_id",
    "需求名称": "demand_name",
    "所属阶段": "stage",
    "归属项目": "project",
    "干系部门": "department",
    "需求重要程度": "importance",
    "优先级": "pri",

    # 状态与时间
    "状态": "_raw_status",
    "期望上线日期": "deadline",
    "end_time": "end_time",
    "begin_time": "begin_time",

    # 需求描述
    "需求描述": "demand_desc",
    "业务现状": "businessdesc",
    "期望达成的业务效果": "businessobjective",

    # 业务需求信息（business_*）
    "业务id": "business_id",
    "业务需求名称": "business_name",
    "业务需求状态": "business_status",
    "业务评审状态": "business_review_status",
    "业务评审结果": "business_review_result",
    "业务审批": "business_approval",
    "业务创建时间": "business_created_date",
    "业务创建人": "business_edited_by",
    "业务最后编辑时间": "business_edited_date",
    "业务PM": "business_pm",
    "业务PM名称": "business_pm_name",
    "业务能力": "business_capability",
    "原因类型": "reason_type",
    "业务描述": "busi_desc",
    "业务描述2": "business_desc",
    "业务目标": "business_objective",
    "业务访问控制": "business_acl",
    "业务架构": "business_architecture",
    "业务流程": "busi_process",
    "应用架构": "application_architecture",

    # 项目审批信息（approval_*）
    "项目立项id": "proj_approval_id",
    "审批状态": "approval_status",
    "审批名称": "approval_name",
    "审批创建人": "approval_created_by",
    "审批创建时间": "approval_created_date",
    "审批编辑人": "approval_edited_by",
    "审批编辑时间": "approval_edited_date",
    "审批描述": "approval_desc",
    "审批评审结果": "approval_review_result",
    "审批评审状态": "approval_review_status",
    "最终审批": "approval_approval",
    "审批访问控制": "approval_acl",
    "mailto": "mailto",
    "方案": "program",
    "产品计划": "product_plan",

    # 项目立项
    "model": "model",
    "type": "type",
    "class": "class_",
    "业务线": "business_line",
    "auth": "auth",
    "days": "days",

    # 成本与资源
    "研发预算": "development_budget",
    "外包预算": "outsourcing_budget",
    "总成本": "total_cost",
    "成本预算": "cost_budget",
    "BRD剩余预算": "brd_remain_budget",

    # 需求池基础信息
    "需求池id": "demandpool_id",
    "dept": "dept",
    "name": "name",
    "需求池描述": "demandpool_desc",
    "需求池访问控制": "demandpool_acl",
    "是否取消": "is_cancel",
    "是否IT确认": "is_it_confirm",
    "负责部门": "responsible_dept",
    "负责部门名称": "responsible_dept_name",
    "记录人": "recorder",

    # 评审与变更记录
    "项目评审日期": "project_review_date",
    "项目编号": "project_number",
    "评审日期": "review_date",
    "评审地点": "review_location",
    "参与人": "participant",
    "备注": "remark",
    "评价反馈人": "evaluation_feedback_by",
    "评价反馈日期": "evaluation_feedback_date",
    "变更申请日期": "change_application_date",
    "变更内容": "change_content",
    "变更原因": "change_reason",
    "项目立项日期": "project_approval_date",
    "终止日期": "termination_date",
    "目标": "target",

    # ITPM 字段
    "ITPM账号": "itpm_account",
    "ITPM姓名": "itpm_realname",
    "ITPM短号": "itpm_shorcq",
    "ITPM部门": "itpm_dept_name",

    # 其他
    "原状态": "old_status",
    "网络安全": "net_info_safe",
    "会议": "meeting",
    "集成": "integrate",
    "风险": "risk",

    # 英文列名（与 CSV 导出格式一致）
    "demand_id": "demand_id",
    "demand_name": "demand_name",
    "demand_status": "_raw_status",
    "demand_desc": "demand_desc",
    "businessobjective": "businessobjective",
    "businessdesc": "businessdesc",
    "business_id": "business_id",
    "business_name": "business_name",
    "business_status": "business_status",
    "business_review_status": "business_review_status",
    "proj_approval_id": "proj_approval_id",
    "approval_status": "approval_status",
    "approval_name": "approval_name",
    "business_pm_name": "business_pm_name",
    "responsible_dept_name": "responsible_dept_name",
    "deadline": "deadline",
    "business_created_date": "business_created_date",
    "last_modified": "last_modified",
    "importance": "importance",
    "reason_type": "reason_type",
    "department": "department",
    "begin_time": "begin_time",
    "end_time": "end_time",
    "type": "type",
    "model": "model",

    # 系统字段
    "creator": "creator",
    "source_dept": "source_dept",
}

CLOSED_STATUSES = {"已关闭", "已取消", "已结项", "关闭"}

HASH_FIELDS = (
    "demand_name", "demand_desc", "businessobjective", "department", "importance",
    "business_desc", "business_objective", "reason_type", "stage", "project",
    "deadline", "business_id", "business_status", "approval_status",
)


def _normalize_status(raw: str) -> str:
    if not raw:
        return "active"
    return "closed" if raw.strip() in CLOSED_STATUSES else "active"


def _row_hash(row: dict) -> str:
    parts = "|".join((row.get(f) or "") for f in HASH_FIELDS)
    return hashlib.md5(parts.encode("utf-8")).hexdigest()


def parse_csv(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    seen_ids: dict[str, int] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row: dict = {}
            for csv_col, model_field in CSV_HEADER_MAP.items():
                row[model_field] = (raw.get(csv_col) or "").strip()
            row["demand_status"] = _normalize_status(row.pop("_raw_status", ""))
            row.pop("_raw_status", None)
            row.pop("last_modified", None)  # preserve server-set import time
            demand_id = row.get("demand_id", "")
            if not demand_id:
                continue
            # Handle duplicate demand_ids by appending suffix
            if demand_id in seen_ids:
                seen_ids[demand_id] += 1
                row["demand_id"] = f"{demand_id}_{seen_ids[demand_id]}"
            else:
                seen_ids[demand_id] = 0
            rows.append(row)
    return rows


def import_rows(db: Session, rows: Iterable[dict]) -> dict:
    new_count = 0
    updated_count = 0
    updated_ids: list[str] = []
    now = datetime.now().isoformat()

    parts_for_global = []
    rows = list(rows)

    for row in rows:
        demand_id = row["demand_id"]
        h = _row_hash(row)
        parts_for_global.append(f"{demand_id}:{h}")

        existing = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
        review = (
            db.query(RequirementReview)
            .filter(RequirementReview.requirement_id == demand_id)
            .first()
        )

        if not existing:
            db.add(Requirement(**row, last_modified=now))
            db.add(
                RequirementReview(
                    requirement_id=demand_id,
                    version_hash=h,
                    is_updated=0,
                    is_reviewed=0,
                )
            )
            new_count += 1
        else:
            for k, v in row.items():
                setattr(existing, k, v)
            old_hash = review.version_hash if review else None
            if old_hash != h:
                existing.last_modified = now
                if not review:
                    db.add(
                        RequirementReview(
                            requirement_id=demand_id,
                            version_hash=h,
                            is_updated=1,
                            is_reviewed=0,
                        )
                    )
                else:
                    review.version_hash = h
                    review.is_updated = 1
                updated_count += 1
                updated_ids.append(demand_id)

    db.flush()
    unreviewed_count = (
        db.query(RequirementReview).filter(RequirementReview.is_reviewed == 0).count()
    )

    global_hash = hashlib.md5("|".join(parts_for_global).encode("utf-8")).hexdigest()

    meta = db.query(ImportMetadata).order_by(ImportMetadata.id.desc()).first()
    if meta is None:
        db.add(
            ImportMetadata(
                last_import_hash=global_hash,
                last_import_at=now,
                total_imported=len(parts_for_global),
            )
        )
    else:
        meta.last_import_hash = global_hash
        meta.last_import_at = now
        meta.total_imported = len(parts_for_global)

    db.commit()
    return {
        "total": len(parts_for_global),
        "imported": len(parts_for_global),
        "new": new_count,
        "updated": updated_count,
        "unreviewed": unreviewed_count,
        "updated_list": updated_ids,
    }
