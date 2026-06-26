"""基金因子计算"""
import numpy as np
import pandas as pd


def calc_fund_factors(nav_df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None,
                      fund_info: dict | None = None) -> dict:
    """计算基金评估因子"""
    if nav_df is None or nav_df.empty or len(nav_df) < 60:
        return {}
    nav = nav_df["nav"].astype(float)
    nav = nav.dropna()
    if len(nav) < 60:
        return {}

    returns = nav.pct_change().dropna()
    factors = {}

    # 收益因子
    for label, days in [("1y", 252), ("3y", 756)]:
        if len(returns) >= days:
            cumulative = (1 + returns.tail(days)).prod() - 1
            factors[f"return_{label}"] = float(cumulative)
            # 年化
            annual = (1 + cumulative) ** (252 / days) - 1
            factors[f"annual_return_{label}"] = float(annual)

    # 最大回撤
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    factors["max_drawdown"] = float(drawdown.min())

    # Sharpe 比率 (假设无风险利率 2.5%)
    rf = 0.025
    if len(returns) >= 60:
        excess = returns - rf / 252
        if excess.std() > 0:
            factors["sharpe_ratio"] = float(excess.mean() / excess.std() * np.sqrt(252))

    # Sortino 比率
    if len(returns) >= 60:
        downside = returns[returns < 0]
        if len(downside) > 0 and downside.std() > 0:
            factors["sortino_ratio"] = float(excess.mean() / downside.std() * np.sqrt(252))

    # Alpha (相对基准)
    if benchmark_df is not None and not benchmark_df.empty:
        bench_close = benchmark_df["close"].astype(float)
        bench_returns = bench_close.pct_change().dropna()
        common = returns.index.intersection(bench_returns.index)
        if len(common) >= 30:
            r = returns.loc[common]
            br = bench_returns.loc[common]
            cov = np.cov(r, br)[0][1]
            beta = cov / np.var(br) if np.var(br) > 0 else 1.0
            alpha = r.mean() - rf / 252 - beta * (br.mean() - rf / 252)
            factors["alpha"] = float(alpha * 252)
            factors["beta"] = float(beta)

    # 基金信息
    if fund_info:
        if "manager_tenure" in fund_info:
            factors["manager_tenure"] = fund_info["manager_tenure"]
        if "fund_size" in fund_info:
            factors["fund_size"] = fund_info["fund_size"]

    return factors
