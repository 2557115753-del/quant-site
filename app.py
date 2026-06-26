# -*- coding: utf-8 -*-
"""A股量化选股模型 — Streamlit版 + 面包多支付"""
import sys, os, json, time, requests, datetime
import streamlit as st
import pandas as pd

# Add quant engine to path
QUANT_PATH = r"C:\Users\25571\quant-model"
sys.path.insert(0, QUANT_PATH)
os.chdir(QUANT_PATH)

st.set_page_config(page_title="📈 A股多因子量化选股", page_icon="📈", layout="wide")

# 配置
MB_PRODUCT_URL = "https://mbd.pub/你的产品链接"
PAYMENT_SERVER = "https://你的服务器.vercel.app"
PRICE = "¥0.9"

def verify_payment(order_id):
    if not order_id or not order_id.strip():
        return False, ""
    try:
        url = f"{PAYMENT_SERVER}/api/verify?order_id={order_id.strip()}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("paid"):
            return True, data.get("data", {}).get("token", "")
        return False, ""
    except:
        return False, ""

# Session state
if "verified" not in st.session_state:
    st.session_state.verified = False
    st.session_state.paid_token = None
    qp = st.query_params.to_dict() if hasattr(st, "query_params") else {}
    token = qp.get("token", "")
    if token:
        st.session_state.paid_token = token
        st.session_state.verified = True

# Custom CSS
st.markdown("""
<style>
.stApp {background:linear-gradient(180deg,#0a0e17,#111827,#0f1729)}
h1,h2,h3 {color:#e2e8f0}
.stButton>button {border-radius:10px;font-weight:600;border:none;transition:0.3s}
.stButton>button:hover {transform:translateY(-1px)}
.stTextInput>div>div>input {border-radius:8px}
.stSelectbox>div>div>select {border-radius:8px}
.paywall {background:linear-gradient(135deg,rgba(255,107,53,0.1),rgba(249,115,22,0.05));
    border:2px solid rgba(255,107,53,0.3);border-radius:20px;padding:50px 30px;text-align:center}
.stock-card {background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
    border-radius:14px;padding:20px;margin:8px 0;transition:0.2s}
.stock-card:hover {border-color:rgba(255,107,53,0.3);background:rgba(255,255,255,0.05)}
.badge-buy {background:rgba(34,197,94,0.15);color:#4ade80;padding:2px 10px;border-radius:6px;font-size:13px}
.badge-strong {background:rgba(255,215,0,0.15);color:#ffd700;padding:2px 10px;border-radius:6px;font-size:13px}
.metric-box {text-align:center;background:rgba(255,255,255,0.03);border-radius:12px;padding:15px 10px}
</style>
""", unsafe_allow_html=True)

st.title("📈 A股多因子量化选股模型")
st.caption("数据源: akshare → baostock → efinance | 自动故障切换 + 交叉验证")

if not st.session_state.verified:
    # ══════════════════ PAYWALL ══════════════════
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="paywall">
            <div style="font-size:60px;margin-bottom:15px">📊</div>
            <h2 style="color:#ff6b35">多因子量化选股工具</h2>
            <p style="color:#94a3b8;font-size:15px;line-height:1.8">
                价值因子 · 动量因子 · 质量因子 · 成长因子<br>
                波动因子 · 技术因子 · 风险监控
            </p>
            <p style="color:#94a3b8;font-size:14px;margin-top:20px">
                每日更新 · AI驱动 · 实时筛选<br>
                仅需 <strong style="font-size:28px;color:#ffd700">{PRICE}</strong>
            </p>
            <br>
            <a href="{MB_PRODUCT_URL}" target="_blank" style="text-decoration:none;">
                <div style="background:linear-gradient(135deg,#FF6B35,#F7931E,#FFD700);color:#fff;
                    text-align:center;padding:18px 40px;border-radius:30px;font-size:18px;font-weight:bold;
                    cursor:pointer;display:inline-block;box-shadow:0 4px 20px rgba(255,107,53,0.4);">
                    💰 立即购买 {PRICE}
                </div>
            </a>
            <br><br>
            <p style="color:#ffd700;font-size:14px">支付后粘贴面包多订单号即可解锁</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        order_id = st.text_input("面包多订单号", placeholder="支付成功后复制订单号", key="mb_order")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔓 验证解锁", use_container_width=True, type="primary"):
                if order_id.strip():
                    with st.spinner("验证订单..."):
                        ok, token = verify_payment(order_id.strip())
                    if ok:
                        st.session_state.verified = True
                        st.session_state.paid_token = token
                        st.success("✅ 验证成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("订单未支付或无效，请先完成付款")
        with col_b:
            if st.button("🆓 免费试用", use_container_width=True):
                st.session_state.verified = True
                st.session_state.free_trial = True
                st.rerun()
        st.caption("免费试用每天限5次，付费用户不限次数")
    st.stop()

# ══════════════════ MAIN APP ══════════════════
# Free trial tracking
if st.session_state.get("free_trial"):
    st.warning("⚠️ 免费试用模式 — 每天限5次查询")

# Sidebar controls
with st.sidebar:
    st.markdown("### ⚙️ 参数设置")
    mode = st.selectbox("分析模式", ["股票筛选", "基金筛选", "风险监控", "完整分析"], index=0)
    top_n = st.slider("返回数量", 5, 50, 20, 5)
    watchlist_str = st.text_input("自选股监控 (逗号分隔)", placeholder="600519,000858")
    capital = st.number_input("资金量", value=100000, step=10000, format="%d")

    if st.button("🚀 开始分析", use_container_width=True, type="primary"):
        st.session_state.run_analysis = True

# Map mode to CLI args
mode_map = {"股票筛选":"stock","基金筛选":"fund","风险监控":"risk","完整分析":"full"}
cli_mode = mode_map.get(mode, "stock")

def run_quant_analysis(mode, top_n, watchlist, capital):
    """Run the quant engine and return results"""
    try:
        from data.manager import DataManager
        from screening.stock_screener import screen_stocks
        from screening.fund_screener import screen_funds
        from signals.buy_signal import generate_buy_signals
        from risk.drawdown import monitor_watchlist

        data_mgr = DataManager()
        results = {"mode": mode, "stocks": [], "funds": [], "risk": []}

        stocks = screen_stocks(data_mgr, top_n=top_n, watchlist=watchlist)
        if not stocks.empty:
            signals = generate_buy_signals(stocks, data_mgr, capital)
            results["stocks"] = signals

        if mode in ("fund", "full"):
            funds = screen_funds(data_mgr, top_n=top_n)
            if not funds.empty:
                results["funds"] = funds.to_dict("records")

        if mode == "risk" and watchlist:
            risk = monitor_watchlist(data_mgr, watchlist)
            results["risk"] = risk

        return results

    except Exception as e:
        return {"error": str(e)}

# Run analysis
if st.session_state.get("run_analysis", False) or st.session_state.get("last_results"):
    watchlist = [c.strip() for c in watchlist_str.split(",") if c.strip()] if watchlist_str else []

    if st.session_state.get("run_analysis"):
        with st.spinner("🔄 正在获取市场数据并计算... 可能需要1-2分钟"):
            results = run_quant_analysis(cli_mode, top_n, watchlist, capital)
            st.session_state.last_results = results
            st.session_state.run_analysis = False
    else:
        results = st.session_state.last_results

    if "error" in results:
        st.error(f"分析出错: {results['error']}")
    else:
        signals = results.get("stocks", [])
        if signals:
            st.markdown("---")
            st.subheader(f"🏆 股票筛选结果 (Top {len(signals)})")

            strong = sum(1 for s in signals if s.get("level") == "强烈推荐")
            buy = sum(1 for s in signals if s.get("level") == "推荐买入")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"<div class='metric-box'><p style='color:#888;font-size:12px'>强烈推荐</p><p style='color:#ffd700;font-size:24px;font-weight:bold'>{strong}</p></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-box'><p style='color:#888;font-size:12px'>推荐买入</p><p style='color:#4ade80;font-size:24px;font-weight:bold'>{buy}</p></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-box'><p style='color:#888;font-size:12px'>总计</p><p style='color:#e2e8f0;font-size:24px;font-weight:bold'>{len(signals)}</p></div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='metric-box'><p style='color:#888;font-size:12px'>更新时间</p><p style='color:#e2e8f0;font-size:14px;font-weight:bold'>{datetime.datetime.now().strftime('%H:%M')}</p></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            for i, sig in enumerate(signals):
                level = sig.get("level", "")
                badge_class = "badge-strong" if level == "强烈推荐" else "badge-buy"
                score = sig.get("score", 0)
                name = sig.get("name", sig.get("code", ""))
                code = sig.get("code", "")

                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <span style="font-size:18px;font-weight:600;color:#e2e8f0">#{i+1} {name}</span>
                            <span style="color:#64748b;margin-left:10px">{code}</span>
                        </div>
                        <div style="display:flex;gap:10px;align-items:center">
                            <span class="{badge_class}">{level}</span>
                            <span style="color:#ffd700;font-size:24px;font-weight:bold">{score}</span>
                            <span style="color:#64748b;font-size:13px">分</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Show details for first stock
            if signals:
                st.markdown("---")
                st.subheader(f"📊 详细分解 — {signals[0].get('name', signals[0].get('code', ''))}")
                detail = signals[0]
                cols = st.columns(3)
                items = [
                    ("综合得分", f"{detail.get('score',0)}分", "#ffd700"),
                    ("PE分位", f"{detail.get('pe_percentile','N/A')}", "#4ade80"),
                    ("PB分位", f"{detail.get('pb_percentile','N/A')}", "#4ade80"),
                    ("ROE", f"{detail.get('roe','N/A')}", "#60a5fa"),
                    ("动量60日", f"{detail.get('momentum_60d','N/A')}", "#c084fc"),
                    ("波动率", f"{detail.get('volatility_60d','N/A')}", "#f472b6"),
                ]
                for i, (label, val, color) in enumerate(items):
                    with cols[i % 3]:
                        st.markdown(f"<div class='metric-box'><p style='color:#888;font-size:12px'>{label}</p><p style='color:{color};font-size:18px;font-weight:bold'>{val}</p></div>", unsafe_allow_html=True)

        # Fund results
        funds = results.get("funds", [])
        if funds:
            st.markdown("---")
            st.subheader(f"💰 基金筛选结果 ({len(funds)} 只)")
            for f in funds:
                st.markdown(f"""
                <div class="stock-card">
                    <span style="color:#e2e8f0">{f.get('name','')}</span>
                    <span style="color:#64748b;margin-left:10px">{f.get('code','')}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("⚠️ 本模型仅供参考，不构成投资建议。股市有风险，投资需谨慎。")

else:
    # Welcome / instruction page
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        ### 🚀 如何使用

        1. **左侧选择分析模式**
           - 股票筛选：多因子打分选出优质股票
           - 基金筛选：筛选优质基金
           - 风险监控：监控持仓回撤风险
           - 完整分析：以上全部

        2. **设置参数**
           - 返回数量、资金规模等

        3. **点击"开始分析"**
           - 系统自动获取市场数据
           - 计算多因子得分
           - 生成买卖信号

        ---
        ### 📊 因子体系
        """)

        cols = st.columns(3)
        factors = [
            ("💎", "价值因子", "PE/PB/PS分位\n股息率"),
            ("🚀", "动量因子", "20/60/120日\n动量信号"),
            ("🛡️", "质量因子", "ROE/ROA\n毛利率/负债率"),
        ]
        for i, (icon, name, desc) in enumerate(factors):
            with cols[i]:
                st.markdown(f"""
                <div style="text-align:center;padding:20px;background:rgba(255,255,255,0.03);border-radius:14px">
                    <div style="font-size:30px">{icon}</div>
                    <p style="color:#e2e8f0;font-weight:600">{name}</p>
                    <p style="color:#64748b;font-size:13px">{desc}</p>
                </div>
                """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("⚡ Powered by akshare/baostock/efinance | 🔒 面包多自动收款")
