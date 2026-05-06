-- =============================================
-- 合同数据宽表视图 - 用于合同任意维度分析
-- 基于用友BIP yonbip_clm_contract 数据库
-- =============================================

CREATE OR REPLACE VIEW v_clm_contract_dw AS
SELECT
    -- ----------------------------
    -- 合同主键与编码
    -- ----------------------------
    c.id AS contract_id,
    c.code AS contract_code,
    c.serial_number AS serial_number,
    c.version AS version,
    c.title AS contract_title,
    c.ct_summary AS contract_summary,

    -- ----------------------------
    -- 合同分类与类型
    -- ----------------------------
    c.type AS contract_type_id,
    c.ct_class AS contract_class_id,          -- 合同性质：1=标准
    c.source_sys AS source_system,             -- 合同来源
    c.conclude_type AS sign_type_id,           -- 签订类型
    c.sign_type AS sign_method_id,             -- 签署方式
    c.bustype AS business_type_id,             -- 交易类型
    c.law_type AS law_type_id,                -- 法律类别
    c.is_econtract AS is_econtract,            -- 是否电子合同
    c.is_back_date AS is_back_date,            -- 是否倒签
    c.is_open_contract AS is_open_contract,   -- 是否开口合同
    c.is_material AS is_material,             -- 物料分类合同

    -- ----------------------------
    -- 合同状态
    -- ----------------------------
    c.status AS contract_status,
    c.change_status AS change_status,
    c.finalize_status AS finalize_status,     -- 定稿状态
    c.econtract_status AS econtract_status,   -- 合同模板状态
    c.stamp_status AS stamp_status,           -- 用印状态
    c.contract_file_status AS file_status,    -- 归档状态
    c.verifystate AS verify_state,           -- 单据状态
    c.b_watermark AS watermark_status,

    -- ----------------------------
    -- 合同金额信息（含税/无税）
    -- ----------------------------
    c.mny AS contract_amount,                 -- 合同金额（本币）
    c.have_tax_mny AS amount_with_tax,        -- 含税金额（本币）
    c.no_tax_mny AS amount_without_tax,       -- 无税金额（本币）
    c.tax_amount AS tax_amount,               -- 税额（本币）

    -- 原币金额
    c.ori_currency_id AS original_currency,
    c.ori_have_tax_mny AS ori_amount_with_tax,
    c.ori_no_tax_mny AS ori_amount_without_tax,
    c.ori_tax_amount AS ori_tax_amount,
    c.exchange_rate,
    c.rate_type AS exchange_rate_type,
    c.rate_date AS exchange_rate_date,

    -- 初版金额
    c.ori_init_mny AS ori_initial_amount,
    c.ori_init_notax_mny AS ori_initial_no_tax,
    c.ori_init_tax_mny AS ori_initial_tax,
    c.init_mny AS initial_amount,
    c.init_notax_mny AS initial_no_tax,
    c.init_tax_mny AS initial_tax,

    -- ----------------------------
    -- 合同执行金额
    -- ----------------------------
    c.paid_mny AS paid_amount,                 -- 已付款金额（本币）
    c.paid_orig_mny AS paid_orig_amount,       -- 已付款金额（原币）
    c.prepay_mny AS prepay_amount,            -- 预付款（本币）
    c.prepay_origmny AS prepay_orig_amount,   -- 预付款（原币）
    c.prepay_paidmny AS prepay_paid_amount,   -- 已付预付款（本币）
    c.prepay_paidorigmny AS prepay_paid_orig, -- 已付预付款（原币）
    c.ap_mny AS ap_amount,                   -- 应付金额（本币）
    c.ap_origmny AS ap_orig_amount,          -- 应付金额（原币）
    c.invoice_mny AS invoice_amount,          -- 收票金额（本币）
    c.invoice_origmny AS invoice_orig_amount, -- 收票金额（原币）
    c.margin_mny AS margin_amount,            -- 履约保证金（本币）
    c.margin_origmny AS margin_orig_amount,   -- 履约保证金（原币）
    c.received_bondmny AS received_bond,      -- 已收保证金（本币）
    c.return_bondmny AS return_bond,         -- 已退保证金（本币）
    c.retention_mny AS retention_amount,       -- 质保金（本币）
    c.retention_origmny AS retention_orig,   -- 质保金（原币）
    c.retention_paidmny AS retention_paid,   -- 已付质保金（本币）
    c.srv_confirmny AS service_confirm_amount, -- 服务确认金额（本币）

    -- ----------------------------
    -- 签证与结算
    -- ----------------------------
    c.ori_visa_confirm_mny AS ori_visa_confirm,
    c.ori_visa_confirm_notax_mny AS ori_visa_confirm_no_tax,
    c.ori_visa_confirm_tax_mny AS ori_visa_confirm_tax,
    c.visa_confirm_mny AS visa_confirm,
    c.visa_confirm_notax_mny AS visa_confirm_no_tax,
    c.visa_confirm_tax_mny AS visa_confirm_tax,
    c.ori_acccomplete_mny AS ori_acc_complete,

    -- ----------------------------
    -- 合同日期信息
    -- ----------------------------
    c.sign_date AS sign_date,                  -- 签订日期
    c.vali_date AS effective_date,            -- 生效日期
    c.invali_date AS expiry_date,             -- 终止日期
    c.plan_validate AS plan_effective_date,   -- 计划生效日期
    c.plan_invallidate AS plan_expiry_date,   -- 计划失效日期
    c.plan_complete_date AS plan_complete_date, -- 计划竣工日期
    c.create_time AS create_time,
    c.modify_time AS modify_time,

    -- ----------------------------
    -- 合同期限与工期
    -- ----------------------------
    c.ct_period AS contract_period_id,
    c.period AS contract_period_days,         -- 工期（天）
    c.warranty_period AS warranty_period,     -- 质保期

    -- ----------------------------
    -- 税率与税种
    -- ----------------------------
    c.tax_rate AS tax_rate,
    c.tax_type AS tax_type_id,
    c.tax_items AS tax_items_id,
    c.is_have_tax AS is_tax_included,

    -- ----------------------------
    -- 签约主体与地点
    -- ----------------------------
    c.sign_subject_id AS sign_subject_id,     -- 签约主体
    c.sign_address AS sign_address,           -- 签订地点
    c.perform_address AS perform_address,     -- 履约地点

    -- ----------------------------
    -- 组织与部门
    -- ----------------------------
    c.org_id AS main_org_id,                  -- 主组织
    c.sign_subject_id AS undertake_org_id,    -- 承办组织
    c.dept_id AS dept_id,                     -- 承办部门
    c.settle_orgid AS settle_org_id,          -- 结算组织

    -- ----------------------------
    -- 人员信息
    -- ----------------------------
    c.person_id AS person_id,                 -- 承办人
    c.creator AS creator,
    c.modifier AS modifier,
    c.auditor AS auditor,
    c.audit_time AS audit_time,

    -- ----------------------------
    -- 流程信息
    -- ----------------------------
    c.procinst_id AS process_instance_id,
    c.bizflow_id AS bizflow_id,
    c.bizflowname AS bizflow_name,
    c.auditnote AS current_auditor_note,

    -- ----------------------------
    -- 变更信息
    -- ----------------------------
    c.change_times AS change_times,
    c.change_contract_id AS change_contract_id,
    c.change_create_date AS change_apply_date,
    c.change_creator AS change_creator,

    -- ----------------------------
    -- 合同标签与特征
    -- ----------------------------
    c.label AS contract_label,
    c.feature AS custom_feature,
    c.ctlib_feature AS ctlib_feature,
    c.memo AS memo,
    c.ct_summary AS summary,

    -- ----------------------------
    -- 电子合同信息
    -- ----------------------------
    c.econtract_temp_id AS econtract_template_id,
    c.econtractTemp_Code AS econtract_template_code,
    c.econtract_version AS econtract_version,
    c.sign_process_id AS sign_process_id,
    c.contract_journal_id AS contract_journal_id,
    c.clm_contract_file_id AS contract_file_id,

    -- ----------------------------
    -- 款项与结算
    -- ----------------------------
    c.settlement_basis AS settlement_basis_id,
    c.settle_account_type AS settle_account_type,
    c.over_pay_ratio AS over_pay_ratio,
    c.warranty_period AS warranty_period_days,

    -- ----------------------------
    -- 上游来源信息
    -- ----------------------------
    c.source_id AS source_id,
    c.sourcechild_id AS source_child_id,
    c.sourcecode AS source_code,
    c.sourcebusiobj AS source_busiobj,
    c.sourcegrand_id AS source_grand_id,
    c.first_id AS first_id,
    c.firstchild_id AS first_child_id,
    c.firstcode AS first_code,
    c.firstbusiobj AS first_busiobj,
    c.billtype_code AS billtype_code,
    c.billtype_id AS billtype_id,
    c.source_sys AS source_system_code,

    -- ----------------------------
    -- 其他信息
    -- ----------------------------
    c.group_id AS group_id,
    c.project_id AS project_id,
    c.contract_id AS parent_contract_id,
    c.re_direction AS re_direction,
    c.secret_level AS secret_level_id,
    c.important_level AS important_level_id,
    c.urgent_level AS urgent_level_id,
    c.create_method AS create_method,
    c.sign_priority AS sign_priority,
    c.beginning_flag AS beginning_flag,

    -- ----------------------------
    -- 金额大写
    -- ----------------------------
    c.mny_words AS amount_in_words,

    -- ----------------------------
    -- 租户与逻辑删除
    -- ----------------------------
    c.ytenant_id AS tenant_id,
    c.dr AS is_deleted,

    -- ----------------------------
    -- 相对方/供应商信息（从clm_contract_counterpart关联）
    -- ----------------------------
    cp.id AS counterpart_link_id,
    cp.clm_counterpart_id AS counterpart_id,
    cp.merchant_type AS merchant_type,
    cp.supplier_id AS supplier_id,
    cp.customer_id AS customer_id,
    cp.contact AS counterpart_contact,
    cp.contact_phone AS counterpart_phone,
    cp.mobile AS counterpart_mobile,
    cp.address AS counterpart_address,
    cp.tax_number AS counterpart_tax_number,
    cp.bank_account AS counterpart_bank_account,
    cp.account_opening_address AS counterpart_bank_address,
    cp.certificate_num AS counterpart_certificate,
    cp.participant AS participant_type,
    cp.is_main_counterpart AS is_main_counterpart,
    cp.sign_sort AS sign_order,

    -- ----------------------------
    -- 供应商主档案信息（从iuap_apdoc_coredoc.aa_vendor，通过base_businesspartner关联）
    -- ----------------------------
    v.id AS vendor_id,
    v.code AS vendor_code,
    v.name AS vendor_name,
    v.nameAlias AS vendor_alias,
    v.cCreditCode AS vendor_credit_code,
    v.cContact AS vendor_contact,
    v.cContactPhone AS vendor_contact_phone,
    v.cContactMobile AS vendor_contact_mobile,
    v.cVendorPhone AS vendor_phone,
    v.cVendorEmail AS vendor_email,
    v.cVendorAddress AS vendor_address,
    v.cVendorRegisterAddress AS vendor_register_address,
    v.cCompanyType AS vendor_company_type,
    v.cCooperationDate AS vendor_first_coop_date,
    v.bFreezeStatus AS vendor_freeze_status,
    v.cAccessStatus AS vendor_status,
    v.legalbody AS vendor_legal_person,
    v.registerfund AS vendor_register_fund,
    v.supply_type AS vendor_supply_type,
    v.trade AS vendor_industry,
    v.service_range AS vendor_service_range

FROM
    yonbip_clm_contract.clm_contract c
    LEFT JOIN yonbip_clm_contract.clm_contract_counterpart cp ON c.id = cp.clm_contract_id AND cp.dr = 0
    LEFT JOIN iuap_apdoc_coredoc.base_businesspartner bp ON cp.supplier_id = bp.id
    LEFT JOIN iuap_apdoc_coredoc.aa_vendor v ON bp.id = v.id
WHERE
    c.dr = 0;

-- =============================================
-- 使用示例
-- =============================================
-- 1. 查看所有合同及其供应商
-- SELECT contract_code, contract_title, vendor_name, contract_amount, contract_status FROM v_clm_contract_dw;

-- 2. 按供应商统计合同金额
-- SELECT vendor_name, COUNT(*) as contract_count, SUM(contract_amount) as total_amount
-- FROM v_clm_contract_dw
-- GROUP BY vendor_name;

-- 3. 按合同状态统计
-- SELECT contract_status, COUNT(*) as cnt, SUM(contract_amount) as total
-- FROM v_clm_contract_dw
-- GROUP BY contract_status;

-- 4. 查询待执行的合同
-- SELECT * FROM v_clm_contract_dw WHERE contract_status = 'EXECUTING';
