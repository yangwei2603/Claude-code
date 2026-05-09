"""
回滚管理器 - 回滚整理操作
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class RollbackManager:
    """回滚管理器"""

    def __init__(self, rollback_dir: Path):
        self.rollback_dir = Path(rollback_dir)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

    def save_operation(self, session_id: str, entries: List[dict]):
        """
        保存操作记录用于回滚

        Args:
            session_id: 会话ID
            entries: 操作记录列表
        """
        rollback_file = self.rollback_dir / f"rollback_{session_id}.json"

        import json
        with open(rollback_file, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "entries": entries,
            }, f, ensure_ascii=False, indent=2)

    def rollback(self, session_id: str) -> int:
        """
        回滚指定会话的操作

        Args:
            session_id: 会话ID

        Returns:
            回滚的文件数量
        """
        rollback_file = self.rollback_dir / f"rollback_{session_id}.json"
        if not rollback_file.exists():
            print(f"未找到回滚记录: {session_id}")
            return 0

        import json
        with open(rollback_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("entries", [])
        restored = 0

        # 逆序回滚（先移动的最后处理）
        for entry in reversed(entries):
            if entry.get("action") not in ("move", "copy"):
                continue

            src = Path(entry.get("target"))
            dst = Path(entry.get("source"))

            if src.exists():
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    restored += 1
                    print(f"✅ 回滚: {src.name} → {dst.parent}")
                except Exception as e:
                    print(f"❌ 回滚失败: {src.name} - {e}")

        # 删除回滚记录
        rollback_file.unlink()

        return restored

    def list_sessions(self) -> List[dict]:
        """列出可回滚的会话"""
        sessions = []
        for f in sorted(self.rollback_dir.glob("rollback_*.json"), reverse=True):
            import json
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "timestamp": data.get("timestamp"),
                        "entries_count": len(data.get("entries", [])),
                    })
            except Exception:
                pass
        return sessions
