"""数据源抽象基类"""
from abc import ABC, abstractmethod
import pandas as pd


class DataSource(ABC):
    """所有数据源必须实现的接口"""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        ...

    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表: code, name, market_cap, industry, board"""
        ...

    @abstractmethod
    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        """获取日K线: date, open, high, low, close, volume, turnover"""
        ...

    @abstractmethod
    def get_financial_data(self, code: str) -> pd.DataFrame:
        """获取财务数据: PE, PB, ROE, ROA, 营收增速等"""
        ...

    @abstractmethod
    def get_fund_list(self) -> pd.DataFrame:
        """获取基金列表"""
        ...

    @abstractmethod
    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        """获取基金净值历史"""
        ...

    @abstractmethod
    def get_index_daily(self, index_code: str, days: int = 250) -> pd.DataFrame:
        """获取指数日线(用于Beta计算)"""
        ...
