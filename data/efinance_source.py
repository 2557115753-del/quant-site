"""efinance 数据源 - 备选（基于东方财富）"""
import pandas as pd
from data.base import DataSource
from utils.logger import logger


class EfinanceSource(DataSource):
    name = "efinance"

    def is_available(self) -> bool:
        try:
            import efinance as ef
            return True
        except Exception:
            logger.warning("efinance 不可用")
            return False

    def get_stock_list(self) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.stock.get_realtime_quotes()
            df = df.rename(columns={"股票代码": "code", "股票名称": "name", "总市值": "market_cap", "市盈率-动态": "pe"})
            df["code"] = df["code"].astype(str)
            return df[["code", "name"]]
        except Exception as e:
            logger.error(f"efinance获取股票列表失败: {e}")
            raise

    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.stock.get_quote_history(code, klt=1, beg=None, end=None)
            if df.empty:
                raise ValueError(f"efinance无K线数据: {code}")
            col_map = {c: c for c in df.columns}
            for c in df.columns:
                low = str(c).lower()
                if "日期" in str(c) or "date" in low:
                    col_map[c] = "date"
                elif "开盘" in str(c) or "open" in low:
                    col_map[c] = "open"
                elif "最高" in str(c) or "high" in low:
                    col_map[c] = "high"
                elif "最低" in str(c) or "low" in low:
                    col_map[c] = "low"
                elif "收盘" in str(c) or "close" in low:
                    col_map[c] = "close"
                elif "成交量" in str(c) or "volume" in low:
                    col_map[c] = "volume"
                elif "成交额" in str(c) or "amount" in low:
                    col_map[c] = "amount"
            df = df.rename(columns=col_map)
            needed = ["date", "open", "high", "low", "close"]
            for c in needed:
                if c not in df.columns:
                    raise ValueError(f"efinance K线缺少列: {c}")
            df["date"] = pd.to_datetime(df["date"])
            for c in ["open", "high", "low", "close"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            return df.sort_values("date").tail(days)
        except Exception as e:
            logger.error(f"efinance获取K线失败 {code}: {e}")
            raise

    def get_financial_data(self, code: str) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.stock.get_base_info(code)
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"efinance获取财务数据失败 {code}: {e}")
            raise

    def get_fund_list(self) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.fund.get_open_fund_rank()
            return df
        except Exception as e:
            logger.error(f"efinance获取基金列表失败: {e}")
            raise

    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.fund.get_quote_history(code)
            if df is not None and not df.empty:
                date_col = [c for c in df.columns if "日期" in str(c) or "date" in str(c).lower()]
                nav_col = [c for c in df.columns if "单位净值" in str(c) or "nav" in str(c).lower()]
                if date_col and nav_col:
                    df = df.rename(columns={date_col[0]: "date", nav_col[0]: "nav"})
                    df["date"] = pd.to_datetime(df["date"])
                    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
                    cutoff = df["date"].max() - pd.DateOffset(years=years)
                    df = df[df["date"] >= cutoff]
                    return df[["date", "nav"]].dropna()
            raise ValueError(f"efinance无基金净值: {code}")
        except Exception as e:
            logger.error(f"efinance获取基金净值失败 {code}: {e}")
            raise

    def get_index_daily(self, index_code: str = "000300", days: int = 250) -> pd.DataFrame:
        import efinance as ef
        try:
            df = ef.stock.get_quote_history(index_code, klt=1)
            if df is not None and not df.empty:
                for c in df.columns:
                    low = str(c).lower()
                    if "日期" in str(c) or "date" in low:
                        df = df.rename(columns={c: "date"})
                    elif "收盘" in str(c) or "close" in low:
                        df = df.rename(columns={c: "close"})
                df["date"] = pd.to_datetime(df["date"])
                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                return df.sort_values("date").tail(days)[["date", "close"]]
            raise ValueError(f"efinance无指数数据")
        except Exception as e:
            logger.error(f"efinance获取指数数据失败: {e}")
            raise
