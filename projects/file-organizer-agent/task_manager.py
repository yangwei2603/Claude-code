#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多任务管理器 — 管理多个整理任务（每个任务 = 一个源目录 + 一套规则）
支持 CRUD 操作、模板导入、任务状态跟踪。
"""

import os
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 默认 agent 目录：本文件所在目录的上级
DEFAULT_AGENT_DIR = Path(__file__).parent


class TaskManager:
    """管理多个文件整理任务"""

    def __init__(self, tasks_dir: str = None, templates_dir: str = None, agent_dir: Path = None):
        self.agent_dir = agent_dir or DEFAULT_AGENT_DIR
        self.tasks_dir = Path(tasks_dir or (self.agent_dir / "tasks"))
        self.templates_dir = Path(templates_dir or (self.agent_dir / "templates"))
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # 任务列表
    # ----------------------------------------------------------

    def list_tasks(self) -> List[dict]:
        """返回所有任务的简要信息列表"""
        tasks = []
        for f in sorted(self.tasks_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                tasks.append({
                    "id": f.stem,
                    "name": data.get("name", f.stem),
                    "source_dir": data.get("source_dir", ""),
                    "target_dir": data.get("target_dir", ""),
                    "enabled": data.get("enabled", True),
                    "created_at": data.get("created_at", ""),
                    "last_run": data.get("last_run"),
                    "rules_name": (data.get("rules") or {}).get("name", "默认规则"),
                })
            except Exception:
                continue
        return tasks

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取完整任务配置"""
        path = self.tasks_dir / f"{task_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def task_exists(self, task_id: str) -> bool:
        return (self.tasks_dir / f"{task_id}.json").exists()

    # ----------------------------------------------------------
    # 任务创建/更新/删除
    # ----------------------------------------------------------

    def create_task(self, config: dict) -> dict:
        """
        创建新任务。
        config 必须包含: name, source_dir
        可选: rules, scan_days, dry_run, protected_folders, delete_patterns 等
        返回完整任务数据（含自动生成的 id 和 created_at）
        """
        task_id = config.get("id") or uuid.uuid4().hex[:12]

        # 验证必填字段
        if not config.get("name"):
            raise ValueError("任务名称 (name) 不能为空")
        if not config.get("source_dir"):
            raise ValueError("源目录 (source_dir) 不能为空")

        # 构建完整任务配置
        now = datetime.now().isoformat()
        task_data = {
            "id": task_id,
            "name": config["name"],
            "description": config.get("description", ""),
            "source_dir": config["source_dir"],
            "target_dir": config.get("target_dir", ""),
            "enabled": config.get("enabled", True),
            "scan_days": config.get("scan_days", 7),
            "dry_run": config.get("dry_run", True),  # 默认预览模式
            "keep_original": config.get("keep_original", False),
            "large_file_threshold_mb": config.get("large_file_threshold_mb", 100),
            "protected_folders": config.get("protected_folders", []),
            "delete_patterns": config.get("delete_patterns", [
                r"\.svn-base$", r"^~\$", r"\.tmp$", r"\.DS_Store$",
                r"^\.~", r"Thumbs\.db$", r"desktop\.ini$"
            ]),
            "backup_extensions": config.get("backup_extensions", [".bak", ".backup"]),
            "old_folder_mapping": config.get("old_folder_mapping", {}),
            "state_file": config.get("state_file", f"state/task_{task_id}_state.json"),
            "log_dir": config.get("log_dir", f"logs/task_{task_id}"),
            "rollback_dir": config.get("rollback_dir", f"state/rollback_{task_id}"),
            "rules": config.get("rules"),  # None 表示使用默认规则
            "created_at": now,
            "updated_at": now,
            "last_run": None,
            "last_status": None,
        }

        path = self.tasks_dir / f"{task_id}.json"
        path.write_text(json.dumps(task_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return task_data

    def update_task(self, task_id: str, updates: dict) -> Optional[dict]:
        """更新任务的部分字段"""
        existing = self.get_task(task_id)
        if not existing:
            return None
        updates["updated_at"] = datetime.now().isoformat()
        existing.update(updates)
        path = self.tasks_dir / f"{task_id}.json"
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return existing

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        path = self.tasks_dir / f"{task_id}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def toggle_task(self, task_id: str) -> Optional[dict]:
        """切换任务启用/禁用状态"""
        task = self.get_task(task_id)
        if not task:
            return None
        return self.update_task(task_id, {"enabled": not task.get("enabled", True)})

    # ----------------------------------------------------------
    # 模板管理
    # ----------------------------------------------------------

    def list_templates(self) -> List[dict]:
        """列出所有可用的规则模板"""
        templates = []
        for f in sorted(self.templates_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                templates.append({
                    "filename": f.name,
                    "name": data.get("name", f.stem),
                    "version": data.get("version", ""),
                    "description": data.get("description", ""),
                    "business_domain_count": len(data.get("business_domain_rules", [])),
                    "keyword_count": len(data.get("keyword_rules", [])),
                    "extension_count": len(data.get("extension_rules", {})),
                })
            except Exception:
                continue
        return templates

    def get_template(self, filename: str) -> Optional[dict]:
        """获取模板内容"""
        path = self.templates_dir / filename
        if not path.exists() or not path.is_relative_to(self.templates_dir):
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def create_template(self, name: str, rules_data: dict) -> str:
        """
        创建新的规则模板文件。
        安全限制：只能在 templates 目录下创建 .json 文件。
        返回生成的文件名。
        """
        safe_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', name)
        filename = f"{safe_name}.json"
        path = self.templates_dir / filename

        template = {
            "version": rules_data.get("version", "1.0"),
            "name": name,
            "description": rules_data.get("description", ""),
            "business_domain_rules": rules_data.get("business_domain_rules", []),
            "infoproject_stage_rules": rules_data.get("infoproject_stage_rules", []),
            "keyword_rules": rules_data.get("keyword_rules", []),
            "extension_rules": rules_data.get("extension_rules", {}),
            "standard_dirs": rules_data.get("standard_dirs", []),
        }

        path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        return filename

    def delete_template(self, filename: str) -> bool:
        """删除模板（安全检查：必须在 templates 目录内）"""
        path = self.templates_dir / filename
        if not path.exists() or not path.is_relative_to(self.templates_dir):
            return False
        # 保护内置默认模板
        if filename == "digital-office.json":
            raise PermissionError("不允许删除内置默认模板")
        path.unlink()
        return True

    def update_template(self, filename: str, rules_data: dict) -> Optional[dict]:
        """
        更新已有规则模板的内容。
        安全检查：必须在 templates 目录内，且为 .json 文件。
        返回更新后的完整模板数据。
        """
        path = self.templates_dir / filename
        if not path.exists() or not path.is_relative_to(self.templates_dir):
            return None
        # 只允许更新 .json 文件
        if not filename.endswith(".json"):
            raise ValueError("只允许更新 .json 格式的模板")

        # 读取现有模板以保留不可变字段
        existing = json.loads(path.read_text(encoding="utf-8"))

        # 用传入数据覆盖可编辑字段
        existing["version"] = rules_data.get("version", existing.get("version", "1.0"))
        existing["name"] = rules_data.get("name", existing.get("name", ""))
        existing["description"] = rules_data.get("description", existing.get("description", ""))
        # 规则数据完整替换
        for key in ("business_domain_rules", "infoproject_stage_rules",
                     "keyword_rules", "extension_rules", "standard_dirs"):
            if key in rules_data:
                existing[key] = rules_data[key]

        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return existing

    def upload_template_file(self, uploaded_name: str, content: str) -> dict:
        """
        从上传的文件内容创建或覆盖规则模板。
        支持 .json / .md / .txt 三种格式。
        - .json: 直接写入
        - .md / .txt: 尝试解析 Markdown 中的结构化规则（YAML frontmatter + 表格），转为 JSON 模板
        返回 {"filename": str, "created": bool, "warnings": list}
        """
        import yaml  # lazy import

        ext = Path(uploaded_name).suffix.lower()

        if ext == ".json":
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 格式错误: {e}")
            safe_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', data.get("name", Path(uploaded_name).stem))
            filename = f"{safe_name}.json"
            path = self.templates_dir / filename
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            created = not path.exists()
            return {"filename": filename, "created": True, "warnings": []}

        elif ext in (".md", ".txt"):
            # 解析 Markdown / 纯文本中的规则
            warnings = []

            # 尝试提取 YAML frontmatter
            meta = {}
            body = content
            fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            if fm_match:
                try:
                    meta = yaml.safe_load(fm_match.group(1)) or {}
                except Exception:
                    pass
                body = fm_match.group(2)

            template_name = meta.get("name") or Path(uploaded_name).stem
            description = meta.get("description", "")
            version = meta.get("version", "1.0")

            # 解析表格形式的业务领域规则
            business_domain_rules = []
            bd_pattern = r'^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$'
            for m in re.finditer(bd_pattern, body, re.MULTILINE):
                cols = [c.strip() for c in [m.group(1), m.group(2), m.group(3)]]
                # 跳过表头行
                if any(h in cols[0].lower() for h in ("领域", "目录名", "---")):
                    continue
                business_domain_rules.append({
                    "domain": cols[0],
                    "target_dir": cols[1],
                    "description": cols[2],
                })

            # 解析关键词规则
            keyword_rules = []
            kw_pattern = r'^\|\s*"?(.+?)"?\s*\|\s*"?(.+?)"?\s*\|\s*(.+?)\s*\|$'
            for m in re.finditer(kw_pattern, body, re.MULTILINE):
                cols = [c.strip() for c in [m.group(1), m.group(2), m.group(3)]]
                if any(h in cols[0].lower() for h in ("关键词", "关键字", "---")):
                    continue
                keyword_rules.append({
                    "keywords": [k.strip() for k in cols[0].split(",")] if "," in cols[0] else [cols[0]],
                    "target_dir": cols[1],
                    "priority": int(cols[2]) if cols[2].isdigit() else 5,
                })

            # 解析扩展名规则（格式：| 扩展名 | 目标目录 |）
            extension_rules = {}
            ext_pattern = r'^\|\s*\.?(\w+)\s*\|\s*(.+?)\s*\|\s*$'
            for m in re.finditer(ext_pattern, body, re.MULTILINE):
                cols = [m.group(1).strip(), m.group(2).strip()]
                if any(h in cols[0].lower() for h in ("扩展名", "后缀", "---")):
                    continue
                extension_rules[f".{cols[0]}"] = cols[1]

            if not business_domain_rules and not keyword_rules and not extension_rules:
                raise ValueError(
                    "无法从上传的 Markdown/文本中解析出规则。"
                    "请使用以下格式之一：\n"
                    "1. JSON 格式的规则文件\n"
                    "2. 包含 YAML frontmatter 和表格的 Markdown 文件\n"
                    "3. 参考文档了解 Markdown 规则格式"
                )

            safe_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', template_name)
            filename = f"{safe_name}.json"

            template = {
                "version": version,
                "name": template_name,
                "description": description,
                "business_domain_rules": business_domain_rules,
                "infoproject_stage_rules": meta.get("infoproject_stage_rules", []),
                "keyword_rules": keyword_rules,
                "extension_rules": extension_rules,
                "standard_dirs": meta.get("standard_dirs", []),
            }

            path = self.templates_dir / filename
            is_overwrite = path.exists()
            path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

            if is_overwrite:
                warnings.append(f"已覆盖已有模板: {filename}")
            if not business_domain_rules:
                warnings.append("未解析到业务领域规则")
            if not keyword_rules:
                warnings.append("未解析到关键词规则")
            if not extension_rules:
                warnings.append("未解析到扩展名规则")

            return {"filename": filename, "created": not is_overwrite, "warnings": warnings}

        else:
            raise ValueError(f"不支持的文件格式: {ext}，仅支持 .json / .md / .txt")

    # ----------------------------------------------------------
    # 任务运行状态更新
    # ----------------------------------------------------------

    def update_run_status(self, task_id: str, status: str, stats: dict = None):
        """更新任务的最后运行状态"""
        updates = {
            "last_run": datetime.now().isoformat(),
            "last_status": status,
        }
        if stats:
            updates["last_stats"] = stats
        self.update_task(task_id, updates)

    # ----------------------------------------------------------
    # 导入/导出
    # ----------------------------------------------------------

    def export_task(self, task_id: str) -> Optional[str]:
        """导出任务为 JSON 字符串"""
        task = self.get_task(task_id)
        if not task:
            return None
        return json.dumps(task, ensure_ascii=False, indent=2)

    def import_task(self, json_str: str) -> dict:
        """从 JSON 字符串导入任务"""
        data = json.loads(json_str)
        # 移除旧 ID，生成新 ID，避免冲突
        data.pop("id", None)
        data.pop("created_at", None)
        return self.create_task(data)

    # ----------------------------------------------------------
    # 验证 & 工具方法
    # ----------------------------------------------------------

    @staticmethod
    def validate_source_dir(path: str) -> dict:
        """验证源目录是否可用"""
        p = Path(path)
        result = {
            "exists": p.exists(),
            "is_dir": p.is_dir() if p.exists() else False,
            "readable": False,
            "writable": False,
            "file_count": 0,
            "error": None,
        }
        if not result["exists"]:
            result["error"] = "目录不存在"
            return result
        if not result["is_dir"]:
            result["error"] = "路径不是目录"
            return result
        try:
            result["readable"] = os.access(p, os.R_OK)
            result["writable"] = os.access(p, os.W_OK)
            result["file_count"] = len(list(p.rglob("*"))) if result["readable"] else 0
        except Exception as e:
            result["error"] = str(e)
        return result
