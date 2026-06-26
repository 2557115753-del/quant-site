"""数据源管理器 — 按优先级故障切换 + 交叉验证 + 缓存"""
import pandas as pd
from data.akshare_source import AkshareSource
from data.baostock_source import BaostockSource
from data.efinance_source import EfinanceSource
from data.tushare_source import TushareSource
from data.base import DataSource
from config import DATA_SOURCES, CROSS_VALIDATION_ENABLED, CROSS_VALIDATION_MAX_DEVIATION
from utils.cache import get_cache, set_cache
from utils.logger import logger


class DataManager:
    """统一数据入口，自动故障切换和缓存"""

    def __init__(self):
        self.sources: list[DataSource] = []
        self._init_sources()

    def _init_sources(self):
        source_classes = {
            "akshare": AkshareSource,
            "baostock": BaostockSource,
            "efinance": EfinanceSource,
            "tushare": TushareSource,
        }
        enabled = []
        for name, cfg in sorted(DATA_SOURCES.items(), key=lambda x: x[1]["priority"]):
            if not cfg.get("enabled", True):
                continue
            cls = source_classes.get(name)
            if cls is None:
                continue
            src = cls()
            if src.is_available():
                enabled.append(src)
                logger.info(f"数据源 [{src.name}] 已就绪 (优先级{cfg['priority']})")
            else:
                logger.warning(f"数据源 [{name}] 不可用，已跳过")
        if not enabled:
            raise RuntimeError("所有数据源均不可用！")
        self.sources = enabled

    def _try_sources(self, method: str, *args, cache_key: str = None, cache_ttl: int = None, **kwargs):
        """按优先级尝试数据源，失败则切换"""
        # 先查缓存
        if cache_key and cache_ttl:
            cached = get_cache(cache_key, cache_ttl)
            if cached is not None and not cached.empty:
                return cached

        errors = []
        for src in self.sources:
            try:
                result = getattr(src, method)(*args, **kwargs)
                if isinstance(result, pd.DataFrame) and result.empty:
                    errors.append(f"{src.name}: 返回空数据")
                    continue
                # 写入缓存
                if cache_key and isinstance(result, pd.DataFrame) and not result.empty:
                    set_cache(cache_key, result)
                return result
            except Exception as e:
                errors.append(f"{src.name}: {e}")
                logger.warning(f"数据源 [{src.name}] {method} 失败，尝试下一个...")
                continue

        raise RuntimeError(f"所有数据源 {method} 均失败: {'; '.join(errors)}")

    def _cross_validate(self, method: str, *args, **kwargs):
        """用两个数据源交叉验证关键数据"""
        if not CROSS_VALIDATION_ENABLED or len(self.sources) < 2:
            return None  # 无法交叉验证

        results = []
        for src in self.sources[:2]:
            try:
                result = getattr(src, method)(*args, **kwargs)
                if isinstance(result, pd.DataFrame) and not result.empty:
                    results.append((src.name, result))
            except Exception:
                continue

        if len(results) < 2:
            return None  # 只有1个数据源成功

        name_a, df_a = results[0]
        name_b, df_b = results[1]

        # 比对数值列
        common_cols = set(df_a.columns) & set(df_b.columns)
        numeric_cols = [c for c in common_cols if df_a[c].dtype in ("float64", "int64")]
        if not numeric_cols:
            return None

        for col in numeric_cols[:5]:
            val_a = df_a[col].mean()
            val_b = df_b[col].mean()
            if val_a == 0 and val_b == 0:
                continue
            if val_a == 0 or val_b == 0:
                deviation = 1.0
            else:
                deviation = abs(val_a - val_b) / max(abs(val_a), abs(val_b))
            if deviation > CROSS_VALIDATION_MAX_DEVIATION:
                logger.warning(
                    f"交叉验证: {name_a} vs {name_b} [{col}] 偏差 {deviation:.1%} > {CROSS_VALIDATION_MAX_DEVIATION:.0%}"
                )
        return None

    # ---- 对外接口 ----

    def get_stock_list(self) -> pd.DataFrame:
        return self._try_sources(
            "get_stock_list",
            cache_key="stock_list",
            cache_ttl=24
        )

    def get_daily_kline(self, code: str, days: int = 250) -> pd.DataFrame:
        return self._try_sources(
            "get_daily_kline", code, days=days,
            cache_key=f"kline_{code}_{days}",
            cache_ttl=6
        )

    def get_financial_data(self, code: str) -> pd.DataFrame:
        self._cross_validate("get_financial_data", code)
        return self._try_sources(
            "get_financial_data", code,
            cache_key=f"fin_{code}",
            cache_ttl=72
        )

    def get_fund_list(self) -> pd.DataFrame:
        return self._try_sources(
            "get_fund_list",
            cache_key="fund_list",
            cache_ttl=24
        )

    def get_fund_nav(self, code: str, years: int = 3) -> pd.DataFrame:
        return self._try_sources(
            "get_fund_nav", code, years=years,
            cache_key=f"nav_{code}_{years}",
            cache_ttl=6
        )

    def get_index_daily(self, index_code: str = "000300", days: int = 250) -> pd.DataFrame:
        return self._try_sources(
            "get_index_daily", index_code, days=days,
            cache_key=f"idx_{index_code}_{days}",
            cache_ttl=6
        )
