"""
日志工具 - 设置和管理日志
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "file_organizer",
    log_dir: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        level: 日志级别

    Returns:
        配置好的 Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"organizer_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class SessionLogger:
    """会话日志记录器"""

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.entries = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log(self, entry: dict):
        """记录会话条目"""
        entry["timestamp"] = datetime.now().isoformat()
        entry["session_id"] = self.session_id
        self.entries.append(entry)

    def save(self, metadata: dict = None) -> Path:
        """保存会话日志"""
        log_path = self.log_dir / f"session_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "entries": self.entries,
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return log_path

    def load(self, session_id: str) -> dict:
        """加载会话日志"""
        log_path = self.log_dir / f"session_{session_id}.json"
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
