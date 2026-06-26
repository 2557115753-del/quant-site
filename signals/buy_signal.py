"""买入信号生成 — 综合多因子得分 + 技术面 + 风险"""
import numpy as np
import pandas as pd
from config import SIGNAL_LEVELS, RISK
from risk.stop_loss import calc_atr, calc_stop_loss_price, suggest_position_size
from risk.drawdown import calc_max_drawdown, check_drawdown_alert
from utils.logger import logger


def generate_buy_signals(screened_stocks: pd.DataFrame, data_mgr,
                         total_capital: float = 100000) -> list[dict]:
    """为筛选出的股票生成买入建议"""
    signals = []

    for _, row in screened_stocks.iterrows():
        code = row["code"]
        score = row["total_score"]
        name = row.get("name", "")

        if score < RISK["min_score_threshold"]:
            continue

        # 确定信号等级
        if score >= SIGNAL_LEVELS["strong_buy"]:
            level = "强烈推荐"
        elif score >= SIGNAL_LEVELS["buy"]:
            level = "推荐买入"
        elif score >= SIGNAL_LEVELS["hold"]:
            level = "持有/观望"
        else:
            level = "建议减仓"

        # 获取最新K线用于技术分析
        try:
            kline = data_mgr.get_daily_kline(code, days=250)
        except Exception:
            kline = None

        stop_loss_info = {}
        position_info = {}
        drawdown_info = {}

        if kline is not None and not kline.empty:
            close = kline["close"].astype(float)
            current_price = float(close.iloc[-1])

            # 止损位
            stop_loss_info = calc_stop_loss_price(kline, current_price)

            # 建议买入区间
            atr = calc_atr(kline, 14)
            buy_low = round(current_price * 0.97, 2)
            buy_high = round(current_price * 1.02, 2)

            # 回撤
            dd_info = calc_max_drawdown(close)
            _, dd_msg = check_drawdown_alert(dd_info["current_drawdown"] / 100)
            drawdown_info = {"percent": dd_info["current_drawdown"], "alert": dd_msg}

            # 仓位建议
            volatility = row.get("factors", {}).get("volatility_60d")
            pos_pct, pos_amt = suggest_position_size(total_capital, score, volatility)
            position_info = {"pct": pos_pct, "amount": pos_amt}
        else:
            buy_low = buy_high = 0
            current_price = 0

        signal = {
            "code": code,
            "name": name,
            "level": level,
            "score": score,
            "category_scores": row.get("category_scores", {}),
            "current_price": current_price,
            "buy_range_low": buy_low,
            "buy_range_high": buy_high,
            "stop_loss": stop_loss_info,
            "position": position_info,
            "drawdown": drawdown_info,
            "pe": row.get("pe"),
        }
        signals.append(signal)

    return signals
