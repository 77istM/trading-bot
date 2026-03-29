import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")

# --- Title & Header ---
st.title("🤖 Trading Bot Dashboard")
st.markdown("Real-time monitoring of your AI-powered trading bot")

# --- Database Connection ---
def get_trades():
    """Fetch all trades from the SQLite database"""
    try:
        conn = sqlite3.connect('trading_bot.db')
        query = "SELECT * FROM trades ORDER BY rowid DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()

# --- Layout: Metrics & Charts ---
col1, col2, col3, col4 = st.columns(4)

trades_df = get_trades()

if not trades_df.empty:
    total_trades = len(trades_df)
    buy_trades = len(trades_df[trades_df['side'] == 'BULLISH'])
    sell_trades = len(trades_df[trades_df['side'] == 'BEARISH'])
    
    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("Buy Orders", buy_trades)
    with col3:
        st.metric("Sell Orders", sell_trades)
    with col4:
        win_rate = (buy_trades / total_trades * 100) if total_trades > 0 else 0
        st.metric("Buy Ratio", f"{win_rate:.1f}%")
else:
    with col1:
        st.metric("Total Trades", 0)
    with col2:
        st.metric("Buy Orders", 0)
    with col3:
        st.metric("Sell Orders", 0)
    with col4:
        st.metric("Buy Ratio", "0%")

# --- Trade History Table ---
st.subheader("📊 Trade History")
if not trades_df.empty:
    st.dataframe(trades_df, use_container_width=True)
else:
    st.info("No trades recorded yet. The bot will populate this table as it executes trades.")

# --- Auto-refresh ---
st.markdown("---")
if st.button("🔄 Refresh Data"):
    st.rerun()

st.caption("Dashboard refreshes automatically. Last update: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
