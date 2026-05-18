from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, RequirementReview
from app.services.workdays import parse_date, workdays_since

router = APIRouter()

BACKLOG_WORKDAYS = 20


def _is_expired(r: Requirement, today: date) -> bool:
    # 优先用项目上线时间（end_time），其次用需求期望上线日期（deadline）
    d = parse_date(r.end_time or r.deadline)
    if not d:
        return False
    return r.demand_status == "active" and d < today


@router.get("/requirements/stats")
def requirements_stats(db: Session = Depends(get_db)):
    items = db.query(Requirement).all()
    today = date.today()
    total = len(items)
    active = sum(1 for r in items if r.demand_status == "active")
    closed = sum(1 for r in items if r.demand_status == "closed")
    expired = sum(1 for r in items if _is_expired(r, today))
    urgent = sum(1 for r in items if (r.importance or "").strip() == "紧急")
    expired_urgent = sum(
        1 for r in items if _is_expired(r, today) and (r.importance or "").strip() == "紧急"
    )

    by_status: dict[str, int] = {}
    by_project: dict[str, int] = {}
    by_creator: dict[str, int] = {}
    by_month: dict[str, int] = {}
    for r in items:
        by_status[r.demand_status or "未知"] = by_status.get(r.demand_status or "未知", 0) + 1
        by_project[r.project or "未指定"] = by_project.get(r.project or "未指定", 0) + 1
        by_creator[r.creator or "未知"] = by_creator.get(r.creator or "未知", 0) + 1
        d = parse_date(r.deadline)
        if d:
            key = f"{d.year}-{d.month:02d}"
            by_month[key] = by_month.get(key, 0) + 1

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "active": active,
            "closed": closed,
            "expired": expired,
            "urgent": urgent,
            "expired_urgent": expired_urgent,
            "by_status": by_status,
            "by_project": by_project,
            "by_creator": by_creator,
            "by_month": by_month,
        },
    }


@router.get("/requirements/backlog")
def backlog_list(db: Session = Depends(get_db)):
    """积压超时：demand_status=active + business_id IS NULL + plan_status != 未来规划 + >20 工作日无操作"""
    items = (
        db.query(Requirement, RequirementReview)
        .outerjoin(RequirementReview, RequirementReview.requirement_id == Requirement.demand_id)
        .filter(Requirement.demand_status == "active")
        .filter((Requirement.business_id == None) | (Requirement.business_id == ""))  # noqa: E711
        .all()
    )
    result = []
    for r, rv in items:
        if rv and rv.plan_status == "未来规划":
            continue
        wd = workdays_since(r.last_modified)
        if wd is None or wd <= BACKLOG_WORKDAYS:
            continue
        result.append(
            {
                "demand_id": r.demand_id,
                "demand_name": r.demand_name,
                "created_date": r.business_created_date,
                "last_modified": r.last_modified,
                "workdays_since_modified": wd,
                "creator": r.creator,
            }
        )
    result.sort(key=lambda x: x["last_modified"] or "")
    return {"code": 0, "message": "success", "data": result, "threshold_workdays": BACKLOG_WORKDAYS}


def _length_bucket(s: Optional[str], satisfy: int, fail: int) -> str:
    n = len(s or "")
    if n >= satisfy:
        return "green"
    if n < fail:
        return "red"
    return "yellow"


@router.get("/requirements/quality-dist")
def quality_dist(db: Session = Depends(get_db)):
    items = db.query(Requirement).all()
    spec = {
        "demand_desc": (50, 20),
        "businessobjective": (30, 10),
        "businessdesc": (30, 10),
    }
    out: dict[str, dict[str, int]] = {}
    for field, (sat, fail) in spec.items():
        buckets = {"red": 0, "yellow": 0, "green": 0}
        for r in items:
            buckets[_length_bucket(getattr(r, field), sat, fail)] += 1
        out[field] = buckets
    return {"code": 0, "message": "success", "data": out}


@router.get("/reviews/stats")
def reviews_stats(db: Session = Depends(get_db)):
    today = date.today()
    month_prefix = f"{today.year}-{today.month:02d}"
    items = db.query(RequirementReview).all()

    new_count = 0
    for r in db.query(Requirement).all():
        d = parse_date(r.business_created_date)
        if d and d.year == today.year and d.month == today.month:
            new_count += 1

    reviewed = [r for r in items if r.reviewed_at and r.reviewed_at.startswith(month_prefix)]
    reviewed_count = len(reviewed)
    rejected = sum(1 for r in reviewed if r.rejection_type)
    future = sum(1 for r in reviewed if r.plan_status == "未来规划")
    passed = reviewed_count - rejected - future

    rejection_dist: dict[str, int] = {}
    for r in reviewed:
        if r.rejection_type:
            rejection_dist[r.rejection_type] = rejection_dist.get(r.rejection_type, 0) + 1

    return {
        "code": 0,
        "message": "success",
        "data": {
            "month": month_prefix,
            "new": new_count,
            "reviewed": reviewed_count,
            "passed": passed,
            "rejected": rejected,
            "future": future,
            "rejection_dist": rejection_dist,
        },
    }
