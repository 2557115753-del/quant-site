import os
import json
import hashlib
import time
from datetime import datetime, timedelta
import pandas as pd
from config import CACHE_DIR, CACHE_TTL_HOURS


def _cache_path(key: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe_key = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{safe_key}.json")


def get_cache(key: str, ttl_hours: int) -> pd.DataFrame | None:
    """读取缓存，过期返回None"""
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - cached_time > timedelta(hours=ttl_hours):
            return None
        return pd.DataFrame(data["payload"])
    except Exception:
        return None


def set_cache(key: str, df: pd.DataFrame):
    """写入缓存"""
    path = _cache_path(key)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "payload": df.to_dict(orient="records"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, default=str)
