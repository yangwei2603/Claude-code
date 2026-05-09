"""信号逻辑测试"""
import pytest
from datetime import date

from src.models import MarketData, MemberPosition, TradingSignal
from src.signals import SignalGenerator


class TestSignalConditions:
    """测试信号条件判断"""

    def setup_method(self):
        self.generator = SignalGenerator(position_change_min=2000)

    def _make_market(
        self,
        close=8000, prev_close=7900,
        volume=100000, prev_volume=90000,
        oi=300000, prev_oi=290000
    ) -> MarketData:
        return MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=close,
            volume=volume,
            open_interest=oi,
            prev_close_price=prev_close,
            prev_volume=prev_volume,
            prev_open_interest=prev_oi,
        )

    def _make_position(
        self,
        long=20000, prev_long=18000,
        short=10000, prev_short=8000
    ) -> MemberPosition:
        return MemberPosition(
            seat_code="JPM001",
            seat_name="摩根大通期货",
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            long_position=long,
            short_position=short,
            prev_long_position=prev_long,
            prev_short_position=prev_short,
        )

    def test_long_conditions_all_met(self):
        """做多信号：条件全部满足"""
        market = self._make_market(
            close=8000, prev_close=7900,  # 价格上涨
            volume=100000, prev_volume=90000,  # 成交量增加
            oi=300000, prev_oi=290000  # 持仓量增加
        )
        position = self._make_position(
            long=22000, prev_long=18000  # 多头持仓增加4000手 > 2000
        )

        conditions = self.generator.check_long_conditions(market, position)
        assert conditions["volume_increased"] is True
        assert conditions["open_interest_increased"] is True
        assert conditions["price_increased"] is True
        assert conditions["seat_long_increased"] is True
        assert conditions["all_met"] is True

    def test_long_conditions_not_met_volume(self):
        """做多信号：成交量未增加"""
        market = self._make_market(
            close=8000, prev_close=7900,
            volume=80000, prev_volume=90000,  # 成交量下降
            oi=300000, prev_oi=290000
        )
        position = self._make_position(long=22000, prev_long=18000)

        conditions = self.generator.check_long_conditions(market, position)
        assert conditions["volume_increased"] is False
        assert conditions["all_met"] is False

    def test_long_conditions_not_met_seat(self):
        """做多信号：席位多头持仓增加不足2000手"""
        market = self._make_market(
            close=8000, prev_close=7900,
            volume=100000, prev_volume=90000,
            oi=300000, prev_oi=290000
        )
        position = self._make_position(
            long=19500, prev_long=18000  # 仅增加1500手 < 2000
        )

        conditions = self.generator.check_long_conditions(market, position)
        assert conditions["seat_long_increased"] is False
        assert conditions["all_met"] is False

    def test_exit_long_conditions_all_met(self):
        """平多信号：条件全部满足"""
        market = self._make_market(
            close=7900, prev_close=8000,  # 价格回落
            volume=100000, prev_volume=90000,  # 成交量增加
            oi=280000, prev_oi=300000  # 持仓量下降
        )
        position = self._make_position(
            long=15000, prev_long=19000  # 多头持仓下降4000手 > 2000
        )

        conditions = self.generator.check_exit_long_conditions(market, position)
        assert conditions["volume_increased"] is True
        assert conditions["open_interest_decreased"] is True
        assert conditions["price_decreased"] is True
        assert conditions["seat_long_decreased"] is True
        assert conditions["all_met"] is True

    def test_short_conditions_all_met(self):
        """做空信号：条件全部满足"""
        market = self._make_market(
            close=7800, prev_close=7900,  # 价格下跌
            volume=100000, prev_volume=90000,  # 成交量增加
            oi=300000, prev_oi=290000  # 持仓量增加
        )
        position = self._make_position(
            short=12000, prev_short=9000  # 空头持仓增加3000手 > 2000
        )

        conditions = self.generator.check_short_conditions(market, position)
        assert conditions["volume_increased"] is True
        assert conditions["open_interest_increased"] is True
        assert conditions["price_decreased"] is True
        assert conditions["seat_short_increased"] is True
        assert conditions["all_met"] is True

    def test_exit_short_conditions_all_met(self):
        """平空信号：条件全部满足"""
        market = self._make_market(
            close=8000, prev_close=7900,  # 价格上涨
            volume=100000, prev_volume=90000,  # 成交量增加
            oi=280000, prev_oi=300000  # 持仓量下降
        )
        position = self._make_position(
            short=7000, prev_short=10000  # 空头持仓下降3000手 > 2000
        )

        conditions = self.generator.check_exit_short_conditions(market, position)
        assert conditions["volume_increased"] is True
        assert conditions["open_interest_decreased"] is True
        assert conditions["price_increased"] is True
        assert conditions["seat_short_decreased"] is True
        assert conditions["all_met"] is True


class TestSignalGeneration:
    """测试信号生成"""

    def setup_method(self):
        self.generator = SignalGenerator(position_change_min=2000)

    def test_generate_long_signal(self):
        """生成做多信号"""
        market = MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=8000, volume=100000, open_interest=300000,
            prev_close_price=7900, prev_volume=90000, prev_open_interest=290000,
        )
        position = MemberPosition(
            seat_code="JPM001", seat_name="摩根大通期货",
            contract_code="P.MAIN", trade_date=date(2026, 5, 8),
            long_position=22000, short_position=10000,
            prev_long_position=18000, prev_short_position=8000,
        )

        signal = self.generator.generate_signal(market, position)

        assert signal is not None
        assert signal.signal_type == "LONG"
        assert signal.contract_code == "P.MAIN"
        assert signal.seat_code == "JPM001"

    def test_no_signal_when_no_conditions_met(self):
        """无信号：条件未满足"""
        market = MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=7900, volume=80000, open_interest=280000,
            prev_close_price=8000, prev_volume=90000, prev_open_interest=300000,
        )
        position = MemberPosition(
            seat_code="JPM001", seat_name="摩根大通期货",
            contract_code="P.MAIN", trade_date=date(2026, 5, 8),
            long_position=17000, short_position=12000,
            prev_long_position=18000, prev_short_position=10000,
        )

        signal = self.generator.generate_signal(market, position)
        assert signal is None


class TestMarketDataModel:
    """测试行情数据模型"""

    def test_volume_increased(self):
        data = MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=8000, volume=100000, open_interest=300000,
            prev_close_price=7900, prev_volume=90000, prev_open_interest=290000,
        )
        assert data.volume_increased is True

    def test_open_interest_increased(self):
        data = MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=8000, volume=100000, open_interest=310000,
            prev_close_price=7900, prev_volume=90000, prev_open_interest=290000,
        )
        assert data.open_interest_increased is True

    def test_price_increased(self):
        data = MarketData(
            contract_code="P.MAIN",
            trade_date=date(2026, 5, 8),
            close_price=8000, volume=100000, open_interest=300000,
            prev_close_price=7900, prev_volume=90000, prev_open_interest=290000,
        )
        assert data.price_increased is True
        assert data.price_decreased is False


class TestMemberPositionModel:
    """测试会员持仓模型"""

    def test_long_position_change(self):
        position = MemberPosition(
            seat_code="JPM001", seat_name="摩根大通期货",
            contract_code="P.MAIN", trade_date=date(2026, 5, 8),
            long_position=22000, short_position=10000,
            prev_long_position=18000, prev_short_position=8000,
        )
        assert position.long_position_change == 4000
        assert position.short_position_change == 2000
