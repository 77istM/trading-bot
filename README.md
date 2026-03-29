## **COMPREHENSIVE TRADING BOT REPOSITORY OVERVIEW**

### **1. DIRECTORY STRUCTURE**

```
trading-bot/
├── .git/                          # Git history
├── .gitignore                     # Excludes .env, trading_bot.db, __pycache__/
├── Dockerfile                     # 23 lines - Python 3.11-slim with TA-Lib
├── docker-compose.yml             # 20 lines - Multi-service setup
├── main.py                        # 744 lines - Core trading bot logic
├── dashboard.py                   # 236 lines - Streamlit dashboard
├── requirements.txt               # 9 lines - Python dependencies
├── requirement.txt                # Legacy/duplicate file (8 lines)
└── README.md / docs/             # None found
```

**Total Lines of Code:** ~989 (main logic only, excluding git)

---

### **2. PROJECT DESCRIPTION: WHAT IT DOES**

This is a **multi-signal AI-powered hedge fund trading bot** that trades stocks on multiple timeframes using:

- **5 Market Signals:** News sentiment, Technical (RSI), Geopolitical risk, Federal Reserve stance, Market fear/VIX
- **LLM Decision Engine:** Uses Ollama (llama3.2:3b) to synthesize signals and decide BUY/SELL/HOLD
- **Dual Trading Modes:** Long (BUY) and Short (SELL) positions
- **Automated Risk Management:** Stop-loss and take-profit execution
- **Position Sizing:** Ring-fenced to max 3% of portfolio per trade
- **Trade History Tracking:** SQLite database with full audit trail and PnL calculations
- **Live Monitoring:** Continuously monitors open positions for stop/target hits
- **Real-time Dashboard:** Streamlit UI showing trades, PnL curve, AI analysis, and risk configuration

---

### **3. EXCHANGE/API & KEY INTEGRATIONS**

| Component | Service | Purpose |
|-----------|---------|---------|
| **Primary Broker** | [Alpaca](https://alpaca.markets) | Paper/live trading, market data, position management |
| **Market Data** | Alpaca StockHistoricalDataClient | 60-day OHLCV bars for RSI calculation |
| **News Sentiment** | [NewsAPI.org](https://newsapi.org) | Headlines for sentiment & geopolitics analysis |
| **AI/LLM** | [Ollama](https://ollama.ai) (llama3.2:3b) | Local reasoning engine for trade decisions |
| **Technical Analysis** | [TA-Lib](https://ta-lib.org) | RSI calculation (14-period) |
| **Data Store** | SQLite | trades & settings tables |

---

### **4. TRADING STRATEGIES IMPLEMENTED**

**Primary Strategy: Multi-Signal AI Synthesis**

1. **Sentiment Analysis** → Analyzes 5 recent news headlines per ticker → Returns: BULLISH, BEARISH, NEUTRAL
2. **Technical Signal** → RSI(14) on 60-day daily bars:
   - RSI < 30 → BULLISH (oversold)
   - RSI > 70 → BEARISH (overbought)
   - Otherwise → NEUTRAL
3. **Geopolitical Risk** → Analyzes war, conflict, sanctions news → Returns: LOW_RISK, MEDIUM_RISK, HIGH_RISK
4. **Federal Reserve Sentiment** → Analyzes Fed rate/inflation headlines → Returns: HAWKISH, DOVISH, NEUTRAL
5. **Market Fear (VIX)** → Analyzes volatility/crash headlines → Returns: HIGH (VIX>30), MEDIUM (VIX 15-30), LOW (VIX<15)

**Pre-Trade AI Decision:**
- LLM prompt includes all 5 signals + risk params (stop %, take %)
- Bot responds with: DIRECTION (BUY/SELL/HOLD), TRADE (YES/NO), CONFIDENCE, REASON
- Decision framework: Step-by-step reasoning through market environment → direction likelihood → risk/reward assessment

**Risk Gates (Hard Rules):**
- Daily max trade limit (default 1000)
- Position size ring-fence: ≤3% of portfolio per trade
- Stop-loss & take-profit auto-execution on price touch

**Ticker Universe:** Default 30 major stocks (AAPL, MSFT, GOOGL, etc.) or custom via TICKERS env var

---

### **5. DOCKER FILES**

**Dockerfile (23 lines):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install compilation tools
RUN apt-get update && apt-get install -y build-essential wget gcc make

# Download, compile, and install TA-Lib C-library natively
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

**docker-compose.yml (20 lines):**
```yaml
version: '3.8'
services:
  bot:
    build: .
    container_name: trading_bot
    network_mode: "host"
    env_file:
      - .env
    volumes:
      - .:/app

  dashboard:
    build: .
    container_name: streamlit_gui
    command: ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
    ports:
      - "8501:8501"
    volumes:
      - .:/app
```

**Key Notes:**
- Two services: `bot` (trading logic, background) and `dashboard` (Streamlit UI, port 8501)
- Uses `host` network mode for bot (direct system access)
- Both mount `.env` for credentials and `.:/app` for database persistence
- TA-Lib must be compiled from source (complex C dependency)

---

### **6. DEPENDENCY FILES**

**requirements.txt (9 lines):**
```
alpaca-py
pandas
TA-Lib
requests
langchain
langchain-community
langchain-core
streamlit>=1.28.0
altair>=4.0,<6.0
```

**requirement.txt (8 lines):** Older/duplicate, missing langchain-core & streamlit deps

**Key Dependencies:**
- `alpaca-py`: Official Alpaca trading client
- `TA-Lib`: Technical analysis library (requires native C compilation)
- `langchain*`: LLM framework & Ollama integration
- `streamlit`: Dashboard web framework
- `pandas`: Data manipulation
- `requests`: HTTP for NewsAPI
- `altair`: Charting (Streamlit uses it)

---

### **7. STREAMLIT APP (dashboard.py - 236 lines)**

**Purpose:** Real-time monitoring & risk configuration UI

**Key Displays:**

1. **Sidebar: Risk Configuration**
   - Stop Loss % slider (0.5%-10%, default 3%)
   - Take Profit % slider (1%-20%, default 5%)
   - Save button persists to SQLite settings table
   - Info box: Ring fence ≤3%, daily max trades, directions (long/short)

2. **Metrics Row (6 columns)**
   - Total Trades (count)
   - Long (BUY) count
   - Short (SELL) count
   - Net Position (longs - shorts)
   - Today's trades (X / daily max)
   - Realized PnL ($)

3. **PnL Curve**
   - Line chart of cumulative P&L over time
   - Uses realized_pnl column or side×qty proxy
   - Auto-refreshable with 10-second cache

4. **Trade History Table**
   - Sortable/scrollable table: trade_rowid, created_at, ticker, side, qty, price, stop_loss_price, take_profit_price, sentiment, technical_signal, geopolitics, fed_sentiment, fear_level, realized_pnl, reason
   - Shows recent trades first (descending by rowid)

5. **AI Pre-Trade Analysis Viewer**
   - Expanders showing last 5 trades' full AI analysis text
   - Format: [TICKER] timestamp — side
   - Contains LLM reasoning and decision breakdown

6. **Refresh Button**
   - Clears cache and reruns dashboard

**Settings Logic:**
- Reads from `settings` table in SQLite (key-value pairs)
- Persists slider changes immediately
- Bot reads these on next run and uses them instead of env defaults

---

### **8. CI/CD CONFIGURATION**

**Status:** ❌ **NONE FOUND**
- No `.github/workflows/` directory
- No GitHub Actions configs
- No CI/CD pipeline (no automated tests, linting, or deployments)

---

### **9. TEST FILES**

**Status:** ❌ **NO TESTS FOUND**
- No `test_*.py` or `*_test.py` files
- No pytest/unittest configuration
- No test data or fixtures

---

### **10. OVERALL ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADING BOT SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  EXTERNAL SERVICES                                            │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Alpaca Broker   │  │  NewsAPI         │                 │
│  │  (Trading +      │  │  (Headlines)     │                 │
│  │   Data Fetch)    │  └──────────────────┘                 │
│  └──────────────────┘         ↑                              │
│         ↑ ↓                    │                              │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  Ollama LLM      │  │  TA-Lib          │                 │
│  │  (llama3.2:3b)   │  │  (Technical RSI) │                 │
│  └──────────────────┘  └──────────────────┘                 │
│         ↑                     ↑                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  CORE COMPONENTS (main.py - 744 lines)                       │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 1. SIGNAL ANALYSIS (5 Functions)                   │     │
│  │    • analyze_sentiment(ticker) → Headlines + LLM   │     │
│  │    • get_technical_signal(ticker) → RSI(14)        │     │
│  │    • analyze_geopolitics() → Global risk           │     │
│  │    • analyze_fed_rate() → Rate policy              │     │
│  │    • analyze_market_fear() → VIX proxy             │     │
│  └────────────────────────────────────────────────────┘     │
│         ↓                                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 2. PRE-TRADE AI ANALYSIS                           │     │
│  │    • Synthesizes 5 signals via LLM                 │     │
│  │    • Returns: Direction, Should_Trade, Reason      │     │
│  └────────────────────────────────────────────────────┘     │
│         ↓                                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 3. RISK ASSESSMENT (Hard Rules)                    │     │
│  │    • Daily trade limit check                       │     │
│  │    • Position direction validation                 │     │
│  └────────────────────────────────────────────────────┘     │
│         ↓                                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 4. POSITION SIZING & EXECUTION                     │     │
│  │    • Ring-fence: ≤3% portfolio per trade           │     │
│  │    • Calculate stop-loss & take-profit prices      │     │
│  │    • Submit market order via Alpaca                │     │
│  │    • Calculate realized PnL                        │     │
│  │    • Log to SQLite                                 │     │
│  └────────────────────────────────────────────────────┘     │
│         ↓                                                     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 5. POSITION MONITOR (Continuous)                   │     │
│  │    • Check all open positions                      │     │
│  │    • Trigger stop-loss on price ≤ threshold       │     │
│  │    • Trigger take-profit on price ≥ threshold      │     │
│  │    • Auto-close via market orders                  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DATABASE (SQLite: trading_bot.db)                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │ trades TABLE                                       │     │
│  │  • ticker, side, qty, price                        │     │
│  │  • stop_loss_price, take_profit_price              │     │
│  │  • sentiment, technical_signal, geopolitics,       │     │
│  │    fed_sentiment, fear_level                       │     │
│  │  • trade_analysis (full LLM reasoning)             │     │
<exited with exit code 0>

Read last 200 lines of exploration output
$ tail -n 200 /tmp/1774749191292-copilot-tool-output-5eflhi.txt
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  DATABASE (SQLite: trading_bot.db)                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │ trades TABLE                                       │     │
│  │  • ticker, side, qty, price                        │     │
│  │  • stop_loss_price, take_profit_price              │     │
│  │  • sentiment, technical_signal, geopolitics,       │     │
│  │    fed_sentiment, fear_level                       │     │
│  │  • trade_analysis (full LLM reasoning)             │     │
│  │  • realized_pnl, reason, created_at                │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │ settings TABLE                                     │     │
│  │  • key: stop_loss_pct, take_profit_pct             │     │
│  │  • value: user-configured from dashboard           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  STREAMLIT DASHBOARD (dashboard.py - 236 lines)              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ • Real-time metrics & trade history                │     │
│  │ • Interactive risk sliders (stop/take)             │     │
│  │ • PnL curve visualization                          │     │
│  │ • AI analysis viewer (last 5 trades)               │     │
│  │ • Persistent settings via SQLite                   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Main Loop** (every execution):
   - Read settings from DB (or env defaults)
   - Monitor existing positions (stop/take-profit)
   - Fetch market-wide signals (geopolitics, Fed, fear) — shared for all tickers
   - **Per ticker:** Fetch sentiment + technical → AI decision → Risk check → Execute/Skip
   - Log all to SQLite

2. **Dashboard Loop** (continuous):
   - Reads SQLite trades table every 10 seconds
   - Displays live metrics and PnL
   - Allows user to adjust stop/take-profit sliders → persisted to DB

---

### **11. KEY FINDINGS: AREAS FOR IMPROVEMENT**

#### **🔴 Critical Issues:**

1. **NO ERROR HANDLING / LOGGING**
   - Many try-except blocks **silently swallow errors** (`except Exception: pass`)
   - No structured logging (just print statements)
   - Silent failures in API calls, LLM invocations, order submissions
   - **Impact:** Bot may trade on stale/invalid data without alerting

2. **HARDCODED VALUES / MAGIC NUMBERS**
   - Mock RSI data (lines 307-313): Uses fake OHLCV if live fetch fails
   - NewsAPI fallback: Returns empty list silently, no alerting
   - Ollama assumes `http://localhost:11434` (line 57) — must be running locally
   - **Impact:** Bot can run on mock data without warning

3. **NO TEST COVERAGE**
   - Zero unit tests for signal analysis, PnL calculations, risk assessment
   - Position sizing logic untested (complex edge cases in `_apply_trade_to_position`)
   - **Impact:** Regressions and bugs go undetected

4. **INCOMPLETE API INTEGRATION**
   - Alpaca data client is optional (`_has_data_client` flag) — falls through to mock
   - No backoff/retry logic for API rate limits
   - No position monitoring on close (only on execution)
   - **Impact:** Trading on stale technical data

5. **DATABASE INTEGRITY ISSUES**
   - No transaction rollbacks on partial failures
   - Foreign key constraints absent (ticker → position mapping loose)
   - Realized PnL calculation assumes contiguous trade history (gaps cause errors)
   - **Impact:** Inconsistent position tracking, incorrect PnL

#### **🟡 Important Limitations:**

6. **SINGLE LOCAL LLM DEPENDENCY**
   - Ollama must be running on `localhost:11434` before bot starts
   - No fallback to alternative LLM or heuristic-based decisions
   - No timeout handling for slow LLM responses
   - **Impact:** Bot halts if Ollama is unavailable

7. **NAIVE SENTIMENT ANALYSIS**
   - Only uses 5 most recent headlines per ticker
   - No entity recognition, weighting, or historical context
   - NewsAPI truncation (5 articles) may miss important stories
   - **Impact:** Sentiment can swing wildly on single headline

8. **INSUFFICIENT TECHNICAL INDICATORS**
   - Only RSI(14) on daily bars
   - No momentum, trend, or volatility filters
   - 60-day lookback may be too short for trending markets
   - Mock fallback mask real issues
   - **Impact:** Technical signals lack depth

9. **MISSING POSITION MANAGEMENT**
   - No trailing stop-loss
   - No partial position scaling (all-or-nothing)
   - No correlation/sector hedging
   - Stop/take prices calculated once at entry; not adjusted post-fill
   - **Impact:** Inflexible risk management

10. **DASHBOARD LIMITATIONS**
    - No real-time updates (10-second cache TTL)
    - No trade execution interface (read-only)
    - No order status visibility (placed vs. filled)
    - No risk scenario modeling (what-if sliders)
    - **Impact:** Limited operational control

#### **🟢 Nice-to-Have Improvements:**

11. **Missing Observability**
    - No metrics export (Prometheus, CloudWatch)
    - No trade alerts (Slack, email, SMS)
    - No audit trail for risk parameter changes
    - No performance attribution (signal contribution)

12. **Deployment Issues**
    - TA-Lib compilation slow (Docker layer)
    - No deployment automation / IaC (Terraform, K8s)
    - No secrets management (.env file checked in gitignore but no vault)
    - No production readiness checklist

13. **Code Quality**
    - No type hints (Python 3.11 available — use TypedDict, Callable)
    - No docstrings on core functions
    - Long functions (main() = 70+ lines)
    - Duplicate requirements.txt / requirement.txt files

---

### **ENVIRONMENT VARIABLES REQUIRED**

```bash
# API Credentials (REQUIRED)
ALPACA_API_KEY=<alpaca-paper-key>
ALPACA_SECRET=<alpaca-secret>
NEWS_API_KEY=<newsapi-org-key>

# Trading Parameters (Optional — defaults provided)
DAILY_MAX_TRADES=1000              # Hard cap per 24 hours
MAX_POSITION_PCT=0.03              # Ring fence: 3% max per trade
STOP_LOSS_PCT=0.03                 # Default 3% stop loss
TAKE_PROFIT_PCT=0.05               # Default 5% take profit
TICKERS="AAPL,MSFT,GOOGL"          # CSV list (if not set, uses 30-stock default)

# Dashboard Settings (Optional)
TRADING_DB_PATH=trading_bot.db     # SQLite database path
```

---

### **QUICK START (Docker)**

```bash
# 1. Create .env file with credentials
cat > .env << EOF
ALPACA_API_KEY=xxxxx
ALPACA_SECRET=yyyyy
NEWS_API_KEY=zzzzz
EOF

# 2. Start Ollama (required)
docker run -d --name ollama -p 11434:11434 ollama/ollama
docker exec ollama ollama pull llama3.2:3b

# 3. Start trading bot + dashboard
docker-compose up -d

# 4. View dashboard at http://localhost:8501
# 5. View bot logs: docker logs trading_bot -f
```

---

### **SUMMARY TABLE**

| Aspect | Status | Notes |
|--------|--------|-------|
| **Exchange** | ✅ Alpaca (paper trading) | Supports live mode |
| **Signals** | ✅ 5 multi-modal (sentiment, technical, geo, Fed, fear) | LLM-synthesized decisions |
| **Trading Modes** | ✅ Long + Short | Dual-directional |
| **Risk Management** | ✅ Stop/take-profit + ring fence | Automated position monitoring |
| **Dashboard** | ✅ Real-time Streamlit UI | Interactive risk controls |
| **Tests** | ❌ None | Critical gap |
| **Logging** | ❌ Print only | No structured observability |
| **CI/CD** | ❌ None | Manual deployment |
| **Documentation** | ❌ Minimal | No README or comments |
| **Error Handling** | ❌ Silent failures | Many try-except passes |
| **Deployment** | ⚠️ Docker-ready | TA-Lib compilation required |

---
