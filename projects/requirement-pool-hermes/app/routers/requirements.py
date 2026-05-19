"""需求 CRUD + 状态流转"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from typing import Optional, List
import hashlib

from app.database import get_db
from app.models import Requirement, RequirementReview, StatusLog, REJECTION_TYPES

router = APIRouter()


def compute_hash(demand_name, demand_desc, businessobjective, department, importance):
    s = f"{demand_name or ''}|{demand_desc or ''}|{businessobjective or ''}|{department or ''}|{importance or ''}"
    return hashlib.md5(s.encode()).hexdigest()


@router.get("/requirements/backlog")
def get_backlog(db: Session = Depends(get_db)):
    """20工作日积压未关联业务线的需求（PRD 规格，路由顺序优先）"""
    all_reqs = db.query(Requirement).filter(
        Requirement.demand_status == "active",
        or_(Requirement.business_id == None, Requirement.business_id == "")
    ).all()

    # 批量获取所有相关评审记录，避免 N+1
    req_ids = [r.demand_id for r in all_reqs]
    reviews_map = {}
    if req_ids:
        reviews = db.query(RequirementReview).filter(
            RequirementReview.requirement_id.in_(req_ids)
        ).all()
        for rev in reviews:
            reviews_map[rev.requirement_id] = rev

    result = []
    now = datetime.now()
    for req in all_reqs:
        review = reviews_map.get(req.demand_id)
        if review and review.plan_status == "未来规划":
            continue

        last_mod_str = req.last_modified or req.business_created_date
        if not last_mod_str:
            continue

        try:
            last_mod = datetime.strptime(last_mod_str[:10], "%Y-%m-%d")
            days = (now - last_mod).days
        except (ValueError, TypeError, AttributeError):
            continue
        workdays = days - (days // 7 * 2)
        if workdays > 20:
            result.append({
                "demand_id": req.demand_id,
                "demand_name": req.demand_name,
                "created_date": req.business_created_date,
                "last_modified": req.last_modified,
                "working_days": workdays,
                "creator": req.creator,
            })

    return {"code": 0, "message": "success", "data": result}


@router.get("/requirements")
def list_requirements(
    demand_status: Optional[str] = None,
    department: Optional[str] = None,
    creator: Optional[str] = None,
    is_reviewed: Optional[int] = None,
    is_updated: Optional[int] = None,
    is_closed: Optional[int] = None,
    plan_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(Requirement)
    if demand_status:
        q = q.filter(Requirement.demand_status == demand_status)
    if department:
        q = q.filter(Requirement.department == department)
    if creator:
        q = q.filter(Requirement.creator == creator)
    if is_closed is not None:
        q = q.filter(Requirement.demand_status == ("closed" if is_closed else "active"))

    if plan_status:
        # 关联 review 表过滤
        ids_with_plan = db.query(RequirementReview.requirement_id).filter(
            RequirementReview.plan_status == plan_status
        ).all()
        q = q.filter(Requirement.demand_id.in_([r[0] for r in ids_with_plan]))

    if is_updated is not None:
        ids_updated = db.query(RequirementReview.requirement_id).filter(
            RequirementReview.is_updated == is_updated
        ).all()
        q = q.filter(Requirement.demand_id.in_([r[0] for r in ids_updated]))

    result = q.offset(skip).limit(limit).all()

    # 关联评审信息
    ids = [r.demand_id for r in result]
    reviews_map = {}
    if ids:
        reviews = db.query(RequirementReview).filter(
            RequirementReview.requirement_id.in_(ids)
        ).all()
        for rev in reviews:
            reviews_map[rev.requirement_id] = rev

    items = []
    for r in result:
        item = {
            "demand_id": r.demand_id,
            "demand_name": r.demand_name,
            "demand_status": r.demand_status,
            "stage": r.stage,
            "project": r.project,
            "department": r.department,
            "demand_desc": r.demand_desc,
            "businessobjective": r.businessobjective,
            "businessdesc": r.businessdesc,
            "business_id": r.business_id,
            "business_name": r.business_name,
            "business_status": r.business_status,
            "business_review_status": r.business_review_status,
            "proj_approval_id": r.proj_approval_id,
            "approval_status": r.approval_status,
            "approval_name": r.approval_name,
            "business_pm_name": r.business_pm_name,
            "responsible_dept_name": r.responsible_dept_name,
            "deadline": r.deadline,
            "business_created_date": r.business_created_date,
            "last_modified": r.last_modified,
            "importance": r.importance,
            "reason_type": r.reason_type,
            "creator": r.creator,
            "source_dept": r.source_dept,
            "business_capability": r.business_capability,
        }
        rev = reviews_map.get(r.demand_id)
        if rev:
            item["review"] = {
                "priority": rev.priority,
                "review_date": rev.review_date,
                "review_notes": rev.review_notes,
                "rejection_type": rev.rejection_type,
                "rejection_reason": rev.rejection_reason,
                "reviewer": rev.reviewer,
                "reviewed_at": rev.reviewed_at,
                "is_updated": rev.is_updated,
                "is_reviewed": rev.is_reviewed,
                "quality_score": rev.quality_score,
                "quality_suggestion": rev.quality_suggestion,
                "plan_status": rev.plan_status,
            }
        items.append(item)
    return {"code": 0, "message": "success", "data": items}


@router.get("/requirements/{demand_id}")
def get_requirement(demand_id: str, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="需求不存在")
    rev = db.query(RequirementReview).filter(
        RequirementReview.requirement_id == demand_id
    ).first()
    logs = db.query(StatusLog).filter(
        StatusLog.requirement_id == demand_id
    ).order_by(StatusLog.operated_at.desc()).all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "demand_id": r.demand_id,
            "demand_name": r.demand_name,
            "demand_status": r.demand_status,
            "stage": r.stage,
            "project": r.project,
            "department": r.department,
            "demand_desc": r.demand_desc,
            "businessobjective": r.businessobjective,
            "businessdesc": r.businessdesc,
            "business_id": r.business_id,
            "business_name": r.business_name,
            "business_status": r.business_status,
            "business_review_status": r.business_review_status,
            "proj_approval_id": r.proj_approval_id,
            "approval_status": r.approval_status,
            "approval_name": r.approval_name,
            "business_pm_name": r.business_pm_name,
            "responsible_dept_name": r.responsible_dept_name,
            "deadline": r.deadline,
            "business_created_date": r.business_created_date,
            "last_modified": r.last_modified,
            "importance": r.importance,
            "reason_type": r.reason_type,
            "creator": r.creator,
            "source_dept": r.source_dept,
            "business_capability": r.business_capability,
            "review": {
                "priority": rev.priority if rev else None,
                "review_date": rev.review_date if rev else None,
                "review_notes": rev.review_notes if rev else None,
                "rejection_type": rev.rejection_type if rev else None,
                "rejection_reason": rev.rejection_reason if rev else None,
                "reviewer": rev.reviewer if rev else None,
                "reviewed_at": rev.reviewed_at if rev else None,
                "is_updated": rev.is_updated if rev else None,
                "is_reviewed": rev.is_reviewed if rev else None,
                "quality_score": rev.quality_score if rev else None,
                "quality_suggestion": rev.quality_suggestion if rev else None,
                "plan_status": rev.plan_status if rev else None,
            } if rev else None,
            "status_logs": [
                {
                    "from_status": log.from_status,
                    "to_status": log.to_status,
                    "operator": log.operator,
                    "operated_at": log.operated_at,
                    "remark": log.remark,
                } for log in logs
            ]
        }
    }


@router.post("/requirements")
def create_requirement(data: dict, db: Session = Depends(get_db)):
    demand_id = data.get("demand_id")
    if not demand_id:
        raise HTTPException(status_code=400, detail="demand_id 必填")

    existing = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="需求已存在")

    req = Requirement(**data)
    db.add(req)
    db.commit()
    return {"code": 0, "message": "success", "data": {"demand_id": demand_id}}


@router.put("/requirements/{demand_id}")
def update_requirement(demand_id: str, data: dict, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")

    for key, value in data.items():
        if hasattr(req, key):
            setattr(req, key, value)

    req.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    return {"code": 0, "message": "success"}


@router.delete("/requirements/{demand_id}")
def delete_requirement(demand_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    db.delete(req)
    db.commit()
    return {"code": 0, "message": "success"}


@router.put("/requirements/{demand_id}/stage")
def update_stage(demand_id: str, data: dict, db: Session = Depends(get_db)):
    """标记需求进入指定阶段（立项）"""
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")

    stage = data.get("stage", "已立项")
    project = data.get("project")
    plan_launch = data.get("plan_launch_date")

    old_stage = req.stage
    req.stage = stage
    if project:
        req.project = project
    if plan_launch:
        req.end_time = plan_launch
    req.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = StatusLog(
        requirement_id=demand_id,
        from_status=f"stage:{old_stage}" if old_stage else "stage:待评审",
        to_status=f"stage:{stage}",
        operator=data.get("operator", "system"),
        operated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        remark=data.get("remark", ""),
    )
    db.add(log)
    db.commit()
    return {"code": 0, "message": "success"}


@router.put("/requirements/{demand_id}/online")
def mark_online(demand_id: str, data: dict, db: Session = Depends(get_db)):
    """标记需求已上线"""
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")

    actual_launch = data.get("actual_launch_date")
    if not actual_launch:
        raise HTTPException(status_code=400, detail="实际上线日期不能为空")

    old_stage = req.stage
    req.stage = "已上线"
    req.end_time = actual_launch
    req.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = StatusLog(
        requirement_id=demand_id,
        from_status=f"stage:{old_stage}",
        to_status="stage:已上线",
        operator=data.get("operator", "system"),
        operated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        remark=f"实际上线：{actual_launch}",
    )
    db.add(log)
    db.commit()
    return {"code": 0, "message": "success"}


@router.put("/requirements/{demand_id}/close")
def close_requirement_put(demand_id: str, data: dict, db: Session = Depends(get_db)):
    """标记需求关闭（PLAN.md 规格：PUT /requirements/{id}/close）"""
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")

    close_date = data.get("close_date")
    close_reason = data.get("close_reason", "")
    if not close_date:
        raise HTTPException(status_code=400, detail="关闭日期不能为空")

    old_status = req.demand_status
    req.demand_status = "closed"
    req.stage = "已关闭"
    req.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = StatusLog(
        requirement_id=demand_id,
        from_status=old_status or "active",
        to_status="closed",
        operator=data.get("operator", "system"),
        operated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        remark=f"关闭日期：{close_date}；原因：{close_reason}",
    )
    db.add(log)
    db.commit()
    return {"message": "ok"}


@router.get("/status-logs/{demand_id}")
def get_status_logs(demand_id: str, db: Session = Depends(get_db)):
    logs = db.query(StatusLog).filter(
        StatusLog.requirement_id == demand_id
    ).order_by(StatusLog.operated_at.desc()).all()
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": log.id,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "operator": log.operator,
                "operated_at": log.operated_at,
                "remark": log.remark,
            } for log in logs
        ]
    }

