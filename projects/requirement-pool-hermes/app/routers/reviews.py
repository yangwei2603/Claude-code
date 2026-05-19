"""评审相关 API"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import Requirement, RequirementReview, StatusLog, REJECTION_TYPES

router = APIRouter()


@router.get("/reviews/rejection-types")
def get_rejection_types():
    return {
        "code": 0,
        "message": "success",
        "data": [
            {"code": code, "name": name, "description": desc}
            for code, name, desc in REJECTION_TYPES
        ]
    }


@router.post("/reviews/{demand_id}")
def submit_review(demand_id: str, data: dict, db: Session = Depends(get_db)):
    """评审提交：通过 / 驳回 / 未来规划"""
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")

    reviewer = data.get("reviewer", "unknown")
    reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action = data.get("action")  # "pass" | "reject" | "future"

    priority = data.get("priority")
    review_date = data.get("review_date")
    review_notes = data.get("review_notes", "")
    rejection_type = data.get("rejection_type")
    rejection_reason = data.get("rejection_reason")
    plan_status = None

    if action == "pass":
        plan_status = "正常"
    elif action == "future":
        plan_status = "未来规划"
    elif action == "reject":
        plan_status = None
        if not rejection_type:
            raise HTTPException(status_code=400, detail="驳回必须选择驳回类型")
    else:
        raise HTTPException(status_code=400, detail="无效的 action")

    # 查找或创建评审记录
    rev = db.query(RequirementReview).filter(
        RequirementReview.requirement_id == demand_id
    ).first()

    if rev:
        rev.priority = priority
        rev.review_date = review_date
        rev.review_notes = review_notes
        rev.rejection_type = rejection_type
        rev.rejection_reason = rejection_reason
        rev.reviewer = reviewer
        rev.reviewed_at = reviewed_at
        rev.plan_status = plan_status
        rev.is_reviewed = 1
    else:
        rev = RequirementReview(
            requirement_id=demand_id,
            priority=priority,
            review_date=review_date,
            review_notes=review_notes,
            rejection_type=rejection_type,
            rejection_reason=rejection_reason,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
            plan_status=plan_status,
            is_reviewed=1,
        )
        db.add(rev)

    # 更新最后修改时间
    req.last_modified = reviewed_at
    db.commit()
    return {"code": 0, "message": "success"}


@router.get("/reviews")
def list_reviews(
    is_reviewed: Optional[int] = None,
    rejection_type: Optional[str] = None,
    plan_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(RequirementReview)
    if is_reviewed is not None:
        q = q.filter(RequirementReview.is_reviewed == is_reviewed)
    if rejection_type:
        q = q.filter(RequirementReview.rejection_type == rejection_type)
    if plan_status:
        q = q.filter(RequirementReview.plan_status == plan_status)

    reviews = q.offset(skip).limit(limit).all()

    ids = [r.requirement_id for r in reviews]
    reqs_map = {}
    if ids:
        reqs = db.query(Requirement).filter(Requirement.demand_id.in_(ids)).all()
        reqs_map = {r.demand_id: r for r in reqs}

    items = []
    for rev in reviews:
        req = reqs_map.get(rev.requirement_id)
        items.append({
            "demand_id": rev.requirement_id,
            "demand_name": req.demand_name if req else None,
            "priority": rev.priority,
            "review_date": rev.review_date,
            "review_notes": rev.review_notes,
            "rejection_type": rev.rejection_type,
            "rejection_reason": rev.rejection_reason,
            "reviewer": rev.reviewer,
            "reviewed_at": rev.reviewed_at,
            "plan_status": rev.plan_status,
            "is_reviewed": rev.is_reviewed,
        })

    return {"code": 0, "message": "success", "data": items}


@router.get("/reviews/stats")
def get_review_stats(db: Session = Depends(get_db)):
    """当月评审统计（含本月新增需求数）"""
    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"

    all_reviews = db.query(RequirementReview).filter(
        RequirementReview.reviewed_at >= month_start
    ).all()

    total = len(all_reviews)
    passed = sum(1 for r in all_reviews if r.rejection_type is None and r.plan_status == "正常")
    rejected = sum(1 for r in all_reviews if r.rejection_type is not None)
    future = sum(1 for r in all_reviews if r.plan_status == "未来规划")

    # 本月新增需求
    new_reqs = db.query(Requirement).filter(
        Requirement.business_created_date >= month_start
    ).count()

    # 驳回类型分布
    rejection_dist = {}
    for r in all_reviews:
        if r.rejection_type:
            rejection_dist[r.rejection_type] = rejection_dist.get(r.rejection_type, 0) + 1

    return {
        "code": 0,
        "message": "success",
        "data": {
            "month": f"{now.year}-{now.month:02d}",
            "new_count": new_reqs,
            "review_count": total,
            "passed_count": passed,
            "rejected_count": rejected,
            "future_count": future,
            "rejection_distribution": rejection_dist,
        }
    }


@router.get("/reviews/monthly-review-stats")
def get_monthly_review_stats(db: Session = Depends(get_db)):
    """Dashboard 本月评审统计卡片专用接口"""
    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"

    all_reviews = db.query(RequirementReview).filter(
        RequirementReview.reviewed_at >= month_start
    ).all()

    passed = sum(1 for r in all_reviews if r.rejection_type is None and r.plan_status == "正常")
    rejected = sum(1 for r in all_reviews if r.rejection_type is not None)
    future = sum(1 for r in all_reviews if r.plan_status == "未来规划")
    total = passed + rejected + future

    return {
        "code": 0,
        "message": "success",
        "data": {
            "passed": passed,
            "rejected": rejected,
            "future": future,
            "total": total,
        }
    }


def _build_review_export(q, category: Optional[str] = None, db: Session = None):
    """共享评审导出逻辑，避免重复代码"""
    from io import BytesIO
    from openpyxl import Workbook

    reviews = q.all()
    ids = [r.requirement_id for r in reviews]
    reqs_map = {}
    if ids:
        reqs_map = {r.demand_id: r for r in
                    db.query(Requirement).filter(Requirement.demand_id.in_(ids)).all()}

    wb = Workbook()
    ws = wb.active
    ws.title = "评审结果"
    ws.append(["需求编号", "需求名称", "评审分类", "描述", "原因"])

    for rev in reviews:
        req = reqs_map.get(rev.requirement_id)
        demand_name = req.demand_name if req else ""

        if rev.plan_status == "未来规划":
            category_label = "未来规划"
            reason = rev.review_notes or ""
        elif rev.rejection_type:
            category_label = "驳回"
            reason = rev.rejection_reason or rev.rejection_type
        else:
            category_label = "通过"
            reason = rev.review_notes or ""

        if category and category != "all" and category_label != category:
            continue

        ws.append([
            rev.requirement_id,
            demand_name,
            category_label,
            rev.review_notes or "",
            reason,
        ])

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@router.get("/reviews/export")
def export_reviews_get(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """导出评审结果 Excel（GET 方式，支持 URL 参数）"""
    from fastapi.responses import StreamingResponse

    q = db.query(RequirementReview).filter(RequirementReview.is_reviewed == 1)
    if start_date:
        q = q.filter(RequirementReview.reviewed_at >= start_date)
    if end_date:
        q = q.filter(RequirementReview.reviewed_at <= end_date)

    buf = _build_review_export(q, category, db)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=review_export.xlsx"}
    )


@router.post("/reviews/export")
def export_reviews_post(
    start_date: Optional[str] = Body(None),
    end_date: Optional[str] = Body(None),
    category: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """导出评审结果 Excel（POST 方式）"""
    from fastapi.responses import StreamingResponse

    q = db.query(RequirementReview).filter(RequirementReview.is_reviewed == 1)
    if start_date:
        q = q.filter(RequirementReview.reviewed_at >= start_date)
    if end_date:
        q = q.filter(RequirementReview.reviewed_at <= end_date)

    buf = _build_review_export(q, category, db)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=review_export.xlsx"}
    )