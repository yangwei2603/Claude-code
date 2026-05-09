"""同花顺API期货交易信号系统 - 主入口"""
import argparse
from datetime import date, timedelta
from pathlib import Path

from config import CONTRACTS, SEATS
from src.simulator import generate_mock_data
from src.signals import SignalGenerator
from src.exporter import get_exporter


def parse_args():
    parser = argparse.ArgumentParser(description="期货交易信号系统 - 模拟原型")
    parser.add_argument(
        "--days", type=int, default=30,
        help="模拟天数（默认30天）"
    )
    parser.add_argument(
        "--start-date", type=str, default=None,
        help="开始日期（YYYY-MM-DD格式，默认：30天前）"
    )
    parser.add_argument(
        "--contracts", type=str, nargs="+",
        default=list(CONTRACTS.keys()),
        help=f"监控合约（默认：{list(CONTRACTS.keys())}）"
    )
    parser.add_argument(
        "--seats", type=str, nargs="+",
        default=list(SEATS.keys()),
        help=f"关注席位（默认：{list(SEATS.keys())}）"
    )
    parser.add_argument(
        "--export", type=str, choices=["csv", "xlsx", "both"], default="csv",
        help="导出格式（默认：csv）"
    )
    parser.add_argument(
        "--output", type=str, default="output",
        help="输出目录（默认：output）"
    )
    parser.add_argument(
        "--threshold", type=int, default=2000,
        help="持仓变化阈值（手，默认：2000）"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 确定开始日期
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    else:
        start_date = date.today() - timedelta(days=args.days)

    print(f"=== 期货交易信号系统 - 模拟原型 ===")
    print(f"模拟期间: {start_date} 至 {date.today()} ({args.days}天)")
    print(f"监控合约: {args.contracts}")
    print(f"关注席位: {args.seats}")
    print(f"持仓变化阈值: {args.threshold}手")
    print()

    # 生成模拟数据
    print("生成模拟数据...")
    mock_data = generate_mock_data(
        contract_codes=args.contracts,
        seat_codes=args.seats,
        start_date=start_date,
        days=args.days
    )

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    # 生成信号
    print("生成交易信号...")
    generator = SignalGenerator(position_change_min=args.threshold)
    all_signals = []

    for contract in args.contracts:
        market_list = mock_data["market_data"].get(contract, [])

        for seat in args.seats:
            key = f"{seat}_{contract}"
            position_list = mock_data["member_positions"].get(key, [])

            signals = generator.scan_signals(market_list, position_list)
            all_signals.extend(signals)

    # 打印信号摘要
    print()
    print("=== 信号摘要 ===")
    signal_counts = {}
    for sig in all_signals:
        sig_name = sig.signal_name
        signal_counts[sig_name] = signal_counts.get(sig_name, 0) + 1

    for sig_name, count in sorted(signal_counts.items()):
        print(f"  {sig_name}: {count}个")

    if all_signals:
        print()
        print("=== 最新信号 ===")
        latest = sorted(all_signals, key=lambda x: x.trade_date)[-5:]
        for sig in latest:
            print(f"  {sig}")

    # 导出数据
    if args.export in ("csv", "both"):
        print()
        print("导出CSV文件...")
        csv_exporter = get_exporter("csv")

        # 导出信号
        csv_exporter.export_signals(
            all_signals,
            str(output_dir / "signals.csv")
        )

        # 导出行情数据
        for contract, data_list in mock_data["market_data"].items():
            csv_exporter.export_market_data(
                data_list,
                str(output_dir / f"market_{contract.replace('.', '_')}.csv")
            )

        print(f"  信号: {output_dir / 'signals.csv'}")

    if args.export in ("xlsx", "both"):
        print()
        print("导出Excel文件...")
        xlsx_exporter = get_exporter("xlsx")

        xlsx_exporter.export_all(
            mock_data["market_data"],
            mock_data["member_positions"],
            all_signals,
            str(output_dir / "futures_signals.xlsx")
        )

        print(f"  完整报告: {output_dir / 'futures_signals.xlsx'}")

    print()
    print("完成!")


if __name__ == "__main__":
    main()
