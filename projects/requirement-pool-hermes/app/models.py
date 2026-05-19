from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Requirement(Base):
    __tablename__ = "requirement"

    demand_id = Column(String(64), primary_key=True)
    demand_name = Column(String(256), nullable=False)
    demand_status = Column(String(32), default="active")
    stage = Column(String(64), nullable=True)
    project = Column(String(128), nullable=True)
    department = Column(String(128), nullable=True)
    demand_desc = Column(Text, nullable=True)
    businessobjective = Column(Text, nullable=True)
    businessdesc = Column(Text, nullable=True)
    business_id = Column(String(64), nullable=True)
    business_name = Column(String(256), nullable=True)
    business_status = Column(String(64), nullable=True)
    business_review_status = Column(String(32), nullable=True)
    proj_approval_id = Column(String(64), nullable=True)
    approval_status = Column(String(64), nullable=True)
    approval_name = Column(String(256), nullable=True)
    business_pm_name = Column(String(128), nullable=True)
    responsible_dept_name = Column(String(128), nullable=True)
    deadline = Column(String(32), nullable=True)      # 需求期望上线时间
    end_time = Column(String(32), nullable=True)     # 项目计划上线时间（关联后从business表同步）
    business_created_date = Column(String(32), nullable=True)
    last_modified = Column(String(32), nullable=True)
    importance = Column(String(32), nullable=True)
    reason_type = Column(String(64), nullable=True)
    creator = Column(String(128), nullable=True)
    source_dept = Column(String(128), nullable=True)
    business_capability = Column(String(128), nullable=True)

    reviews = relationship("RequirementReview", back_populates="requirement", cascade="all, delete-orphan")
    status_logs = relationship("StatusLog", back_populates="requirement", cascade="all, delete-orphan")


class RequirementReview(Base):
    __tablename__ = "requirement_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(String(64), ForeignKey("requirement.demand_id"), nullable=False)
    priority = Column(String(16), nullable=True)
    review_date = Column(String(32), nullable=True)
    review_notes = Column(Text, nullable=True)
    rejection_type = Column(String(16), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    reviewer = Column(String(128), nullable=False)
    reviewed_at = Column(String(32), nullable=False)
    version_hash = Column(String(64), nullable=True)
    is_updated = Column(Integer, default=0)
    is_reviewed = Column(Integer, default=0)
    quality_score = Column(Integer, nullable=True)
    quality_suggestion = Column(Text, nullable=True)
    plan_status = Column(String(32), nullable=True)

    requirement = relationship("Requirement", back_populates="reviews")
    __table_args__ = (UniqueConstraint("requirement_id", name="uq_requirement_review"),)


class StatusLog(Base):
    __tablename__ = "status_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(String(64), ForeignKey("requirement.demand_id"), nullable=False)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    operator = Column(String(128), nullable=False)
    operated_at = Column(String(32), nullable=False)
    remark = Column(Text, nullable=True)

    requirement = relationship("Requirement", back_populates="status_logs")


class ReviewSession(Base):
    __tablename__ = "review_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_date = Column(String(32), nullable=False)
    total_count = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(String(32), nullable=False)


REJECTION_TYPES = [
    ("P001", "优先级过高", "需求紧急程度与业务价值不匹配，建议降低优先级排队"),
    ("P002", "重复需求", "与已有需求重复，功能重叠，建议合并或引用已有需求"),
    ("P003", "范围不清", "需求描述模糊，无法准确评估范围和工作量，需补充说明"),
    ("P004", "依赖缺失", "存在未识别的上游依赖或关联系统，需先解决依赖问题"),
    ("P005", "资源不足", "当前无足够人力或技术资源承接，建议调整时间或拆解"),
    ("P006", "业务调整", "业务方向调整或战略变更，暂不纳入本期范围"),
    ("P007", "条件不成熟", "前提条件不满足（如需先完成XX系统改造），建议暂缓"),
    ("P999", "其他", "其他原因，需在备注中说明"),
]