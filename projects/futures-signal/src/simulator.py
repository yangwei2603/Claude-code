"""模拟数据生成器"""
import random
from datetime import date, timedelta
from typing import List, Dict

from .models import MarketData, MemberPosition
from config import CONTRACTS, SEATS, MOCK_PARAMS


class MarketSimulator:
    """市场数据模拟器"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_market_data_series(
        self,
        contract_code: str,
        start_date: date,
        days: int
    ) -> List[MarketData]:
        """生成指定合约的历史行情数据"""
        if contract_code not in CONTRACTS:
            raise ValueError(f"Unknown contract: {contract_code}")

        base_price = MOCK_PARAMS["base_price"] * random.uniform(0.8, 1.2)
        data_list = []

        for i in range(days):
            trade_date = start_date + timedelta(days=i)

            # 模拟价格变化
            price_change = random.gauss(0, MOCK_PARAMS["volatility"])
            close_price = base_price * (1 + price_change)

            # 模拟成交量和持仓量
            volume = int(MOCK_PARAMS["base_volume"] * random.uniform(0.7, 1.3))
            open_interest = int(MOCK_PARAMS["base_open_interest"] * random.uniform(0.8, 1.2))

            prev_close = data_list[-1].close_price if data_list else close_price
            prev_volume = data_list[-1].volume if data_list else volume
            prev_oi = data_list[-1].open_interest if data_list else open_interest

            market_data = MarketData(
                contract_code=contract_code,
                trade_date=trade_date,
                close_price=close_price,
                volume=volume,
                open_interest=open_interest,
                prev_close_price=prev_close,
                prev_volume=prev_volume,
                prev_open_interest=prev_oi,
            )
            data_list.append(market_data)

            # 更新基础价格
            base_price = close_price

        return data_list


class PositionSimulator:
    """会员持仓模拟器"""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def generate_position_series(
        self,
        seat_code: str,
        contract_code: str,
        start_date: date,
        days: int
    ) -> List[MemberPosition]:
        """生成指定席位的持仓数据序列"""
        if seat_code not in SEATS:
            raise ValueError(f"Unknown seat: {seat_code}")

        seat_info = SEATS[seat_code]
        base_long = random.randint(15000, 25000)
        base_short = random.randint(10000, 20000)
        data_list = []

        for i in range(days):
            trade_date = start_date + timedelta(days=i)

            # 模拟持仓变化
            long_change = random.randint(-3000, 4000)
            short_change = random.randint(-3000, 4000)

            long_position = max(0, base_long + long_change)
            short_position = max(0, base_short + short_change)

            prev_long = data_list[-1].long_position if data_list else long_position
            prev_short = data_list[-1].short_position if data_list else short_position

            position = MemberPosition(
                seat_code=seat_code,
                seat_name=seat_info["name"],
                contract_code=contract_code,
                trade_date=trade_date,
                long_position=long_position,
                short_position=short_position,
                prev_long_position=prev_long,
                prev_short_position=prev_short,
            )
            data_list.append(position)

            base_long = long_position
            base_short = short_position

        return data_list


def generate_mock_data(
    contract_codes: List[str],
    seat_codes: List[str],
    start_date: date,
    days: int
) -> Dict[str, Dict[str, List]]:
    """生成完整的模拟数据"""
    market_sim = MarketSimulator()
    position_sim = PositionSimulator()

    result = {
        "market_data": {},
        "member_positions": {},
    }

    for contract in contract_codes:
        result["market_data"][contract] = market_sim.generate_market_data_series(
            contract, start_date, days
        )

    for seat in seat_codes:
        for contract in contract_codes:
            key = f"{seat}_{contract}"
            result["member_positions"][key] = position_sim.generate_position_series(
                seat, contract, start_date, days
            )

    return result
