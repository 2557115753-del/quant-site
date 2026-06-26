"""因子标准化 + 综合打分"""
import numpy as np
import pandas as pd
from config import (
    STOCK_FACTOR_WEIGHTS, VALUE_SUB_WEIGHTS, MOMENTUM_SUB_WEIGHTS,
    QUALITY_SUB_WEIGHTS, GROWTH_SUB_WEIGHTS, VOLATILITY_SUB_WEIGHTS,
    TECHNICAL_SUB_WEIGHTS, FUND_FACTOR_WEIGHTS,
)


# 因子方向：1 表示越高越好，-1 表示越低越好
STOCK_FACTOR_DIRECTION = {
    # 价值
    "pe": -1, "pb": -1, "ps": -1, "dividend_yield": 1,
    # 动量
    "momentum_20d": 1, "momentum_60d": 1, "momentum_120d": 1, "volume_momentum": 1,
    # 质量
    "roe": 1, "roa": 1, "gross_margin": 1, "debt_ratio": -1, "cashflow_to_revenue": 1,
    # 成长
    "revenue_growth_yoy": 1, "earnings_growth_yoy": 1, "eps_growth": 1,
    # 波动
    "volatility_60d": -1, "beta": -1,
    # 技术
    "ma_deviation": 1, "rsi_signal": 1, "macd_signal": 1, "volume_anomaly": 1,
}

FUND_FACTOR_DIRECTION = {
    "return_1y": 1, "return_3y": 1, "annual_return_1y": 1, "annual_return_3y": 1,
    "max_drawdown": -1, "sharpe_ratio": 1, "sortino_ratio": 1,
    "alpha": 1, "beta": -1, "manager_tenure": 1, "fund_size": 1,
}

SUB_WEIGHT_MAP = {
    "pe": VALUE_SUB_WEIGHTS.get("pe_percentile", 0.3),
    "pb": VALUE_SUB_WEIGHTS.get("pb_percentile", 0.3),
    "ps": VALUE_SUB_WEIGHTS.get("ps_percentile", 0.15),
    "dividend_yield": VALUE_SUB_WEIGHTS.get("dividend_yield", 0.25),
    "momentum_20d": MOMENTUM_SUB_WEIGHTS.get("momentum_20d", 0.25),
    "momentum_60d": MOMENTUM_SUB_WEIGHTS.get("momentum_60d", 0.35),
    "momentum_120d": MOMENTUM_SUB_WEIGHTS.get("momentum_120d", 0.25),
    "volume_momentum": MOMENTUM_SUB_WEIGHTS.get("volume_momentum", 0.15),
    "roe": QUALITY_SUB_WEIGHTS.get("roe", 0.30),
    "roa": QUALITY_SUB_WEIGHTS.get("roa", 0.15),
    "gross_margin": QUALITY_SUB_WEIGHTS.get("gross_margin", 0.15),
    "debt_ratio": QUALITY_SUB_WEIGHTS.get("debt_ratio", 0.20),
    "cashflow_to_revenue": QUALITY_SUB_WEIGHTS.get("cashflow_to_revenue", 0.20),
    "revenue_growth_yoy": GROWTH_SUB_WEIGHTS.get("revenue_growth_yoy", 0.35),
    "earnings_growth_yoy": GROWTH_SUB_WEIGHTS.get("earnings_growth_yoy", 0.40),
    "eps_growth": GROWTH_SUB_WEIGHTS.get("eps_growth", 0.25),
    "volatility_60d": VOLATILITY_SUB_WEIGHTS.get("volatility_60d", 0.55),
    "beta": VOLATILITY_SUB_WEIGHTS.get("beta", 0.45),
    "ma_deviation": TECHNICAL_SUB_WEIGHTS.get("ma_deviation", 0.25),
    "rsi_signal": TECHNICAL_SUB_WEIGHTS.get("rsi_signal", 0.25),
    "macd_signal": TECHNICAL_SUB_WEIGHTS.get("macd_signal", 0.25),
    "volume_anomaly": TECHNICAL_SUB_WEIGHTS.get("volume_anomaly", 0.25),
}

# 子因子到父类别的映射
FACTOR_TO_CATEGORY = {
    "pe": "value", "pb": "value", "ps": "value", "dividend_yield": "value",
    "momentum_20d": "momentum", "momentum_60d": "momentum",
    "momentum_120d": "momentum", "volume_momentum": "momentum",
    "roe": "quality", "roa": "quality", "gross_margin": "quality",
    "debt_ratio": "quality", "cashflow_to_revenue": "quality",
    "revenue_growth_yoy": "growth", "earnings_growth_yoy": "growth", "eps_growth": "growth",
    "volatility_60d": "volatility", "beta": "volatility",
    "ma_deviation": "technical", "rsi_signal": "technical",
    "macd_signal": "technical", "volume_anomaly": "technical",
}


def score_stock_factors(factors: dict) -> dict:
    """对单个股票的因子进行打分，返回分类得分和综合得分"""
    category_scores = {cat: {"raw": [], "weights": []} for cat in STOCK_FACTOR_WEIGHTS}

    for factor_name, value in factors.items():
        if factor_name not in STOCK_FACTOR_DIRECTION:
            continue
        direction = STOCK_FACTOR_DIRECTION[factor_name]
        category = FACTOR_TO_CATEGORY.get(factor_name)
        sub_weight = SUB_WEIGHT_MAP.get(factor_name, 0.1)

        # 原始因子值标准化到 0-100
        normalized = _normalize_factor(factor_name, value)
        category_scores[category]["raw"].append(normalized * direction)
        category_scores[category]["weights"].append(sub_weight)

    # 计算各类别得分
    final_category_scores = {}
    for cat, data in category_scores.items():
        if data["raw"]:
            total_w = sum(data["weights"]) or 1.0
            weighted = sum(r * w for r, w in zip(data["raw"], data["weights"])) / total_w
            final_category_scores[cat] = max(0, min(100, weighted + 50))  # 中心化为50
        else:
            final_category_scores[cat] = 50.0  # 缺数据给中性分

    # 加权综合得分
    total_score = 0.0
    for cat, weight in STOCK_FACTOR_WEIGHTS.items():
        total_score += final_category_scores.get(cat, 50.0) * weight

    result = {
        "total_score": round(total_score, 1),
        "category_scores": {k: round(v, 1) for k, v in final_category_scores.items()},
    }
    return result


def score_fund_factors(factors: dict) -> dict:
    """对基金因子打分"""
    total = 0.0
    total_weight = 0.0
    category_scores = {}

    for factor_name, value in factors.items():
        if factor_name not in FUND_FACTOR_DIRECTION:
            continue
        direction = FUND_FACTOR_DIRECTION[factor_name]
        weight = FUND_FACTOR_WEIGHTS.get(factor_name, 0.05)
        normalized = _normalize_factor(factor_name, value)
        score = max(0, min(100, normalized * direction + 50))
        total += score * weight
        total_weight += weight
        category_scores[factor_name] = round(score, 1)

    final = round(total / total_weight, 1) if total_weight > 0 else 50.0
    return {"total_score": final, "factor_scores": category_scores}


def _normalize_factor(factor_name: str, value: float) -> float:
    """将因子值映射到近似 Z-score，裁剪到 [-3, 3] 再映射到 [0, 100]"""
    # 基于经验设定各因子的均值和标准差用于标准化
    ranges = {
        "pe": (25, 40), "pb": (2, 3), "ps": (2, 4), "dividend_yield": (0.01, 0.03),
        "momentum_20d": (0.0, 0.08), "momentum_60d": (0.02, 0.15), "momentum_120d": (0.05, 0.25),
        "volume_momentum": (-0.2, 0.3),
        "roe": (0.08, 0.15), "roa": (0.03, 0.08), "gross_margin": (0.25, 0.15),
        "debt_ratio": (0.45, 0.20), "cashflow_to_revenue": (0.05, 0.15),
        "revenue_growth_yoy": (0.05, 0.20), "earnings_growth_yoy": (0.05, 0.25), "eps_growth": (0.05, 0.30),
        "volatility_60d": (0.30, 0.10), "beta": (1.0, 0.3),
        "ma_deviation": (0.0, 0.05), "rsi_signal": (0.0, 0.5), "macd_signal": (0.0, 0.5),
        "volume_anomaly": (0.5, 0.3),
        # 基金
        "return_1y": (0.0, 0.20), "return_3y": (0.15, 0.30), "annual_return_1y": (0.0, 0.20),
        "annual_return_3y": (0.05, 0.15), "max_drawdown": (0.20, 0.10),
        "sharpe_ratio": (0.5, 0.5), "sortino_ratio": (0.5, 0.5),
        "alpha": (0.0, 0.05), "manager_tenure": (3.0, 2.0), "fund_size": (20, 50),
    }
    mean_val, std_val = ranges.get(factor_name, (0, 1))
    if std_val == 0:
        return 0.0
    z_score = (value - mean_val) / std_val
    z_score = max(-3, min(3, z_score))
    return (z_score + 3) / 6 * 100  # 映射到 [0, 100]
