from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.constants import REJECTION_TYPES, REJECTION_CODES
from app.database import get_db
from app.models import Requirement, RequirementReview

router = APIRouter()


class ReviewSubmit(BaseModel):
    decision: Literal["pass", "reject", "future"]
    priority: Optional[str] = None  # 高/中/低
    review_date: Optional[str] = None  # YYYY-MM-DD
    review_notes: Optional[str] = None
    rejection_type: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewer: str


def _ensure_review(db: Session, demand_id: str) -> RequirementReview:
    review = (
        db.query(RequirementReview)
        .filter(RequirementReview.requirement_id == demand_id)
        .first()
    )
    if review is None:
        review = RequirementReview(requirement_id=demand_id, is_reviewed=0, is_updated=0)
        db.add(review)
        db.flush()
    return review


@router.get("/reviews/rejection-types")
def get_rejection_types():
    return {"code": 0, "message": "success", "data": REJECTION_TYPES}


@router.post("/reviews/{demand_id}")
def submit_review(demand_id: str, payload: ReviewSubmit, db: Session = Depends(get_db)):
    if not db.query(Requirement).filter(Requirement.demand_id == demand_id).first():
        raise HTTPException(status_code=404, detail="Requirement not found")

    if payload.decision == "reject":
        if not payload.rejection_type or payload.rejection_type not in REJECTION_CODES:
            raise HTTPException(status_code=422, detail="rejection_type required and must be valid code")
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(status_code=422, detail="rejection_reason required")

    review = _ensure_review(db, demand_id)
    review.priority = payload.priority
    review.review_date = payload.review_date
    review.review_notes = payload.review_notes
    review.reviewer = payload.reviewer
    review.reviewed_at = datetime.now().isoformat()
    review.is_reviewed = 1
    review.is_updated = 0

    if payload.decision == "reject":
        review.rejection_type = payload.rejection_type
        review.rejection_reason = payload.rejection_reason
        review.plan_status = None
    elif payload.decision == "future":
        review.rejection_type = None
        review.rejection_reason = None
        review.plan_status = "未来规划"
    else:  # pass
        review.rejection_type = None
        review.rejection_reason = None
        review.plan_status = "正常"

    db.commit()
    db.refresh(review)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "requirement_id": review.requirement_id,
            "decision": payload.decision,
            "priority": review.priority,
            "review_date": review.review_date,
            "review_notes": review.review_notes,
            "rejection_type": review.rejection_type,
            "rejection_reason": review.rejection_reason,
            "plan_status": review.plan_status,
            "reviewer": review.reviewer,
            "reviewed_at": review.reviewed_at,
            "is_reviewed": review.is_reviewed,
        },
    }


@router.get("/reviews")
def list_reviews(
    is_reviewed: Optional[int] = None,
    plan_status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(RequirementReview)
    if is_reviewed is not None:
        q = q.filter(RequirementReview.is_reviewed == is_reviewed)
    if plan_status:
        q = q.filter(RequirementReview.plan_status == plan_status)
    items = q.all()
    return {
        "code": 0,
        "message": "success",
        "data": [
            {
                "requirement_id": r.requirement_id,
                "priority": r.priority,
                "review_date": r.review_date,
                "review_notes": r.review_notes,
                "rejection_type": r.rejection_type,
                "rejection_reason": r.rejection_reason,
                "plan_status": r.plan_status,
                "reviewer": r.reviewer,
                "reviewed_at": r.reviewed_at,
                "is_updated": r.is_updated,
                "is_reviewed": r.is_reviewed,
            }
            for r in items
        ],
    }
