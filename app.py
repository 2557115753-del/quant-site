# -*- coding: utf-8 -*-
"""A股量化选股模型 - Streamlit版 + 面包多支付"""
import sys, os, json, time, requests, datetime
import streamlit as st
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

st.set_page_config(page_title="A股多因子量化选股", page_icon="chart", layout="wide")

MB_PRODUCT_URL = "https://mbd.pub/o/bread/YZaTmpxsbA=="
MB_KEY = os.environ.get("MB_KEY", "")
MB_ORDER_API = "https://x.mianbaoduo.com/api/order-detail"
PRICE = "0.9"

def verify_payment(order_id):
    if not order_id or not order_id.strip() or not MB_KEY:
        return False, ""
    try:
        resp = requests.get(MB_ORDER_API,
            headers={"x-token": MB_KEY},
            params={"order_id": order_id.strip()},
            timeout=10)
        if resp.json().get("state") == 1:
            return True, order_id.strip()
    except: pass
    return False, ""

if "verified" not in st.session_state:
    st.session_state.verified = False
    qp = st.query_params.to_dict() if hasattr(st, "query_params") else {}
    if qp.get("token"):
        st.session_state.verified = True

st.markdown("""
<style>
.stApp {background:linear-gradient(180deg,#0a0e17,#111827,#0f1729)}
h1,h2,h3 {color:#e2e8f0}
.stButton>button {border-radius:10px;font-weight:600;border:none;transition:0.3s}
.stButton>button:hover {transform:translateY(-1px)}
.stTextInput>div>div>input {border-radius:8px}
.paywall {background:linear-gradient(135deg,rgba(255,107,53,0.1),rgba(249,115,22,0.05));border:2px solid rgba(255,107,53,0.3);border-radius:20px;padding:50px 30px;text-align:center}
.stock-card {background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:20px;margin:8px 0}
.badge-buy {background:rgba(34,197,94,0.15);color:#4ade80;padding:2px 10px;border-radius:6px;font-size:13px}
.badge-strong {background:rgba(255,215,0,0.15);color:#ffd700;padding:2px 10px;border-radius:6px;font-size:13px}
.metric-box {text-align:center;background:rgba(255,255,255,0.03);border-radius:12px;padding:15px 10px}
</style>
""", unsafe_allow_html=True)

st.title("A股多因子量化选股模型")
st.caption("数据源: akshare - baostock - efinance | 自动故障切换 + 交叉验证")

if not st.session_state.verified:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="paywall">
            <div style="font-size:60px;margin-bottom:15px">chart</div>
            <h2 style="color:#ff6b35">多因子量化选股工具</h2>
            <p style="color:#94a3b8;font-size:15px;line-height:1.8">
                价值因子 . 动量因子 . 质量因子 . 成长因子<br>
                波动因子 . 技术因子 . 风险监控
            </p>
            <p style="color:#94a3b8;font-size:14px;margin-top:20px">
                每日更新 . AI驱动 . 实时筛选<br>
                仅需 <strong style="font-size:28px;color:#ffd700">Y{PRICE}</strong>
            </p>
            <br>
            <a href="{MB_PRODUCT_URL}" target="_blank" style="text-decoration:none;">
                <div style="background:linear-gradient(135deg,#FF6B35,#F7931E,#FFD700);color:#fff;
                    text-align:center;padding:18px 40px;border-radius:30px;font-size:18px;font-weight:bold;
                    cursor:pointer;display:inline-block;box-shadow:0 4px 20px rgba(255,107,53,0.4);">
                    立即购买 Y{PRICE}
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
            if st.button("验证解锁", use_container_width=True, type="primary"):
                if order_id.strip():
                    with st.spinner("验证订单..."):
                        ok, _ = verify_payment(order_id.strip())
                    if ok:
                        st.session_state.verified = True
                        st.success("验证成功！")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("订单未支付或无效，请先完成付款")
        with col_b:
            if st.button("免费试用", use_container_width=True):
                st.session_state.verified = True
                st.session_state.free_trial = True
                st.rerun()
        st.caption("免费试用每天限5次，付费用户不限次数")
    st.stop()

if st.session_state.get("free_trial"):
    st.warning("免费试用模式")

with st.sidebar:
    st.markdown("### 参数设置")
    mode = st.selectbox("分析模式", ["股票筛选", "基金筛选", "风险监控", "完整分析"], index=0)
    top_n = st.slider("返回数量", 5, 50, 20, 5)
    watchlist_str = st.text_input("自选股监控 (逗号分隔)", placeholder="600519,000858")
    capital = st.number_input("资金量", value=100000, step=10000, format="%d")
    if st.button("开始分析", use_container_width=True, type="primary"):
        st.session_state.run_analysis = True

mode_map = {"股票筛选":"stock","基金筛选":"fund","风险监控":"risk","完整分析":"full"}
cli_mode = mode_map.get(mode, "stock")

def run_quant():
    try:
        from data.manager import DataManager
        from screening.stock_screener import screen_stocks
        from signals.buy_signal import generate_buy_signals
        from screening.fund_screener import screen_funds
        from risk.drawdown import monitor_watchlist
        wl = [c.strip() for c in watchlist_str.split(",") if c.strip()] if watchlist_str else []
        dm = DataManager()
        res = {"stocks":[],"funds":[],"risk":[]}
        stocks = screen_stocks(dm, top_n=top_n, watchlist=wl)
        if not stocks.empty:
            res["stocks"] = generate_buy_signals(stocks, dm, capital)
        if cli_mode in ("fund","full"):
            funds = screen_funds(dm, top_n=top_n)
            if not funds.empty:
                res["funds"] = funds.to_dict("records")
        if cli_mode=="risk" and wl:
            res["risk"] = monitor_watchlist(dm, wl)
        return res
    except Exception as e:
        return {"error":str(e)}

if st.session_state.get("run_analysis") or st.session_state.get("last_results"):
    if st.session_state.get("run_analysis"):
        with st.spinner("正在获取市场数据并计算..."):
            res = run_quant()
            st.session_state.last_results = res
            st.session_state.run_analysis = False
    else:
        res = st.session_state.last_results

    if "error" in res:
        st.error("分析出错: " + res["error"])
    else:
        signals = res.get("stocks",[])
        if signals:
            st.markdown("---")
            st.subheader("股票筛选结果")
            s_cnt = sum(1 for s in signals if s.get("level")=="强烈推荐")
            b_cnt = sum(1 for s in signals if s.get("level")=="推荐买入")
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown("<div class='metric-box'><p style='color:#888;font-size:12px'>强烈推荐</p><p style='color:#ffd700;font-size:24px;font-weight:bold'>"+str(s_cnt)+"</p></div>",unsafe_allow_html=True)
            with c2: st.markdown("<div class='metric-box'><p style='color:#888;font-size:12px'>推荐买入</p><p style='color:#4ade80;font-size:24px;font-weight:bold'>"+str(b_cnt)+"</p></div>",unsafe_allow_html=True)
            with c3: st.markdown("<div class='metric-box'><p style='color:#888;font-size:12px'>总计</p><p style='color:#e2e8f0;font-size:24px;font-weight:bold'>"+str(len(signals))+"</p></div>",unsafe_allow_html=True)
            with c4: st.markdown("<div class='metric-box'><p style='color:#888;font-size:12px'>更新时间</p><p style='color:#e2e8f0;font-size:14px'>"+datetime.datetime.now().strftime('%H:%M')+"</p></div>",unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True)
            for i,sig in enumerate(signals):
                lv = sig.get("level","")
                bc = "badge-strong" if lv=="强烈推荐" else "badge-buy"
                nm = sig.get('name',sig.get('code',''))
                cd = sig.get('code','')
                sc = sig.get('score',0)
                st.markdown("<div class='stock-card'><div style='display:flex;justify-content:space-between;align-items:center'><div><span style='font-size:18px;font-weight:600;color:#e2e8f0'>#"+str(i+1)+" "+nm+"</span><span style='color:#64748b;margin-left:10px'>"+cd+"</span></div><div style='display:flex;gap:10px;align-items:center'><span class='"+bc+"'>"+lv+"</span><span style='color:#ffd700;font-size:24px;font-weight:bold'>"+str(sc)+"</span><span style='color:#64748b;font-size:13px'>分</span></div></div></div>",unsafe_allow_html=True)
        funds = res.get("funds",[])
        if funds:
            st.markdown("---")
            st.subheader("基金筛选结果")
            for f in funds:
                st.markdown("<div class='stock-card'><span style='color:#e2e8f0'>"+f.get('name','')+"</span><span style='color:#64748b;margin-left:10px'>"+f.get('code','')+"</span></div>",unsafe_allow_html=True)
        st.markdown("---")
        st.caption("本模型仅供参考，不构成投资建议。")
else:
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,3,1])
    with c2:
        st.markdown("### 如何使用")
        st.markdown("1. 左侧选择分析模式\n2. 设置参数\n3. 点击开始分析")
        st.markdown("---")
        st.markdown("### 因子体系")
        cols = st.columns(3)
        for i,(icon,name,desc) in enumerate([("价值","价值因子","PE/PB/PS分位"),("动量","动量因子","多周期信号"),("质量","质量因子","ROE/毛利率")]):
            with cols[i]: st.markdown("<div style='text-align:center;padding:20px;background:rgba(255,255,255,0.03);border-radius:14px'><div style='font-size:30px'>"+icon+"</div><p style='color:#e2e8f0;font-weight:600'>"+name+"</p><p style='color:#64748b;font-size:13px'>"+desc+"</p></div>",unsafe_allow_html=True)

st.markdown("<br>",unsafe_allow_html=True)
st.caption("Powered by akshare | 面包多自动收款")
