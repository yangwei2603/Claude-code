"""智能问答 API — 基于本地数据生成回答"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Requirement, RequirementReview

router = APIRouter()


def answer_stats(db: Session) -> str:
    total = db.query(Requirement).count()
    active = db.query(Requirement).filter(Requirement.demand_status == "active").count()
    closed = db.query(Requirement).filter(Requirement.demand_status == "closed").count()
    reviewed = db.query(RequirementReview).filter(RequirementReview.is_reviewed == 1).count()
    unreviewed = total - reviewed
    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"
    month_new = db.query(Requirement).filter(
        Requirement.business_created_date >= month_start
    ).count()
    return (f"当前需求池共有 {total} 条需求，"
            f"进行中 {active} 条，已关闭 {closed} 条，"
            f"已评审 {reviewed} 条，待评审 {unreviewed} 条，"
            f"本月新增 {month_new} 条。")


def answer_by_department(db: Session) -> str:
    rows = db.query(Requirement.department, func.count(Requirement.demand_id)).group_by(Requirement.department).all()
    if not rows:
        return "暂无部门分布数据"
    lines = [f"{r[0] or '未知'}: {r[1]} 条" for r in rows]
    return "需求按部门分布：\n" + "\n".join(lines)


def answer_by_importance(db: Session) -> str:
    rows = db.query(Requirement.importance, func.count(Requirement.demand_id)).group_by(Requirement.importance).all()
    if not rows:
        return "暂无重要性分布数据"
    lines = [f"{r[0] or '未知'}: {r[1]} 条" for r in rows]
    return "需求按重要性分布：\n" + "\n".join(lines)


def answer_overdue(db: Session) -> str:
    five_days_ago = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    rows = db.query(Requirement).filter(
        Requirement.demand_status == "active",
        Requirement.last_modified < five_days_ago
    ).all()
    urgent = []
    for req in rows:
        rev = db.query(RequirementReview).filter(
            RequirementReview.requirement_id == req.demand_id
        ).first()
        if rev and rev.priority == "高":
            urgent.append(f"{req.demand_id}（{req.demand_name}）")
    if urgent:
        return f"发现 {len(urgent)} 条紧急需求（5天以上未处理+高优先级）：\n" + "\n".join(urgent[:10])
    return "目前没有发现紧急超期需求"


def answer_rejected(db: Session) -> str:
    rows = db.query(RequirementReview).filter(
        RequirementReview.rejection_type != None
    ).all()
    if not rows:
        return "暂无驳回记录"
    dist = {}
    for r in rows:
        t = r.rejection_type
        dist[t] = dist.get(t, 0) + 1
    lines = [f"{k}: {v} 条" for k, v in dist.items()]
    return f"共有 {len(rows)} 条驳回记录，驳回类型分布：\n" + "\n".join(lines)


def answer_future(db: Session) -> str:
    rows = db.query(RequirementReview).filter(
        RequirementReview.plan_status == "未来规划"
    ).all()
    if not rows:
        return "暂无标记为未来规划的需求"
    names = []
    for rev in rows:
        req = db.query(Requirement).filter(Requirement.demand_id == rev.requirement_id).first()
        names.append(f"{rev.requirement_id}（{req.demand_name if req else ''}）")
    return f"共有 {len(rows)} 条标记为未来规划的需求：\n" + "\n".join(names[:10])


def answer_recent_added(db: Session, days: int = 7) -> str:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = db.query(Requirement).filter(
        Requirement.business_created_date >= since
    ).all()
    if not rows:
        return f"最近 {days} 天没有新增需求"
    lines = [f"{r.demand_id}: {r.demand_name}" for r in rows]
    return f"最近 {days} 天新增 {len(rows)} 条需求：\n" + "\n".join(lines)


def answer_quality(db: Session) -> str:
    all_reqs = db.query(Requirement).filter(
        Requirement.demand_desc != None, Requirement.demand_desc != ""
    ).all()
    short = sum(1 for r in all_reqs if len(r.demand_desc or "") < 50)
    medium = sum(1 for r in all_reqs if 50 <= len(r.demand_desc or "") <= 200)
    good = sum(1 for r in all_reqs if len(r.demand_desc or "") > 200)
    total = short + medium + good
    if total == 0:
        return "暂无需求描述数据"
    return (f"共 {total} 条需求有描述，"
            f"质量差（<50字）{short} 条({short*100//total if total else 0}%)，"
            f"质量中（50-200字）{medium} 条({medium*100//total if total else 0}%)，"
            f"质量好（>200字）{good} 条({good*100//total if total else 0}%)")


@router.post("/qa/ask")
def ask_question(data: dict, db: Session = Depends(get_db)):
    question = data.get("question", "").lower()
    history = data.get("history", [])

    # 路由到对应回答函数
    if any(k in question for k in ["统计", "多少", "总数", "共", "数量"]):
        if "部门" in question:
            return {"code": 0, "message": "success", "data": {"answer": answer_by_department(db)}}
        if "重要性" in question or "重要" in question:
            return {"code": 0, "message": "success", "data": {"answer": answer_by_importance(db)}}
        if "质量" in question or "描述" in question:
            return {"code": 0, "message": "success", "data": {"answer": answer_quality(db)}}
        if "新增" in question or "本月" in question or "最近" in question:
            days = 7
            for d in ["30", "三十", "15", "十五", "7", "七"]:
                if d in question:
                    days = int(d) if d.isdigit() else (30 if "三十" in question or "30" in question else 15 if "十五" in question or "15" in question else 7)
            return {"code": 0, "message": "success", "data": {"answer": answer_recent_added(db, days)}}
        return {"code": 0, "message": "success", "data": {"answer": answer_stats(db)}}

    if any(k in question for k in ["过期", "紧急", "超期", "积压"]):
        return {"code": 0, "message": "success", "data": {"answer": answer_overdue(db)}}

    if "驳回" in question:
        return {"code": 0, "message": "success", "data": {"answer": answer_rejected(db)}}

    if "未来" in question:
        return {"code": 0, "message": "success", "data": {"answer": answer_future(db)}}

    if "通过" in question and "评审" in question:
        passed = db.query(RequirementReview).filter(
            RequirementReview.plan_status == "正常"
        ).count()
        return {"code": 0, "message": "success", "data": {"answer": f"已评审通过的需求共 {passed} 条"}}

    if "待评审" in question or "未评审" in question:
        unreviewed = db.query(Requirement).outerjoin(
            RequirementReview,
            Requirement.demand_id == RequirementReview.requirement_id
        ).filter(
            or_(RequirementReview.requirement_id == None, RequirementReview.is_reviewed == 0)
        ).count()
        return {"code": 0, "message": "success", "data": {"answer": f"待评审需求共 {unreviewed} 条"}}

    # 默认：返回统计摘要
    return {"code": 0, "message": "success", "data": {"answer": answer_stats(db)}}