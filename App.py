import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# TradeLab Pro - Version 1.0
# ==========================================

st.set_page_config(
    page_title="TradeLab Pro",
    page_icon="📈",
    layout="wide"
)

# ---------- Styling ----------

st.markdown("""
<style>
.stApp {
    background-color: #0b1120;
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #111827;
}
h1, h2, h3 {
    color: #38bdf8;
}
div[data-testid="stMetric"] {
    background: #172033;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #263449;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------

st.title("📈 TradeLab Pro")
st.caption("Stock Analysis • Trading Journal • Risk Management")
st.divider()

# ---------- Sidebar ----------

st.sidebar.title("TradeLab Pro")
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Stock Data & CSV",
        "Trading Journal",
        "Risk Calculator",
        "Settings"
    ]
)

st.sidebar.caption("Version 1.0")
st.sidebar.caption("Data: CSV / Manual")

# ---------- Dashboard ----------

if page == "Dashboard":
    st.header("Dashboard")
    st.write("Welcome to your personal trading workspace.")

    col1, col2, col3 = st.columns(3)

    col1.metric("Uploaded Rows", "0")
    col2.metric("Journal Trades", "0")
    col3.metric("Data Source", "CSV / Manual")

    st.subheader("Getting Started")
    st.markdown("""
    1. Open **Stock Data & CSV** to import market data.
    2. Open **Trading Journal** to record your trades.
    3. Open **Risk Calculator** to calculate position size.
    4. Use **Settings** to review future data-source options.
    """)

    st.info(
        "This version is for analysis and record keeping. "
        "It does not place live orders."
    )

# ---------- Stock Data & CSV ----------

elif page == "Stock Data & CSV":
    st.header("Stock Data & CSV Import")

    st.write(
        "Upload a CSV file containing stock prices or "
        "other tabular market data."
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"]
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.success("CSV file loaded successfully.")
            st.write("Rows:", len(df))
            st.write("Columns:", len(df.columns))

            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)

            st.subheader("Column Statistics")
            numeric_df = df.select_dtypes(include="number")

            if not numeric_df.empty:
                st.dataframe(
                    numeric_df.describe(),
                    use_container_width=True
                )
            else:
                st.info("No numeric columns were found.")

            st.download_button(
                "Download Imported CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="tradelab_export.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Could not read the CSV file: {e}")

    st.divider()
    st.subheader("Expected Stock Data Columns")

    st.code(
        "Date, Symbol, Open, High, Low, Close, Volume",
        language="text"
    )

    st.caption(
        "Column names can vary. Automatic stock indicators "
        "will be added in a later version."
    )

# ---------- Trading Journal ----------

elif page == "Trading Journal":
    st.header("Trading Journal")

    with st.form("trade_form"):
        trade_date = st.date_input(
            "Trade Date",
            value=datetime.today().date()
        )

        symbol = st.text_input(
            "Stock Symbol",
            placeholder="e.g. RELIANCE"
        ).strip().upper()

        side = st.selectbox(
            "Trade Type",
            ["BUY", "SELL"]
        )

        entry = st.number_input(
            "Entry Price (₹)",
            min_value=0.0,
            value=0.0,
            step=0.05
        )

        exit_price = st.number_input(
            "Exit Price (₹)",
            min_value=0.0,
            value=0.0,
            step=0.05
        )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1
        )

        notes = st.text_area("Notes")

        submitted = st.form_submit_button(
            "Calculate & Add Trade"
        )

    if submitted:
        if not symbol or entry <= 0 or exit_price <= 0:
            st.error(
                "Enter a stock symbol and positive entry "
                "and exit prices."
            )
        else:
            if side == "BUY":
                pnl = (exit_price - entry) * quantity
            else:
                pnl = (entry - exit_price) * quantity

            st.subheader("Trade Result")
            st.metric("Gross P&L (₹)", f"{pnl:,.2f}")

            st.caption(
                "This result excludes brokerage, taxes, "
                "slippage, and other charges."
            )

            trade_record = pd.DataFrame([{
                "Date": str(trade_date),
                "Symbol": symbol,
                "Side": side,
                "Entry": entry,
                "Exit": exit_price,
                "Quantity": quantity,
                "Gross_PnL": round(pnl, 2),
                "Notes": notes
            }])

            st.download_button(
                "Download This Trade as CSV",
                data=trade_record.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="tradelab_trade.csv",
                mime="text/csv"
            )

            st.info(
                "Download your record to keep it. "
                "Persistent journal storage will be added later."
            )

# ---------- Risk Calculator ----------

elif page == "Risk Calculator":
    st.header("Risk Calculator")

    capital = st.number_input(
        "Trading Capital (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0
    )

    risk_percent = st.number_input(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=100.0,
        value=1.0,
        step=0.1
    )

    entry_price = st.number_input(
        "Entry Price (₹)",
        min_value=0.0,
        value=100.0,
        step=0.5
    )

    stop_loss = st.number_input(
        "Stop-Loss Price (₹)",
        min_value=0.0,
        value=95.0,
        step=0.5
    )

    if st.button("Calculate Position Size"):
        risk_amount = capital * risk_percent / 100
        risk_per_share = abs(entry_price - stop_loss)

        if capital <= 0 or entry_price <= 0:
            st.error("Capital and entry price must be positive.")
        elif risk_per_share <= 0:
            st.error(
                "Entry and stop-loss prices must be different."
            )
        elif stop_loss >= entry_price:
            st.warning(
                "For a BUY trade, the stop-loss is normally "
                "below the entry price. Check your inputs."
            )
        else:
            quantity = int(risk_amount // risk_per_share)

            st.metric(
                "Maximum Planned Risk",
                f"₹{risk_amount:,.2f}"
            )
            st.metric(
                "Risk per Share",
                f"₹{risk_per_share:,.2f}"
            )
            st.metric(
                "Calculated Quantity",
                f"{quantity:,}"
            )
            st.metric(
                "Approximate Position Value",
                f"₹{quantity * entry_price:,.2f}"
            )

            st.caption(
                "Planning estimate only. Actual losses can exceed "
                "planned risk because of gaps, slippage, and execution."
            )

# ---------- Settings ----------

elif page == "Settings":
    st.header("Settings & Data Sources")

    st.subheader("Currently Available")
    st.write("✅ CSV file import")
    st.write("✅ Manual trade entry")
    st.write("✅ Basic risk calculator")

    st.subheader("Future Integrations")
    st.write("⬜ Yahoo Finance data")
    st.write("⬜ Upstox API connection")
    st.write("⬜ Persistent database")
    st.write("⬜ Technical indicators and stock screener")

    st.warning(
        "These integrations are not active in this version. "
        "API credentials should never be committed to GitHub."
    )

st.divider()
st.caption(
    "TradeLab Pro | Educational and analytical tool | "
    "Not investment advice"
  )
  
