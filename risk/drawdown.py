"""回撤计算与监控"""
import numpy as np
import pandas as pd
from data.manager import DataManager
from config import RISK
from utils.logger import logger


def calc_max_drawdown(close: pd.Series) -> dict:
    """计算最大回撤及当前回撤"""
    cummax = close.cummax()
    drawdown = (close - cummax) / cummax
    max_dd = drawdown.min()
    current_dd = drawdown.iloc[-1]
    max_dd_date = drawdown.idxmin() if hasattr(drawdown, 'idxmin') else None

    return {
        "max_drawdown": round(float(max_dd) * 100, 2),
        "current_drawdown": round(float(current_dd) * 100, 2),
        "max_drawdown_date": str(max_dd_date)[:10] if max_dd_date is not None else "N/A",
    }


def check_drawdown_alert(current_drawdown: float) -> tuple[str, str]:
    """检查回撤预警等级"""
    abs_dd = abs(current_drawdown)
    if abs_dd >= RISK["drawdown_critical"]:
        return "red", f"!! 回撤超过{RISK['drawdown_critical']*100:.0f}%，强烈建议止损或减仓"
    elif abs_dd >= RISK["drawdown_warn"]:
        return "yellow", f"! 回撤超过{RISK['drawdown_warn']*100:.0f}%，注意风险"
    return "green", "回撤正常"


def monitor_watchlist(data_mgr: DataManager, watchlist: list[str]) -> list[dict]:
    """监控自选股/持仓的回撤情况"""
    results = []
    for code in watchlist:
        code = str(code).zfill(6)
        try:
            kline = data_mgr.get_daily_kline(code, days=250)
            if kline is None or kline.empty:
                continue
            close = kline["close"].astype(float)
            dd_info = calc_max_drawdown(close)
            alert_level, alert_msg = check_drawdown_alert(dd_info["current_drawdown"] / 100)
            dd_info["code"] = code
            dd_info["alert_level"] = alert_level
            dd_info["alert_msg"] = alert_msg
            dd_info["latest_price"] = round(float(close.iloc[-1]), 2)
            results.append(dd_info)
        except Exception as e:
            logger.error(f"监控 {code} 回撤失败: {e}")
    return results
