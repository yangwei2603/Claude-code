"""统计看板 API"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Requirement, RequirementReview, StatusLog

router = APIRouter()


@router.get("/requirements/stats")
def get_stats(db: Session = Depends(get_db)):
    """首页 KPI + 分布图"""
    total = db.query(Requirement).count()
    active = db.query(Requirement).filter(Requirement.demand_status == "active").count()
    closed = db.query(Requirement).filter(Requirement.demand_status == "closed").count()
    reviewed = db.query(RequirementReview).filter(RequirementReview.is_reviewed == 1).count()

    # 优先级分布
    priority_dist = {}
    reviews = db.query(RequirementReview).filter(RequirementReview.priority != None).all()
    for r in reviews:
        p = r.priority or "未标注"
        priority_dist[p] = priority_dist.get(p, 0) + 1

    # 当月新增
    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"
    month_new = db.query(Requirement).filter(
        Requirement.business_created_date >= month_start
    ).count()

    # 过期紧急（最后修改时间 5 天前 + 高优先级）
    urgent_reqs = []
    five_days_ago = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    urgent_rows = db.query(Requirement).filter(
        Requirement.demand_status == "active",
        Requirement.last_modified < five_days_ago
    ).all()
    for req in urgent_rows:
        rev = db.query(RequirementReview).filter(
            RequirementReview.requirement_id == req.demand_id
        ).first()
        if rev and rev.priority == "高":
            urgent_reqs.append({"demand_id": req.demand_id, "demand_name": req.demand_name})

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "active": active,
            "closed": closed,
            "reviewed": reviewed,
            "unreviewed": total - reviewed,
            "month_new": month_new,
            "priority_distribution": priority_dist,
            "urgent_list": urgent_reqs,
        }
    }


@router.get("/requirements/quality-dist")
def get_quality_dist(db: Session = Depends(get_db)):
    """描述质量分布"""
    all_reqs = db.query(Requirement).filter(
        Requirement.demand_desc != None,
        Requirement.demand_desc != ""
    ).all()

    short = 0    # < 50 字
    medium = 0   # 50-200 字
    good = 0     # > 200 字

    for req in all_reqs:
        desc_len = len(req.demand_desc or "")
        if desc_len < 50:
            short += 1
        elif desc_len <= 200:
            medium += 1
        else:
            good += 1

    total = short + medium + good
    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "short": short,
            "medium": medium,
            "good": good,
            "short_pct": round(short / total * 100, 1) if total else 0,
            "medium_pct": round(medium / total * 100, 1) if total else 0,
            "good_pct": round(good / total * 100, 1) if total else 0,
        }
    }


@router.get("/requirements/distribution")
def get_distribution(
    group_by: str = "department",  # department / importance / stage / creator
    db: Session = Depends(get_db)
):
    """多维分布统计"""
    if group_by == "department":
        field = Requirement.department
    elif group_by == "importance":
        field = Requirement.importance
    elif group_by == "stage":
        field = Requirement.stage
    elif group_by == "creator":
        field = Requirement.creator
    else:
        field = Requirement.department

    rows = db.query(field, func.count(Requirement.demand_id)).group_by(field).all()
    return {
        "code": 0,
        "message": "success",
        "data": {
            "group_by": group_by,
            "distribution": [{"name": r[0] or "未知", "count": r[1]} for r in rows]
        }
    }


@router.get("/requirements/deadline-warning")
def get_deadline_warning(
    days: int = 20,
    db: Session = Depends(get_db)
):
    """项目计划上线时间到期前 N 天提醒（基于 end_time，非 deadline）"""
    now = datetime.now()
    warning_date = (now + timedelta(days=days)).strftime("%Y-%m-%d")

    rows = db.query(Requirement).filter(
        Requirement.demand_status == "active",
        Requirement.end_time != None,
        Requirement.end_time != "",
        Requirement.end_time <= warning_date,
    ).all()

    items = []
    for req in rows:
        end_str = req.end_time[:10]
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
            remaining = (end_date - now).days
        except:
            remaining = -1

        rev = db.query(RequirementReview).filter(
            RequirementReview.requirement_id == req.demand_id
        ).first()

        items.append({
            "demand_id": req.demand_id,
            "demand_name": req.demand_name,
            "project": req.project,
            "business_name": req.business_name,
            "end_time": req.end_time,
            "remaining_days": remaining,
            "priority": rev.priority if rev else None,
            "plan_status": rev.plan_status if rev else None,
            "department": req.department,
        })

    items.sort(key=lambda x: x["remaining_days"])
    return {"code": 0, "message": "success", "data": items}


@router.get("/requirements/by-business")
def get_requirements_by_business(
    business_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """按业务需求（business_id）查看关联的所有需求 + 项目信息"""
    q = db.query(Requirement).filter(
        Requirement.business_id != None,
        Requirement.business_id != "",
    )
    if business_id:
        q = q.filter(Requirement.business_id == business_id)

    rows = q.all()

    # 按 business_id 分组
    by_business = {}
    for req in rows:
        bid = req.business_id
        if bid not in by_business:
            by_business[bid] = {
                "business_id": bid,
                "business_name": req.business_name,
                "project_number": req.project,
                "requirements": []
            }
        rev = db.query(RequirementReview).filter(
            RequirementReview.requirement_id == req.demand_id
        ).first()
        by_business[bid]["requirements"].append({
            "demand_id": req.demand_id,
            "demand_name": req.demand_name,
            "demand_status": req.demand_status,
            "stage": req.stage,
            "end_time": req.end_time,
            "deadline": req.deadline,
            "priority": rev.priority if rev else None,
            "plan_status": rev.plan_status if rev else None,
            "is_reviewed": rev.is_reviewed if rev else 0,
        })

    result = list(by_business.values())
    return {"code": 0, "message": "success", "data": result}


@router.get("/requirements/backlog")
def get_backlog(db: Session = Depends(get_db)):
    """积压超时需求：未关联业务ID + 20个工作日未处理（排除周六日）"""
    now = datetime.now()

    def working_days_ago(n: int) -> str:
        """计算 N 个工作日前的日期（排除周六日）"""
        days = 0
        d = now
        while days < n:
            d -= timedelta(days=1)
            if d.weekday() < 5:  # Mon-Fri
                days += 1
        return d.strftime("%Y-%m-%d")

    cutoff = working_days_ago(20)
    rows = db.query(Requirement).filter(
        or_(Requirement.business_id == None, Requirement.business_id == ""),
        Requirement.demand_status == "active",
        Requirement.last_modified < cutoff,
    ).all()

    items = []
    for req in rows:
        # 计算工作日天数
        workdays = 0
        d = now
        while d.strftime("%Y-%m-%d") > req.last_modified:
            d -= timedelta(days=1)
            if d.weekday() < 5:
                workdays += 1
        items.append({
            "demand_id": req.demand_id,
            "demand_name": req.demand_name or "",
            "working_days": workdays,
            "last_modified": req.last_modified,
        })

    return {"code": 0, "message": "success", "data": items}


@router.get("/business/summary")
def get_business_summary(db: Session = Depends(get_db)):
    """业务需求汇总：每个 business_id 下有多少需求，已评审/未评审，各项目状态"""
    reqs = db.query(Requirement).filter(
        Requirement.business_id != None,
        Requirement.business_id != "",
    ).all()

    by_biz = {}
    for req in reqs:
        bid = req.business_id
        if bid not in by_biz:
            by_biz[bid] = {
                "business_id": bid,
                "business_name": req.business_name,
                "project_number": req.project,
                "total": 0,
                "reviewed": 0,
                "pass": 0,
                "reject": 0,
                "pending": 0,
            }
        by_biz[bid]["total"] += 1

        rev = db.query(RequirementReview).filter(
            RequirementReview.requirement_id == req.demand_id
        ).first()
        if rev and rev.is_reviewed:
            by_biz[bid]["reviewed"] += 1
            if rev.plan_status == "正常":
                by_biz[bid]["pass"] += 1
            elif rev.rejection_type:
                by_biz[bid]["reject"] += 1
            else:
                by_biz[bid]["pending"] += 1
        else:
            by_biz[bid]["pending"] += 1

    return {
        "code": 0,
        "message": "success",
        "data": list(by_biz.values())
    }