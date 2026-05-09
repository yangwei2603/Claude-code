"""配置文件"""

# 监控品种
CONTRACTS = {
    "P.MAIN": {"name": "棕榈油", "unit": "元/吨"},
    "M.MAIN": {"name": "豆粕", "unit": "元/吨"},
    "C.MAIN": {"name": "玉米", "unit": "元/吨"},
}

# 关注席位
SEATS = {
    "JPM001": {"name": "摩根大通期货", "type": "foreign"},
}

# 信号触发阈值
SIGNAL_THRESHOLDS = {
    "position_change_min": 2000,  # 席位持仓变化最小阈值（手）
}

# 模拟数据参数
MOCK_PARAMS = {
    "base_volume": 100000,
    "base_open_interest": 300000,
    "base_price": 8000,
    "volatility": 0.02,
}
