"""tushare 数据源 - 备选（需token）"""
import pandas as pd
from data.base import DataSource
from utils.logger import logger
from config import DATA_SOURCES


class TushareSource(DataSource):
    name = "tushare"

    def _get_pro(self):
        import tushare as ts
        token = DATA_SOURCES.get("tushare", {}).get("token", "")
        if not token:
            raise ValueError("未配置 tushare token")
        ts.set_token(token)
        return ts.pro_api()

    def is_available(self) -> bool:
        try:
            pro = self._get_pro()
            pro.query("stock_basic", limit="1")
            return True
        except Exception:
            logger.warning("tushare 不可用(检查token)")
            return False

    def get_stock_list(self) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,name,market")
            df = df[df["market"].isin(["主板", "创业板", "科创板"])]
            df["code"] = df["ts_code"].str.split(".").str[0]
            return df[["code", "name"]]
        except Exception as e:
            logger.error(f"tushare获取股票列表失败: {e}")
            raise

    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            suffix = "SH" if code.startswith(("6", "9")) else "SZ"
            ts_code = f"{code}.{suffix}"
            end = pd.Timestamp.today().strftime("%Y%m%d")
            start = (pd.Timestamp.today() - pd.DateOffset(days=days + 50)).strftime("%Y%m%d")
            df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
            if df.empty:
                raise ValueError(f"tushare无K线数据: {code}")
            df = df.rename(columns={
                "trade_date": "date", "open": "open", "high": "high",
                "low": "low", "close": "close", "vol": "volume", "amount": "amount"
            })
            df["date"] = pd.to_datetime(df["date"])
            for c in ["open", "high", "low", "close", "volume", "amount"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            return df.sort_values("date").tail(days)
        except Exception as e:
            logger.error(f"tushare获取K线失败 {code}: {e}")
            raise

    def get_financial_data(self, code: str) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            suffix = "SH" if code.startswith(("6", "9")) else "SZ"
            ts_code = f"{code}.{suffix}"
            df = pro.fina_indicator(ts_code=ts_code)
            return df
        except Exception as e:
            logger.error(f"tushare获取财务数据失败 {code}: {e}")
            raise

    def get_fund_list(self) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            df = pro.fund_basic(market="E")
            return df
        except Exception as e:
            logger.error(f"tushare获取基金列表失败: {e}")
            raise

    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            end = pd.Timestamp.today().strftime("%Y%m%d")
            start = (pd.Timestamp.today() - pd.DateOffset(years=years)).strftime("%Y%m%d")
            df = pro.fund_nav(ts_code=code, start_date=start, end_date=end)
            if df.empty:
                raise ValueError(f"tushare无基金净值: {code}")
            df = df.rename(columns={"nav_date": "date", "unit_nav": "nav"})
            df["date"] = pd.to_datetime(df["date"])
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            return df.sort_values("date")[["date", "nav"]]
        except Exception as e:
            logger.error(f"tushare获取基金净值失败 {code}: {e}")
            raise

    def get_index_daily(self, index_code: str = "000300", days: int = 250) -> pd.DataFrame:
        try:
            pro = self._get_pro()
            end = pd.Timestamp.today().strftime("%Y%m%d")
            start = (pd.Timestamp.today() - pd.DateOffset(days=days + 50)).strftime("%Y%m%d")
            df = pro.index_daily(ts_code=f"{index_code}.SH", start_date=start, end_date=end)
            df = df.rename(columns={"trade_date": "date", "close": "close"})
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            return df.sort_values("date").tail(days)[["date", "close"]]
        except Exception as e:
            logger.error(f"tushare获取指数数据失败: {e}")
            raise
