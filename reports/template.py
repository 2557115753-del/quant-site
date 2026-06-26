"""输出格式化 — 兼容Windows GBK编码"""
import sys
import io

# 强制UTF-8输出，解决Windows GBK编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import SIGNAL_LEVELS


def print_header(title: str):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_stock_signal(signal: dict, idx: int = 0):
    """打印单只股票的买入建议"""
    level = signal["level"]
    level_icon = {"强烈推荐": "[***]", "推荐买入": "[** ]", "持有/观望": "[*  ]", "建议减仓": "[---]"}.get(level, "")

    print(f"\n{'─' * 55}")
    print(f"  [{level}] {level_icon}  {signal['name']} ({signal['code']})")
    print(f"{'─' * 55}")
    print(f"  综合得分: {signal['score']}/100")

    # 分类得分
    cats = signal.get("category_scores", {})
    if cats:
        cat_labels = {"value": "价值", "momentum": "动量", "quality": "质量",
                       "growth": "成长", "volatility": "波动", "technical": "技术"}
        parts = []
        for k, label in cat_labels.items():
            s = cats.get(k, 50)
            stars = _stars(s)
            parts.append(f"{label}: {stars}")
        print(f"  {'  '.join(parts)}")

    if signal.get("current_price"):
        print(f"\n  现价: {signal['current_price']}")
    if signal.get("buy_range_low") and signal.get("buy_range_high"):
        print(f"  建议买入区间: {signal['buy_range_low']} - {signal['buy_range_high']}")

    sl = signal.get("stop_loss", {})
    if sl:
        print(f"  硬止损位: {sl.get('hard_stop', 'N/A')} ({sl.get('stop_loss_pct', 'N/A')}%)")
        if sl.get("trailing_stop"):
            print(f"  移动止盈: {sl.get('trailing_stop', 'N/A')}")

    pos = signal.get("position", {})
    if pos:
        print(f"  仓位建议: {pos.get('pct', 'N/A')}% (约 {pos.get('amount', 0):,.0f})")

    dd = signal.get("drawdown", {})
    if dd:
        print(f"  [!] 近60日最大回撤: {dd.get('percent', 'N/A')}% -- {dd.get('alert', '')}")

    if signal.get("pe"):
        pe_str = f"  PE(TTM): {signal['pe']:.1f}" if isinstance(signal['pe'], (int, float)) else f"  PE: {signal['pe']}"
        print(pe_str)


def print_fund_signal(signal: dict, idx: int = 0):
    """打印基金建议"""
    print(f"\n{'─' * 55}")
    print(f"  [{signal.get('rank', '?')}] {signal['name']} ({signal['code']})")
    print(f"{'─' * 55}")
    print(f"  综合得分: {signal['total_score']}/100")

    fs = signal.get("factor_scores", {})
    if fs:
        labels_map = {
            "return_1y": "近1年收益", "return_3y": "近3年收益",
            "sharpe_ratio": "Sharpe", "sortino_ratio": "Sortino",
            "max_drawdown": "最大回撤", "alpha": "Alpha",
        }
        for k, v in fs.items():
            label = labels_map.get(k, k)
            print(f"    {label}: {v}")

    factors = signal.get("factors", {})
    if factors.get("annual_return_3y"):
        print(f"  年化收益(3Y): {factors['annual_return_3y']*100:.1f}%")
    if factors.get("max_drawdown"):
        print(f"  最大回撤: {factors['max_drawdown']*100:.1f}%")


def print_risk_report(watchlist_results: list[dict]):
    """打印风险评估报告"""
    print_header("持仓风险评估")
    for item in watchlist_results:
        icon = {"red": "!!", "yellow": "!", "green": "OK"}.get(item["alert_level"], "??")
        print(f"\n  [{icon}] {item['code']}  现价: {item['latest_price']}")
        print(f"     当前回撤: {item['current_drawdown']}% | 最大回撤: {item['max_drawdown']}%")
        print(f"     {item['alert_msg']}")


def _stars(score: float) -> str:
    if score >= 80:
        return "5/5"
    elif score >= 65:
        return "4/5"
    elif score >= 50:
        return "3/5"
    elif score >= 35:
        return "2/5"
    return "1/5"


def print_disclaimer():
    print(f"\n{'=' * 60}")
    print("  [!] 免责声明")
    print("  量化模型仅供参考，不构成投资建议。")
    print("  股市有风险，入市需谨慎。请独立判断。")
    print(f"{'=' * 60}\n")
