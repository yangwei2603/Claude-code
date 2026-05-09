"""
状态管理器 - 管理整理状态和历史
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from organizer.constants import FILE_HASH_CHUNK_SIZE


class StateManager:
    """状态管理器"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "processed_files": {},
            "last_scan": None,
            "last_session": None,
        }

    def save(self):
        """保存状态"""
        self.state["last_scan"] = datetime.now().isoformat()
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def mark_processed(self, filepath: Path, target: Path, rule: str, priority: int):
        """标记文件已处理"""
        fh = self._file_hash(filepath)
        if fh:
            self.state["processed_files"][fh] = {
                "original": str(filepath),
                "target": str(target),
                "time": datetime.now().isoformat(),
                "rule": rule,
                "priority": priority,
            }

    def is_processed(self, filepath: Path) -> bool:
        """检查文件是否已处理"""
        fh = self._file_hash(filepath)
        return fh in self.state["processed_files"]

    def _file_hash(self, filepath: Path) -> str:
        """计算文件 MD5 哈希"""
        try:
            h = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(FILE_HASH_CHUNK_SIZE), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def get_last_session(self) -> Optional[str]:
        """获取最近会话ID"""
        return self.state.get("last_session")

    def set_last_session(self, session_id: str):
        """设置最近会话ID"""
        self.state["last_session"] = session_id

    def clear(self):
        """清除状态"""
        self.state = {
            "processed_files": {},
            "last_scan": None,
            "last_session": None,
        }
        self.save()
