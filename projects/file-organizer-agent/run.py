#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字化转型办公室 - 文件自动整理 Agent
统一 CLI 入口

用法:
  python run.py --preview              # 预览模式（默认，不移动文件）
  python run.py --execute              # 执行整理（实际移动文件）
  python run.py --execute --full       # 全量整理（不限修改时间）
  python run.py --execute --days 3     # 整理最近3天修改的文件
  python run.py --setup                # 初始化标准目录结构（预览）
  python run.py --setup --execute      # 初始化标准目录结构（执行创建）
  python run.py --duplicates           # 检测重复文件（预览）
  python run.py --duplicates --execute # 处理重复文件（实际移动）
  python run.py --rollback             # 回滚上一次整理操作
  python run.py --watch                # 守护模式：持续轮询（按config.json间隔）
  python run.py --config other.json    # 指定配置文件
  python run.py --source D:\\mydir     # 临时指定源目录（覆盖配置文件）
  python run.py --target D:\\output    # 临时指定目标目录（默认=源目录内）
  python run.py --template my-rule     # 指定规则模板名称（templates/*.json）
  python run.py --stats                # 查看运行统计
  python run.py --web                 # 启动 Web 管理界面
  python run.py --web --port 5001     # 指定端口启动 Web 界面
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime


# ============================================================
# 默认配置（config.json 不存在时使用）
# ============================================================
DEFAULT_CONFIG = {
    "source_dir": r"C:\数字化办公室SVN",
    "state_file": r"state\organizer_state.json",
    "log_dir": "logs",
    "rollback_dir": r"state\rollback",
    "dry_run": True,
    "keep_original": False,
    "scan_days": 7,
    "watch_interval_seconds": 300,
    "large_file_threshold_mb": 100,
    "protected_folders": [
        ".svn", ".git", ".idea", "__pycache__",
        ".organizer", "node_modules", ".vscode",
        "logs", "state"
    ],
    "delete_patterns": [
        r"^~\$",
        r"\.svn-base$",
        r"\.tmp$",
        r"\.temp$",
        r"^\.DS_Store$",
        r"^Thumbs\.db$"
    ],
    "backup_extensions": [".bak", ".backup"],
    "standard_dirs": [
        r"00-战略与架构\00-数字化战略",
        r"00-战略与架构\01-业务架构",
        r"01-知识库管理\00-知识体系",
        r"01-知识库管理\01-最佳实践",
        r"01-知识库管理\02-培训学习",
        r"01-知识库管理\03-规章制度",
        r"01-知识库管理\04-问答知识库",
        r"02-信息化项目",
        r"03-数字化项目\00-客舱数字化",
        r"03-数字化项目\01-飞行数字化",
        r"03-数字化项目\02-维修数字化",
        r"03-数字化项目\03-司库管理数字化",
        r"03-数字化项目\04-共享数字化",
        r"03-数字化项目\05-核算与报告数字化",
        r"03-数字化项目\06-机供品数字化",
        r"03-数字化项目\07-起降数字化",
        r"03-数字化项目\08-数据分析报告\00-经营分析",
        r"03-数字化项目\08-数据分析报告\01-专题分析",
        r"03-数字化项目\08-数据分析报告\02-数据报表",
        r"04-创新应用\00-Agent智能体",
        r"04-创新应用\01-流程自动化",
        r"04-创新应用\02-智能分析",
        r"05-数据资产\00-数据标准",
        r"05-数据资产\01-数据治理",
        r"05-数据资产\02-数据开发",
        r"05-数据资产\03-数据集成",
        r"05-数据资产\04-数据安全",
        r"06-团队与运营\00-团队建设",
        r"06-团队与运营\01-沟通协作\周报月报",
        r"06-团队与运营\01-沟通协作\会议纪要",
        r"06-团队与运营\02-资源库",
        r"06-团队与运营\03-通知公告",
        r"06-团队与运营\04-调研访谈",
        r"07-商务与采购\00-合同协议",
        r"07-商务与采购\01-供应商管理",
        r"08-财务文档\00-预算决算",
        r"08-财务文档\01-票据报销",
        r"08-财务文档\02-收付款",
        r"09-人事行政\00-招聘入职",
        r"09-人事行政\01-考勤假期",
        r"09-人事行政\02-薪酬福利",
        r"09-人事行政\03-绩效考核",
        r"10-项目管理\00-项目里程碑",
        r"10-项目管理\01-变更管理",
        r"10-项目管理\02-评审记录",
        r"10-项目管理\03-项目计划",
        r"99-归档\00-历史项目",
        r"99-归档\01-临时文件\备份文件",
        r"99-归档\01-临时文件\大文件待处理",
    ],
}


# ============================================================
# 工具函数
# ============================================================

def load_config(config_path: Path) -> dict:
    """加载 JSON 配置文件，不存在时使用默认值"""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 过滤以 _ 开头的注释键
        cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
        return cfg
    return DEFAULT_CONFIG.copy()


def print_banner():
    print("=" * 60)
    print("  数字化转型办公室 - 文件自动整理 Agent v5.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def print_stats(stats: dict, dry_run: bool):
    mode = "预览模式" if dry_run else "执行模式"
    print(f"\n[{mode}] 整理完成")
    print(f"  扫描文件 : {stats.get('scanned', 0)}")
    print(f"  待整理   : {stats.get('organized', 0)}")
    print(f"  删除文件 : {stats.get('deleted', 0)}")
    print(f"  已跳过   : {stats.get('skipped', 0)}")
    print(f"  错误     : {stats.get('errors', 0)}")


def show_stats(log_dir: Path):
    """汇总历史统计信息"""
    logs = sorted(log_dir.glob("session_*.json"), reverse=True)
    if not logs:
        print("暂无运行记录")
        return
    print(f"\n最近 {min(5, len(logs))} 次运行记录：")
    print("-" * 60)
    for lf in logs[:5]:
        with open(lf, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("timestamp", "")[:19]
        s = data.get("stats", {})
        mode = "预览" if data.get("dry_run") else "执行"
        print(f"  [{ts}] [{mode}] 整理:{s.get('organized',0)} | "
              f"删除:{s.get('deleted',0)} | 错误:{s.get('errors',0)}")
    print("-" * 60)


# ============================================================
# 主函数
# ============================================================

def main():
    agent_dir = Path(__file__).parent

    parser = argparse.ArgumentParser(
        description="数字化转型办公室文件自动整理 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 模式开关
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--preview",    action="store_true", help="预览模式（默认，不移动文件）")
    mode_group.add_argument("--execute",    action="store_true", help="执行整理（实际移动文件）")
    mode_group.add_argument("--watch",      action="store_true", help="守护模式：持续轮询整理")
    mode_group.add_argument("--rollback",   action="store_true", help="回滚上一次整理")
    mode_group.add_argument("--stats",      action="store_true", help="查看运行统计")
    mode_group.add_argument("--web",        action="store_true", help="启动 Web 管理界面")

    # 功能选项
    parser.add_argument("--setup",      action="store_true",  help="初始化/检查标准目录结构")
    parser.add_argument("--duplicates", action="store_true",  help="检测并处理重复文件")
    parser.add_argument("--full",       action="store_true",  help="全量扫描（默认增量）")
    parser.add_argument("--days",       type=int, default=None, help="增量扫描天数（覆盖配置文件）")

    # 配置覆盖
    parser.add_argument("--config",   type=str, default=None, help="指定配置文件路径")
    parser.add_argument("--source",   type=str, default=None, help="临时指定源目录")
    parser.add_argument("--target",   type=str, default=None, help="临时指定目标目录（默认=源目录内）")
    parser.add_argument("--template", type=str, default=None,
                        help="指定规则模板名称，对应 templates/<name>.json")
    parser.add_argument("--port",     type=int, default=5000, help="Web 服务端口号（仅 --web 模式）")
    parser.add_argument("--host",     type=str, default="0.0.0.0", help="Web 服务监听地址（仅 --web 模式）")
    parser.add_argument("--rules",    type=str, default=None, help="传入 JSON 规则覆盖（如 '{\"keyword_rules\":[{\"keywords\":[\"合同\"],\"target\":\"07-商务与采购\\\\00-合同协议\"}]}')")
    parser.add_argument("--keep-original", action="store_true", help="保留原文件（复制模式，不移动）")

    args = parser.parse_args()

    # ---- 加载配置 ----
    config_path = Path(args.config) if args.config else agent_dir / "config.json"
    config = load_config(config_path)

    # 命令行覆盖配置
    if args.source:
        config["source_dir"] = args.source
    if args.target:
        config["target_dir"] = args.target
    if args.template:
        config["template"] = args.template
    if args.rules:
        try:
            rules_override = json.loads(args.rules)
            config["rules"] = rules_override
        except json.JSONDecodeError as e:
            print(f"[ERROR] --rules 参数 JSON 格式错误: {e}")
            return
    if args.keep_original:
        config["keep_original"] = True
    if args.days is not None:
        config["scan_days"] = args.days

    # 确定运行模式
    dry_run = not args.execute  # 只要没有 --execute 就是预览
    config["dry_run"] = dry_run

    # ---- Web 模式 ----
    if args.web:
        try:
            from web import run_web
        except ImportError:
            print("[ERROR] 启动 Web 模式需要安装 Flask 和 Flask-CORS：")
            print("  pip install flask flask-cors")
            return
        run_web(host=args.host, port=args.port)
        return

    # ---- Watch 模式 ----
    if args.watch:
        from scheduler import run_watch_mode
        print_banner()
        print(f"  ▶ Watch 模式（每 {config.get('watch_interval_seconds', 300)}s 执行一次）")
        run_watch_mode(config, agent_dir)
        return

    # ---- Stats 模式 ----
    if args.stats:
        log_dir = agent_dir / config.get("log_dir", "logs")
        print_banner()
        show_stats(log_dir)
        return

    # ---- 导入引擎 ----
    from organizer import DocumentOrganizer

    print_banner()
    mode_str = "执行模式" if args.execute else "预览模式（使用 --execute 执行实际整理）"
    print(f"  模式: {mode_str}")
    print(f"  源目录: {config['source_dir']}")
    if config.get("target_dir"):
        print(f"  目标目录: {config['target_dir']}")
    if config.get("template"):
        print(f"  规则模板: {config['template']}")
    if config.get("rules"):
        print(f"  规则覆盖: 是（通过 --rules 传入）")
    if config.get("keep_original"):
        print(f"  文件模式: 复制（保留原文件）")
    print()

    organizer = DocumentOrganizer(config, agent_dir=agent_dir)

    # ---- Rollback ----
    if args.rollback:
        organizer.rollback_last_session()
        return

    # ---- Setup：初始化目录结构 ----
    if args.setup:
        organizer.setup_directory_structure()
        if not dry_run:
            print("\n[OK] 标准目录结构初始化完成")
        else:
            print("\n[预览] 以上目录将被创建（使用 --setup --execute 执行）")
        return

    # ---- Duplicates ----
    if args.duplicates:
        organizer.handle_duplicates()
        return

    # ---- 默认：扫描整理 ----
    incremental = not args.full
    organizer.scan_and_organize(incremental=incremental)
    print_stats(organizer.stats, dry_run)

    if dry_run:
        print("\n💡 提示：以上为预览结果，使用 --execute 执行实际整理")


if __name__ == "__main__":
    main()
