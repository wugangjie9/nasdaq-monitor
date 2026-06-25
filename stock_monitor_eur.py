import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time
import os

# 修复 Cloud 缓存问题
os.environ["YFINANCE_CACHE_DIR"] = "/tmp"

st.set_page_config(page_title="Nasdaq 盯盘 (欧元)", layout="wide")

# ================== 配置 ==================
tickers = ['TEM', 'DELL', 'AAPL', 'NVDA', 'TSLA', 'MSFT']

levels = {
    'TEM': {'support': [49.5, 46.5], 'resistance': [55.0, 60.0]},
    'DELL': {'support': [390, 368], 'resistance': [435, 460]},
}

# ===========================================

st.title("🚀 Nasdaq 实时盯盘 (欧元显示)")
st.caption("数据来自 Yahoo Finance")

with st.sidebar:
    st.header("设置")
    selected_tickers = st.multiselect("选择股票", tickers, default=tickers)
    auto_refresh = st.checkbox("开启自动刷新", value=True)
    refresh_interval = st.slider("刷新间隔 (秒)", 5, 60, 15)

def get_usd_to_eur():
    try:
        rate = yf.Ticker("EURUSD=X").info.get('regularMarketPrice', 1.135)
        return 1 / rate
    except:
        return 0.88

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period='1d', interval='1m')
        
        price_usd = info.get('regularMarketPrice') or (hist['Close'].iloc[-1] if not hist.empty else None)
        prev_close = info.get('regularMarketPreviousClose')
        change_pct = ((price_usd - prev_close) / prev_close * 100) if prev_close and price_usd else 0
        
        price_eur = round(price_usd * get_usd_to_eur(), 2) if price_usd else None
        volume = info.get('regularMarketVolume')
        
        return {
            '代码': ticker,
            '价格 (USD)': round(price_usd, 2) if price_usd else None,
            '价格 (EUR)': price_eur,
            '涨跌%': round(change_pct, 2),
            '成交量': f"{volume:,}" if volume else "-",
            '更新时间': datetime.datetime.now().strftime('%H:%M:%S')
        }
    except:
        return {'代码': ticker, '价格 (USD)': None, '价格 (EUR)': None, 
                '涨跌%': None, '成交量': '-', '更新时间': '错误'}

# 手动刷新按钮
if st.button("🔄 手动刷新数据"):
    st.rerun()

# 数据显示
placeholder = st.empty()

# 主循环（改进版，不会一直转圈）
data_list = []
for ticker in selected_tickers:
    data = get_stock_data(ticker)
    
    hint = ""
    if ticker in levels and data['价格 (USD)']:
        sup = levels[ticker]['support']
        res = levels[ticker]['resistance']
        p = data['价格 (USD)']
        if p <= sup[0] + 3:
            hint = "🟢 接近支撑 - 适合考虑买入"
        elif p >= res[0] - 5:
            hint = "🔴 接近阻力 - 适合考虑卖出/减仓"
    
    data['买卖提示'] = hint
    data_list.append(data)

df = pd.DataFrame(data_list)

def color_change(val):
    if isinstance(val, float):
        return 'color: green' if val > 0 else 'color: red'
    return ''

styled_df = df.style.applymap(color_change, subset=['涨跌%'])

with placeholder.container():
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    st.caption(f"最后更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 1 USD ≈ {get_usd_to_eur():.4f} EUR")
    st.info("💡 提示：接近支撑位考虑买入，接近阻力位考虑卖出。非投资建议，仅供参考。")

# 自动刷新（改进版）
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
