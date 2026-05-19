"""CSV 导入 API"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import csv
import hashlib
import io

from app.database import get_db
from app.models import Requirement, RequirementReview

router = APIRouter()


def compute_hash(demand_name, demand_desc, businessobjective, department, importance):
    s = f"{demand_name or ''}|{demand_desc or ''}|{businessobjective or ''}|{department or ''}|{importance or ''}"
    return hashlib.md5(s.encode()).hexdigest()


@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件")

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except:
        decoded = content.decode("gbk")

    reader = csv.DictReader(io.StringIO(decoded))
    fieldnames = reader.fieldnames or []

    def get_field(row, *keys):
        for k in keys:
            for fn in fieldnames:
                if fn.strip().lower().replace("_", "").replace(" ", "") == k.lower().replace("_", "").replace(" ", ""):
                    return row.get(fn, "").strip()
        return ""

    total = 0
    new_count = 0
    updated_count = 0
    updated_list = []
    unchanged = 0
    seen_ids = set()

    for row in reader:
        total += 1
        demand_id = get_field(row, "demand_id", "id")
        demand_name = get_field(row, "demand_name", "name")
        demand_status = get_field(row, "demand_status", "status") or "active"
        demand_desc = get_field(row, "demand_desc", "description")
        businessobjective = get_field(row, "businessobjective")
        businessdesc = get_field(row, "businessdesc")
        business_id = get_field(row, "business_id", "businessid")
        business_name = get_field(row, "business_name")
        business_status = get_field(row, "business_status")
        business_review_status = get_field(row, "business_review_status")
        proj_approval_id = get_field(row, "proj_approval_id")
        approval_status = get_field(row, "approval_status")
        approval_name = get_field(row, "approval_name")
        business_pm_name = get_field(row, "business_pm_name")
        responsible_dept_name = get_field(row, "responsible_dept_name")
        deadline = get_field(row, "deadline")
        business_created_date = get_field(row, "business_created_date", "created_date")
        last_modified = get_field(row, "last_modified")
        importance = get_field(row, "importance")
        reason_type = get_field(row, "reason_type")
        creator = get_field(row, "creator")
        source_dept = get_field(row, "source_dept")
        business_capability = get_field(row, "business_capability")
        department = get_field(row, "department")
        stage = get_field(row, "stage")
        project = get_field(row, "project")

        if not demand_id or demand_id in seen_ids:
            continue
        seen_ids.add(demand_id)

        version_hash = compute_hash(demand_name, demand_desc, businessobjective, department, importance)
        existing = db.query(Requirement).filter(Requirement.demand_id == demand_id).first()

        if existing:
            existing_hash = compute_hash(
                existing.demand_name, existing.demand_desc,
                existing.businessobjective, existing.department, existing.importance
            )
            if existing_hash != version_hash:
                existing.demand_name = demand_name
                existing.demand_status = demand_status
                existing.demand_desc = demand_desc
                existing.businessobjective = businessobjective
                existing.businessdesc = businessdesc
                existing.business_id = business_id
                existing.business_name = business_name
                existing.business_status = business_status
                existing.business_review_status = business_review_status
                existing.proj_approval_id = proj_approval_id
                existing.approval_status = approval_status
                existing.approval_name = approval_name
                existing.business_pm_name = business_pm_name
                existing.responsible_dept_name = responsible_dept_name
                existing.deadline = deadline
                existing.business_created_date = business_created_date
                existing.last_modified = last_modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                existing.importance = importance
                existing.reason_type = reason_type
                existing.creator = creator
                existing.source_dept = source_dept
                existing.business_capability = business_capability
                existing.department = department
                existing.stage = stage
                existing.project = project

                rev = db.query(RequirementReview).filter(
                    RequirementReview.requirement_id == demand_id
                ).first()
                if rev and rev.is_reviewed:
                    rev.is_updated = 1
                    updated_list.append(demand_id)

                updated_count += 1
            else:
                unchanged += 1
        else:
            req = Requirement(
                demand_id=demand_id,
                demand_name=demand_name,
                demand_status=demand_status,
                demand_desc=demand_desc,
                businessobjective=businessobjective,
                businessdesc=businessdesc,
                business_id=business_id,
                business_name=business_name,
                business_status=business_status,
                business_review_status=business_review_status,
                proj_approval_id=proj_approval_id,
                approval_status=approval_status,
                approval_name=approval_name,
                business_pm_name=business_pm_name,
                responsible_dept_name=responsible_dept_name,
                deadline=deadline,
                business_created_date=business_created_date,
                last_modified=last_modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                importance=importance,
                reason_type=reason_type,
                creator=creator,
                source_dept=source_dept,
                business_capability=business_capability,
                department=department,
                stage=stage,
                project=project,
            )
            db.add(req)
            new_count += 1

    unreviewed = db.query(Requirement).outerjoin(
        RequirementReview,
        Requirement.demand_id == RequirementReview.requirement_id
    ).filter(
        or_(RequirementReview.requirement_id == None, RequirementReview.is_reviewed == 0)
    ).count()

    db.commit()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "total": total,
            "new": new_count,
            "updated": updated_count,
            "unchanged": unchanged,
            "updated_list": updated_list,
            "unreviewed_count": unreviewed,
        }
    }