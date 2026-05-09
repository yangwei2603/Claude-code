#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时调度器 - 支持两种运行模式：
  1. --watch   : 内置轮询（永久运行，适用于服务器 / 后台守护）
  2. Windows任务计划程序直接调用 run.py（推荐，见 setup_task.ps1）
"""

import time
import logging
from datetime import datetime
from pathlib import Path


class OrganizerScheduler:
    """定时调度器：按固定间隔触发整理任务"""

    def __init__(self, organizer, interval_seconds: int = 300):
        """
        Args:
            organizer: DocumentOrganizer 实例
            interval_seconds: 扫描间隔（秒），默认 300s（5分钟）
        """
        self.organizer = organizer
        self.interval = interval_seconds
        self.logger = logging.getLogger("scheduler")
        self._running = False

    def start(self):
        """启动轮询守护模式（阻塞运行）"""
        self._running = True
        self.logger.info("=" * 60)
        self.logger.info(f"  调度器启动 - 轮询间隔: {self.interval}s")
        self.logger.info(f"  监控目录  : {self.organizer.source_dir}")
        self.logger.info(f"  按 Ctrl+C 停止")
        self.logger.info("=" * 60)

        try:
            while self._running:
                self._run_once()
                self._wait_next(self.interval)
        except KeyboardInterrupt:
            self.logger.info("\n调度器已手动停止")
        finally:
            self._running = False

    def stop(self):
        """停止调度器"""
        self._running = False

    def _run_once(self):
        """执行一次增量整理"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"\n[{now}] 开始增量扫描...")
        try:
            self.organizer.organize(incremental=True)
        except Exception as e:
            self.logger.error(f"整理过程出错: {e}", exc_info=True)

    def _wait_next(self, seconds: int):
        """等待下次触发，支持中断"""
        next_run = datetime.now().strftime("%H:%M:%S")
        self.logger.info(f"下次扫描: {seconds}s 后 | 当前: {next_run}")
        slept = 0
        while slept < seconds and self._running:
            time.sleep(1)
            slept += 1


def run_watch_mode(config: dict, agent_dir: Path):
    """
    启动 watch 模式的便捷入口（由 run.py 调用）

    Args:
        config: 配置字典
        agent_dir: agent 所在目录
    """
    from organizer import FileOrganizer

    # watch 模式强制 execute（否则没有意义）
    watch_config = config.copy()
    watch_config["dry_run"] = False

    organizer = FileOrganizer(
        source_dir=watch_config["source_dir"],
        target_dir=watch_config.get("target_dir") or None,
        dry_run=False,
        keep_original=watch_config.get("keep_original", False),
        scan_days=watch_config.get("scan_days", 7),
        large_file_threshold_mb=watch_config.get("large_file_threshold_mb", 100),
    )
    interval = config.get("watch_interval_seconds", 300)

    scheduler = OrganizerScheduler(organizer, interval_seconds=interval)
    scheduler.start()
