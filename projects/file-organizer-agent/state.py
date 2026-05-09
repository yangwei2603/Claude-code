#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态管理模块 — 状态读/写、文件哈希、回滚
从 organizer.py 拆分出来：StateManager、_file_hash、_find_duplicates、_move_file
"""

import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from rules import ClassificationResult

# 魔法数字
HASH_CHUNK_SIZE = 65536
MAX_LOG_ENTRIES = 200


class StateManager:
    """管理处理状态和回滚会话"""

    def __init__(self, state_file: Path, rollback_dir: Path):
        self.state_file = Path(state_file)
        self.rollback_dir = Path(rollback_dir)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"processed_files": {}, "last_scan": None}

    def _save_state(self):
        self.state["last_scan"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def mark_processed(self, file_hash: str, original: str, target: str, rule: str, priority: int):
        """记录已处理文件"""
        self.state["processed_files"][file_hash] = {
            "original": original,
            "target": target,
            "time": datetime.now().isoformat(),
            "rule": rule,
            "priority": priority,
        }

    def is_processed(self, file_hash: str) -> bool:
        """检查文件是否已处理"""
        return file_hash in self.state["processed_files"]

    def save(self):
        """保存状态到文件"""
        self._save_state()

    def clear(self):
        """清空已处理记录（用于回滚后）"""
        self.state["processed_files"] = {}
        self._save_state()


def compute_hash(filepath: Path) -> str:
    """计算文件 MD5 哈希"""
    try:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def find_duplicates(source_dir: Path, is_protected_fn, is_file_fn) -> dict:
    """扫描重复文件（文件名 + 大小）"""
    seen = {}
    for fp in source_dir.rglob("*"):
        if not is_file_fn(fp) or is_protected_fn(fp):
            continue
        key = (fp.name, fp.stat().st_size)
        seen.setdefault(key, []).append(fp)
    return {k: v for k, v in seen.items() if len(v) > 1}


def move_file(
    src: Path,
    result: ClassificationResult,
    source_dir: Path,
    target_dir: Path,
    dry_run: bool,
    keep_original: bool,
    state_mgr: Optional[StateManager] = None,
    log_fn=None,
    stats: Optional[dict] = None,
) -> bool:
    """
    将文件移动到目标位置，处理冲突。
    返回是否成功。
    """
    target_rel = result.target_path

    effective_target_rel = target_rel
    target_dir_path = target_dir / effective_target_rel
    target_path = target_dir_path / src.name

    # 重名冲突处理
    if target_path.exists() and target_path.resolve() != src.resolve():
        stem, suffix = src.stem, src.suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir_path / f"{stem}_{counter:03d}{suffix}"
            counter += 1

    if dry_run:
        if log_fn:
            log_fn("preview", src, target_path, "preview",
                   f"规则: {result.rule_name}", result.rule_name,
                   result.priority, result.confidence, result.analysis_method)
        if stats is not None:
            stats["organized"] += 1
        return True

    try:
        target_dir_path.mkdir(parents=True, exist_ok=True)
        if keep_original:
            shutil.copy2(src, target_path)
            action = "copy"
        else:
            shutil.move(str(src), str(target_path))
            action = "move"

        if log_fn:
            log_fn(action, src, target_path, "success",
                   f"规则: {result.rule_name}", result.rule_name,
                   result.priority, result.confidence, result.analysis_method)

        if state_mgr and not keep_original:
            fh = compute_hash(target_path)
            if fh:
                state_mgr.mark_processed(
                    fh,
                    str(src),
                    str(target_path),
                    result.rule_name,
                    result.priority,
                )

        if stats is not None:
            stats["organized"] += 1
        return True

    except Exception as e:
        if log_fn:
            log_fn("error", src, status="error", msg=str(e))
        if stats is not None:
            stats["errors"] += 1
        return False


def rollback_last_session(log_dir: Path, dry_run: bool, logger=None):
    """回滚最后一次会话操作"""
    if dry_run:
        if logger:
            logger.warning("预览模式不支持回滚，请使用 --execute 模式后再回滚")
        return 0

    log_files = sorted(Path(log_dir).glob("session_*.json"), reverse=True)
    if not log_files:
        if logger:
            logger.warning("没有找到操作日志，无法回滚")
        return 0

    last_log = log_files[0]
    if logger:
        logger.info(f"回滚会话日志: {last_log.name}")

    with open(last_log, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    restored = 0
    for entry in reversed(entries):
        if entry["action"] not in ("move", "copy"):
            continue
        src = Path(entry["target"])
        dst = Path(entry["source"])
        if src.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                if logger:
                    logger.info(f"[回滚] {src.name} -> {dst.parent}")
                restored += 1
            except Exception as e:
                if logger:
                    logger.error(f"回滚失败: {src.name} - {e}")

    if logger:
        logger.info(f"回滚完成，已恢复 {restored} 个文件")
    return restored
