"""组合风险评估"""
import pandas as pd
from config import RISK


def check_portfolio_risk(positions: list[dict]) -> dict:
    """检查组合风险
    positions: [{"code": "..", "weight": 0.1, "industry": "..."}]
    """
    alerts = []
    total_weight = sum(p["weight"] for p in positions)

    # 单只股票权重
    for p in positions:
        if p["weight"] > RISK["max_single_position"]:
            alerts.append(f"{p['code']} 权重 {p['weight']*100:.1f}% 超过上限 {RISK['max_single_position']*100:.0f}%")

    # 行业集中度
    industry_weights = {}
    for p in positions:
        ind = p.get("industry", "未知")
        industry_weights[ind] = industry_weights.get(ind, 0) + p["weight"]

    for ind, w in industry_weights.items():
        if w > RISK["max_industry_exposure"]:
            alerts.append(f"行业 [{ind}] 敞口 {w*100:.1f}% 超过上限 {RISK['max_industry_exposure']*100:.0f}%")

    return {
        "total_weight": round(total_weight * 100, 1),
        "num_positions": len(positions),
        "alerts": alerts,
        "industry_weights": {k: round(v * 100, 1) for k, v in industry_weights.items()},
        "risk_level": "high" if len(alerts) > 2 else ("medium" if alerts else "low"),
    }
