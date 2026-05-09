"""
文件整理器 - 整合规则分类和 LLM 智能分类
"""

import hashlib
import re
import shutil
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from rules.classifier import RuleBasedClassifier, ClassificationResult
from rules.rule_loader import RuleLoader
from llm.llm_classifier import LLMClassifier
from .content_extractor import ContentExtractor
from .constants import DEFAULT_LARGE_FILE_THRESHOLD_MB, BYTES_PER_MB


@dataclass
class OrganizerStats:
    """整理统计"""
    scanned: int = 0
    organized: int = 0
    skipped: int = 0
    deleted: int = 0
    errors: int = 0
    archived: int = 0
    unmatched: int = 0
    rule_matched: int = 0
    llm_matched: int = 0


class FileOrganizer:
    """
    文件整理器

    分类流程:
    1. 关键词规则分类 → 命中则直接归类
    2. LLM 智能分类（DeepSeek/Claude）→ 规则未命中时
    3. 扩展名兜底（LLM 不可用时）
    """

    def __init__(
        self,
        source_dir: str,
        target_dir: Optional[str] = None,
        rule_loader: Optional[RuleLoader] = None,
        use_llm: bool = True,
        dry_run: bool = True,
        keep_original: bool = False,
        scan_days: int = 7,
        large_file_threshold_mb: int = DEFAULT_LARGE_FILE_THRESHOLD_MB
    ):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir) if target_dir else self.source_dir

        # 规则和 LLM
        self.rule_loader = rule_loader or RuleLoader()
        self.rule_classifier = RuleBasedClassifier(self.rule_loader)
        self.llm_classifier = LLMClassifier() if use_llm else None
        self.content_extractor = ContentExtractor()

        # 运行参数
        self.dry_run = dry_run
        self.keep_original = keep_original
        self.scan_days = scan_days
        self.large_file_threshold_mb = large_file_threshold_mb

        # 保护和删除模式
        self.protected_folders = {".svn", ".git", ".idea", "__pycache__", "node_modules", ".vscode", "logs", "state"}
        self.delete_patterns = [
            r"^~\$",  # Office 临时文件
            r"\.svn-base$",
            r"\.tmp$",
            r"\.temp$",
            r"^\.DS_Store$",
            r"^Thumbs\.db$"
        ]
        self._delete_compiled = [re.compile(p) for p in self.delete_patterns]
        self.backup_extensions = {".bak", ".backup"}

        # 统计和状态
        self.stats = OrganizerStats()
        self.session_logs: List[Dict] = []
        self.unmatched_files: List[Dict] = []
        self.rule_hit_counts: Dict[str, int] = {}

    def organize(self, incremental: bool = True) -> OrganizerStats:
        """
        执行文件整理

        Args:
            incremental: 是否只扫描最近修改的文件

        Returns:
            OrganizerStats 统计信息
        """
        if not self.source_dir.exists():
            raise ValueError(f"源目录不存在: {self.source_dir}")

        # 确保目标目录存在
        if self.target_dir != self.source_dir and not self.target_dir.exists():
            if self.dry_run:
                print(f"[预览] 目标目录不存在，将创建: {self.target_dir}")
            else:
                self.target_dir.mkdir(parents=True, exist_ok=True)

        cutoff = (datetime.now() - timedelta(days=self.scan_days)) if incremental else None

        for filepath in self.source_dir.rglob("*"):
            if not filepath.is_file():
                continue

            # 增量扫描过滤
            if cutoff:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff:
                    continue

            self._process_file(filepath)

        return self.stats

    def _process_file(self, filepath: Path):
        """处理单个文件"""
        filename = filepath.name
        self.stats.scanned += 1

        # 1. 检查是否保护目录
        if self._is_protected(filepath):
            self._log("skip", filepath, msg="保护目录")
            self.stats.skipped += 1
            return

        # 2. 检查是否临时文件（删除）
        if self._should_delete(filename):
            if self.dry_run:
                self._log("preview-delete", filepath, msg="临时/系统文件")
            else:
                try:
                    filepath.unlink()
                    self._log("delete", filepath, msg="临时/系统文件")
                except Exception as e:
                    self._log("error", filepath, msg=str(e))
                    self.stats.errors += 1
            self.stats.deleted += 1
            return

        # 3. 检查备份文件
        if filepath.suffix.lower() in self.backup_extensions:
            result = ClassificationResult(
                target_path=os.path.join("99-归档", "01-临时文件", "备份文件"),
                rule_name="备份文件规则",
                priority=0,
                confidence=1.0,
                method="rule"
            )
            self._move_file(filepath, result)
            self.stats.archived += 1
            return

        # 4. 检查大文件
        if self._is_large_file(filepath):
            result = ClassificationResult(
                target_path=os.path.join("99-归档", "01-临时文件", "大文件待处理"),
                rule_name="大文件规则",
                priority=0,
                confidence=1.0,
                method="rule"
            )
            self._move_file(filepath, result)
            self.stats.archived += 1
            return

        # 5. 分类（规则优先）
        result = self._classify(filepath)

        # 6. 追踪未匹配
        if result.method == "extension":
            try:
                src_rel = str(filepath.relative_to(self.source_dir))
            except ValueError:
                src_rel = str(filepath)
            self.unmatched_files.append({
                "filename": filename,
                "source_rel": src_rel,
                "target_rel": result.target_path,
                "rule": result.rule_name,
                "confidence": result.confidence,
            })
            self.stats.unmatched += 1

        # 7. 执行移动/复制
        is_archive = result.target_path.startswith("99-归档")
        self._move_file(filepath, result, preserve_path=is_archive)

    def _classify(self, filepath: Path) -> ClassificationResult:
        """
        分类文件（四级优先级级联）

        P1: 关键词规则（不含业务领域）
        P2: LLM 智能分类
        P3: 内容分析
        P4: 扩展名兜底
        """
        result = self.rule_classifier.classify_cascade(
            filepath,
            llm_classifier=self.llm_classifier,
            content_extractor=self.content_extractor,
        )

        # 统计
        if result.method == "rule":
            self.stats.rule_matched += 1
        elif result.method == "llm":
            self.stats.llm_matched += 1

        self._record_rule_hit(result.rule_name)
        return result

    def _move_file(self, src: Path, result: ClassificationResult, preserve_path: bool = False):
        """移动或复制文件"""
        target_rel = result.target_path

        if preserve_path:
            try:
                src_rel_dir = src.relative_to(self.source_dir).parent
                if str(src_rel_dir) == ".":
                    effective_target_rel = target_rel
                else:
                    effective_target_rel = str(Path(target_rel) / src_rel_dir)
            except ValueError:
                effective_target_rel = target_rel
        else:
            effective_target_rel = target_rel

        target_dir = self.target_dir / effective_target_rel
        target_path = target_dir / src.name

        # 冲突处理
        if target_path.exists() and target_path.resolve() != src.resolve():
            stem, suffix = src.stem, src.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{counter:03d}{suffix}"
                counter += 1

        if self.dry_run:
            self._log("preview", src, target_path, result)
            self.stats.organized += 1
        else:
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                if self.keep_original:
                    shutil.copy2(src, target_path)
                    self._log("copy", src, target_path, result)
                else:
                    shutil.move(str(src), str(target_path))
                    self._log("move", src, target_path, result)
                self.stats.organized += 1
            except Exception as e:
                self._log("error", src, msg=str(e))
                self.stats.errors += 1

    def _is_protected(self, filepath: Path) -> bool:
        """检查是否在保护目录中"""
        try:
            rel = filepath.relative_to(self.source_dir)
        except ValueError:
            return False
        for part in rel.parts:
            if part in self.protected_folders:
                return True
        return False

    def _should_delete(self, filename: str) -> bool:
        """检查是否应该删除"""
        for compiled in self._delete_compiled:
            if compiled.search(filename):
                return True
        return False

    def _is_large_file(self, filepath: Path) -> bool:
        """检查是否是大文件"""
        try:
            size_mb = filepath.stat().st_size / BYTES_PER_MB
            return size_mb > self.large_file_threshold_mb
        except Exception:
            return False

    def _record_rule_hit(self, rule_name: str):
        """记录规则命中"""
        self.rule_hit_counts[rule_name] = self.rule_hit_counts.get(rule_name, 0) + 1

    def _log(self, action: str, src: Path, target: Path = None, result: ClassificationResult = None, msg: str = ""):
        """记录日志"""
        try:
            source_rel = str(src.relative_to(self.source_dir))
        except ValueError:
            source_rel = str(src)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source": str(src),
            "source_rel": source_rel,
            "target": str(target) if target else None,
            "rule": result.rule_name if result else None,
            "method": result.method if result else None,
            "message": msg,
        }
        self.session_logs.append(entry)

        # 控制台输出
        icon = {"success": "✅", "error": "❌", "warning": "⚠️", "preview": "👁️", "skip": "⏭️"}.get(action, "•")
        line = f"{icon} [{action}] {src.name}"
        if target:
            try:
                line += f" → {target.relative_to(self.target_dir)}"
            except ValueError:
                line += f" → {target}"
        if result:
            line += f" ({result.rule_name})"
        if msg:
            line += f" - {msg}"
        print(line)

    def preview_classify(self, filepath: str) -> dict:
        """预览单个文件的分类结果"""
        p = Path(filepath)
        if not p.is_absolute():
            p = self.source_dir / p
        if not p.exists():
            return {"error": f"文件不存在: {filepath}"}

        result = self._classify(p)

        return {
            "file": str(p),
            "filename": p.name,
            "target": str(self.target_dir / result.target_path),
            "target_relative": result.target_path,
            "rule": result.rule_name,
            "confidence": result.confidence,
            "method": result.method,
            "matched_keywords": result.matched_keywords,
        }

    def setup_directories(self):
        """创建标准目录结构"""
        created = 0
        for rel in self.rule_loader.standard_dirs:
            full = self.target_dir / rel
            if not full.exists():
                if not self.dry_run:
                    full.mkdir(parents=True, exist_ok=True)
                print(f"{'[预览]' if self.dry_run else '[创建]'} {rel}")
                created += 1
        print(f"\n完成：{'预览' if self.dry_run else '已创建'} {created} 个目录")

    def get_summary(self) -> dict:
        """获取统计摘要"""
        return {
            "source_dir": str(self.source_dir),
            "target_dir": str(self.target_dir),
            "stats": {
                "scanned": self.stats.scanned,
                "organized": self.stats.organized,
                "skipped": self.stats.skipped,
                "deleted": self.stats.deleted,
                "errors": self.stats.errors,
                "archived": self.stats.archived,
                "unmatched": self.stats.unmatched,
                "rule_matched": self.stats.rule_matched,
                "llm_matched": self.stats.llm_matched,
            },
            "rule_hits": sorted(self.rule_hit_counts.items(), key=lambda x: x[1], reverse=True)[:15],
        }

    def save_session_logs(self) -> str:
        """保存当前会话日志到磁盘，返回 session_id"""
        from datetime import datetime
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        from .rollback import RollbackHandler
        handler = RollbackHandler(Path("logs"))
        handler.save_session(session_id, self.session_logs)
        return session_id

    def rollback_last_session(self):
        """回滚最近一次操作"""
        from .rollback import RollbackHandler
        handler = RollbackHandler(Path("logs"))
        restored, session_id = handler.rollback_last()
        if session_id:
            print(f"回滚完成，已恢复 {restored} 个文件 (会话: {session_id})")
        else:
            print("没有找到可回滚的会话日志")

    def find_duplicates(self) -> Dict:
        """查找重复文件（按名称+大小分组）"""
        from .rollback import RollbackHandler
        handler = RollbackHandler(Path("logs"))
        return handler.find_duplicates(self.source_dir)

    def handle_duplicates(self):
        """检测并归档重复文件"""
        dups = self.find_duplicates()
        if not dups:
            print("未发现重复文件")
            return

        today = datetime.now().strftime("%Y%m%d")
        for (name, size), paths in dups.items():
            paths_sorted = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
            keep = paths_sorted[0]
            for dup in paths_sorted[1:]:
                new_name = f"{dup.stem}_duplicate_{today}{dup.suffix}"
                backup_dir = self.target_dir / "99-归档/01-临时文件/备份文件"
                backup_path = backup_dir / new_name
                if self.dry_run:
                    print(f"[预览] 重复文件 {dup.name} → {backup_path}")
                else:
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dup), str(backup_path))
                    print(f"[移动] 重复文件 {dup.name} → 备份目录")
            print(f"处理 {len(paths_sorted) - 1} 个重复文件 (保留: {keep.name})")
        print(f"重复文件处理完成，发现 {len(dups)} 组")
