"""数据模型"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class MarketData:
    """行情数据"""
    contract_code: str          # 合约代码，如 P.MAIN
    trade_date: date            # 交易日期
    close_price: float          # 收盘价
    volume: int                 # 成交量
    open_interest: int          # 持仓量
    prev_close_price: float = 0 # 前一日收盘价
    prev_volume: int = 0        # 前一日成交量
    prev_open_interest: int = 0 # 前一日持仓量

    @property
    def volume_increased(self) -> bool:
        return self.volume > self.prev_volume

    @property
    def open_interest_increased(self) -> bool:
        return self.open_interest > self.prev_open_interest

    @property
    def price_increased(self) -> bool:
        return self.close_price > self.prev_close_price

    @property
    def price_decreased(self) -> bool:
        return self.close_price < self.prev_close_price


@dataclass
class MemberPosition:
    """会员持仓数据"""
    seat_code: str              # 席位代码，如 JPM001
    seat_name: str              # 席位名称
    contract_code: str          # 合约代码
    trade_date: date            # 交易日期
    long_position: int          # 多头持仓量
    short_position: int         # 空头持仓量
    prev_long_position: int = 0 # 前一日多头持仓
    prev_short_position: int = 0 # 前一日空头持仓

    @property
    def long_position_change(self) -> int:
        """多头持仓变化量"""
        return self.long_position - self.prev_long_position

    @property
    def short_position_change(self) -> int:
        """空头持仓变化量"""
        return self.short_position - self.prev_short_position

    @property
    def long_position_increased(self) -> bool:
        return self.long_position_change > 0

    @property
    def short_position_increased(self) -> bool:
        return self.short_position_change > 0


@dataclass
class TradingSignal:
    """交易信号"""
    signal_type: str            # 信号类型：LONG(做多), EXIT_LONG(平多), SHORT(做空), EXIT_SHORT(平空)
    contract_code: str          # 合约代码
    seat_code: str              # 席位代码
    trade_date: date           # 信号日期
    confidence: float = 1.0    # 置信度
    conditions: dict = field(default_factory=dict)  # 满足的条件详情

    def __str__(self) -> str:
        signal_names = {
            "LONG": "做多",
            "EXIT_LONG": "平多",
            "SHORT": "做空",
            "EXIT_SHORT": "平空",
        }
        return f"{self.trade_date} {self.contract_code} {signal_names.get(self.signal_type, self.signal_type)}信号"

    @property
    def signal_name(self) -> str:
        names = {
            "LONG": "做多",
            "EXIT_LONG": "平多",
            "SHORT": "做空",
            "EXIT_SHORT": "平空",
        }
        return names.get(self.signal_type, self.signal_type)
