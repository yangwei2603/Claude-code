#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件智能整理器 - 统一入口
简化版 CLI，支持规则分类和 LLM 智能分类

用法:
  python main.py                              # 交互式引导
  python main.py --source ./files             # 预览整理
  python main.py --source ./files --execute   # 执行整理
  python main.py --source ./files --setup     # 创建目录结构
  python main.py --preview "文件路径"         # 预览单个文件分类
  python main.py --rollback                   # 回滚上次操作
  python main.py --stats                      # 查看统计
  python main.py --no-llm                    # 禁用 LLM（纯规则）
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from organizer import FileOrganizer
from rules.rule_loader import RuleLoader
from utils.rollback import RollbackManager


def print_banner():
    print("=" * 60)
    print("  文件智能整理器 - 规则优先 + LLM 智能分类")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


def print_stats(stats, dry_run: bool):
    """打印统计信息"""
    mode = "预览模式" if dry_run else "执行模式"
    print(f"\n[{mode}] 整理完成")

    # 支持 dataclass 和 dict
    if hasattr(stats, '__dataclass_fields__'):
        # dataclass
        print(f"  扫描文件 : {stats.scanned}")
        print(f"  整理文件 : {stats.organized}")
        print(f"  规则命中 : {stats.rule_matched}")
        print(f"  LLM 分类 : {stats.llm_matched}")
        print(f"  跳过     : {stats.skipped}")
        print(f"  删除     : {stats.deleted}")
        print(f"  归档     : {stats.archived}")
        print(f"  错误     : {stats.errors}")
    else:
        # dict
        print(f"  扫描文件 : {stats.get('scanned', 0)}")
        print(f"  整理文件 : {stats.get('organized', 0)}")
        print(f"  规则命中 : {stats.get('rule_matched', 0)}")
        print(f"  LLM 分类 : {stats.get('llm_matched', 0)}")
        print(f"  跳过     : {stats.get('skipped', 0)}")
        print(f"  删除     : {stats.get('deleted', 0)}")
        print(f"  归档     : {stats.get('archived', 0)}")
        print(f"  错误     : {stats.get('errors', 0)}")


def interactive_mode():
    """交互式引导模式"""
    print_banner()
    print("\n📁 交互模式 - 请按提示输入\n")

    # 源目录
    source = input("请输入源目录路径（或直接回车使用当前目录）: ").strip()
    if not source:
        source = os.getcwd()
    else:
        # 处理 Windows 路径
        source = source.replace("\\", "/")

    if not Path(source).exists():
        print(f"❌ 目录不存在: {source}")
        return

    # 目标目录
    target = input("请输入目标目录路径（直接回车=与源目录相同）: ").strip().replace("\\", "/")
    if not target:
        target = source

    # 模式
    mode = input("\n请选择模式:\n  1. 预览（不移动文件）\n  2. 执行（实际移动）\n请选择 [1/2]: ").strip()

    execute = mode == "2"
    dry_run = not execute

    # LLM
    use_llm = input("\n是否启用 LLM 智能分类? [Y/n]: ").strip().lower() != "n"
    if use_llm and not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️ 未设置 ANTHROPIC_API_KEY，LLM 将被禁用")
        use_llm = False

    print(f"\n{'='*60}")
    print(f"源目录: {source}")
    print(f"目标目录: {target}")
    print(f"模式: {'执行' if execute else '预览'}")
    print(f"LLM: {'启用' if use_llm else '禁用'}")
    print(f"{'='*60}\n")

    confirm = input("确认开始整理? [Y/n]: ").strip().lower()
    if confirm and confirm != 'y':
        print("已取消")
        return

    # 执行整理
    organizer = FileOrganizer(
        source_dir=source,
        target_dir=target if target != source else None,
        use_llm=use_llm,
        dry_run=dry_run,
    )

    print("\n开始整理...\n")
    organizer.organize(incremental=False)
    print_stats(organizer.stats, dry_run)

    # 显示未匹配文件
    if organizer.unmatched_files:
        print(f"\n📋 未匹配文件 ({len(organizer.unmatched_files)} 个):")
        for uf in organizer.unmatched_files[:10]:
            print(f"  • {uf['filename']} → {uf['target_rel']}")
        if len(organizer.unmatched_files) > 10:
            print(f"  ... 还有 {len(organizer.unmatched_files) - 10} 个")

    if dry_run:
        print("\n💡 提示：以上为预览结果，使用 --execute 执行实际整理")


def main():
    parser = argparse.ArgumentParser(
        description="文件智能整理器 - 规则优先 + LLM 智能分类",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # 位置参数
    parser.add_argument("source", nargs="?", type=str, default=None,
                        help="源目录路径（位置参数）")
    parser.add_argument("-s", "--source-dir", dest="source_dir", type=str, default=None,
                        help="源目录路径")

    # 模式开关
    parser.add_argument("--preview", action="store_true",
                        help="预览模式（不移动文件）")
    parser.add_argument("--execute", action="store_true",
                        help="执行模式（实际移动文件）")
    parser.add_argument("--setup", action="store_true",
                        help="创建标准目录结构")
    parser.add_argument("--rollback", action="store_true",
                        help="回滚上次操作")
    parser.add_argument("--stats", action="store_true",
                        help="查看历史统计")
    parser.add_argument("--interactive", action="store_true",
                        help="交互式引导模式")

    # 单文件预览
    parser.add_argument("--preview-file", type=str,
                        help="预览单个文件的分类结果")

    # 配置选项
    parser.add_argument("--target", type=str, default=None,
                        help="目标目录（默认与源相同）")
    parser.add_argument("--days", type=int, default=7,
                        help="增量扫描天数（默认7天）")
    parser.add_argument("--full", action="store_true",
                        help="全量扫描（不限时间）")
    parser.add_argument("--no-llm", action="store_true",
                        help="禁用 LLM 智能分类（纯规则）")
    parser.add_argument("--keep-original", action="store_true",
                        help="保留原文件（复制模式）")
    parser.add_argument("--config", type=str,
                        help="配置文件路径")

    # 日志目录
    parser.add_argument("--log-dir", type=str, default="logs",
                        help="日志目录")

    args = parser.parse_args()

    # 交互模式
    if args.interactive or (not any([args.source, args.source_dir, args.preview_file, args.stats,
                                      args.rollback, args.setup])):
        interactive_mode()
        return

    print_banner()

    # 确定源目录
    source = args.source or args.source_dir or os.getcwd()

    # 确定模式
    dry_run = not args.execute

    # 回滚模式
    if args.rollback:
        rollback_dir = Path(__file__).parent / "state" / "rollback"
        manager = RollbackManager(rollback_dir)
        sessions = manager.list_sessions()
        if not sessions:
            print("没有可回滚的会话")
            return
        print("\n可回滚的会话:")
        for i, s in enumerate(sessions[:5], 1):
            print(f"  {i}. {s['session_id']} ({s['entries_count']} 个文件)")
        choice = input("\n请选择会话编号，或直接回车取消: ").strip()
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(sessions):
                    restored = manager.rollback(sessions[idx]["session_id"])
                    print(f"\n✅ 已回滚 {restored} 个文件")
            except ValueError:
                print("无效选择")
        return

    # 统计模式
    if args.stats:
        log_dir = Path(__file__).parent / args.log_dir
        if not log_dir.exists():
            print("暂无运行记录")
            return
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
            entries = data.get("entries", [])
            moves = sum(1 for e in entries if e.get("action") in ("move", "copy"))
            print(f"  [{ts}] 整理: {moves} | 总操作: {len(entries)}")
        print("-" * 60)
        return

    # 单文件预览
    if args.preview_file:
        organizer = FileOrganizer(
            source_dir=source,
            target_dir=args.target,
            use_llm=not args.no_llm,
            dry_run=True,
        )
        result = organizer.preview_classify(args.preview_file)
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"\n📄 文件: {result['filename']}")
            print(f"📍 目标: {result['target_relative']}")
            print(f"📏 方法: {result['method']}")
            print(f"🎯 规则: {result['rule']}")
            print(f"📊 置信度: {result['confidence']:.0%}")
        return

    # 创建整理器
    organizer = FileOrganizer(
        source_dir=source,
        target_dir=args.target,
        use_llm=not args.no_llm,
        dry_run=dry_run,
        keep_original=args.keep_original,
        scan_days=args.days if not args.full else 99999,
    )

    # 设置目录结构
    if args.setup:
        organizer.setup_directories()
        return

    # 执行整理
    print(f"\n📂 源目录: {source}")
    if args.target:
        print(f"📂 目标目录: {args.target}")
    print(f"🔧 模式: {'执行' if args.execute else '预览'}")
    print(f"🤖 LLM: {'启用' if not args.no_llm else '禁用'}")
    print(f"📅 扫描: {'全量' if args.full else f'最近{args.days}天'}")
    print()

    organizer.organize(incremental=not args.full)
    print_stats(organizer.stats, dry_run)

    # 显示规则命中率
    if organizer.rule_hit_counts:
        print(f"\n📊 规则命中率 (Top 10):")
        sorted_rules = sorted(organizer.rule_hit_counts.items(),
                             key=lambda x: x[1], reverse=True)[:10]
        for rule, count in sorted_rules:
            print(f"  {count:4d} 次  {rule}")

    # 显示未匹配文件
    if organizer.unmatched_files:
        print(f"\n📋 未匹配/兜底文件 ({len(organizer.unmatched_files)} 个):")
        for uf in organizer.unmatched_files[:10]:
            print(f"  • {uf['filename']} → {uf['target_rel']}")
        if len(organizer.unmatched_files) > 10:
            print(f"  ... 还有 {len(organizer.unmatched_files) - 10} 个")

    if dry_run:
        print("\n💡 提示：以上为预览结果，使用 --execute 执行实际整理")
    else:
        # 执行完成后打开日志目录
        import webbrowser
        log_dir = Path(__file__).parent / args.log_dir
        if log_dir.exists():
            log_path = log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            # 使用 file:// 协议打开日志目录
            log_url = log_dir.resolve().as_uri()
            print(f"\n🌐 打开日志目录: {log_dir}")
            webbrowser.open(log_url)


if __name__ == "__main__":
    main()
