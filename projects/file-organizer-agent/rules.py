#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则模块 — 规则数据与 I/O
从 organizer.py 拆分出来：DEFAULT_RULES、ClassificationResult、规则加载函数
"""

import os
import json
import copy
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


# 路径分隔符兼容常量
PATH_SEP = os.sep  # '/' on macOS/Linux, '\\' on Windows


# ============================================================
# 默认规则模板（当 config 中未提供 rules 时自动使用）
# ============================================================
DEFAULT_RULES = {
    "version": "4.0",
    "name": "数字化转型办公室 - 文件存放指引 v5.0",
    "description": "基于《文件存放指引》的四级分类规则，支持内容智能分析",

    # ---- 优先级1：业务领域匹配（最高）----
    "business_domain_rules": [
        # 数字化项目 - 业务线
        {"keywords": ["客舱"],       "target": f"03-数字化项目{PATH_SEP}00-客舱数字化"},
        {"keywords": ["飞行"],       "target": f"03-数字化项目{PATH_SEP}01-飞行数字化"},
        {"keywords": ["维修"],       "target": f"03-数字化项目{PATH_SEP}02-维修数字化"},
        {"keywords": ["司库"],       "target": f"03-数字化项目{PATH_SEP}03-司库管理数字化"},
        {"keywords": ["共享"],       "target": f"03-数字化项目{PATH_SEP}04-共享数字化"},
        {"keywords": ["核算"],       "target": f"03-数字化项目{PATH_SEP}05-核算与报告数字化"},
        {"keywords": ["机供品"],     "target": f"03-数字化项目{PATH_SEP}06-机供品数字化"},
        {"keywords": ["起降"],       "target": f"03-数字化项目{PATH_SEP}07-起降数字化"},
        # 数据分析报告
        {"keywords": ["经营分析", "成本分析", "收益分析"],
                                     "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}00-经营分析"},
        {"keywords": ["专题分析", "专题报告"],
                                     "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}01-专题分析"},
        {"keywords": ["数据报表", "BI报表", "Dashboard"],
                                     "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}02-数据报表"},
        # 信息化项目 - 通用系统
        {"keywords": ["ERP"],        "target": "02-信息化项目"},
        {"keywords": ["OA"],         "target": "02-信息化项目"},
        {"keywords": ["HR", "人力资源"], "target": "02-信息化项目"},
        {"keywords": ["报销"],       "target": "02-信息化项目"},
        {"keywords": ["财务共享"],   "target": "02-信息化项目"},
    ],

    # 信息化项目子阶段规则
    "infoproject_stage_rules": [
        {"keywords": ["立项", "可行性", "投资估算"],   "sub": f"00-项目立项"},
        {"keywords": ["BRD", "业务需求"],              "sub": f"01-需求文档{PATH_SEP}BRD"},
        {"keywords": ["PRD", "产品需求", "功能需求"],  "sub": f"01-需求文档{PATH_SEP}PRD"},
        {"keywords": ["概要设计", "详细设计", "数据库设计", "接口设计", "设计文档"],
                                                    "sub": f"02-设计文档"},
        {"keywords": ["使用手册", "操作手册", "用户手册", "操作指南"],
                                                    "sub": f"03-运维文档{PATH_SEP}系统使用手册"},
        {"keywords": ["运维手册", "运维指南", "应急预案"],
                                                    "sub": f"03-运维文档{PATH_SEP}运维手册"},
        {"keywords": ["测试用例", "测试报告", "集成测试"],
                                                    "sub": f"04-测试文档"},
    ],

    # ---- 优先级2：关键词规则 ----
    "keyword_rules": [
        # =========================================================
        # 00-战略与架构
        # =========================================================
        {"keywords": ["数字化战略", "转型战略", "战略规划", "数字化转型", "成本策略", "策略"],
                                             "target": f"00-战略与架构{PATH_SEP}00-数字化战略"},
        {"keywords": ["业务架构", "应用架构", "技术架构", "架构设计"],
                                             "target": f"00-战略与架构{PATH_SEP}01-业务架构"},
        {"keywords": ["战略", "规划"],
                                             "target": f"00-战略与架构{PATH_SEP}00-数字化战略"},

        # =========================================================
        # 01-知识库管理
        # =========================================================
        {"keywords": ["培训", "教程", "课程", "学习资料", "学习方法", "学习指南", "学习手册",
                       "数据清洗", "数据处理", "数据整理", "数据预处理", "数据入门", "数据教程",
                       "ETL", "数据仓库", "数仓", "数据建模", "数据开发"],
                                             "target": f"01-知识库管理{PATH_SEP}02-培训学习"},
        {"keywords": ["管理制度", "管理办法", "操作规范", "规章制度", "流程制度",
                       "制度", "规范", "标准",
                       "合同", "协议", "采购", "招投标", "招标", "投标", "中标", "报价",
                       "招聘", "入职", "离职", "转正", "调动",
                       "考勤", "请假", "加班", "出差", "休假",
                       "薪酬", "工资", "薪资", "福利", "社保", "公积金",
                       "变更", "需求变更", "范围变更"],
                                             "target": f"01-知识库管理{PATH_SEP}03-规章制度"},
        {"keywords": ["最佳实践", "案例", "经验总结", "复盘",
                       "供应商", "外包", "外包商", "服务商", "合作方"],
                                             "target": f"01-知识库管理{PATH_SEP}01-最佳实践"},
        {"keywords": ["FAQ", "问答", "Q&A", "常见问题"],
                                             "target": f"01-知识库管理{PATH_SEP}04-问答知识库"},
        {"keywords": ["概念", "术语", "知识体系", "业务流程", "业务规则"],
                                             "target": f"01-知识库管理{PATH_SEP}00-知识体系"},

        # =========================================================
        # 03-数字化项目 - 经营/专题分析报告
        # =========================================================
        {"keywords": ["经营分析", "成本分析", "收益分析", "经营报告", "成本报告",
                       "预算", "决算", "结算",
                       "里程碑", "验收", "交付", "上线", "发布",
                       "甘特图", "进度计划", "里程碑计划", "WBS"],
                                             "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}00-经营分析"},
        {"keywords": ["专题分析", "专题报告", "评审", "评审会", "技术评审", "方案评审"],
                                             "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}01-专题分析"},
        {"keywords": ["数据报表", "BI报表", "Dashboard"],
                                             "target": f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}02-数据报表"},
        {"keywords": ["核算", "财务共享", "报销",
                       "发票", "票据", "收据", "报销单", "费用",
                       "付款", "收款", "对账", "账户", "资金"],
                                             "target": f"03-数字化项目{PATH_SEP}05-核算与报告数字化"},

        # =========================================================
        # 04-创新应用
        # =========================================================
        {"keywords": ["Agent", "智能体", "机器人", "Bot"],
                                             "target": f"04-创新应用{PATH_SEP}00-Agent智能体"},
        {"keywords": ["RPA", "自动化流程", "自动化脚本"],
                                             "target": f"04-创新应用{PATH_SEP}01-流程自动化"},
        {"keywords": ["机器学习", "ML", "算法", "预测", "训练模型", "深度学习"],
                                             "target": f"04-创新应用{PATH_SEP}02-智能分析"},

        # =========================================================
        # 05-数据资产
        # =========================================================
        {"keywords": ["数据标准", "数据字典", "元数据", "指标", "KPI"],
                                             "target": f"05-数据资产{PATH_SEP}00-数据标准"},
        {"keywords": ["数据治理", "数据质量"],
                                             "target": f"05-数据资产{PATH_SEP}01-数据治理"},
        {"keywords": ["数据迁移", "数据同步", "数据接入", "数据采集"],
                                             "target": f"05-数据资产{PATH_SEP}03-数据集成"},
        {"keywords": ["数据备份", "灾备", "恢复方案", "数据安全"],
                                             "target": f"05-数据资产{PATH_SEP}04-数据安全"},

        # =========================================================
        # 06-团队与运营
        # =========================================================
        {"keywords": ["周报", "月报", "日报", "进度报告", "汇报"],
                                             "target": f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}周报月报"},
        {"keywords": ["会议纪要", "会议记录", "会议", "研讨会", "座谈会"],
                                             "target": f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}会议纪要"},
        {"keywords": ["团建", "团队活动", "团队建设"],
                                             "target": f"06-团队与运营{PATH_SEP}00-团队建设"},
        {"keywords": ["工具", "模板", "资源", "清单", "列表", "checklist"],
                                             "target": f"06-团队与运营{PATH_SEP}02-资源库"},
        {"keywords": ["通知", "公告", "通报", "简报", "通讯"],
                                             "target": f"06-团队与运营{PATH_SEP}03-通知公告"},
        {"keywords": ["访谈", "调研", "问卷", "反馈", "满意度"],
                                             "target": f"06-团队与运营{PATH_SEP}04-调研访谈"},
    ],

    # ---- 优先级3：文件内容分析规则（新增）----
    "content_analysis_rules": {
        "enabled": True,
        "max_file_size_mb": 10,  # 超过此大小的文件不读取内容
        "supported_extensions": [".txt", ".md", ".docx", ".pdf", ".doc", ".rtf", ".csv", ".xlsx", ".xls", ".pptx", ".ppt", ".json", ".xml", ".html", ".htm", ".py", ".js", ".java", ".sql"],
        "content_keywords": [
            # 业务领域关键词（用于内容匹配）
            {"keywords": ["客舱", "cabin", "乘务员", "客舱服务"], "target": f"03-数字化项目{PATH_SEP}00-客舱数字化", "weight": 3},
            {"keywords": ["飞行", "flight", "飞行员", "航班", "航路"], "target": f"03-数字化项目{PATH_SEP}01-飞行数字化", "weight": 3},
            {"keywords": ["维修", "maintenance", "机务", "定检", "航材"], "target": f"03-数字化项目{PATH_SEP}02-维修数字化", "weight": 3},
            {"keywords": ["司库", "treasury", "资金", "现金流", "理财"], "target": f"03-数字化项目{PATH_SEP}03-司库管理数字化", "weight": 3},
            {"keywords": ["共享", "shared", "财务共享", "共享中心"], "target": f"03-数字化项目{PATH_SEP}04-共享数字化", "weight": 3},
            {"keywords": ["核算", "accounting", "会计", "账务", "总账"], "target": f"03-数字化项目{PATH_SEP}05-核算与报告数字化", "weight": 3},
            {"keywords": ["机供品", "catering", "餐食", "机供", "机上用品"], "target": f"03-数字化项目{PATH_SEP}06-机供品数字化", "weight": 3},
            {"keywords": ["起降", "landing", "起飞", "降落", "机场", "地服"], "target": f"03-数字化项目{PATH_SEP}07-起降数字化", "weight": 3},

            # 文档类型关键词
            {"keywords": ["需求", "requirement", "BRD", "PRD", "用户故事"], "target": f"02-信息化项目{PATH_SEP}01-需求文档", "weight": 2},
            {"keywords": ["设计", "design", "架构", "概要设计", "详细设计"], "target": f"02-信息化项目{PATH_SEP}02-设计文档", "weight": 2},
            {"keywords": ["测试", "test", "测试用例", "测试报告", "UAT"], "target": f"02-信息化项目{PATH_SEP}04-测试文档", "weight": 2},
            {"keywords": ["手册", "manual", "指南", "guide", "说明书"], "target": f"02-信息化项目{PATH_SEP}03-运维文档", "weight": 2},

            # 通用业务关键词
            {"keywords": ["合同", "contract", "协议", "agreement", "条款"], "target": f"07-商务与采购{PATH_SEP}00-合同协议", "weight": 2},
            {"keywords": ["采购", "procurement", "招标", "投标", "询价"], "target": f"07-商务与采购{PATH_SEP}01-供应商管理", "weight": 2},
            {"keywords": ["人事", "HR", "招聘", "入职", "离职", "考勤"], "target": "09-人事行政", "weight": 2},
            {"keywords": ["财务", "finance", "预算", "报销", "发票", "付款"], "target": "08-财务文档", "weight": 2},
            {"keywords": ["项目", "project", "里程碑", "进度", "计划"], "target": "10-项目管理", "weight": 2},
            {"keywords": ["会议", "meeting", "纪要", "会议记录", "决议"], "target": f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}会议纪要", "weight": 2},
            {"keywords": ["周报", "weekly", "月报", "monthly", "日报"], "target": f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}周报月报", "weight": 2},
            {"keywords": ["数据", "data", "分析", "报表", "统计"], "target": "05-数据资产", "weight": 2},
            {"keywords": ["AI", "人工智能", "机器学习", "算法", "模型"], "target": "04-创新应用", "weight": 2},
        ]
    },

    # ---- 优先级4：扩展名兜底规则 ----
    "extension_rules": {
        # 文档
        ".doc":  f"00-文档{PATH_SEP}Word文档",
        ".docx": f"00-文档{PATH_SEP}Word文档",
        ".pdf":  f"00-文档{PATH_SEP}PDF文档",
        ".txt":  f"00-文档{PATH_SEP}文本文件",
        ".md":   f"00-文档{PATH_SEP}文本文件",
        ".rtf":  f"00-文档{PATH_SEP}富文本",
        ".odt":  f"00-文档{PATH_SEP}OpenDocument",
        # 表格
        ".xls":  f"01-表格{PATH_SEP}Excel表格",
        ".xlsx": f"01-表格{PATH_SEP}Excel表格",
        ".csv":  f"01-表格{PATH_SEP}CSV数据",
        ".ods":  f"01-表格{PATH_SEP}OpenDocument",
        # 演示
        ".ppt":  f"02-演示{PATH_SEP}PPT演示",
        ".pptx": f"02-演示{PATH_SEP}PPT演示",
        ".odp":  f"02-演示{PATH_SEP}OpenDocument",
        # 代码
        ".py":   f"03-代码{PATH_SEP}Python",
        ".sql":  f"03-代码{PATH_SEP}SQL脚本",
        ".js":   f"03-代码{PATH_SEP}Web前端",
        ".ts":   f"03-代码{PATH_SEP}Web前端",
        ".html": f"03-代码{PATH_SEP}Web前端",
        ".css":  f"03-代码{PATH_SEP}Web前端",
        ".java": f"03-代码{PATH_SEP}Java",
        ".go":   f"03-代码{PATH_SEP}Go",
        ".rs":   f"03-代码{PATH_SEP}Rust",
        ".cpp":  f"03-代码{PATH_SEP}C++",
        ".c":    f"03-代码{PATH_SEP}C",
        ".h":    f"03-代码{PATH_SEP}头文件",
        ".hpp":  f"03-代码{PATH_SEP}头文件",
        ".cs":   f"03-代码{PATH_SEP}C#",
        ".rb":   f"03-代码{PATH_SEP}Ruby",
        ".php":  f"03-代码{PATH_SEP}PHP",
        ".swift": f"03-代码{PATH_SEP}Swift",
        ".kt":   f"03-代码{PATH_SEP}Kotlin",
        ".scala": f"03-代码{PATH_SEP}Scala",
        ".r":    f"03-代码{PATH_SEP}R语言",
        ".m":    f"03-代码{PATH_SEP}MATLAB",
        ".mm":   f"03-代码{PATH_SEP}Objective-C",
        ".sh":   f"03-代码{PATH_SEP}Shell",
        ".ps1":  f"03-代码{PATH_SEP}PowerShell",
        ".bat":  f"03-代码{PATH_SEP}批处理",
        ".cmd":  f"03-代码{PATH_SEP}批处理",
        # 配置
        ".json": f"04-配置{PATH_SEP}配置文件",
        ".xml":  f"04-配置{PATH_SEP}配置文件",
        ".yaml": f"04-配置{PATH_SEP}配置文件",
        ".yml":  f"04-配置{PATH_SEP}配置文件",
        ".ini":  f"04-配置{PATH_SEP}配置文件",
        ".conf": f"04-配置{PATH_SEP}配置文件",
        ".env":  f"04-配置{PATH_SEP}环境配置",
        ".properties": f"04-配置{PATH_SEP}配置文件",
        ".toml": f"04-配置{PATH_SEP}配置文件",
        # 设计
        ".rp":    f"05-设计{PATH_SEP}Axure原型",
        ".xmind": f"05-设计{PATH_SEP}思维导图",
        ".emmx":  f"05-设计{PATH_SEP}思维导图",
        ".vsdx":  f"05-设计{PATH_SEP}Visio图表",
        ".vsd":   f"05-设计{PATH_SEP}Visio图表",
        ".dwg":   f"05-设计{PATH_SEP}CAD图纸",
        ".dxf":   f"05-设计{PATH_SEP}CAD图纸",
        ".sketch": f"05-设计{PATH_SEP}Sketch",
        ".fig":   f"05-设计{PATH_SEP}Figma",
        ".psd":   f"05-设计{PATH_SEP}Photoshop",
        ".ai":    f"05-设计{PATH_SEP}Illustrator",
        ".xd":    f"05-设计{PATH_SEP}Adobe XD",
        # 媒体
        ".png":  f"06-媒体{PATH_SEP}图片",
        ".jpg":  f"06-媒体{PATH_SEP}图片",
        ".jpeg": f"06-媒体{PATH_SEP}图片",
        ".gif":  f"06-媒体{PATH_SEP}图片",
        ".svg":  f"06-媒体{PATH_SEP}矢量图",
        ".bmp":  f"06-媒体{PATH_SEP}图片",
        ".tiff": f"06-媒体{PATH_SEP}图片",
        ".webp": f"06-媒体{PATH_SEP}图片",
        ".ico":  f"06-媒体{PATH_SEP}图标",
        ".mp4":  f"06-媒体{PATH_SEP}视频",
        ".avi":  f"06-媒体{PATH_SEP}视频",
        ".mov":  f"06-媒体{PATH_SEP}视频",
        ".mkv":  f"06-媒体{PATH_SEP}视频",
        ".wmv":  f"06-媒体{PATH_SEP}视频",
        ".flv":  f"06-媒体{PATH_SEP}视频",
        ".webm": f"06-媒体{PATH_SEP}视频",
        ".mp3":  f"06-媒体{PATH_SEP}音频",
        ".wav":  f"06-媒体{PATH_SEP}音频",
        ".m4a":  f"06-媒体{PATH_SEP}音频",
        ".flac": f"06-媒体{PATH_SEP}音频",
        ".aac":  f"06-媒体{PATH_SEP}音频",
        ".ogg":  f"06-媒体{PATH_SEP}音频",
        ".wma":  f"06-媒体{PATH_SEP}音频",
        # 数据
        ".pkl":    f"07-数据{PATH_SEP}模型文件",
        ".h5":     f"07-数据{PATH_SEP}模型文件",
        ".pth":    f"07-数据{PATH_SEP}模型文件",
        ".onnx":   f"07-数据{PATH_SEP}模型文件",
        ".model":  f"07-数据{PATH_SEP}模型文件",
        ".pb":     f"07-数据{PATH_SEP}模型文件",
        ".erm":    f"07-数据{PATH_SEP}ER模型",
        ".db":     f"07-数据{PATH_SEP}数据库",
        ".sqlite": f"07-数据{PATH_SEP}数据库",
        ".mdb":    f"07-数据{PATH_SEP}数据库",
        ".parquet": f"07-数据{PATH_SEP}Parquet",
        ".feather": f"07-数据{PATH_SEP}Feather",
        # 压缩包
        ".zip": f"99-其他{PATH_SEP}压缩包",
        ".rar": f"99-其他{PATH_SEP}压缩包",
        ".7z":  f"99-其他{PATH_SEP}压缩包",
        ".tar": f"99-其他{PATH_SEP}压缩包",
        ".gz":  f"99-其他{PATH_SEP}压缩包",
        ".bz2": f"99-其他{PATH_SEP}压缩包",
        ".xz":  f"99-其他{PATH_SEP}压缩包",
        ".tgz": f"99-其他{PATH_SEP}压缩包",
    },

    # 默认目录结构
    "standard_dirs": [
        f"00-战略与架构{PATH_SEP}00-数字化战略",
        f"00-战略与架构{PATH_SEP}01-业务架构",
        f"01-知识库管理{PATH_SEP}00-知识体系",
        f"01-知识库管理{PATH_SEP}01-最佳实践",
        f"01-知识库管理{PATH_SEP}02-培训学习",
        f"01-知识库管理{PATH_SEP}03-规章制度",
        f"01-知识库管理{PATH_SEP}04-问答知识库",
        f"02-信息化项目{PATH_SEP}00-项目立项",
        f"02-信息化项目{PATH_SEP}01-需求文档{PATH_SEP}BRD",
        f"02-信息化项目{PATH_SEP}01-需求文档{PATH_SEP}PRD",
        f"02-信息化项目{PATH_SEP}02-设计文档",
        f"02-信息化项目{PATH_SEP}03-运维文档{PATH_SEP}系统使用手册",
        f"02-信息化项目{PATH_SEP}03-运维文档{PATH_SEP}运维手册",
        f"02-信息化项目{PATH_SEP}04-测试文档",
        f"03-数字化项目{PATH_SEP}00-客舱数字化",
        f"03-数字化项目{PATH_SEP}01-飞行数字化",
        f"03-数字化项目{PATH_SEP}02-维修数字化",
        f"03-数字化项目{PATH_SEP}03-司库管理数字化",
        f"03-数字化项目{PATH_SEP}04-共享数字化",
        f"03-数字化项目{PATH_SEP}05-核算与报告数字化",
        f"03-数字化项目{PATH_SEP}06-机供品数字化",
        f"03-数字化项目{PATH_SEP}07-起降数字化",
        f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}00-经营分析",
        f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}01-专题分析",
        f"03-数字化项目{PATH_SEP}08-数据分析报告{PATH_SEP}02-数据报表",
        f"04-创新应用{PATH_SEP}00-Agent智能体",
        f"04-创新应用{PATH_SEP}01-流程自动化",
        f"04-创新应用{PATH_SEP}02-智能分析",
        f"05-数据资产{PATH_SEP}00-数据标准",
        f"05-数据资产{PATH_SEP}01-数据治理",
        f"05-数据资产{PATH_SEP}02-数据开发",
        f"05-数据资产{PATH_SEP}03-数据集成",
        f"05-数据资产{PATH_SEP}04-数据安全",
        f"06-团队与运营{PATH_SEP}00-团队建设",
        f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}周报月报",
        f"06-团队与运营{PATH_SEP}01-沟通协作{PATH_SEP}会议纪要",
        f"06-团队与运营{PATH_SEP}02-资源库",
        f"06-团队与运营{PATH_SEP}03-通知公告",
        f"06-团队与运营{PATH_SEP}04-调研访谈",
        f"07-商务与采购{PATH_SEP}00-合同协议",
        f"07-商务与采购{PATH_SEP}01-供应商管理",
        f"08-财务文档{PATH_SEP}00-预算决算",
        f"08-财务文档{PATH_SEP}01-票据报销",
        f"08-财务文档{PATH_SEP}02-收付款",
        f"09-人事行政{PATH_SEP}00-招聘入职",
        f"09-人事行政{PATH_SEP}01-考勤假期",
        f"09-人事行政{PATH_SEP}02-薪酬福利",
        f"09-人事行政{PATH_SEP}03-绩效考核",
        f"10-项目管理{PATH_SEP}00-项目里程碑",
        f"10-项目管理{PATH_SEP}01-变更管理",
        f"10-项目管理{PATH_SEP}02-评审记录",
        f"10-项目管理{PATH_SEP}03-项目计划",
        f"99-归档{PATH_SEP}00-历史项目",
        f"99-归档{PATH_SEP}01-临时文件{PATH_SEP}备份文件",
        f"99-归档{PATH_SEP}01-临时文件{PATH_SEP}大文件待处理",
    ],
}


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    target_path: str
    rule_name: str
    priority: int
    confidence: float = 0.0  # 置信度 0-1
    matched_keywords: List[str] = field(default_factory=list)
    analysis_method: str = ""  # 分类方法：filename, content, extension, ai


def get_default_rules() -> dict:
    """获取默认规则的深拷贝"""
    return copy.deepcopy(DEFAULT_RULES)


def save_default_template(path: str):
    """将默认规则导出为模板 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_RULES, f, ensure_ascii=False, indent=2)


def load_rules(rules_data: dict) -> dict:
    """
    从字典加载并验证规则，缺失字段用默认值补全。
    返回完整的、可直接使用的规则字典。
    """
    rules = copy.deepcopy(DEFAULT_RULES)

    if not rules_data:
        return rules

    # 逐字段合并，只接受合法字段
    valid_top_keys = {
        "business_domain_rules", "infoproject_stage_rules",
        "keyword_rules", "extension_rules", "standard_dirs",
        "content_analysis_rules",
        "name", "description", "version"
    }

    for key in valid_top_keys:
        if key in rules_data and rules_data[key] is not None:
            if key == "extension_rules" and isinstance(rules_data[key], dict):
                rules[key] = rules_data[key]
            elif key == "content_analysis_rules" and isinstance(rules_data[key], dict):
                rules[key] = {**rules.get(key, {}), **rules_data[key]}
            elif isinstance(rules_data[key], list):
                rules[key] = rules_data[key]
            elif key in ("name", "description", "version"):
                rules[key] = rules_data[key]

    return rules
