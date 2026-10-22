
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

st.set_page_config(
    page_title="TradeLab Pro",
    page_icon="📈",
    layout="wide",
)

# =========================================================
# 1. APP DESIGN
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #131722;
    color: #D1D4DC;
}
[data-testid="stSidebar"] {
    background-color: #1E222D;
}
h1, h2, h3, p, label {
    color: #D1D4DC;
}
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
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
st.caption("Stock Scanner • Trading Journal • Risk Management")

# =========================================================
# 2. SOURCE REGISTRY
# Add real adapters here as integrations are implemented.
# =========================================================
DATA_SOURCES = {
    "CSV Upload": {
        "status": "Available",
        "kind": "file",
    },
    "Upstox Analytics Token": {
        "status": "Integration required",
        "kind": "api",
    },
    "yfinance": {
        "status": "Integration required",
        "kind": "api",
    },
    "NSE Bhavcopy": {
        "status": "Integration required",
        "kind": "file",
    },
    "Angel One SmartAPI": {
        "status": "Integration required",
        "kind": "api",
    },
    "Dhan API": {
        "status": "Integration required",
        "kind": "api",
    },
    "FYERS API": {
        "status": "Integration required",
        "kind": "api",
    },
    "Zerodha Kite Connect": {
        "status": "Integration required",
        "kind": "api",
    },
}

# Future indicators can be registered here without
# redesigning the whole app.
INDICATOR_REGISTRY = {
    "SMA": {"enabled": False, "module": None},
    "EMA": {"enabled": False, "module": None},
    "RSI": {"enabled": False, "module": None},
    "MACD": {"enabled": False, "module": None},
    "Bollinger Bands": {"enabled": False, "module": None},
    "Volume Indicators": {"enabled": False, "module": None},
}

# =========================================================
# 3. SESSION STATE
# =========================================================
if "journal" not in st.session_state:
    st.session_state.journal = []

# =========================================================
# 4. SIDEBAR NAVIGATION
# =========================================================
page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Dashboard",
        "Data Source & Stock Scanner",
        "Stock Data & CSV",
        "Trading Journal",
        "Risk Calculator",
        "Settings",
    ],
)

st.sidebar.divider()
st.sidebar.caption("TradeLab Pro • Modular Architecture")

# =========================================================
# 5. DASHBOARD
# =========================================================
if page == "Dashboard":
    st.header("Dashboard")

    journal = st.session_state.journal
    total_trades = len(journal)
    total_pnl = sum(t["P&L"] for t in journal)

    c1, c2, c3 = st.columns(3)
    c1.metric("Journal Trades", total_trades)
    c2.metric("Recorded Gross P&L", f"₹{total_pnl:,.2f}")
    c3.metric("Data Engine", "Modular")

    st.subheader("Project Modules")
    st.write("- Data Source Manager")
    st.write("- NSE / BSE Exchange Selection")
    st.write("- Market Capitalization Filters")
    st.write("- Optional Technical Indicators")
    st.write("- Trading Journal")
    st.write("- Risk Calculator")
    st.info(
        "Market data and broker APIs must be connected "
        "and verified before their data can be used."
    )

# =========================================================
# 6. DATA SOURCE & STOCK SCANNER
# =========================================================
elif page == "Data Source & Stock Scanner":
    st.header("Data Source Manager")

    st.write(
        "এক বা একাধিক Source নির্বাচন করুন। "
        "CSV বাধ্যতামূলক নয়।"
    )

    selected_sources = st.multiselect(
        "Select Data Sources",
        options=list(DATA_SOURCES.keys()),
        default=["CSV Upload"],
        help="একাধিক Source নির্বাচন করা যাবে।",
    )

    if not selected_sources:
        st.warning("অন্তত একটি Data Source নির্বাচন করুন।")

    st.subheader("Source Availability")

    for source in selected_sources:
        status = DATA_SOURCES[source]["status"]
        if status == "Available":
            st.success(f"{source}: {status}")
        else:
            st.warning(
                f"{source}: {status}. "
                "প্রকৃত সংযোগ তৈরি ও পরীক্ষা করতে হবে।"
            )

    st.divider()
    st.subheader("Multiple Source Mode")

    source_mode = st.selectbox(
        "Choose how to use multiple sources",
        [
            "Compare",
            "Fallback",
            "Combine",
        ],
        help=(
            "Compare: ডেটা তুলনা। "
            "Fallback: বিকল্প Source ব্যবহার। "
            "Combine: বিভিন্ন Source-এর ডেটা একত্র করা।"
        ),
    )

    st.caption(
        f"Selected mode: {source_mode}. "
        "এই সংস্করণে mode নির্বাচন করা যায়; "
        "একাধিক API-এর প্রকৃত orchestration এখনো সংযুক্ত নয়।"
    )

    st.divider()
    st.subheader("Exchange Selection")

    exchange = st.selectbox(
        "Choose Exchange",
        ["NSE", "BSE", "Both"],
    )

    st.divider()
    st.subheader("Market Capitalization Filter")

    cap_mode = st.radio(
        "Market Cap Selection",
        [
            "All Market Caps",
            "Preset Categories",
            "Custom Range",
        ],
        horizontal=False,
    )

    cap_categories = []
    min_cap = None
    max_cap = None
    cap_unit = "₹ Crore"

    if cap_mode == "All Market Caps":
        st.info("কোনো Market Cap category বাদ দেওয়া হবে না।")

    elif cap_mode == "Preset Categories":
        cap_categories = st.multiselect(
            "Select Market Cap Categories",
            ["Large Cap", "Mid Cap", "Small Cap"],
            default=["Large Cap", "Mid Cap", "Small Cap"],
        )
        st.caption(
            "Preset categories কার্যকর করতে stock universe-এর "
            "সঙ্গে নির্ভরযোগ্য market-cap classification লাগবে।"
        )

    else:
        cap_unit = st.selectbox(
            "Market Cap Unit",
            ["₹ Crore", "₹ Lakh Crore"],
        )

        c1, c2 = st.columns(2)
        with c1:
            min_cap = st.number_input(
                "Minimum Market Cap",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )
        with c2:
            max_cap = st.number_input(
                "Maximum Market Cap (0 = no upper limit)",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

        if max_cap > 0 and max_cap < min_cap:
            st.error("Maximum Market Cap, Minimum-এর চেয়ে কম হতে পারে না।")

    st.divider()
    st.subheader("Sector Filter")

    sectors = [
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
        "Other",
    ]

    selected_sectors = st.multiselect(
        "Select Sector(s)",
        sectors,
        default=["All Sectors"],
    )

    st.divider()
    st.subheader("Technical Indicators")

    use_indicators = st.toggle(
        "Enable Technical Indicators",
        value=False,
        help="বন্ধ থাকলে Indicator-এর শর্ত প্রয়োগ হবে না।",
    )

    selected_indicators = []

    if use_indicators:
        selected_indicators = st.multiselect(
            "Choose Indicators",
            list(INDICATOR_REGISTRY.keys()),
            default=[],
        )

        if selected_indicators:
            st.warning(
                "Indicator নির্বাচন করা হয়েছে। "
                "প্রকৃত calculation modules এখনো যোগ করা হয়নি।"
            )
        else:
            st.info("এখনো কোনো Indicator নির্বাচন করা হয়নি।")
    else:
        st.info(
            "Indicators বন্ধ। "
            "এটি ভবিষ্যতে নতুন Indicator যোগ করার জন্য প্রস্তুত।"
        )

    st.divider()

    if st.button("Validate Scanner Configuration", type="primary"):
        st.session_state.scanner_config = {
            "sources": selected_sources,
            "mode": source_mode,
            "exchange": exchange,
            "cap_mode": cap_mode,
            "cap_categories": cap_categories,
            "min_cap": min_cap,
            "max_cap": max_cap,
            "cap_unit": cap_unit,
            "sectors": selected_sectors,
            "indicators_enabled": use_indicators,
            "indicators": selected_indicators,
        }
        st.success("Configuration যাচাইয়ের জন্য সংরক্ষিত হয়েছে।")
        st.json(st.session_state.scanner_config)

    st.caption(
        "Note: এই পেজে configuration তৈরি হয়। "
        "পূর্ণ stock scan চালাতে প্রকৃত market data, "
        "symbol universe এবং filter engine সংযুক্ত করা বাকি।"
    )

# =========================================================
# 7. STOCK DATA & CSV
# =========================================================
elif page == "Stock Data & CSV":
    st.header("Stock Data & CSV")

    st.write(
        "CSV ব্যবহার করতে চাইলে আপলোড করুন। "
        "CSV ব্যবহার না করলেও অন্য Data Source নির্বাচন করা যাবে।"
    )

    uploaded_file = st.file_uploader(
        "Upload stock CSV",
        type=["csv"],
        key="stock_csv",
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)

            st.success("CSV সফলভাবে পড়া হয়েছে।")
            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)

            c1, c2 = st.columns(2)
            c1.metric("Rows", len(df))
            c2.metric("Columns", len(df.columns))

            st.subheader("Column Information")
            info_df = pd.DataFrame({
                "Column": df.columns,
                "Data Type": [str(x) for x in df.dtypes],
                "Missing Values": [
                    int(df[col].isna().sum())
                    for col in df.columns
                ],
            })
            st.dataframe(info_df, use_container_width=True)

            numeric_cols = df.select_dtypes(
                include="number"
            ).columns.tolist()

            if numeric_cols:
                st.subheader("Numeric Summary")
                st.dataframe(
                    df[numeric_cols].describe(),
                    use_container_width=True,
                )

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Clean Copy",
                data=csv_bytes,
                file_name="tradelab_data.csv",
                mime="text/csv",
            )

        except Exception as e:
            st.error(f"CSV পড়তে সমস্যা হয়েছে: {e}")

    else:
        st.info(
            "এখন কোনো CSV আপলোড করা হয়নি। "
            "এটি বাধ্যতামূলক নয়।"
        )

# =========================================================
# 8. TRADING JOURNAL
# =========================================================
elif page == "Trading Journal":
    st.header("Trading Journal")

    with st.form("journal_form", clear_on_submit=True):
        trade_date = st.date_input(
            "Trade Date",
            value=date.today(),
        )
        symbol = st.text_input("Stock Symbol").upper().strip()

        side = st.selectbox(
            "Trade Side",
            ["BUY", "SELL"],
        )

        c1, c2 = st.columns(2)
        with c1:
            entry = st.number_input(
                "Entry Price",
                min_value=0.0,
                value=0.0,
                step=0.05,
            )
        with c2:
            exit_price = st.number_input(
                "Exit Price",
                min_value=0.0,
                value=0.0,
                step=0.05,
            )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1,
        )

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Trade")

    if submitted:
        if not symbol:
            st.error("Stock Symbol লিখুন।")
        elif entry <= 0 or exit_price <= 0:
            st.error("Entry ও Exit Price শূন্যের বেশি হতে হবে।")
        else:
            pnl = (
                (exit_price - entry) * quantity
                if side == "BUY"
                else (entry - exit_price) * quantity
            )

            st.session_state.journal.append({
                "Date": str(trade_date),
                "Symbol": symbol,
                "Side": side,
                "Entry": entry,
                "Exit": exit_price,
                "Quantity": quantity,
                "P&L": round(pnl, 2),
                "Notes": notes,
            })

            st.success(
                f"Trade recorded. Gross P&L: ₹{pnl:,.2f}"
            )

    journal = st.session_state.journal

    if journal:
        journal_df = pd.DataFrame(journal)

        st.subheader("Recorded Trades")
        st.dataframe(journal_df, use_container_width=True)

        st.metric(
            "Total Gross P&L",
            f"₹{journal_df['P&L'].sum():,.2f}",
        )

        st.download_button(
            "Download Journal CSV",
            data=journal_df.to_csv(index=False).encode("utf-8"),
            file_name="tradelab_journal.csv",
            mime="text/csv",
        )

        if st.button("Clear Session Journal"):
            st.session_state.journal = []
            st.rerun()
    else:
        st.info(
            "এখনো কোনো trade নেই। "
            "এই সংস্করণে journal browser session-এ থাকে; "
            "স্থায়ী database storage এখনো যোগ করা হয়নি।"
        )

# =========================================================
# 9. RISK CALCULATOR
# =========================================================
elif page == "Risk Calculator":
    st.header("Risk Calculator")

    capital = st.number_input(
        "Trading Capital (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
    )

    risk_percent = st.number_input(
        "Risk per Trade (%)",
        min_value=0.1,
        max_value=100.0,
        value=1.0,
        step=0.1,
    )

    c1, c2 = st.columns(2)

    with c1:
        entry_price = st.number_input(
            "Entry Price (₹)",
            min_value=0.0,
            value=100.0,
            step=0.5,
        )

    with c2:
        stop_loss = st.number_input(
            "Stop-Loss Price (₹)",
            min_value=0.0,
            value=95.0,
            step=0.5,
        )

    if st.button("Calculate Risk", type="primary"):
        risk_amount = capital * risk_percent / 100
        risk_per_share = abs(entry_price - stop_loss)

        if capital <= 0:
            st.error("Capital শূন্যের বেশি হতে হবে।")
        elif entry_price <= 0 or stop_loss <= 0:
            st.error("Entry ও Stop-Loss সঠিকভাবে দিন।")
        elif risk_per_share == 0:
            st.error("Entry ও Stop-Loss আলাদা হতে হবে।")
        else:
            quantity_by_risk = int(
                risk_amount // risk_per_share
            )
            quantity_by_capital = int(
                capital // entry_price
            )
            quantity = min(
                quantity_by_risk,
                quantity_by_capital,
            )
            position_value = quantity * entry_price
            planned_risk = quantity * risk_per_share

            c1, c2 = st.columns(2)
            c1.metric("Risk Budget", f"₹{risk_amount:,.2f}")
            c2.metric("Risk per Share", f"₹{risk_per_share:,.2f}")

            c3, c4 = st.columns(2)
            c3.metric("Suggested Quantity", quantity)
            c4.metric("Position Value", f"₹{position_value:,.2f}")

            st.write(
                f"Estimated planned risk: ₹{planned_risk:,.2f}"
            )

            if quantity == 0:
                st.warning(
                    "এই Capital ও Risk সেটিংয়ে কেনার উপযোগী "
                    "quantity শূন্য।"
                )

            st.caption(
                "এটি একটি হিসাবের সহায়ক, বিনিয়োগের পরামর্শ নয়। "
                "Slippage, fees, taxes ও liquidity অন্তর্ভুক্ত নয়।"
            )

# =========================================================
# 10. SETTINGS
# =========================================================
elif page == "Settings":
    st.header("Settings")

    st.subheader("Application")
    st.write("App: TradeLab Pro")
    st.write("Architecture: Modular")
    st.write("CSV Upload: Optional")
    st.write("Technical Indicators: Optional")

    st.subheader("Data Source Status")
    status_df = pd.DataFrame([
        {
            "Data Source": name,
            "Status": details["status"],
            "Type": details["kind"],
        }
        for name, details in DATA_SOURCES.items()
    ])
    st.dataframe(status_df, use_container_width=True)

    st.subheader("Future Modules")
    st.write("- Real API adapters and credential management")
    st.write("- Verified NSE/BSE stock universe")
    st.write("- Market cap classification")
    st.write("- Sector mapping")
    st.write("- Expandable technical indicator registry")
    st.write("- Backtesting engine")
    st.write("- Persistent journal database")

    st.warning(
        "API keys সরাসরি app.py বা public GitHub repository-তে "
        "রাখবেন না। প্রকৃত API সংযোগের সময় Streamlit Secrets "
        "বা নিরাপদ credential management ব্যবহার করতে হবে।"
    )

st.divider()
st.caption(
    "TradeLab Pro • Educational and analytical tool. "
    "No live orders are placed."
)
