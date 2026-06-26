"""baostock 数据源 - 备选"""
import pandas as pd
from data.base import DataSource
from utils.logger import logger


class BaostockSource(DataSource):
    name = "baostock"

    def is_available(self) -> bool:
        try:
            import baostock as bs
            lg = bs.login()
            if lg.error_code == '0':
                bs.logout()
                return True
            return False
        except Exception:
            logger.warning("baostock 不可用")
            return False

    def _login(self):
        import baostock as bs
        bs.login()

    def _logout(self):
        import baostock as bs
        bs.logout()

    def get_stock_list(self) -> pd.DataFrame:
        import baostock as bs
        self._login()
        try:
            rs = bs.query_stock_basic()
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            df = pd.DataFrame(rows, columns=rs.fields)
            df = df[df["type"] == "1"]  # 只取A股
            df = df.rename(columns={"code": "code", "code_name": "name"})
            df["code"] = df["code"].astype(str).replace(r"^sh\.|^sz\.", "", regex=True)
            return df[["code", "name"]]
        except Exception as e:
            logger.error(f"baostock获取股票列表失败: {e}")
            raise
        finally:
            self._logout()

    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        import baostock as bs
        import datetime
        self._login()
        try:
            symbol = f"sh.{code}" if code.startswith(("6", "9")) else f"sz.{code}"
            end = datetime.date.today().strftime("%Y-%m-%d")
            start = (datetime.date.today() - datetime.timedelta(days=days + 50)).strftime("%Y-%m-%d")
            rs = bs.query_history_k_data_plus(
                symbol, "date,open,high,low,close,volume,amount",
                start_date=start, end_date=end,
                frequency="d", adjustflag="2"
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            df = pd.DataFrame(rows, columns=rs.fields)
            if df.empty:
                raise ValueError(f"baostock无K线数据: {code}")
            for col in ["open", "high", "low", "close", "volume", "amount"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").tail(days)
        except Exception as e:
            logger.error(f"baostock获取K线失败 {code}: {e}")
            raise
        finally:
            self._logout()

    def get_financial_data(self, code: str) -> pd.DataFrame:
        import baostock as bs
        self._login()
        try:
            symbol = f"sh.{code}" if code.startswith(("6", "9")) else f"sz.{code}"
            # 利润表
            rs_profit = bs.query_profit_data(code=symbol, year=2024, quarter=4)
            rows_p = []
            while rs_profit.next():
                rows_p.append(rs_profit.get_row_data())
            if not rows_p:
                return pd.DataFrame()
            df = pd.DataFrame(rows_p, columns=rs_profit.fields)
            return df
        except Exception as e:
            logger.error(f"baostock获取财务数据失败 {code}: {e}")
            raise
        finally:
            self._logout()

    def get_fund_list(self) -> pd.DataFrame:
        logger.warning("baostock不支持基金数据")
        return pd.DataFrame()

    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        logger.warning("baostock不支持基金净值")
        return pd.DataFrame()

    def get_index_daily(self, index_code: str = "000300", days: int = 250) -> pd.DataFrame:
        import baostock as bs
        import datetime
        self._login()
        try:
            end = datetime.date.today().strftime("%Y-%m-%d")
            start = (datetime.date.today() - datetime.timedelta(days=days + 50)).strftime("%Y-%m-%d")
            rs = bs.query_history_k_data_plus(
                f"sh.{index_code}", "date,close",
                start_date=start, end_date=end,
                frequency="d", adjustflag="2"
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            df = pd.DataFrame(rows, columns=rs.fields)
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date").tail(days)
        except Exception as e:
            logger.error(f"baostock获取指数数据失败: {e}")
            raise
        finally:
            self._logout()
