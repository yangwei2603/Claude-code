#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件自动整理引擎 v4.0 — 支持规则注入 + 内容智能分析
基于《文件存放指引》实现四级优先级智能分类：
  优先级1：业务领域匹配（最高）
  优先级2：关键词规则分类
  优先级3：文件内容智能分析（新增）
  优先级4：扩展名兜底分类

v4.0 新增：
- 文件内容智能分析：读取文档内容提取关键词进行语义分类
- 智能文件名分析：支持日期、项目编号、版本号等模式识别
- 文件属性分析：作者、标题、主题等元数据提取

模块拆分（v5.0 重构）：
- rules.py: 规则数据与 I/O（DEFAULT_RULES、ClassificationResult、load_rules）
- classifier.py: 四级分类决策逻辑
- content_analyzer.py: ContentExtractor、FilenameAnalyzer
- state.py: StateManager、文件哈希、回滚
- organizer.py: 编排层（组装各子模块）
"""

import os
import re
import json
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from rules import (
    DEFAULT_RULES,
    ClassificationResult,
    load_rules,
    get_default_rules,
    save_default_template,
)
from content_analyzer import ContentExtractor, FilenameAnalyzer
from state import StateManager, compute_hash, find_duplicates, move_file, rollback_last_session


# ============================================================
# 核心引擎类
# ============================================================

class DocumentOrganizer:
    """文件自动整理引擎 — 支持自定义规则注入和内容智能分析"""

    def __init__(self, config: dict, agent_dir: Path = None):
        self.config = config
        self.source_dir = Path(config["source_dir"])
        raw_target = config.get("target_dir", "")
        self.target_dir = Path(raw_target) if raw_target else self.source_dir
        self.agent_dir = agent_dir or Path(__file__).parent

        # ---- 规则注入：从 config 提取规则，缺失则使用默认 ----
        self.rules = load_rules(config.get("rules"))
        self.business_domain_rules = self.rules.get("business_domain_rules", [])
        self.infoproject_stage_rules = self.rules.get("infoproject_stage_rules", [])
        self.keyword_rules = self.rules.get("keyword_rules", [])
        self.extension_rules = self.rules.get("extension_rules", {})
        self.standard_dirs = self.rules.get("standard_dirs", [])

        # v4.0: 内容分析规则
        self.content_analysis_rules = self.rules.get("content_analysis_rules", {})
        self.enable_content_analysis = self.content_analysis_rules.get("enabled", True)

        # 允许 config 覆盖 standard_dirs（向后兼容旧 config 格式）
        if "standard_dirs" in config and config["standard_dirs"]:
            self.standard_dirs = config["standard_dirs"]

        # 状态和日志路径（相对 agent 目录，修复跨平台路径）
        state_file_cfg = config.get("state_file", "")
        self.state_file = (
            self.agent_dir / state_file_cfg
            if Path(state_file_cfg).is_absolute()
            else self.agent_dir / state_file_cfg.replace("\\", "/")
        )
        log_dir_cfg = config.get("log_dir", "logs")
        self.log_dir = (
            self.agent_dir / log_dir_cfg
            if Path(log_dir_cfg).is_absolute()
            else self.agent_dir / log_dir_cfg.replace("\\", "/")
        )
        rollback_dir_cfg = config.get("rollback_dir", "")
        self.rollback_dir = (
            self.agent_dir / rollback_dir_cfg
            if not rollback_dir_cfg or Path(rollback_dir_cfg).is_absolute()
            else self.agent_dir / rollback_dir_cfg.replace("\\", "/")
        )

        # 运行参数
        self.dry_run = config.get("dry_run", True)
        self.keep_original = config.get("keep_original", False)
        self.scan_days = config.get("scan_days", 7)
        self.large_file_mb = config.get("large_file_threshold_mb", 100)

        self.protected_folders = set(config.get("protected_folders", []))
        self.old_folder_mapping = config.get("old_folder_mapping", {})

        # 删除模式
        raw_delete = config.get("delete_patterns", [])
        self.delete_patterns = [re.compile(p) for p in raw_delete]
        self.backup_extensions = set(config.get("backup_extensions", [".bak", ".backup"]))

        # 状态管理
        self.state_mgr = StateManager(self.state_file, self.rollback_dir)

        # 会话日志与统计
        self.session_logs = []
        self.unmatched_files = []
        self.rule_hit_counts = {}
        self.stats = {
            "scanned": 0, "organized": 0, "skipped": 0,
            "deleted": 0, "errors": 0, "archived": 0, "unmatched": 0,
            "content_analyzed": 0,
        }

        # 内容提取器和文件名分析器
        max_content_size = self.content_analysis_rules.get("max_file_size_mb", 10)
        self.content_extractor = ContentExtractor(max_size_mb=max_content_size)
        self.filename_analyzer = FilenameAnalyzer()

        # 日志配置
        self._setup_logging()

    @property
    def rules_name(self) -> str:
        """当前规则集名称"""
        return self.rules.get("name", "未命名规则")

    @property
    def rules_version(self) -> str:
        """当前规则版本"""
        return self.rules.get("version", "未知版本")

    # ----------------------------------------------------------
    # 日志记录
    # ----------------------------------------------------------

    def _log(self, action: str, src: Path, dst: Path = None, status: str = "info",
             msg: str = "", rule: str = "", priority: int = 0, confidence: float = 0.0,
             method: str = ""):
        """记录会话日志条目"""
        try:
            source_rel = str(src.relative_to(self.source_dir))
        except ValueError:
            source_rel = str(src)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source": str(src),
            "source_rel": source_rel,
            "target": str(dst) if dst else None,
            "status": status,
            "rule": rule,
            "priority": priority,
            "confidence": confidence,
            "method": method,
            "message": msg,
        }
        self.session_logs.append(entry)

        if rule and status in ("success", "preview"):
            self.rule_hit_counts[rule] = self.rule_hit_counts.get(rule, 0) + 1

        icon = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️", "preview": "👁️"}.get(status, "•")
        priority_label = {1: "P1业务", 2: "P2关键词", 3: "P3内容", 4: "P4扩展名", 0: "兜底"}.get(priority, "")
        line = f"{icon} [{action}] {src.name}"
        if dst:
            try:
                line += f"\n      → {dst.relative_to(self.target_dir)}"
            except ValueError:
                line += f"\n      → {dst}"
        if rule:
            line += f"\n      规则: {rule} ({priority_label})" if priority_label else f"\n      规则: {rule}"
        if confidence > 0:
            line += f" 置信度:{confidence:.0%}"
        if method:
            line += f" 方法:{method}"
        if msg:
            line += f"\n      ({msg})"
        self.logger.info(line)

    def _save_log(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.log_dir / f"session_{ts}.json"
        rule_hit_stats = sorted(
            self.rule_hit_counts.items(), key=lambda x: x[1], reverse=True
        )
        data = {
            "timestamp": datetime.now().isoformat(),
            "rules_name": self.rules_name,
            "rules_version": self.rules_version,
            "dry_run": self.dry_run,
            "stats": self.stats,
            "rule_hit_stats": rule_hit_stats,
            "unmatched_files": self.unmatched_files[:200],
            "entries": self.session_logs[-200:],
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"会话日志已保存: {log_path}")
        return log_path

    # ----------------------------------------------------------
    # 初始化方法
    # ----------------------------------------------------------

    def _setup_logging(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_dir / f"organizer_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_path, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("organizer")

    # ----------------------------------------------------------
    # 目录结构初始化
    # ----------------------------------------------------------

    def setup_directory_structure(self):
        """在目标目录中初始化标准目录结构"""
        base = self.target_dir
        self.logger.info(f"=== 初始化标准目录结构 ({self.rules_name}) → {base} ===")
        created = 0
        for rel in self.standard_dirs:
            # 统一用 Path 处理路径分隔符
            full = base / rel.replace("\\", "/")
            if not full.exists():
                if not self.dry_run:
                    full.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"{'[预览]' if self.dry_run else '[创建]'} {rel}")
                created += 1
        self.logger.info(f"完成：{'预览' if self.dry_run else '已创建'} {created} 个目录")

    # ----------------------------------------------------------
    # 特殊文件判断
    # ----------------------------------------------------------

    def _should_delete(self, filename: str) -> bool:
        for pat in self.delete_patterns:
            if pat.search(filename):
                return True
        return False

    def _is_backup_file(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.backup_extensions

    def _is_large_file(self, filepath: Path) -> bool:
        try:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            return size_mb > self.large_file_mb
        except Exception:
            return False

    def _is_protected(self, filepath: Path) -> bool:
        try:
            rel = filepath.relative_to(self.source_dir)
        except ValueError:
            return False
        for part in rel.parts:
            if part in self.protected_folders:
                return True
        return False

    # ----------------------------------------------------------
    # 单文件处理
    # ----------------------------------------------------------

    def process_file(self, filepath: Path):
        filepath = Path(filepath)
        filename = filepath.name
        self.stats["scanned"] += 1

        # 保护目录检查
        if self._is_protected(filepath):
            self._log("skip", filepath, msg="保护目录")
            self.stats["skipped"] += 1
            return

        # 隐藏/临时文件 -> 删除
        if self._should_delete(filename):
            if self.dry_run:
                self._log("preview-delete", filepath, status="preview", msg="临时/系统文件")
            else:
                try:
                    filepath.unlink()
                    self._log("delete", filepath, status="success", msg="临时/系统文件")
                except Exception as e:
                    self._log("error", filepath, status="error", msg=str(e))
            self.stats["deleted"] += 1
            return

        # .bak/.backup -> 归档备份目录
        if self._is_backup_file(filepath):
            result = ClassificationResult(
                target_path="99-归档/01-临时文件/备份文件",
                rule_name="备份文件规则",
                priority=0,
                confidence=1.0,
                analysis_method="extension"
            )
            self._move_file(filepath, result)
            self.stats["archived"] += 1
            return

        # 大文件 -> 大文件待处理
        if self._is_large_file(filepath):
            result = ClassificationResult(
                target_path="99-归档/01-临时文件/大文件待处理",
                rule_name="大文件规则",
                priority=0,
                confidence=1.0,
                analysis_method="size"
            )
            self._move_file(filepath, result)
            self.stats["archived"] += 1
            return

        # 已处理过（基于哈希）
        fh = compute_hash(filepath)
        if fh and self.state_mgr.is_processed(fh):
            self._log("skip", filepath, msg="已处理过（哈希匹配）")
            self.stats["skipped"] += 1
            return

        # 四级分类
        result = self._classify(filepath)

        # 已在正确位置
        expected = self.source_dir / result.target_path.replace("\\", "/") / filename
        if filepath.resolve() == expected.resolve():
            self._log("skip", filepath, msg="已在正确位置")
            self.stats["skipped"] += 1
            return

        # 追踪未匹配文件（兜底或扩展名兜底）
        if result.priority <= 0 or result.priority >= 4:
            try:
                src_rel = str(filepath.relative_to(self.source_dir))
            except ValueError:
                src_rel = str(filepath)
            self.unmatched_files.append({
                "filename": filename,
                "source_rel": src_rel,
                "target_rel": result.target_path,
                "rule": result.rule_name,
                "priority": result.priority,
                "confidence": result.confidence,
            })
            self.stats["unmatched"] += 1

        # 归档类目标保留原始路径结构
        is_archive = result.target_path.startswith("99-归档")
        self._move_file(filepath, result, preserve_path=is_archive)

    # ----------------------------------------------------------
    # 分类决策（四级优先级）
    # ----------------------------------------------------------

    def _classify(self, filepath: Path) -> ClassificationResult:
        """四级优先级分类（委托给 classifier.py）"""
        from classifier import classify_file

        result = classify_file(
            filepath=filepath,
            source_dir=self.source_dir,
            business_domain_rules=self.business_domain_rules,
            infoproject_stage_rules=self.infoproject_stage_rules,
            keyword_rules=self.keyword_rules,
            extension_rules=self.extension_rules,
            content_extractor=self.content_extractor,
            enable_content_analysis=self.enable_content_analysis,
            content_analysis_rules=self.content_analysis_rules,
        )

        if result.analysis_method == "content":
            self.stats["content_analyzed"] += 1

        return result

    # ----------------------------------------------------------
    # 文件移动/复制
    # ----------------------------------------------------------

    def _move_file(self, src: Path, result: ClassificationResult, preserve_path: bool = False):
        """将文件移动到目标位置（委托给 state.py）"""
        move_file(
            src=src,
            result=result,
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            dry_run=self.dry_run,
            keep_original=self.keep_original,
            state_mgr=self.state_mgr,
            log_fn=self._log,
            stats=self.stats,
        )

    # ----------------------------------------------------------
    # 批量扫描整理
    # ----------------------------------------------------------

    def scan_and_organize(self, incremental: bool = True):
        """主入口：扫描并整理文件"""
        mode_label = "预览模式" if self.dry_run else "执行模式"
        scan_label = f"增量({self.scan_days}天)" if incremental else "全量"
        content_label = "启用内容分析" if self.enable_content_analysis else "禁用内容分析"

        self.logger.info("=" * 60)
        self.logger.info(f"  文件自动整理引擎 v4.0")
        self.logger.info(f"  规则集 : {self.rules_name} ({self.rules_version})")
        self.logger.info(f"  源目录 : {self.source_dir}")
        if self.target_dir != self.source_dir:
            self.logger.info(f"  目标目录: {self.target_dir}")
        self.logger.info(f"  模式   : {mode_label} | 扫描: {scan_label} | {content_label}")
        self.logger.info("=" * 60)

        if not self.source_dir.exists():
            self.logger.error(f"源目录不存在: {self.source_dir}")
            return

        if self.target_dir != self.source_dir and not self.target_dir.exists():
            if self.dry_run:
                self.logger.warning(f"[预览] 目标目录不存在，将创建: {self.target_dir}")
            else:
                self.target_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"已创建目标目录: {self.target_dir}")

        cutoff = (datetime.now() - timedelta(days=self.scan_days)) if incremental else None

        for fp in self.source_dir.rglob("*"):
            if not fp.is_file():
                continue
            if cutoff:
                mtime = datetime.fromtimestamp(fp.stat().st_mtime)
                if mtime < cutoff:
                    continue
            self.process_file(fp)

        self._report_stats()

        if not self.dry_run:
            self.state_mgr.save()
        self._save_log()

    def _report_stats(self):
        self.logger.info("=" * 60)
        self.logger.info(f"  扫描: {self.stats['scanned']}  |  "
                         f"整理: {self.stats['organized']}  |  "
                         f"删除: {self.stats['deleted']}  |  "
                         f"跳过: {self.stats['skipped']}  |  "
                         f"错误: {self.stats['errors']}")
        self.logger.info(f"  归档: {self.stats['archived']}  |  "
                         f"未匹配: {self.stats['unmatched']}  |  "
                         f"内容分析: {self.stats['content_analyzed']}")
        self.logger.info("=" * 60)

        if self.rule_hit_counts:
            self.logger.info(f"📊 规则命中率统计（共 {len(self.rule_hit_counts)} 条规则被命中）:")
            sorted_rules = sorted(self.rule_hit_counts.items(), key=lambda x: x[1], reverse=True)
            for rule_name, count in sorted_rules[:15]:
                self.logger.info(f"  {count:4d} 次  {rule_name}")
            if len(sorted_rules) > 15:
                self.logger.info(f"  ... 还有 {len(sorted_rules) - 15} 条未显示")
            self.logger.info("")

        if self.unmatched_files:
            self.logger.info(f"📋 未匹配/兜底文件 ({len(self.unmatched_files)} 个，显示前 20):")
            for i, uf in enumerate(self.unmatched_files[:20]):
                conf_str = f" 置信度:{uf.get('confidence', 0):.0%}" if uf.get('confidence') else ""
                self.logger.info(f"  {i+1}. {uf['source_rel']} → {uf['target_rel']} [{uf['rule']}]{conf_str}")
            if len(self.unmatched_files) > 20:
                self.logger.info(f"  ... 还有 {len(self.unmatched_files) - 20} 个未显示")
            self.logger.info("")

    # ----------------------------------------------------------
    # 重复文件处理
    # ----------------------------------------------------------

    def handle_duplicates(self):
        """检测并处理重复文件"""
        self.logger.info("=== 重复文件检测 ===")
        dups = find_duplicates(
            self.source_dir,
            is_protected_fn=self._is_protected,
            is_file_fn=lambda p: p.is_file(),
        )
        if not dups:
            self.logger.info("未发现重复文件")
            return

        today = datetime.now().strftime("%Y%m%d")
        for (name, size), paths in dups.items():
            paths_sorted = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
            keep = paths_sorted[0]
            for dup in paths_sorted[1:]:
                new_name = f"{dup.stem}_duplicate_{today}{dup.suffix}"
                backup_path = self.target_dir / f"99-归档/01-临时文件/备份文件" / new_name
                if self.dry_run:
                    self.logger.info(f"[预览] 重复文件 {dup} -> {backup_path}")
                else:
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dup), str(backup_path))
                    self.logger.info(f"[移动] 重复文件 {dup.name} -> 备份目录")
        self.logger.info(f"重复文件处理完成，发现 {len(dups)} 组")

    # ----------------------------------------------------------
    # 回滚
    # ----------------------------------------------------------

    def rollback_last_session(self):
        """回滚最后一次会话操作"""
        rollback_last_session(self.log_dir, self.dry_run, self.logger)
        self.state_mgr.clear()

    # ----------------------------------------------------------
    # 规则预览（供 Web UI 使用）
    # ----------------------------------------------------------

    def preview_classify(self, filepath: str) -> dict:
        """对单个路径进行分类预览，返回结果（不执行任何操作）"""
        p = Path(filepath)
        if not p.is_absolute():
            p = self.source_dir / p
        if not p.exists():
            return {"error": f"文件不存在: {filepath}"}

        result = self._classify(p)
        filename_analysis = self.filename_analyzer.analyze(p.name)

        return {
            "file": str(p),
            "filename": p.name,
            "target": str(self.target_dir / result.target_path.replace("\\", "/")),
            "target_relative": result.target_path,
            "rule": result.rule_name,
            "priority": result.priority,
            "confidence": result.confidence,
            "method": result.analysis_method,
            "matched_keywords": result.matched_keywords,
            "filename_analysis": filename_analysis,
        }

    def get_rules_summary(self) -> dict:
        """返回当前规则的摘要信息（供 Web UI 展示）"""
        return {
            "name": self.rules_name,
            "version": self.rules_version,
            "description": self.rules.get("description", ""),
            "business_domain_count": len(self.business_domain_rules),
            "infoproject_stage_count": len(self.infoproject_stage_rules),
            "keyword_count": len(self.keyword_rules),
            "extension_count": len(self.extension_rules),
            "standard_dir_count": len(self.standard_dirs),
            "content_analysis_enabled": self.enable_content_analysis,
            "content_analysis_supported": len(self.content_analysis_rules.get("supported_extensions", [])),
        }


# 保持向后兼容的别名
get_default_rules = get_default_rules
save_default_template = save_default_template
load_rules = load_rules
