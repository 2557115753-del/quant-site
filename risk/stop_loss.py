"""止损/止盈信号"""
import numpy as np
import pandas as pd
from config import RISK


def calc_atr(kline: pd.DataFrame, period: int = 14) -> float:
    """计算ATR（平均真实波幅）"""
    if kline is None or kline.empty or len(kline) < period:
        return 0.0
    high = kline["high"].astype(float)
    low = kline["low"].astype(float)
    close = kline["close"].astype(float)

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return float(atr) if pd.notna(atr) else 0.0


def calc_stop_loss_price(kline: pd.DataFrame, entry_price: float) -> dict:
    """计算止损价和止盈价"""
    atr = calc_atr(kline, 14)
    current_price = float(kline["close"].astype(float).iloc[-1])

    stop_loss = entry_price - RISK["atr_stop_multiplier"] * atr if atr > 0 else entry_price * 0.93
    stop_loss = max(stop_loss, entry_price * 0.9)

    # 移动止盈：已盈利时，回撤10%止盈
    if current_price > entry_price:
        trailing_stop = current_price * (1 - RISK["trailing_stop"])
    else:
        trailing_stop = stop_loss

    return {
        "entry_price": round(entry_price, 2),
        "current_price": round(current_price, 2),
        "atr": round(atr, 2),
        "hard_stop": round(stop_loss, 2),
        "trailing_stop": round(trailing_stop, 2),
        "stop_loss_pct": round((stop_loss / entry_price - 1) * 100, 1),
        "pnl_pct": round((current_price / entry_price - 1) * 100, 1),
    }


def suggest_position_size(total_capital: float, stock_score: float,
                          volatility: float | None = None) -> float:
    """建议仓位大小"""
    base_pct = RISK["max_single_position"]

    # 得分越高，仓位越大
    score_mult = min(1.0, stock_score / 80) if stock_score > 0 else 0.3

    # 波动率越高，仓位越小
    vol_mult = 1.0
    if volatility is not None and volatility > 0:
        vol_mult = min(1.0, 0.25 / max(volatility, 0.15))

    position_pct = base_pct * score_mult * vol_mult
    position_amount = total_capital * position_pct

    return round(position_pct * 100, 1), round(position_amount, 0)
