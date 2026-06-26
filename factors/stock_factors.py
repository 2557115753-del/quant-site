"""股票多因子计算 — 6大类 20+因子"""
import numpy as np
import pandas as pd
from config import (
    VALUE_SUB_WEIGHTS, MOMENTUM_SUB_WEIGHTS, QUALITY_SUB_WEIGHTS,
    GROWTH_SUB_WEIGHTS, VOLATILITY_SUB_WEIGHTS, TECHNICAL_SUB_WEIGHTS,
)


def calc_value_factors(financial: pd.DataFrame, kline: pd.DataFrame) -> dict:
    """价值因子：PE分位、PB分位、PS分位、股息率"""
    factors = {}
    if financial is not None and not financial.empty:
        pe_col = _find_col(financial, ["pe", "市盈率", "pe_ttm"])
        pb_col = _find_col(financial, ["pb", "市净率"])
        ps_col = _find_col(financial, ["ps", "ps_ttm", "市销率"])
        div_col = _find_col(financial, ["dividend_yield", "股息率"])

        for name, col in [("pe", pe_col), ("pb", pb_col), ("ps", ps_col), ("dividend_yield", div_col)]:
            if col:
                val = pd.to_numeric(financial[col], errors="coerce").dropna()
                if not val.empty:
                    factors[name] = float(val.iloc[0])
    return factors


def calc_momentum_factors(kline: pd.DataFrame) -> dict:
    """动量因子：20/60/120日收益、成交量动量"""
    if kline is None or kline.empty:
        return {}
    close = kline["close"].astype(float)
    volume = kline.get("volume", pd.Series(dtype=float)).astype(float)

    factors = {}
    for d in [20, 60, 120]:
        if len(close) >= d:
            factors[f"momentum_{d}d"] = float(close.iloc[-1] / close.iloc[-d] - 1)

    if len(volume) >= 20:
        vol_short = volume.iloc[-5:].mean()
        vol_long = volume.iloc[-20:].mean()
        if vol_long > 0:
            factors["volume_momentum"] = float(vol_short / vol_long - 1)
    return factors


def calc_quality_factors(financial: pd.DataFrame) -> dict:
    """质量因子：ROE、ROA、毛利率、资产负债率、经营现金流/营收"""
    if financial is None or financial.empty:
        return {}
    factors = {}
    mapping = [
        ("roe", ["roe", "净资产收益率"]),
        ("roa", ["roa", "总资产收益率"]),
        ("gross_margin", ["grossprofit_margin", "gross_margin", "毛利率"]),
        ("debt_ratio", ["debt_to_assets", "debt_ratio", "资产负债率"]),
        ("cashflow_to_revenue", ["ocf_to_revenue", "cf_sales", "经营现金流/营收"]),
    ]
    for key, candidates in mapping:
        col = _find_col(financial, candidates)
        if col:
            val = pd.to_numeric(financial[col], errors="coerce").dropna()
            if not val.empty:
                factors[key] = float(val.iloc[0])
    return factors


def calc_growth_factors(financial: pd.DataFrame) -> dict:
    """成长因子：营收增速、净利润增速、EPS增速"""
    if financial is None or financial.empty:
        return {}
    factors = {}
    mapping = [
        ("revenue_growth_yoy", ["or_yoy", "revenue_yoy", "营业收入同比增长率", "revenue_growth"]),
        ("earnings_growth_yoy", ["profit_yoy", "earnings_yoy", "净利润同比增长率", "earnings_growth"]),
        ("eps_growth", ["eps_yoy", "eps_growth", "基本每股收益增长率"]),
    ]
    for key, candidates in mapping:
        col = _find_col(financial, candidates)
        if col:
            vals = pd.to_numeric(financial[col], errors="coerce").dropna()
            if not vals.empty:
                factors[key] = float(vals.iloc[0])
    return factors


def calc_volatility_factors(kline: pd.DataFrame, index_kline: pd.DataFrame | None = None) -> dict:
    """波动因子：60日波动率、Beta"""
    if kline is None or kline.empty:
        return {}
    close = kline["close"].astype(float)
    factors = {}
    if len(close) >= 60:
        returns = close.pct_change().dropna().tail(60)
        factors["volatility_60d"] = float(returns.std() * np.sqrt(252))

        if index_kline is not None and not index_kline.empty:
            idx_close = index_kline["close"].astype(float)
            idx_returns = idx_close.pct_change().dropna()
            common_dates = returns.index.intersection(idx_returns.index)
            if len(common_dates) >= 30:
                r = returns.loc[common_dates]
                ir = idx_returns.loc[common_dates]
                cov = np.cov(r, ir)[0][1]
                var = np.var(ir)
                factors["beta"] = float(cov / var) if var > 0 else 1.0
    return factors


def calc_technical_factors(kline: pd.DataFrame) -> dict:
    """技术因子：MA偏离度、RSI、MACD信号、成交量异动"""
    if kline is None or kline.empty:
        return {}
    close = kline["close"].astype(float)
    volume = kline.get("volume", pd.Series(dtype=float)).astype(float)
    factors = {}

    # MA偏离度
    for d in [20, 60]:
        if len(close) >= d:
            ma = close.rolling(d).mean()
            deviation = (close.iloc[-1] / ma.iloc[-1] - 1) if ma.iloc[-1] > 0 else 0
            if d == 20:
                factors["ma_deviation"] = float(deviation)

    # RSI 信号
    if len(close) >= 15:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        if pd.notna(rsi_val):
            if rsi_val < 30:
                factors["rsi_signal"] = 1.0  # 超卖，利好
            elif rsi_val > 70:
                factors["rsi_signal"] = -1.0  # 超买，利空
            else:
                factors["rsi_signal"] = 0.0

    # MACD 信号
    if len(close) >= 26:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        factors["macd_signal"] = float(1.0 if macd.iloc[-1] > signal.iloc[-1] else -1.0)

    # 成交量异动
    if len(volume) >= 20:
        avg_vol = volume.rolling(20).mean()
        if avg_vol.iloc[-1] > 0:
            ratio = volume.iloc[-1] / avg_vol.iloc[-1]
            factors["volume_anomaly"] = float(min(ratio, 3.0) / 3.0)

    return factors


def calc_all_stock_factors(financial: pd.DataFrame, kline: pd.DataFrame,
                           index_kline: pd.DataFrame | None = None) -> dict:
    """汇总全部股票因子"""
    all_factors = {}
    all_factors.update(calc_value_factors(financial, kline))
    all_factors.update(calc_momentum_factors(kline))
    all_factors.update(calc_quality_factors(financial))
    all_factors.update(calc_growth_factors(financial))
    all_factors.update(calc_volatility_factors(kline, index_kline))
    all_factors.update(calc_technical_factors(kline))
    return all_factors


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """在DataFrame中查找匹配列名"""
    for c in candidates:
        for col in df.columns:
            if c.lower() in str(col).lower():
                return col
    return None
