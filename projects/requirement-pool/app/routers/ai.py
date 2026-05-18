from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models import Requirement, RequirementReview
from app.services.ai import score_requirement
from app.services.workdays import parse_date

router = APIRouter()


class QualityResponse(BaseModel):
    demand_id: str
    demand_name: str
    total: float
    desc_score: float
    obj_score: float
    dep_score: float
    scope_score: float
    suggestions: list[str]
    level: str

    @staticmethod
    def from_requirement(r: Requirement) -> "QualityResponse":
        qs = score_requirement(r)
        if qs.total >= 80:
            level = "green"
        elif qs.total >= 60:
            level = "yellow"
        else:
            level = "red"
        return QualityResponse(
            demand_id=r.demand_id,
            demand_name=r.demand_name,
            total=qs.total,
            desc_score=qs.desc_score,
            obj_score=qs.obj_score,
            dep_score=qs.dep_score,
            scope_score=qs.scope_score,
            suggestions=qs.suggestions,
            level=level,
        )


@router.get("/ai/quality/{demand_id}")
def quality_one(demand_id: str, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not r:
        return {"code": 404, "message": "Requirement not found", "data": None}
    return {
        "code": 0,
        "message": "success",
        "data": QualityResponse.from_requirement(r),
    }


@router.get("/ai/quality")
def quality_batch(db: Session = Depends(get_db)):
    items = db.query(Requirement).all()
    return {
        "code": 0,
        "message": "success",
        "data": [QualityResponse.from_requirement(r) for r in items],
    }


def _build_summary(db: Session) -> dict:
    today = date.today()
    month_prefix = f"{today.year}-{today.month:02d}"

    total = db.query(Requirement).count()
    active = db.query(Requirement).filter(Requirement.demand_status == "active").count()

    new_count = 0
    for r in db.query(Requirement).all():
        d = parse_date(r.business_created_date)
        if d and d.year == today.year and d.month == today.month:
            new_count += 1

    all_reviews = db.query(RequirementReview).all()
    reviewed = [r for r in all_reviews if r.reviewed_at and r.reviewed_at.startswith(month_prefix)]
    rejected = [r for r in reviewed if r.rejection_type]
    future_plan = [r for r in reviewed if r.plan_status == "未来规划"]
    passed = len(reviewed) - len(rejected) - len(future_plan)

    rej_dist: dict[str, int] = {}
    for r in rejected:
        if r.rejection_type:
            rej_dist[r.rejection_type] = rej_dist.get(r.rejection_type, 0) + 1

    backlog_items = (
        db.query(Requirement, RequirementReview)
        .outerjoin(RequirementReview, RequirementReview.requirement_id == Requirement.demand_id)
        .filter(Requirement.demand_status == "active")
        .filter((Requirement.business_id == None) | (Requirement.business_id == ""))
        .all()
    )
    backlog_count = 0
    for r, rv in backlog_items:
        if rv and rv.plan_status == "未来规划":
            continue
        from app.services.workdays import workdays_since
        wd = workdays_since(r.last_modified)
        if wd is not None and wd > 20:
            backlog_count += 1

    low_quality = db.query(Requirement).all()
    lq_count = sum(1 for r in low_quality if score_requirement(r).total < 60)

    return {
        "month": month_prefix,
        "total": total,
        "active": active,
        "new_count": new_count,
        "reviewed": len(reviewed),
        "passed": passed,
        "rejected": len(rejected),
        "future": len(future_plan),
        "rejection_dist": rej_dist,
        "backlog_count": backlog_count,
        "low_quality_count": lq_count,
    }


@router.get("/ai/summary")
def ai_summary(db: Session = Depends(get_db)):
    d = _build_summary(db)
    lines = [
        f"## {d['month']} 评审月度总结",
        "",
        "### 一、总体情况",
        f"- 本月新增需求：{d['new_count']} 条",
        f"- 本月评审需求：{d['reviewed']} 条",
        f"- 评审通过：{d['passed']} 条",
        f"- 评审驳回：{d['rejected']} 条",
        f"- 标记未来规划：{d['future']} 条",
        "",
        "### 二、驳回分布",
    ]
    if d["rejection_dist"]:
        for code, cnt in sorted(d["rejection_dist"].items(), key=lambda x: -x[1]):
            lines.append(f"- {code}：{cnt} 条")
    else:
        lines.append("- 本月无驳回")

    lines.extend([
        "",
        "### 三、积压预警",
        f"- 当前活跃需求总数：{d['active']} 条",
        f"- 积压超时需求（>20工作日无操作）：{d['backlog_count']} 条",
        f"- 描述质量低下（评分<60）：{d['low_quality_count']} 条",
        "",
        "### 四、建议",
    ])

    if d["rejected"] > d["passed"] * 0.3:
        lines.append("- 驳回率偏高，建议加强需求预审，减少无效评审")
    if d["backlog_count"] > 5:
        lines.append(f"- 积压需求较多（{d['backlog_count']}条），建议尽快评审或标记未来规划")
    if d["low_quality_count"] > 3:
        lines.append(f"- 存在 {d['low_quality_count']} 条低质量需求，建议补充描述后重新提交评审")
    if not lines[-1].startswith("- "):
        lines.append("- 整体运行良好，继续保持")

    return {
        "code": 0,
        "message": "success",
        "data": {"month": d["month"], "text": "\n".join(lines)},
    }