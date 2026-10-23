import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime

st.set_page_config(
    page_title="TradeLab Pro",
    page_icon="📈",
    layout="wide"
)

# -------------------- Styling --------------------
st.markdown("""
<style>
.stApp {
    background: #131722;
    color: #D1D4DC;
}
[data-testid="stSidebar"] {
    background: #1E222D;
}
h1, h2, h3, p, label {
    color: #D1D4DC;
}
div[data-testid="stMetric"] {
    background: #1E222D;
    border: 1px solid #363C4E;
    padding: 12px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 TradeLab Pro")
st.caption(
    "Market Data • Stock Scanner • Trading Journal • Risk Management"
)

# -------------------- Provider Catalog --------------------
PROVIDERS = {
    "Upstox": {
        "type": "Broker API",
        "capability": "Quotes, historical data and streaming; permissions vary"
    },
    "Angel One SmartAPI": {
        "type": "Broker API",
        "capability": "Quotes, historical data and WebSocket"
    },
    "DhanHQ API": {
        "type": "Broker API",
        "capability": "Quotes, historical data and live feed"
    },
    "FYERS API": {
        "type": "Broker API",
        "capability": "Quotes, historical data and data socket"
    },
    "Zerodha Kite Connect": {
        "type": "Broker API",
        "capability": "Quotes, historical data and WebSocket; plan dependent"
    },
    "ICICI Direct Breeze": {
        "type": "Broker API",
        "capability": "Quotes, historical data and streaming"
    },
    "Groww Trading API": {
        "type": "Broker API",
        "capability": "Access and permissions vary"
    },
    "5paisa Xstream API": {
        "type": "Broker API",
        "capability": "Account and API access required"
    },
    "Alice Blue ANT API": {
        "type": "Broker API",
        "capability": "Account and API access required"
    },
    "Motilal Oswal OpenAPI": {
        "type": "Broker API",
        "capability": "Account and API access required"
    },
    "yfinance": {
        "type": "Third-party library",
        "capability": "Historical/quote availability varies; not guaranteed live"
    },
    "Alpha Vantage": {
        "type": "Market-data API",
        "capability": "Plan and exchange coverage dependent"
    },
    "Twelve Data": {
        "type": "Market-data API",
        "capability": "Plan and exchange coverage dependent"
    },
    "Finnhub": {
        "type": "Market-data API",
        "capability": "Plan and exchange coverage dependent"
    },
    "EODHD": {
        "type": "Market-data API",
        "capability": "Plan and exchange coverage dependent"
    },
    "NSE Bhavcopy / UDiFF": {
        "type": "Exchange files",
        "capability": "End-of-day files; not live streaming"
    },
    "BSE Official Data": {
        "type": "Exchange data",
        "capability": "Product and access dependent"
    },
    "CSV Upload": {
        "type": "File",
        "capability": "Optional user-provided data"
    }
}

# -------------------- Session State --------------------
if "journal" not in st.session_state:
    st.session_state.journal = []

if "provider_results" not in st.session_state:
    st.session_state.provider_results = {}

if "scanner_config" not in st.session_state:
    st.session_state.scanner_config = {}

# -------------------- HTTP Helper --------------------
def get_json(url, headers=None, params=None, timeout=20):
    response = requests.get(
        url,
        headers=headers or {},
        params=params or {},
        timeout=timeout
    )

    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_response": response.text[:1000]}

    return response.status_code, payload


# -------------------- Upstox Quote --------------------
def quote_upstox(token, instrument_key):
    status, payload = get_json(
        "https://api.upstox.com/v3/market-quote/quotes",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        },
        params={"instrument_key": instrument_key}
    )

    if status != 200:
        raise RuntimeError(
            f"Upstox HTTP {status}: "
            f"{payload.get('message', payload.get('errors', 'Request failed'))}"
        )

    data = payload.get("data") or {}

    if not data:
        raise RuntimeError(
            "No quote returned. Check the instrument key and permissions."
        )

    return data


# -------------------- yfinance Quote --------------------
def quote_yfinance(symbol):
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError(
            "yfinance is missing. Add yfinance to requirements.txt."
        )

    ticker = yf.Ticker(symbol)
    history = ticker.history(
        period="5d",
        interval="1d",
        auto_adjust=False
    )

    if history is None or history.empty:
        raise RuntimeError(
            "No data returned. Check the symbol, for example SBIN.NS."
        )

    latest = history.iloc[-1]

    return {
        "symbol": symbol,
        "latest_available_daily_bar": str(history.index[-1]),
        "open": float(latest["Open"]) if pd.notna(latest["Open"]) else None,
        "high": float(latest["High"]) if pd.notna(latest["High"]) else None,
        "low": float(latest["Low"]) if pd.notna(latest["Low"]) else None,
        "close": float(latest["Close"]) if pd.notna(latest["Close"]) else None,
        "volume": int(latest["Volume"]) if pd.notna(latest["Volume"]) else None,
        "warning": "Latest available daily bar; not guaranteed real-time."
    }


# -------------------- Alpha Vantage Quote --------------------
def quote_alpha_vantage(api_key, symbol):
    status, payload = get_json(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }
    )

    if status != 200:
        raise RuntimeError(f"Alpha Vantage HTTP {status}")

    message = (
        payload.get("Error Message")
        or payload.get("Note")
        or payload.get("Information")
    )

    if message:
        raise RuntimeError(str(message))

    quote = payload.get("Global Quote")

    if not quote:
        raise RuntimeError(
            "No quote returned. Check symbol coverage and API quota."
        )

    return quote


# -------------------- Twelve Data Quote --------------------
def quote_twelve_data(api_key, symbol):
    status, payload = get_json(
        "https://api.twelvedata.com/quote",
        params={"symbol": symbol, "apikey": api_key}
    )

    if (
        status != 200
        or payload.get("status") == "error"
        or payload.get("code")
    ):
        raise RuntimeError(
            str(payload.get("message", f"Twelve Data HTTP {status}"))
        )

    if not payload.get("symbol"):
        raise RuntimeError(
            "No quote returned. Check exchange coverage and plan."
        )

    return payload


# -------------------- Finnhub Quote --------------------
def quote_finnhub(api_key, symbol):
    status, payload = get_json(
        "https://finnhub.io/api/v1/quote",
        params={"symbol": symbol, "token": api_key}
    )

    if status != 200:
        raise RuntimeError(f"Finnhub HTTP {status}")

    if not payload or not payload.get("c"):
        raise RuntimeError(
            "No current quote returned. Check symbol coverage and API quota."
        )

    return payload


# -------------------- EODHD Quote --------------------
def quote_eodhd(api_key, symbol):
    status, payload = get_json(
        f"https://eodhd.com/api/real-time/{symbol}",
        params={"api_token": api_key, "fmt": "json"}
    )

    if status != 200:
        raise RuntimeError(f"EODHD HTTP {status}")

    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("error")
        if message:
            raise RuntimeError(str(message))

    if not payload:
        raise RuntimeError(
            "No quote returned. Check symbol format, coverage and plan."
        )

    return payload


# -------------------- Navigation --------------------
page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Data Source & Stock Scanner",
        "Stock Data & CSV",
        "Trading Journal",
        "Risk Calculator",
        "Settings"
    ]
)

st.sidebar.divider()
st.sidebar.caption("No synthetic market prices are generated.")

# -------------------- Dashboard --------------------
if page == "Dashboard":
    st.header("Dashboard")

    journal = st.session_state.journal
    total_pnl = sum(trade["P&L"] for trade in journal)

    c1, c2, c3 = st.columns(3)
    c1.metric("Journal Trades", len(journal))
    c2.metric("Recorded Gross P&L", f"₹{total_pnl:,.2f}")
    c3.metric("Providers in Catalog", len(PROVIDERS))

    st.subheader("Modules")
    st.write("- Data Source Manager and connection testing")
    st.write("- Exchange, Market Cap and Sector configuration")
    st.write("- Optional Technical Indicators")
    st.write("- CSV import and export")
    st.write("- Trading Journal")
    st.write("- Risk Calculator")

    st.info(
        "Connection status is updated only after an actual provider request."
    )

# -------------------- Data Sources and Scanner --------------------
elif page == "Data Source & Stock Scanner":
    st.header("Data Source & Stock Scanner")

    st.caption(
        "Choose sources and filters. A configured source is not automatically connected."
    )

    selected_sources = st.multiselect(
        "Data Sources",
        list(PROVIDERS.keys()),
        default=["Upstox"]
    )

    st.subheader("Provider Information")

    for provider in selected_sources:
        st.caption(
            f"{provider}: {PROVIDERS[provider]['capability']}"
        )

    mode = st.selectbox(
        "Multi-source Mode",
        ["Compare", "Fallback", "Combine"]
    )

    exchange = st.selectbox(
        "Exchange",
        ["NSE", "BSE", "Both"]
    )

    cap_mode = st.radio(
        "Market Capitalization",
        ["All Market Caps", "Preset Categories", "Custom Range"]
    )

    categories = []
    min_cap = None
    max_cap = None
    cap_unit = "₹ Crore"

    if cap_mode == "Preset Categories":
        categories = st.multiselect(
            "Market Cap Categories",
            ["Large Cap", "Mid Cap", "Small Cap"],
            default=["Large Cap", "Mid Cap", "Small Cap"]
        )

    elif cap_mode == "Custom Range":
        cap_unit = st.selectbox(
            "Market Cap Unit",
            ["₹ Crore", "₹ Lakh Crore"]
        )

        a, b = st.columns(2)

        min_cap = a.number_input(
            "Minimum Market Cap",
            min_value=0.0,
            value=0.0,
            step=100.0
        )

        max_cap = b.number_input(
            "Maximum Market Cap (0 = no upper limit)",
            min_value=0.0,
            value=0.0,
            step=100.0
        )

        if max_cap > 0 and max_cap < min_cap:
            st.error(
                "Maximum market cap must be greater than or equal to minimum."
            )

    sectors = st.multiselect(
        "Sector(s)",
        [
            "All Sectors",
            "Banking",
            "Information Technology",
            "Energy",
            "Healthcare",
            "Consumer Goods",
            "Automobile",
            "Telecom",
            "Metals",
            "Real Estate",
            "Capital Goods",
            "Chemicals",
            "Infrastructure",
            "Utilities",
            "Other"
        ],
        default=["All Sectors"]
    )

    indicators_on = st.toggle(
        "Enable Technical Indicators",
        value=False
    )

    indicator_names = [
        "SMA",
        "EMA",
        "RSI",
        "MACD",
        "Bollinger Bands",
        "ATR",
        "ADX",
        "VWAP",
        "OBV",
        "Volume Breakout"
    ]

    selected_indicators = st.multiselect(
        "Indicators (Optional)",
        indicator_names,
        disabled=not indicators_on
    )

    if st.button("Save Scanner Configuration", type="primary"):
        st.session_state.scanner_config = {
            "sources": selected_sources,
            "mode": mode,
            "exchange": exchange,
            "cap_mode": cap_mode,
            "categories": categories,
            "min_cap": min_cap,
            "max_cap": max_cap,
            "cap_unit": cap_unit,
            "sectors": sectors,
            "indicators_on": indicators_on,
            "indicators": selected_indicators
        }

        st.success("Configuration saved for this app session.")
        st.json(st.session_state.scanner_config)

    st.divider()
    st.subheader("Test a Real Quote Source")

    provider_to_test = st.selectbox(
        "Choose Provider to Test",
        [
            "Upstox",
            "yfinance",
            "Alpha Vantage",
            "Twelve Data",
            "Finnhub",
            "EODHD"
        ]
    )

    if provider_to_test == "Upstox":
        symbol = st.text_input(
            "Upstox Instrument Key",
            value="NSE_EQ|INE062A01020"
        )
    elif provider_to_test == "yfinance":
        symbol = st.text_input(
            "Yahoo Finance Symbol",
            value="SBIN.NS"
        )
    elif provider_to_test == "EODHD":
        symbol = st.text_input(
            "EODHD Symbol with Exchange Suffix",
            value="SBIN.NSE"
        )
    else:
        symbol = st.text_input(
            "Symbol",
            value="SBIN"
        )

    secret_value = ""

    if provider_to_test in [
        "Upstox",
        "Alpha Vantage",
        "Twelve Data",
        "Finnhub",
        "EODHD"
    ]:
        credential_label = {
            "Upstox": "Access Token",
            "Alpha Vantage": "API Key",
            "Twelve Data": "API Key",
            "Finnhub": "API Token",
            "EODHD": "API Token"
        }[provider_to_test]

        secret_value = st.text_input(
            credential_label,
            type="password",
            key=f"test_{provider_to_test}"
        )

    if st.button("Test Provider and Fetch Quote"):
        try:
            if not symbol.strip():
                raise RuntimeError("Enter a symbol first.")

            if provider_to_test == "Upstox":
                if not secret_value.strip():
                    raise RuntimeError("Enter the Upstox access token.")

                result = quote_upstox(
                    secret_value.strip(),
                    symbol.strip()
                )

            elif provider_to_test == "yfinance":
                result = quote_yfinance(symbol.strip())

            elif provider_to_test == "Alpha Vantage":
                if not secret_value.strip():
                    raise RuntimeError("Enter the Alpha Vantage API key.")

                result = quote_alpha_vantage(
                    secret_value.strip(),
                    symbol.strip()
                )

            elif provider_to_test == "Twelve Data":
                if not secret_value.strip():
                    raise RuntimeError("Enter the Twelve Data API key.")

                result = quote_twelve_data(
                    secret_value.strip(),
                    symbol.strip()
                )

            elif provider_to_test == "Finnhub":
                if not secret_value.strip():
                    raise RuntimeError("Enter the Finnhub API token.")

                result = quote_finnhub(
                    secret_value.strip(),
                    symbol.strip()
                )

            elif provider_to_test == "EODHD":
                if not secret_value.strip():
                    raise RuntimeError("Enter the EODHD API token.")

                result = quote_eodhd(
                    secret_value.strip(),
                    symbol.strip().replace(" ", "")
                )

            else:
                raise RuntimeError(
                    "This provider connector is not implemented."
                )

            st.session_state.provider_results[provider_to_test] = {
                "status": "Connected (request succeeded)",
                "tested_at": datetime.now().isoformat(timespec="seconds")
            }

            st.success(f"{provider_to_test}: request succeeded.")
            st.json(result)

            if provider_to_test == "yfinance":
                st.warning(result.get("warning", "Data may be delayed."))
            else:
                st.caption(
                    "Check provider timestamps and permissions to determine "
                    "whether the returned data is real-time or delayed."
                )

        except Exception as exc:
            st.session_state.provider_results[provider_to_test] = {
                "status": "Failed",
                "tested_at": datetime.now().isoformat(timespec="seconds")
            }

            st.error(f"Request failed: {exc}")

    st.subheader("Provider Connection Status")

    if st.session_state.provider_results:
        st.dataframe(
            pd.DataFrame([
                {"Provider": name, **details}
                for name, details
                in st.session_state.provider_results.items()
            ]),
            use_container_width=True
        )
    else:
        st.info("No provider request has been tested in this session.")

    st.warning(
        "A quote test is not a full-market scanner. Full scanning needs "
        "a verified instrument universe, market-cap and sector data, "
        "provider coverage, and rate-limit handling."
    )

# -------------------- Stock Data and CSV --------------------
elif page == "Stock Data & CSV":
    st.header("Stock Data & CSV")

    st.write(
        "CSV is optional. Upload a file only if you want to analyze your own data."
    )

    file = st.file_uploader(
        "Upload CSV",
        type=["csv"]
    )

    if file is None:
        st.info(
            "No CSV selected. You can continue using another connected data source."
        )

    else:
        try:
            df = pd.read_csv(file)

            st.success("CSV read successfully.")
            st.dataframe(df, use_container_width=True)

            a, b = st.columns(2)
            a.metric("Rows", len(df))
            b.metric("Columns", len(df.columns))

            st.subheader("Data Quality")

            st.dataframe(
                pd.DataFrame({
                    "Column": df.columns,
                    "Type": [str(t) for t in df.dtypes],
                    "Missing": [
                        int(df[column].isna().sum())
                        for column in df.columns
                    ]
                }),
                use_container_width=True
            )

            st.download_button(
                "Download CSV Copy",
                df.to_csv(index=False).encode("utf-8"),
                "tradelab_data.csv",
                "text/csv"
            )

        except Exception as exc:
            st.error(f"CSV read failed: {exc}")

# -------------------- Trading Journal --------------------
elif page == "Trading Journal":
    st.header("Trading Journal")

    with st.form("journal_form", clear_on_submit=True):
        trade_date = st.date_input(
            "Trade Date",
            value=date.today()
        )

        symbol = st.text_input(
            "Stock Symbol"
        ).upper().strip()

        side = st.selectbox(
            "Side",
            ["BUY", "SELL"]
        )

        a, b = st.columns(2)

        entry = a.number_input(
            "Entry Price",
            min_value=0.0,
            value=0.0,
            step=0.05
        )

        exit_price = b.number_input(
            "Exit Price",
            min_value=0.0,
            value=0.0,
            step=0.05
        )

        qty = st.number_input(
            "Quantity",
            min_value=1,)
  
