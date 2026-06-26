"""
A股多因子量化模型 — 全局配置
"""

# ============================================================
# 数据源配置
# ============================================================
DATA_SOURCES = {
    "akshare": {
        "priority": 1,
        "enabled": True,
        "timeout": 15,
        "retry": 2,
    },
    "baostock": {
        "priority": 2,
        "enabled": True,
        "timeout": 15,
        "retry": 2,
    },
    "efinance": {
        "priority": 3,
        "enabled": True,
        "timeout": 15,
        "retry": 2,
    },
    "tushare": {
        "priority": 4,
        "enabled": True,
        "timeout": 15,
        "retry": 2,
        "token": "",  # 填入你的 tushare token，没有则自动跳过
    },
}

# 交叉验证：关键数据用2个数据源对比
CROSS_VALIDATION_ENABLED = True
CROSS_VALIDATION_MAX_DEVIATION = 0.05  # 5%偏差阈值

# ============================================================
# 缓存配置
# ============================================================
CACHE_DIR = "cache"
CACHE_TTL_HOURS = {
    "stock_list": 24,
    "daily_kline": 6,
    "financial": 72,  # 财务数据72小时更新一次
    "fund_nav": 6,
}

# ============================================================
# 股票池配置
# ============================================================
STOCK_POOL = {
    "min_market_cap": 50,  # 最低市值（亿）, 过滤小盘垃圾股
    "exclude_st": True,     # 排除ST
    "exclude_new": True,    # 排除上市不满1年
    "boards": ["主板", "创业板", "科创板"],
}

# ============================================================
# 多因子权重配置 (股票)
# ============================================================
STOCK_FACTOR_WEIGHTS = {
    "value": 0.25,      # 价值因子
    "momentum": 0.15,   # 动量因子
    "quality": 0.20,    # 质量因子
    "growth": 0.15,     # 成长因子
    "volatility": 0.10, # 波动因子
    "technical": 0.15,  # 技术因子
}

# 子因子权重
VALUE_SUB_WEIGHTS = {
    "pe_percentile": 0.30,      # PE分位数(越低越好)
    "pb_percentile": 0.30,      # PB分位数(越低越好)
    "ps_percentile": 0.15,      # PS分位数(越低越好)
    "dividend_yield": 0.25,     # 股息率(越高越好)
}

MOMENTUM_SUB_WEIGHTS = {
    "momentum_20d": 0.25,
    "momentum_60d": 0.35,
    "momentum_120d": 0.25,
    "volume_momentum": 0.15,
}

QUALITY_SUB_WEIGHTS = {
    "roe": 0.30,
    "roa": 0.15,
    "gross_margin": 0.15,
    "debt_ratio": 0.20,         # 资产负债率(越低越好)
    "cashflow_to_revenue": 0.20,
}

GROWTH_SUB_WEIGHTS = {
    "revenue_growth_yoy": 0.35,
    "earnings_growth_yoy": 0.40,
    "eps_growth": 0.25,
}

VOLATILITY_SUB_WEIGHTS = {
    "volatility_60d": 0.55,     # 波动率(越低越好)
    "beta": 0.45,               # Beta(越低越好)
}

TECHNICAL_SUB_WEIGHTS = {
    "ma_deviation": 0.25,       # MA偏离度
    "rsi_signal": 0.25,         # RSI信号
    "macd_signal": 0.25,        # MACD信号
    "volume_anomaly": 0.25,     # 成交量异动
}

# ============================================================
# 基金筛选配置
# ============================================================
FUND_FILTER = {
    "min_history_years": 3,       # 最少3年历史
    "min_asset": 5,               # 最少5亿规模(亿)
    "max_drawdown_1y": 0.25,      # 近1年最大回撤不超过25%
    "min_annual_return_3y": 0.08, # 近3年年化不低于8%
}

FUND_FACTOR_WEIGHTS = {
    "return_1y": 0.15,
    "return_3y": 0.25,
    "sharpe_ratio": 0.20,
    "sortino_ratio": 0.10,
    "max_drawdown": 0.15,     # 越低越好
    "manager_tenure": 0.05,
    "fund_size": 0.05,
    "alpha": 0.05,
}

# ============================================================
# 风险控制配置
# ============================================================
RISK = {
    "drawdown_warn": 0.15,      # 回撤15%黄色预警
    "drawdown_critical": 0.25,  # 回撤25%红色预警
    "atr_stop_multiplier": 2.0, # ATR止损倍数
    "trailing_stop": 0.10,      # 移动止盈回撤10%
    "max_single_position": 0.10, # 单只股票最大仓位10%
    "max_industry_exposure": 0.30, # 单行业最大敞口30%
    "min_score_threshold": 60,   # 最低综合得分阈值
}

# ============================================================
# 信号等级
# ============================================================
SIGNAL_LEVELS = {
    "strong_buy": 80,    # 强烈推荐 >= 80分
    "buy": 65,           # 推荐 >= 65分
    "hold": 50,          # 持有/观望 >= 50分
    "sell": 40,          # 建议减仓 < 50分
}
