from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database import Base


class Requirement(Base):
    __tablename__ = "requirement"

    # 基础识别字段
    demand_id = Column(String, primary_key=True)
    demand_name = Column(String, nullable=False)

    # 状态字段
    demand_status = Column(String, nullable=False)  # active / closed
    stage = Column(String)
    project = Column(String)
    department = Column(String)
    importance = Column(String)
    pri = Column(String)

    # 需求描述字段
    demand_desc = Column(Text)
    businessobjective = Column(Text)
    businessdesc = Column(Text)
    deadline = Column(String)
    end_time = Column(String)
    begin_time = Column(String)

    # 业务需求信息（来自 zt_demand_pool.business_*）
    business_id = Column(String)
    business_name = Column(String)
    business_status = Column(String)
    business_review_status = Column(String)
    business_review_result = Column(String)
    business_approval = Column(String)
    business_created_date = Column(String)
    business_edited_by = Column(String)
    business_edited_date = Column(String)
    business_pm = Column(String)
    business_pm_name = Column(String)
    business_capability = Column(String)
    reason_type = Column(String)
    busi_desc = Column(Text)
    business_desc = Column(Text)
    business_objective = Column(Text)
    business_acl = Column(String)
    business_architecture = Column(String)
    busi_process = Column(String)
    application_architecture = Column(String)

    # 项目审批信息（来自 zt_demand_pool.approval_* + proj_*）
    proj_approval_id = Column(String)
    approval_status = Column(String)
    approval_name = Column(String)
    approval_created_by = Column(String)
    approval_created_date = Column(String)
    approval_edited_by = Column(String)
    approval_edited_date = Column(String)
    approval_desc = Column(Text)
    approval_review_result = Column(String)
    approval_review_status = Column(String)
    approval_approval = Column(String)
    approval_acl = Column(String)
    mailto = Column(String)
    program = Column(String)
    product_plan = Column(String)

    # 项目立项信息
    model = Column(String)
    type = Column(String)
    class_ = Column("class", String)
    business_line = Column(String)
    auth = Column(String)
    days = Column(String)

    # 成本与资源
    development_budget = Column(String)
    outsourcing_budget = Column(String)
    total_cost = Column(String)
    cost_budget = Column(String)
    brd_remain_budget = Column(String)

    # 需求池基础信息
    demandpool_id = Column(String)
    dept = Column(String)
    name = Column(String)
    demandpool_desc = Column(Text)
    demandpool_acl = Column(String)
    is_cancel = Column(String)
    is_it_confirm = Column(String)
    responsible_dept = Column(String)
    responsible_dept_name = Column(String)
    recorder = Column(String)

    # 评审与变更记录
    project_review_date = Column(String)
    project_number = Column(String)
    review_date = Column(String)
    review_location = Column(String)
    participant = Column(Text)
    remark = Column(Text)
    evaluation_feedback_by = Column(String)
    evaluation_feedback_date = Column(String)
    change_application_date = Column(String)
    change_content = Column(Text)
    change_reason = Column(Text)
    project_approval_date = Column(String)
    termination_date = Column(String)
    target = Column(Text)

    # ITPM 字段
    itpm_account = Column(String)
    itpm_realname = Column(String)
    itpm_shorcq = Column(String)
    itpm_dept_name = Column(String)

    # 其他字段
    old_status = Column(String)
    net_info_safe = Column(String)
    meeting = Column(String)
    integrate = Column(String)
    risk = Column(String)

    # 系统字段
    creator = Column(String)
    source_dept = Column(String)
    last_modified = Column(String)


class RequirementReview(Base):
    __tablename__ = "requirement_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(String, ForeignKey("requirement.demand_id"), nullable=False, unique=True)
    priority = Column(String)  # 高/中/低
    review_date = Column(String)  # YYYY-MM-DD
    review_notes = Column(Text)
    rejection_type = Column(String)  # P001~P999
    rejection_reason = Column(Text)
    reviewer = Column(String)
    reviewed_at = Column(String)
    version_hash = Column(String)
    is_updated = Column(Integer, default=0)  # 0/1
    is_reviewed = Column(Integer, default=0)  # 0/1
    quality_score = Column(Integer)
    quality_suggestion = Column(Text)
    plan_status = Column(String)  # 正常/未来规划


class StatusLog(Base):
    __tablename__ = "status_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(String, ForeignKey("requirement.demand_id"), nullable=False)
    from_status = Column(String)
    to_status = Column(String, nullable=False)
    operator = Column(String, nullable=False)
    operated_at = Column(String, nullable=False)
    remark = Column(Text)


class ReviewSession(Base):
    __tablename__ = "review_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_date = Column(String, nullable=False)
    total_count = Column(Integer, nullable=False)
    passed_count = Column(Integer, nullable=False)
    rejected_count = Column(Integer, nullable=False)
    ai_summary = Column(Text)
    created_at = Column(String, nullable=False, default=lambda: datetime.now().isoformat())


class ImportMetadata(Base):
    __tablename__ = "import_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_import_hash = Column(String, nullable=False)
    last_import_at = Column(String, nullable=False)
    total_imported = Column(Integer, nullable=False)
