from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, StatusLog
from app.schemas import RequirementCreate, RequirementUpdate, CloseRequest

router = APIRouter()


def _to_dict(req: Requirement) -> dict:
    d = {c.name: getattr(req, c.name) for c in req.__table__.columns}
    d["is_closed"] = 1 if req.demand_status == "closed" else 0
    return d


@router.get("/requirements")
def list_requirements(
    demand_status: Optional[str] = None,
    department: Optional[str] = None,
    creator: Optional[str] = None,
    is_closed: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(Requirement)
    if demand_status:
        q = q.filter(Requirement.demand_status == demand_status)
    if department:
        q = q.filter(Requirement.department == department)
    if creator:
        q = q.filter(Requirement.creator == creator)
    if is_closed is not None:
        if is_closed == 1:
            q = q.filter(Requirement.demand_status == "closed")
        else:
            q = q.filter(Requirement.demand_status != "closed")
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    return {
        "code": 0,
        "message": "success",
        "data": {"total": total, "items": [_to_dict(r) for r in items]},
    }


@router.get("/requirements/{demand_id}")
def get_requirement(demand_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"code": 0, "message": "success", "data": _to_dict(req)}


@router.post("/requirements")
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db)):
    if db.query(Requirement).filter(Requirement.demand_id == payload.demand_id).first():
        raise HTTPException(status_code=409, detail="demand_id already exists")
    req = Requirement(**payload.model_dump())
    if not req.last_modified:
        req.last_modified = datetime.now().isoformat()
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"code": 0, "message": "success", "data": _to_dict(req)}


@router.put("/requirements/{demand_id}")
def update_requirement(demand_id: str, payload: RequirementUpdate, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(req, k, v)
    req.last_modified = datetime.now().isoformat()
    db.commit()
    db.refresh(req)
    return {"code": 0, "message": "success", "data": _to_dict(req)}


@router.delete("/requirements/{demand_id}")
def delete_requirement(demand_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(req)
    db.commit()
    return {"code": 0, "message": "success", "data": {"demand_id": demand_id}}


@router.post("/requirements/{demand_id}/close")
def close_requirement(demand_id: str, payload: CloseRequest, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if not payload.remark or not payload.remark.strip():
        raise HTTPException(status_code=422, detail="remark required")
    from_status = req.demand_status
    req.demand_status = "closed"
    req.last_modified = datetime.now().isoformat()
    log = StatusLog(
        requirement_id=demand_id,
        from_status=from_status,
        to_status="closed",
        operator=payload.operator,
        operated_at=datetime.now().isoformat(),
        remark=payload.remark,
    )
    db.add(log)
    db.commit()
    return {"code": 0, "message": "success", "data": _to_dict(req)}


@router.get("/status-logs/{demand_id}")
def list_status_logs(demand_id: str, db: Session = Depends(get_db)):
    logs = db.query(StatusLog).filter(StatusLog.requirement_id == demand_id).order_by(StatusLog.id.desc()).all()
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "id": l.id,
                "requirement_id": l.requirement_id,
                "from_status": l.from_status,
                "to_status": l.to_status,
                "operator": l.operator,
                "operated_at": l.operated_at,
                "remark": l.remark,
            }
            for l in logs
        ],
    }
