"""akshare 数据源 - 主数据源"""
import pandas as pd
import numpy as np
from data.base import DataSource
from utils.logger import logger


class AkshareSource(DataSource):
    name = "akshare"

    def is_available(self) -> bool:
        try:
            import akshare as ak
            return True
        except Exception:
            logger.warning("akshare 不可用")
            return False

    def get_stock_list(self) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_info_a_code_name()
            df = df.rename(columns={"code": "code", "name": "name"})
            df["code"] = df["code"].astype(str).str.zfill(6)
            # 获取市值信息
            try:
                mkt = ak.stock_a_indicator_lg(symbol="all")
                mkt = mkt.rename(columns={"code": "code", "pe": "pe", "pb": "pb", "total_mv": "market_cap"})
            except Exception:
                mkt = pd.DataFrame()
            if not mkt.empty:
                df = df.merge(mkt[["code", "pe", "pb", "market_cap"]], on="code", how="left")
            return df
        except Exception as e:
            logger.error(f"akshare获取股票列表失败: {e}")
            raise

    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if df.empty:
                raise ValueError(f"无K线数据: {code}")
            df = df.rename(columns={
                "日期": "date", "开盘": "open", "最高": "high",
                "最低": "low", "收盘": "close", "成交量": "volume",
                "成交额": "amount"
            })
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").tail(days)
            return df[["date", "open", "high", "low", "close", "volume", "amount"]]
        except Exception as e:
            logger.error(f"akshare获取K线失败 {code}: {e}")
            raise

    def get_financial_data(self, code: str) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            if df.empty:
                return pd.DataFrame()
            return df
        except Exception:
            try:
                indicators = ak.stock_a_indicator_lg(symbol=code)
                return indicators
            except Exception as e:
                logger.error(f"akshare获取财务数据失败 {code}: {e}")
                raise

    def get_fund_list(self) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.fund_open_fund_rank_em(symbol="全部")
            return df
        except Exception as e:
            logger.error(f"akshare获取基金列表失败: {e}")
            raise

    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is None or df.empty:
                df = ak.fund_nav_em(symbol=code)
            if df is not None and not df.empty:
                date_col = [c for c in df.columns if "日期" in c or "date" in str(c).lower()]
                nav_col = [c for c in df.columns if "单位净值" in c or "nav" in str(c).lower() or "累计净值" in c]
                if date_col and nav_col:
                    df = df.rename(columns={date_col[0]: "date", nav_col[0]: "nav"})
                    df["date"] = pd.to_datetime(df["date"])
                    cutoff = df["date"].max() - pd.DateOffset(years=years)
                    df = df[df["date"] >= cutoff]
                    return df[["date", "nav"]]
            raise ValueError(f"无净值数据: {code}")
        except Exception as e:
            logger.error(f"akshare获取基金净值失败 {code}: {e}")
            raise

    def get_index_daily(self, index_code: str = "000300", days: int = 250) -> pd.DataFrame:
        import akshare as ak
        try:
            df = ak.stock_zh_index_daily(symbol=f"sh{index_code}")
            df = df.rename(columns={"date": "date", "close": "close"})
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").tail(days)
        except Exception as e:
            logger.error(f"akshare获取指数数据失败: {e}")
            raise
