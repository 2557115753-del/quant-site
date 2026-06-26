"""基金筛选器"""
import pandas as pd
from data.manager import DataManager
from factors.fund_factors import calc_fund_factors
from factors.scoring import score_fund_factors
from config import FUND_FILTER
from utils.logger import logger


def screen_funds(data_mgr: DataManager, top_n: int = 10) -> pd.DataFrame:
    """筛选优质基金"""
    logger.info("获取基金列表...")
    fund_list = data_mgr.get_fund_list()
    if fund_list is None or fund_list.empty:
        logger.error("无法获取基金列表")
        return pd.DataFrame()

    # 尝试提取基金代码和名称
    code_col = _find_col(fund_list, ["基金代码", "code", "fund_code", "ts_code"])
    name_col = _find_col(fund_list, ["基金名称", "name", "fund_name"])

    if not code_col:
        logger.error("无法识别基金代码列")
        return pd.DataFrame()

    codes = fund_list[code_col].astype(str).tolist()
    names = {}
    if name_col:
        names = dict(zip(fund_list[code_col].astype(str), fund_list[name_col].astype(str)))

    # 获取指数基准
    try:
        benchmark = data_mgr.get_index_daily("000300", days=252)
    except Exception:
        benchmark = None

    results = []
    for i, code in enumerate(codes[:100]):  # 先分析前100只
        try:
            nav = data_mgr.get_fund_nav(code, years=3)
            if nav is None or nav.empty or len(nav) < 60:
                continue

            factors = calc_fund_factors(nav, benchmark)
            if not factors:
                continue

            # 基础过滤
            if "return_3y" in factors and factors["return_3y"] < FUND_FILTER["min_annual_return_3y"] * 3:
                continue
            if "max_drawdown" in factors and abs(factors["max_drawdown"]) > FUND_FILTER["max_drawdown_1y"]:
                continue

            scored = score_fund_factors(factors)
            scored["code"] = code
            scored["name"] = names.get(code, "")
            scored["factors"] = factors
            results.append(scored)
        except Exception as e:
            logger.debug(f"分析基金 {code} 失败: {e}")
            continue

        if (i + 1) % 20 == 0:
            logger.info(f"  基金进度: {i + 1}/100")

    if not results:
        logger.warning("没有符合条件的基金")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = df.sort_values("total_score", ascending=False)
    df["rank"] = range(1, len(df) + 1)
    return df.head(top_n)


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        for col in df.columns:
            if c.lower() in str(col).lower():
                return col
    return None
