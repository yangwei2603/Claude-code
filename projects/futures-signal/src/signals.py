"""交易信号生成引擎"""
from datetime import date
from typing import List, Optional

from .models import MarketData, MemberPosition, TradingSignal
from config import SIGNAL_THRESHOLDS


class SignalGenerator:
    """交易信号生成器"""

    def __init__(self, position_change_min: int = None):
        self.position_change_min = position_change_min or SIGNAL_THRESHOLDS["position_change_min"]

    def check_long_conditions(self, market: MarketData, position: MemberPosition) -> dict:
        """检查做多条件"""
        conditions = {
            "volume_increased": market.volume_increased,
            "open_interest_increased": market.open_interest_increased,
            "price_increased": market.price_increased,
            "seat_long_increased": position.long_position_change > self.position_change_min,
        }
        conditions["all_met"] = all(conditions.values())
        return conditions

    def check_exit_long_conditions(self, market: MarketData, position: MemberPosition) -> dict:
        """检查平多条件"""
        conditions = {
            "volume_increased": market.volume_increased,
            "open_interest_decreased": market.open_interest < market.prev_open_interest,
            "price_decreased": market.price_decreased,
            "seat_long_decreased": position.long_position_change < -self.position_change_min,
        }
        conditions["all_met"] = all(conditions.values())
        return conditions

    def check_short_conditions(self, market: MarketData, position: MemberPosition) -> dict:
        """检查做空条件"""
        conditions = {
            "volume_increased": market.volume_increased,
            "open_interest_increased": market.open_interest_increased,
            "price_decreased": market.price_decreased,
            "seat_short_increased": position.short_position_change > self.position_change_min,
        }
        conditions["all_met"] = all(conditions.values())
        return conditions

    def check_exit_short_conditions(self, market: MarketData, position: MemberPosition) -> dict:
        """检查平空条件"""
        conditions = {
            "volume_increased": market.volume_increased,
            "open_interest_decreased": market.open_interest < market.prev_open_interest,
            "price_increased": market.price_increased,
            "seat_short_decreased": position.short_position_change < -self.position_change_min,
        }
        conditions["all_met"] = all(conditions.values())
        return conditions

    def generate_signal(
        self,
        market: MarketData,
        position: MemberPosition,
        trade_date: Optional[date] = None
    ) -> Optional[TradingSignal]:
        """生成交易信号"""
        signals = []

        # 检查做多条件
        long_cond = self.check_long_conditions(market, position)
        if long_cond["all_met"]:
            signals.append(TradingSignal(
                signal_type="LONG",
                contract_code=market.contract_code,
                seat_code=position.seat_code,
                trade_date=trade_date or market.trade_date,
                confidence=1.0,
                conditions=long_cond,
            ))

        # 检查平多条件
        exit_long_cond = self.check_exit_long_conditions(market, position)
        if exit_long_cond["all_met"]:
            signals.append(TradingSignal(
                signal_type="EXIT_LONG",
                contract_code=market.contract_code,
                seat_code=position.seat_code,
                trade_date=trade_date or market.trade_date,
                confidence=1.0,
                conditions=exit_long_cond,
            ))

        # 检查做空条件
        short_cond = self.check_short_conditions(market, position)
        if short_cond["all_met"]:
            signals.append(TradingSignal(
                signal_type="SHORT",
                contract_code=market.contract_code,
                seat_code=position.seat_code,
                trade_date=trade_date or market.trade_date,
                confidence=1.0,
                conditions=short_cond,
            ))

        # 检查平空条件
        exit_short_cond = self.check_exit_short_conditions(market, position)
        if exit_short_cond["all_met"]:
            signals.append(TradingSignal(
                signal_type="EXIT_SHORT",
                contract_code=market.contract_code,
                seat_code=position.seat_code,
                trade_date=trade_date or market.trade_date,
                confidence=1.0,
                conditions=exit_short_cond,
            ))

        # 返回第一个触发的信号（如果有多个，优先级：做多 > 平多 > 做空 > 平空）
        if signals:
            priority = {"LONG": 0, "EXIT_LONG": 1, "SHORT": 2, "EXIT_SHORT": 3}
            return min(signals, key=lambda x: priority[x.signal_type])

        return None

    def scan_signals(
        self,
        market_data_list: List[MarketData],
        position_list: List[MemberPosition]
    ) -> List[TradingSignal]:
        """扫描多个交易日生成信号"""
        signals = []

        # 找到共同交易日的数据
        market_dict = {m.trade_date: m for m in market_data_list}
        position_dict = {p.trade_date: p for p in position_list}

        common_dates = set(market_dict.keys()) & set(position_dict.keys())

        for trade_date in sorted(common_dates):
            market = market_dict[trade_date]
            position = position_dict[trade_date]

            signal = self.generate_signal(market, position)
            if signal:
                signals.append(signal)

        return signals
