#!/usr/bin/env python3
"""FX quant research/backtest pipeline (for paper trading first, not live execution).

Input CSV (required headers):
- timestamp
- close

Optional headers:
- spread_bps (transaction cost proxy, default from cli)

Example:
  python3 tools/fx_quant_strategy.py \
    --csv data/usdcny_daily.csv \
    --lookback 20 --vol-window 30 --target-vol 0.10 \
    --max-leverage 2.0 --out reports/fx_signals.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import pstdev


TRADING_DAYS = 252


@dataclass
class Bar:
    ts: dt.datetime
    close: float
    spread_bps: float


@dataclass
class ResultRow:
    ts: dt.datetime
    close: float
    signal: float
    position: float
    ret_gross: float
    ret_net: float
    equity: float
    drawdown: float


def parse_dt(s: str) -> dt.datetime:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported timestamp format: {s}")


def load_bars(path: Path, default_spread_bps: float) -> list[Bar]:
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "close"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV must include headers: timestamp, close")
        for row in reader:
            close = float(row["close"])
            spread = float(row.get("spread_bps") or default_spread_bps)
            bars.append(Bar(parse_dt(row["timestamp"]), close, spread))
    if len(bars) < 100:
        raise ValueError("Need at least 100 rows for stable rolling statistics.")
    bars.sort(key=lambda x: x.ts)
    return bars


def pct_returns(closes: list[float]) -> list[float]:
    out = [0.0]
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        out.append(0.0 if prev == 0 else closes[i] / prev - 1.0)
    return out


def rolling_std(vals: list[float], window: int) -> list[float]:
    out: list[float] = [0.0] * len(vals)
    for i in range(window, len(vals)):
        sample = vals[i - window + 1 : i + 1]
        out[i] = pstdev(sample) if len(sample) > 1 else 0.0
    return out


def rolling_mean(vals: list[float], window: int) -> list[float]:
    out: list[float] = [0.0] * len(vals)
    run = 0.0
    for i, v in enumerate(vals):
        run += v
        if i >= window:
            run -= vals[i - window]
        if i >= window - 1:
            out[i] = run / window
    return out


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def generate_signal(rets: list[float], lookback: int) -> list[float]:
    momentum = rolling_mean(rets, lookback)
    vol = rolling_std(rets, lookback)
    sig = [0.0] * len(rets)
    for i in range(len(rets)):
        if vol[i] <= 1e-12:
            sig[i] = 0.0
            continue
        z = momentum[i] / vol[i]
        sig[i] = math.tanh(z)  # bounded in [-1, 1]
    return sig


def backtest(
    bars: list[Bar],
    lookback: int,
    vol_window: int,
    target_vol: float,
    max_leverage: float,
    stop_loss: float,
) -> list[ResultRow]:
    closes = [b.close for b in bars]
    raw_rets = pct_returns(closes)
    signal = generate_signal(raw_rets, lookback)
    realized_vol = rolling_std(raw_rets, vol_window)

    rows: list[ResultRow] = []
    equity = 1.0
    peak = 1.0
    prev_position = 0.0

    for i, b in enumerate(bars):
        rv = realized_vol[i] * math.sqrt(TRADING_DAYS)
        risk_scale = 0.0 if rv <= 1e-12 else target_vol / rv
        position = clamp(signal[i] * risk_scale, -max_leverage, max_leverage)

        # trade return uses position from previous bar to avoid look-ahead bias
        gross = prev_position * raw_rets[i]

        # turnover-based transaction cost proxy
        turnover = abs(position - prev_position)
        cost = turnover * (b.spread_bps / 10000.0)
        net = gross - cost

        # single-period stop-loss cap (tail-risk guardrail)
        net = max(net, -abs(stop_loss))

        equity *= 1.0 + net
        peak = max(peak, equity)
        dd = 0.0 if peak <= 0 else equity / peak - 1.0

        rows.append(
            ResultRow(
                ts=b.ts,
                close=b.close,
                signal=signal[i],
                position=position,
                ret_gross=gross,
                ret_net=net,
                equity=equity,
                drawdown=dd,
            )
        )
        prev_position = position

    return rows


def summarize(rows: list[ResultRow]) -> dict[str, float]:
    rets = [r.ret_net for r in rows]
    mean_r = sum(rets) / len(rets)
    vol = pstdev(rets) if len(rets) > 1 else 0.0
    sharpe = 0.0 if vol <= 1e-12 else (mean_r / vol) * math.sqrt(TRADING_DAYS)

    years = max(len(rows) / TRADING_DAYS, 1e-9)
    total = rows[-1].equity - 1.0
    cagr = rows[-1].equity ** (1 / years) - 1.0
    mdd = min(r.drawdown for r in rows)
    win_rate = sum(1 for r in rows if r.ret_net > 0) / len(rows)

    return {
        "total_return": total,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": mdd,
        "win_rate": win_rate,
    }


def write_rows(path: Path, rows: list[ResultRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "close", "signal", "position", "ret_gross", "ret_net", "equity", "drawdown"])
        for r in rows:
            w.writerow(
                [
                    r.ts.isoformat(sep=" "),
                    f"{r.close:.8f}",
                    f"{r.signal:.6f}",
                    f"{r.position:.6f}",
                    f"{r.ret_gross:.8f}",
                    f"{r.ret_net:.8f}",
                    f"{r.equity:.8f}",
                    f"{r.drawdown:.8f}",
                ]
            )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FX quant backtest tool (research/paper-trading)")
    p.add_argument("--csv", required=True, type=Path, help="Input price CSV with timestamp,close")
    p.add_argument("--out", type=Path, default=Path("reports/fx_signals.csv"))
    p.add_argument("--lookback", type=int, default=20)
    p.add_argument("--vol-window", type=int, default=30)
    p.add_argument("--target-vol", type=float, default=0.10, help="Annualized target volatility")
    p.add_argument("--max-leverage", type=float, default=2.0)
    p.add_argument("--stop-loss", type=float, default=0.02, help="Per-period stop loss cap (e.g., 0.02=2%)")
    p.add_argument("--spread-bps", type=float, default=1.5, help="Fallback spread in basis points")
    return p


def main() -> None:
    args = build_parser().parse_args()
    bars = load_bars(args.csv, args.spread_bps)
    rows = backtest(
        bars=bars,
        lookback=args.lookback,
        vol_window=args.vol_window,
        target_vol=args.target_vol,
        max_leverage=args.max_leverage,
        stop_loss=args.stop_loss,
    )
    stats = summarize(rows)
    write_rows(args.out, rows)

    print("Backtest complete (research only).")
    print(f"rows={len(rows)} out={args.out}")
    print(
        " ".join(
            [
                f"total={stats['total_return']:.2%}",
                f"cagr={stats['cagr']:.2%}",
                f"sharpe={stats['sharpe']:.2f}",
                f"mdd={stats['max_drawdown']:.2%}",
                f"win={stats['win_rate']:.2%}",
            ]
        )
    )


if __name__ == "__main__":
    main()
