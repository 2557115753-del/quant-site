"""股票筛选器 — 多因子综合筛选"""
import pandas as pd
from data.manager import DataManager
from factors.stock_factors import calc_all_stock_factors
from factors.scoring import score_stock_factors
from config import STOCK_POOL
from utils.logger import logger


def screen_stocks(data_mgr: DataManager, top_n: int = 20,
                  watchlist: list[str] | None = None) -> pd.DataFrame:
    """筛选优质股票并返回Top N"""
    logger.info("获取A股股票列表...")
    all_stocks = data_mgr.get_stock_list()
    if all_stocks.empty:
        logger.error("无法获取股票列表")
        return pd.DataFrame()

    # 过滤：市值 >= 50亿
    if "market_cap" in all_stocks.columns:
        all_stocks["market_cap_num"] = pd.to_numeric(all_stocks["market_cap"], errors="coerce")
        all_stocks = all_stocks[all_stocks["market_cap_num"] >= STOCK_POOL["min_market_cap"] * 1e8]

    # 如果指定了自选股，只检查自选股
    if watchlist:
        all_stocks = all_stocks[all_stocks["code"].astype(str).isin([str(w).zfill(6) for w in watchlist])]

    if all_stocks.empty:
        logger.warning("无符合条件的股票")
        return pd.DataFrame()

    codes = all_stocks["code"].astype(str).str.zfill(6).tolist()
    names = dict(zip(all_stocks["code"].astype(str).str.zfill(6), all_stocks.get("name", codes)))

    # 获取指数K线用于Beta计算
    logger.info("获取沪深300基准数据...")
    try:
        index_kline = data_mgr.get_index_daily("000300", days=250)
    except Exception:
        index_kline = None

    results = []
    total = len(codes)
    logger.info(f"开始分析 {total} 只股票...")

    for i, code in enumerate(codes):
        try:
            kline = data_mgr.get_daily_kline(code, days=250)
            if kline is None or kline.empty:
                continue

            financial = pd.DataFrame()
            try:
                financial = data_mgr.get_financial_data(code)
            except Exception:
                pass

            factors = calc_all_stock_factors(financial, kline, index_kline)
            if not factors:
                continue

            scored = score_stock_factors(factors)
            scored["code"] = code
            scored["name"] = names.get(code, "")
            scored["factors"] = factors

            # 提取关键指标
            close = kline["close"].astype(float)
            scored["latest_price"] = round(float(close.iloc[-1]), 2)
            if pd.to_numeric(financial.get("pe", pd.Series([None])), errors="coerce").dropna().size > 0:
                scored["pe"] = float(pd.to_numeric(financial["pe"], errors="coerce").iloc[0])

            results.append(scored)
        except Exception as e:
            logger.debug(f"分析 {code} 失败: {e}")
            continue

        if (i + 1) % 50 == 0:
            logger.info(f"  进度: {i + 1}/{total}")

    if not results:
        logger.warning("没有成功分析的股票")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = df.sort_values("total_score", ascending=False)
    df["rank"] = range(1, len(df) + 1)
    return df.head(top_n)
