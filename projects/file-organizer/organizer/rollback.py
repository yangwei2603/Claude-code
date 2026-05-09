"""回滚与重复文件处理器"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RollbackHandler:
    """操作回滚与重复文件检测"""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session_id: str, entries: List[dict]) -> Path:
        """保存会话日志到磁盘"""
        log_path = self.log_dir / f"session_{session_id}.json"
        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "entries": entries,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return log_path

    def list_sessions(self) -> List[dict]:
        """列出可回滚的会话"""
        sessions = []
        for f in sorted(self.log_dir.glob("session_*.json"), reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "timestamp": data.get("timestamp"),
                        "file": str(f),
                        "entries_count": len(data.get("entries", [])),
                    })
            except Exception:
                continue
        return sessions

    def rollback_last(self) -> Tuple[int, Optional[str]]:
        """回滚最近一次会话，返回 (恢复数量, session_id)"""
        log_files = sorted(self.log_dir.glob("session_*.json"), reverse=True)
        if not log_files:
            return 0, None

        last_log = log_files[0]
        with open(last_log, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("entries", [])
        session_id = data.get("session_id")
        restored = 0

        for entry in reversed(entries):
            if entry.get("action") not in ("move", "copy"):
                continue
            src = Path(entry.get("target", ""))
            dst = Path(entry.get("source", ""))
            if src.exists():
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    restored += 1
                except OSError as e:
                    print(f"[回滚失败] {src.name}: {e}")

        return restored, session_id

    def rollback_session(self, session_id: str) -> int:
        """回滚指定会话，返回恢复数量"""
        log_path = self.log_dir / f"session_{session_id}.json"
        if not log_path.exists():
            return 0

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("entries", [])
        restored = 0

        for entry in reversed(entries):
            if entry.get("action") not in ("move", "copy"):
                continue
            src = Path(entry.get("target", ""))
            dst = Path(entry.get("source", ""))
            if src.exists():
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    restored += 1
                except OSError as e:
                    print(f"[回滚失败] {src.name}: {e}")

        return restored

    def find_duplicates(self, directory: Path) -> Dict[Tuple[str, int], List[Path]]:
        """查找重复文件，返回 {(name, size): [paths]}"""
        files_by_key: Dict[Tuple[str, int], List[Path]] = {}

        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                stat = filepath.stat()
                key = (filepath.name, stat.st_size)
            except OSError:
                continue

            if key not in files_by_key:
                files_by_key[key] = []
            files_by_key[key].append(filepath)

        return {k: v for k, v in files_by_key.items() if len(v) > 1}

    @staticmethod
    def file_hash(filepath: Path, chunk_size: int = 65536) -> str:
        """计算文件 MD5"""
        h = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    h.update(chunk)
        except OSError:
            return ""
        return h.hexdigest()
