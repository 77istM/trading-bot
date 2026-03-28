import os
import sqlite3
import pandas as pd
import talib
import requests
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

# --- Configuration & Setup ---
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TICKER = "AAPL"

# Initialise Clients
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET, paper=True)
llm = Ollama(model="llama3.2:3b", base_url="http://localhost:11434")

# Initialise Database
def init_db():
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS trades 
                      (id INTEGER PRIMARY KEY, ticker TEXT, side TEXT, qty REAL, reason TEXT)''')
    conn.commit()
    return conn

# --- The "Brain" (Sentiment Analysis) ---
def analyze_sentiment(ticker):
    # 1. Fetch News (Mock URL for structure)
    url = f"https://newsapi.org/v2/everything?q={ticker}&apiKey={NEWS_API_KEY}"
    response = requests.get(url).json()
    headlines = [article['title'] for article in response.get('articles', [])[:3]]
    news_text = " | ".join(headlines)

    # 2. LangChain Prompt
    template = """
    You are an expert financial analyst. Read the following news headlines about {ticker}:
    {news}
    Deduce the market sentiment. Reply ONLY with one word: BULLISH, BEARISH, or NEUTRAL.
    """
    prompt = PromptTemplate(template=template, input_variables=["ticker", "news"])
    chain = prompt | llm
    
    sentiment = chain.invoke({"ticker": ticker, "news": news_text}).strip().upper()
    return sentiment

# --- The Technical Engine ---
def get_technical_signal(ticker):
    # In a live environment, you fetch OHLCV data from Alpaca here into a DataFrame.
    # For demonstration, we use a mock DataFrame structure.
    data = {'close': [150.0, 151.0, 152.0, 149.0, 148.0, 145.0, 143.0, 140.0, 138.0, 135.0, 130.0, 128.0, 125.0, 124.0, 123.0]}
    df = pd.DataFrame(data)
    
    # Calculate RSI using TA-Lib
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    current_rsi = df['RSI'].iloc[-1]
    
    if current_rsi < 30:
        return "BULLISH" # Oversold
    elif current_rsi > 70:
        return "BEARISH" # Overbought
    return "NEUTRAL"

# --- Execution Engine ---
def execute_trade(ticker, side, reason, conn):
    market_order_data = MarketOrderRequest(
        symbol=ticker,
        qty=1,
        side=OrderSide.BUY if side == "BULLISH" else OrderSide.SELL,
        time_in_force=TimeInForce.GTC
    )
    
    # Execute via Alpaca
    trading_client.submit_order(order_data=market_order_data)
    print(f"Executed {side} order for {ticker}. Reason: {reason}")
    
    # Log to SQLite
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trades (ticker, side, qty, reason) VALUES (?, ?, ?, ?)", 
                   (ticker, side, 1.0, reason))
    conn.commit()

# --- Main Trading Loop ---
def main():
    conn = init_db()
    print("Agent Initialised. Analysing market...")
    
    sentiment = analyze_sentiment(TICKER)
    technical_signal = get_technical_signal(TICKER)
    
    print(f"[{TICKER}] Sentiment: {sentiment} | Technicals: {technical_signal}")
    
    # Confluence Check: Only trade if Brain and Technicals agree
    if sentiment == "BULLISH" and technical_signal == "BULLISH":
        execute_trade(TICKER, "BULLISH", "Confluence: RSI Oversold + Positive News", conn)
    elif sentiment == "BEARISH" and technical_signal == "BEARISH":
        execute_trade(TICKER, "BEARISH", "Confluence: RSI Overbought + Negative News", conn)
    else:
        print("Signals mixed. Holding position to preserve capital.")

if __name__ == "__main__":
    main()
