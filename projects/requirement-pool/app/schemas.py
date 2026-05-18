from typing import Optional, List
from pydantic import BaseModel


class RequirementBase(BaseModel):
    # 基础识别字段
    demand_id: str
    demand_name: str

    # 状态字段
    demand_status: str
    stage: Optional[str] = None
    project: Optional[str] = None
    department: Optional[str] = None
    importance: Optional[str] = None
    pri: Optional[str] = None

    # 需求描述字段
    demand_desc: Optional[str] = None
    businessobjective: Optional[str] = None
    businessdesc: Optional[str] = None
    deadline: Optional[str] = None
    end_time: Optional[str] = None
    begin_time: Optional[str] = None

    # 业务需求信息
    business_id: Optional[str] = None
    business_name: Optional[str] = None
    business_status: Optional[str] = None
    business_review_status: Optional[str] = None
    business_review_result: Optional[str] = None
    business_approval: Optional[str] = None
    business_created_date: Optional[str] = None
    business_edited_by: Optional[str] = None
    business_edited_date: Optional[str] = None
    business_pm: Optional[str] = None
    business_pm_name: Optional[str] = None
    business_capability: Optional[str] = None
    reason_type: Optional[str] = None
    busi_desc: Optional[str] = None
    business_desc: Optional[str] = None
    business_objective: Optional[str] = None
    business_acl: Optional[str] = None
    business_architecture: Optional[str] = None
    busi_process: Optional[str] = None
    application_architecture: Optional[str] = None

    # 项目审批信息
    proj_approval_id: Optional[str] = None
    approval_status: Optional[str] = None
    approval_name: Optional[str] = None
    approval_created_by: Optional[str] = None
    approval_created_date: Optional[str] = None
    approval_edited_by: Optional[str] = None
    approval_edited_date: Optional[str] = None
    approval_desc: Optional[str] = None
    approval_review_result: Optional[str] = None
    approval_review_status: Optional[str] = None
    approval_approval: Optional[str] = None
    approval_acl: Optional[str] = None
    mailto: Optional[str] = None
    program: Optional[str] = None
    product_plan: Optional[str] = None

    # 项目立项
    model: Optional[str] = None
    type: Optional[str] = None
    class_: Optional[str] = None
    business_line: Optional[str] = None
    auth: Optional[str] = None
    days: Optional[str] = None

    # 成本与资源
    development_budget: Optional[str] = None
    outsourcing_budget: Optional[str] = None
    total_cost: Optional[str] = None
    cost_budget: Optional[str] = None
    brd_remain_budget: Optional[str] = None

    # 需求池基础信息
    demandpool_id: Optional[str] = None
    dept: Optional[str] = None
    name: Optional[str] = None
    demandpool_desc: Optional[str] = None
    demandpool_acl: Optional[str] = None
    is_cancel: Optional[str] = None
    is_it_confirm: Optional[str] = None
    responsible_dept: Optional[str] = None
    responsible_dept_name: Optional[str] = None
    recorder: Optional[str] = None

    # 评审与变更记录
    project_review_date: Optional[str] = None
    project_number: Optional[str] = None
    review_date: Optional[str] = None
    review_location: Optional[str] = None
    participant: Optional[str] = None
    remark: Optional[str] = None
    evaluation_feedback_by: Optional[str] = None
    evaluation_feedback_date: Optional[str] = None
    change_application_date: Optional[str] = None
    change_content: Optional[str] = None
    change_reason: Optional[str] = None
    project_approval_date: Optional[str] = None
    termination_date: Optional[str] = None
    target: Optional[str] = None

    # ITPM 字段
    itpm_account: Optional[str] = None
    itpm_realname: Optional[str] = None
    itpm_shorcq: Optional[str] = None
    itpm_dept_name: Optional[str] = None

    # 其他字段
    old_status: Optional[str] = None
    net_info_safe: Optional[str] = None
    meeting: Optional[str] = None
    integrate: Optional[str] = None
    risk: Optional[str] = None

    # 系统字段
    creator: Optional[str] = None
    source_dept: Optional[str] = None
    last_modified: Optional[str] = None


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    demand_name: Optional[str] = None
    demand_status: Optional[str] = None
    stage: Optional[str] = None
    project: Optional[str] = None
    department: Optional[str] = None
    demand_desc: Optional[str] = None
    businessobjective: Optional[str] = None
    businessdesc: Optional[str] = None
    deadline: Optional[str] = None
    importance: Optional[str] = None


class RequirementOut(RequirementBase):
    is_closed: int = 0  # derived

    class Config:
        from_attributes = True


class CloseRequest(BaseModel):
    operator: str
    remark: str


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[dict | list] = None