import os
import json
import tempfile
from pathlib import Path
from typing import List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
BQ_PROJECT = "zoomcamp-data-engineer-484608"
BQ_DATASET = "ph_economy_staging"

st.set_page_config(page_title="PhilsPulse Dashboard", page_icon="PH", layout="wide")


def _pick_column(df: pd.DataFrame, candidates: List[str], fallback_index: int = 0) -> Optional[str]:
    for name in candidates:
        if name in df.columns:
            return name
    if len(df.columns) == 0:
        return None
    return df.columns[min(fallback_index, len(df.columns) - 1)]


def _safe_pct_change(current: float, baseline: float) -> float:
    if pd.isna(current) or pd.isna(baseline) or baseline == 0:
        return 0.0
    return ((current - baseline) / baseline) * 100


def _read_csv_fallback(filename: str, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    candidate_paths = [
        BASE_DIR / "data" / filename,
        BASE_DIR / "datass" / filename,
        BASE_DIR / filename,
        BASE_DIR / "datasets" / filename,
    ]
    for path in candidate_paths:
        if path.exists():
            return pd.read_csv(path, parse_dates=parse_dates)
    return pd.DataFrame()


@st.cache_resource(show_spinner=False)
def _bigquery_client() -> Optional[object]:
    try:
        from google.cloud import bigquery

        # Support Streamlit Cloud secrets: either store the full JSON string in
        # `gcp_service_account_json` or the object in `gcp_service_account`.
        # If present, write a temporary JSON file and point GOOGLE_APPLICATION_CREDENTIALS to it.
        try:
            if "gcp_service_account_json" in st.secrets:
                with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as f:
                    f.write(st.secrets["gcp_service_account_json"])
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
            elif "gcp_service_account" in st.secrets:
                with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".json") as f:
                    json.dump(dict(st.secrets["gcp_service_account"]), f)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
            else:
                os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(BASE_DIR / "config" / "google_credentials.json"))
        except Exception:
            # If writing secrets fails, fall back to existing file path
            os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(BASE_DIR / "config" / "google_credentials.json"))

        return bigquery.Client()
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def load_food_prices(_client=None) -> pd.DataFrame:
    if _client is not None:
        try:
            query = f"""
                SELECT
                    date,
                    admin1,
                    market,
                    category,
                    commodity,
                    unit,
                    price,
                    usdprice
                FROM `{BQ_PROJECT}.{BQ_DATASET}.wfp_prices_raw`
            """
            df = _client.query(query).to_dataframe()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            for col in ["admin1", "market", "category", "commodity", "unit"]:
                if col in df.columns:
                    df[col] = df[col].astype("category")
            return df
        except Exception:
            pass

    df = _read_csv_fallback("raw_wfp_food_prices.csv", parse_dates=["date"])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_poverty(_client=None) -> pd.DataFrame:
    if _client is not None:
        try:
            query = f"SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.poverty_phl_raw`"
            return _client.query(query).to_dataframe()
        except Exception:
            pass
    return _read_csv_fallback("poverty_phl.csv")


@st.cache_data(ttl=1800, show_spinner=False)
def load_economic(_client=None) -> pd.DataFrame:
    if _client is not None:
        try:
            query = f"SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.economy_growth_raw`"
            return _client.query(query).to_dataframe()
        except Exception:
            pass
    return _read_csv_fallback("economy-and-growth_phl.csv")


def overview_page(_client=None):
    st.title("PhilsPulse Overview")
    st.caption("Clean snapshot of food prices, poverty indicators, and macro-economy trends.")

    food_df = load_food_prices(_client)
    pov_df = load_poverty(_client)
    econ_df = load_economic(_client)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Food Rows", f"{len(food_df):,}")
    with metric_cols[1]:
        st.metric("Poverty Rows", f"{len(pov_df):,}")
    with metric_cols[2]:
        st.metric("Economy Rows", f"{len(econ_df):,}")
    with metric_cols[3]:
        if not food_df.empty and "date" in food_df.columns:
            st.metric("Latest Food Date", str(food_df["date"].max().date()))
        else:
            st.metric("Latest Food Date", "N/A")

    if not food_df.empty and {"date", "commodity", "price"}.issubset(food_df.columns):
        st.markdown("### Monthly Food Price Trend (Top Commodities)")
        top_commodities = list(food_df["commodity"].value_counts().head(5).index)
        quick = food_df[food_df["commodity"].isin(top_commodities)].copy()
        quick = (
            quick.groupby([pd.Grouper(key="date", freq="MS"), "commodity"], observed=True)["price"]
            .median()
            .reset_index()
            .sort_values("date")
        )
        fig = px.line(
            quick,
            x="date",
            y="price",
            color="commodity",
            labels={"date": "Month", "price": "Median Price (PHP)"},
        )
        fig.update_traces(line=dict(width=2))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Preview data samples"):
        tabs = st.tabs(["Food", "Poverty", "Economy"])
        with tabs[0]:
            if food_df.empty:
                st.info("No food data available.")
            else:
                cols = [c for c in ["date", "admin1", "market", "commodity", "price"] if c in food_df.columns]
                st.dataframe(food_df[cols].sort_values("date", ascending=False).head(12), use_container_width=True)
        with tabs[1]:
            if pov_df.empty:
                st.info("No poverty data available.")
            else:
                st.dataframe(pov_df.head(12), use_container_width=True)
        with tabs[2]:
            if econ_df.empty:
                st.info("No economy data available.")
            else:
                st.dataframe(econ_df.head(12), use_container_width=True)


def food_page(_client=None):
    st.title("Food Prices")
    st.caption("Faster, cleaner monthly trends with optional smoothing and market ranking.")

    food_df = load_food_prices(_client)
    if food_df.empty:
        st.warning("No food price data available.")
        return

    required = {"date", "commodity", "price"}
    if not required.issubset(food_df.columns):
        st.error("Food dataset is missing required columns: date, commodity, price.")
        return

    food_df = food_df.dropna(subset=["date", "commodity", "price"]).copy()
    food_df["price"] = pd.to_numeric(food_df["price"], errors="coerce")
    food_df = food_df.dropna(subset=["price"])

    st.sidebar.subheader("Food Filters")
    commodities = sorted(food_df["commodity"].astype(str).unique())
    default_commodities = list(food_df["commodity"].value_counts().head(5).index)
    selected_commodities = st.sidebar.multiselect("Commodities", commodities, default=default_commodities)
    if not selected_commodities:
        st.info("Select at least one commodity.")
        return

    min_date = food_df["date"].min().date()
    max_date = food_df["date"].max().date()
    date_start, date_end = st.sidebar.date_input("Date Range", value=(min_date, max_date))

    agg_method = st.sidebar.radio("Monthly aggregation", ["Median", "Mean"], index=0, horizontal=True)
    smoothing_window = st.sidebar.slider("Rolling average (months)", 1, 12, 3)

    filtered = food_df[
        (food_df["commodity"].isin(selected_commodities))
        & (food_df["date"] >= pd.to_datetime(date_start))
        & (food_df["date"] <= pd.to_datetime(date_end))
    ].copy()
    if filtered.empty:
        st.warning("No food data for selected filters.")
        return

    group = filtered.groupby([pd.Grouper(key="date", freq="MS"), "commodity"], observed=True)["price"]
    if agg_method == "Median":
        monthly = group.median().reset_index()
    else:
        monthly = group.mean().reset_index()
    monthly = monthly.sort_values(["commodity", "date"])
    monthly["smoothed_price"] = monthly.groupby("commodity")["price"].transform(
        lambda s: s.rolling(window=smoothing_window, min_periods=1).mean()
    )

    latest_month = monthly["date"].max()
    latest_avg = monthly[monthly["date"] == latest_month]["smoothed_price"].mean()
    one_year_ago = latest_month - pd.DateOffset(years=1)
    baseline_rows = monthly[monthly["date"] == one_year_ago]
    baseline_avg = baseline_rows["smoothed_price"].mean() if not baseline_rows.empty else 0
    yoy_change = _safe_pct_change(latest_avg, baseline_avg)

    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        st.metric("Latest Avg Price", f"PHP {latest_avg:,.2f}")
    with kpi_cols[1]:
        st.metric("Year-over-Year", f"{yoy_change:+.1f}%")
    with kpi_cols[2]:
        st.metric("Observations", f"{len(filtered):,}")

    line_fig = px.line(
        monthly,
        x="date",
        y="smoothed_price",
        color="commodity",
        markers=True,
        labels={"date": "Month", "smoothed_price": f"{agg_method} Price (PHP)"},
        title="Monthly Commodity Price Trends",
    )
    line_fig.update_traces(line=dict(width=2))
    st.plotly_chart(line_fig, use_container_width=True)

    lower_col, right_col = st.columns([1.3, 1])
    with lower_col:
        box_fig = px.box(
            filtered,
            x="commodity",
            y="price",
            color="commodity",
            points=False,
            title="Price Distribution by Commodity",
            labels={"price": "Price (PHP)", "commodity": "Commodity"},
        )
        box_fig.update_layout(showlegend=False)
        st.plotly_chart(box_fig, use_container_width=True)

    with right_col:
        st.markdown("### Top Markets (Avg Price)")
        if "market" in filtered.columns:
            market_rank = (
                filtered.groupby("market", observed=True)["price"]
                .mean()
                .reset_index()
                .sort_values("price", ascending=False)
                .head(12)
            )
            market_rank = market_rank.rename(columns={"market": "Market", "price": "Avg Price (PHP)"})
            st.dataframe(market_rank, use_container_width=True, height=360)
        else:
            st.info("Market column not available in data source.")

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered food data",
        data=csv_bytes,
        file_name="food_filtered.csv",
        mime="text/csv",
    )


def poverty_page(_client=None):
    st.title("Poverty")
    st.caption("Indicator trends and latest snapshot with clean filtering.")

    pov_df = load_poverty(_client)
    if pov_df.empty:
        st.warning("No poverty data available.")
        return

    year_col = _pick_column(pov_df, ["year", "report_year"], fallback_index=2)
    value_col = _pick_column(pov_df, ["value", "poverty_rate_pct", "poverty_rate"])
    indicator_col = _pick_column(pov_df, ["indicator_name", "indicator", "indicator_code"], fallback_index=3)

    if year_col is None or value_col is None or indicator_col is None:
        st.error("Poverty dataset does not have enough structured columns for charting.")
        st.dataframe(pov_df.head(20), use_container_width=True)
        return

    df = pov_df[[year_col, indicator_col, value_col]].copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[year_col, value_col, indicator_col])

    years = sorted(df[year_col].astype(int).unique().tolist())
    if not years:
        st.warning("No valid poverty years found.")
        return

    st.sidebar.subheader("Poverty Filters")
    year_min, year_max = st.sidebar.select_slider("Year Range", options=years, value=(years[0], years[-1]))
    indicator_options = sorted(df[indicator_col].astype(str).unique().tolist())
    default_indicators = indicator_options[:4]
    selected_indicators = st.sidebar.multiselect("Indicators", indicator_options, default=default_indicators)
    if not selected_indicators:
        st.info("Select at least one indicator.")
        return

    filtered = df[
        (df[year_col] >= year_min)
        & (df[year_col] <= year_max)
        & (df[indicator_col].isin(selected_indicators))
    ]
    if filtered.empty:
        st.warning("No poverty data for selected filters.")
        return

    trend = (
        filtered.groupby([year_col, indicator_col], observed=True)[value_col]
        .mean()
        .reset_index()
        .sort_values(year_col)
    )
    trend_fig = px.line(
        trend,
        x=year_col,
        y=value_col,
        color=indicator_col,
        markers=True,
        labels={year_col: "Year", value_col: "Value"},
        title="Poverty Indicator Trends",
    )
    trend_fig.update_traces(line=dict(width=2))
    st.plotly_chart(trend_fig, use_container_width=True)

    latest_year = int(trend[year_col].max())
    latest = trend[trend[year_col] == latest_year].sort_values(value_col, ascending=False)
    bar_fig = px.bar(
        latest.head(12),
        x=value_col,
        y=indicator_col,
        orientation="h",
        labels={value_col: "Latest Value", indicator_col: "Indicator"},
        title=f"Latest Indicator Snapshot ({latest_year})",
    )
    st.plotly_chart(bar_fig, use_container_width=True)


def economy_page(_client=None):
    st.title("Economic Growth")
    st.caption("Indicator-focused view that avoids mixed-series spikes and invalid KPI rows.")

    econ_df = load_economic(_client)
    if econ_df.empty:
        st.warning("No economic growth data available.")
        return

    year_col = _pick_column(econ_df, ["year", "report_year", "date"], fallback_index=0)
    if year_col is None:
        st.error("Could not infer year column for economy data.")
        return

    indicator_col = _pick_column(econ_df, ["indicator_name", "indicator", "indicator_code"], fallback_index=3)
    value_col = _pick_column(econ_df, ["value"], fallback_index=5)

    df = econ_df.copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    current_year = pd.Timestamp.today().year

    st.sidebar.subheader("Economy Filters")
    exclude_non_positive = st.sidebar.checkbox("Exclude zero/negative values", value=True)
    chart_style = st.sidebar.radio("Chart style", ["Bar", "Line"], index=0, horizontal=True)

    # Preferred handling for World Bank long-format data
    if indicator_col in df.columns and value_col in df.columns:
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df = df.dropna(subset=[year_col, value_col, indicator_col])
        df = df[(df[year_col] >= 1960) & (df[year_col] <= current_year)]
        if exclude_non_positive:
            df = df[df[value_col] > 0]

        if df.empty:
            st.warning("No valid economic rows remain after cleaning filters.")
            return

        indicators = sorted(df[indicator_col].astype(str).unique().tolist())
        selected_indicator = st.sidebar.selectbox("Indicator", indicators)

        df_filtered = (
            df[df[indicator_col] == selected_indicator]
            .groupby(year_col, observed=True)[value_col]
            .mean()
            .reset_index()
            .sort_values(year_col)
        )

        if df_filtered.empty:
            st.warning("No rows for the selected indicator.")
            return

        if chart_style == "Bar":
            fig = px.bar(
                df_filtered,
                x=year_col,
                y=value_col,
                labels={year_col: "Year", value_col: "Value"},
                title=f"{selected_indicator} by Year",
            )
        else:
            fig = px.line(
                df_filtered,
                x=year_col,
                y=value_col,
                markers=True,
                labels={year_col: "Year", value_col: "Value"},
                title=f"{selected_indicator} by Year",
            )
            fig.update_traces(line=dict(width=2))
        st.plotly_chart(fig, use_container_width=True)

        latest_year = int(df_filtered[year_col].max())
        latest_val = float(df_filtered[df_filtered[year_col] == latest_year][value_col].iloc[-1])
        first_year = int(df_filtered[year_col].min())
        first_val = float(df_filtered[df_filtered[year_col] == first_year][value_col].iloc[0])
        growth_pct = _safe_pct_change(latest_val, first_val)

        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.metric("Latest", f"{latest_val:,.2f}")
        with kpi_cols[1]:
            st.metric("Latest Year", f"{latest_year}")
        with kpi_cols[2]:
            st.metric("Since First Year", f"{growth_pct:+.1f}%")
        with kpi_cols[3]:
            st.metric("Years Covered", f"{df_filtered[year_col].nunique()}")

        with st.expander("Show cleaned economic dataset"):
            st.dataframe(df_filtered, use_container_width=True)

        return

    # Fallback for wide-format economy tables
    numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != year_col]
    if not numeric_cols:
        st.error("No numeric economic metrics available.")
        return

    selected_metric = st.sidebar.selectbox("Metric", numeric_cols, index=0)
    trend_df = df[[year_col, selected_metric]].dropna().sort_values(year_col)
    trend_df = trend_df[(trend_df[year_col] >= 1960) & (trend_df[year_col] <= current_year)]
    if exclude_non_positive:
        trend_df = trend_df[trend_df[selected_metric] > 0]

    if trend_df.empty:
        st.warning("No valid metric rows remain after cleaning filters.")
        return

    if chart_style == "Bar":
        fig = px.bar(
            trend_df,
            x=year_col,
            y=selected_metric,
            labels={year_col: "Year", selected_metric: "Value"},
            title=f"{selected_metric} by Year",
        )
    else:
        fig = px.line(
            trend_df,
            x=year_col,
            y=selected_metric,
            markers=True,
            labels={year_col: "Year", selected_metric: "Value"},
            title=f"{selected_metric} by Year",
        )
        fig.update_traces(line=dict(width=2))
    st.plotly_chart(fig, use_container_width=True)

    latest_val = float(trend_df[selected_metric].iloc[-1])
    first_val = float(trend_df[selected_metric].iloc[0])
    growth_pct = _safe_pct_change(latest_val, first_val)
    kpi_cols = st.columns(3)
    with kpi_cols[0]:
        st.metric("Latest", f"{latest_val:,.2f}")
    with kpi_cols[1]:
        st.metric("Since First Year", f"{growth_pct:+.1f}%")
    with kpi_cols[2]:
        st.metric("Years Covered", f"{trend_df[year_col].nunique()}")


def cross_dataset_page(_client=None):
    st.title("Cross-dataset Analysis")
    st.caption("Compare food prices, poverty, and economy with clearer options for single or multiple food commodities.")

    label_map = {
        "Annualized average growth rate in per capita real survey mean consumption or income, total population (%)": "Avg Growth (Total)",
        "Annualized average growth rate in per capita real survey mean consumption or income, bottom 40% of population (%)": "Avg Growth (Bottom 40%)",
        "Proportion of people living below 50 percent of median income (%)": "Below 50% Median Income (%)",
        "Income share held by fourth 20%": "Income Share 4th 20%",
        "Gini index": "Gini Index",
    }

    food_df = load_food_prices(_client)
    pov_df = load_poverty(_client)
    econ_df = load_economic(_client)

    if food_df.empty or pov_df.empty or econ_df.empty:
        st.warning("Cross analysis requires all three datasets.")
        return

    if not {"date", "commodity", "price"}.issubset(food_df.columns):
        st.warning("Food dataset missing required columns for cross analysis.")
        return

    pov_year_col = _pick_column(pov_df, ["year", "report_year"], fallback_index=2)
    pov_value_col = _pick_column(pov_df, ["value", "poverty_rate_pct", "poverty_rate"])
    pov_indicator_col = _pick_column(pov_df, ["indicator_name", "indicator", "indicator_code"], fallback_index=3)
    econ_year_col = _pick_column(econ_df, ["year", "report_year", "date"], fallback_index=0)
    econ_indicator_col = _pick_column(econ_df, ["indicator_name", "indicator", "indicator_code"], fallback_index=3)
    econ_value_col = _pick_column(econ_df, ["value"], fallback_index=5)

    if None in [pov_year_col, pov_value_col, pov_indicator_col, econ_year_col]:
        st.warning("Could not infer columns for poverty/economy cross-analysis.")
        return

    food_df = food_df.copy()
    food_df["date"] = pd.to_datetime(food_df["date"], errors="coerce")
    food_df["year"] = food_df["date"].dt.year
    food_df["price"] = pd.to_numeric(food_df["price"], errors="coerce")
    food_df = food_df.dropna(subset=["year", "price", "commodity"])

    pov = pov_df[[pov_year_col, pov_indicator_col, pov_value_col]].copy()
    pov[pov_year_col] = pd.to_numeric(pov[pov_year_col], errors="coerce")
    pov[pov_value_col] = pd.to_numeric(pov[pov_value_col], errors="coerce")
    pov = pov.dropna(subset=[pov_year_col, pov_value_col, pov_indicator_col])

    econ = econ_df.copy()
    econ[econ_year_col] = pd.to_numeric(econ[econ_year_col], errors="coerce")
    econ = econ.dropna(subset=[econ_year_col])
    econ_long_format = (econ_indicator_col in econ.columns) and (econ_value_col in econ.columns)
    if econ_long_format:
        econ[econ_value_col] = pd.to_numeric(econ[econ_value_col], errors="coerce")
        econ = econ.dropna(subset=[econ_value_col, econ_indicator_col])
    else:
        econ_numeric_cols = [c for c in econ.select_dtypes(include="number").columns if c != econ_year_col]
        if not econ_numeric_cols:
            st.warning("No numeric economy metric available for cross analysis.")
            return

    st.sidebar.subheader("Cross-analysis Filters")
    food_mode = st.sidebar.radio(
        "Food mode",
        [
            "Single commodity",
            "Multiple commodities average",
            "Multiple commodities separate",
        ],
        index=1,
    )
    food_agg = st.sidebar.selectbox("Food aggregation", ["Median", "Mean"], index=0)

    commodity_options = sorted(food_df["commodity"].astype(str).unique().tolist())
    default_foods = commodity_options[:3]

    if food_mode == "Single commodity":
        single_food = st.sidebar.selectbox("Food commodity", commodity_options)
        selected_foods = [single_food]
    else:
        selected_foods = st.sidebar.multiselect("Food commodities", commodity_options, default=default_foods)
        if not selected_foods:
            st.info("Select at least one food commodity.")
            return

    poverty_options = sorted(pov[pov_indicator_col].astype(str).unique().tolist())
    poverty_choice = st.sidebar.selectbox(
        "Poverty indicator",
        poverty_options,
        format_func=lambda x: label_map.get(x, x if len(x) <= 48 else f"{x[:45]}..."),
    )
    st.sidebar.caption("Tip: pick Gini Index or Income Share 4th 20% for denser yearly coverage.")

    if econ_long_format:
        econ_options = sorted(econ[econ_indicator_col].astype(str).unique().tolist())
        econ_choice = st.sidebar.selectbox(
            "Economy indicator",
            econ_options,
            format_func=lambda x: label_map.get(x, x if len(x) <= 48 else f"{x[:45]}..."),
        )
    else:
        econ_choice = st.sidebar.selectbox("Economy metric", econ_numeric_cols)
    value_mode = st.sidebar.radio("Display mode", ["Indexed (Base=100)", "Raw values"], index=0)
    year_alignment = st.sidebar.radio(
        "Year alignment",
        ["Use full timeline", "Only overlapping years"],
        index=0,
        help="Full timeline keeps all years from selected series and shows gaps when one series has missing years.",
    )

    food_filtered = food_df[food_df["commodity"].isin(selected_foods)].copy()
    food_grouped = food_filtered.groupby(["year", "commodity"], observed=True)["price"]
    if food_agg == "Median":
        food_grouped = food_grouped.median().reset_index(name="food_price")
    else:
        food_grouped = food_grouped.mean().reset_index(name="food_price")

    food_series_names = []
    if food_mode == "Single commodity":
        food_col_name = f"Food: {selected_foods[0]}"
        food_series = (
            food_grouped[food_grouped["commodity"] == selected_foods[0]][["year", "food_price"]]
            .rename(columns={"food_price": food_col_name})
            .sort_values("year")
        )
        food_series_names = [food_col_name]
    elif food_mode == "Multiple commodities average":
        food_col_name = f"Food average ({len(selected_foods)} items)"
        food_series = (
            food_grouped.groupby("year", observed=True)["food_price"]
            .mean()
            .reset_index()
            .rename(columns={"food_price": food_col_name})
            .sort_values("year")
        )
        food_series_names = [food_col_name]
    else:
        if len(selected_foods) > 6:
            selected_foods = selected_foods[:6]
            st.info("Showing the first 6 selected commodities for readability.")
        food_series = (
            food_grouped[food_grouped["commodity"].isin(selected_foods)]
            .pivot_table(index="year", columns="commodity", values="food_price", aggfunc="mean")
            .reset_index()
            .sort_values("year")
        )
        rename_map = {c: f"Food: {c}" for c in food_series.columns if c != "year"}
        food_series = food_series.rename(columns=rename_map)
        food_series_names = [c for c in food_series.columns if c != "year"]

    pov_series = (
        pov[pov[pov_indicator_col] == poverty_choice]
        .groupby(pov_year_col, observed=True)[pov_value_col]
        .mean()
        .reset_index()
        .rename(columns={pov_year_col: "year", pov_value_col: "poverty_value"})
    )
    if econ_long_format:
        econ_series = (
            econ[econ[econ_indicator_col] == econ_choice]
            .groupby(econ_year_col, observed=True)[econ_value_col]
            .mean()
            .reset_index()
            .rename(columns={econ_year_col: "year", econ_value_col: "economy_value"})
        )
    else:
        econ_series = (
            econ.groupby(econ_year_col, observed=True)[econ_choice]
            .mean()
            .reset_index()
            .rename(columns={econ_year_col: "year", econ_choice: "economy_value"})
        )

    poverty_series_name = f"Poverty: {label_map.get(poverty_choice, poverty_choice)}"
    economy_series_name = f"Economy: {label_map.get(econ_choice, econ_choice)}"
    pov_series = pov_series.rename(columns={"poverty_value": poverty_series_name})
    econ_series = econ_series.rename(columns={"economy_value": economy_series_name})

    # Fill poverty survey gaps forward so yearly comparisons/correlations are less sparse.
    year_candidates = pd.concat(
        [
            food_series[["year"]],
            econ_series[["year"]],
        ],
        ignore_index=True,
    ).dropna()
    if not year_candidates.empty:
        year_candidates = year_candidates["year"].astype(int)
        full_years = pd.DataFrame({"year": range(int(year_candidates.min()), int(year_candidates.max()) + 1)})
        pov_series = full_years.merge(pov_series, on="year", how="left").sort_values("year")
        pov_series[poverty_series_name] = pov_series[poverty_series_name].ffill()

    join_type = "outer" if year_alignment == "Use full timeline" else "inner"
    merged = food_series.merge(pov_series, on="year", how=join_type).merge(econ_series, on="year", how=join_type)
    merged = merged.sort_values("year")
    if merged.empty:
        st.warning("No overlapping years across selected series.")
        return

    year_options = sorted(merged["year"].astype(int).unique().tolist())
    if len(year_options) >= 2:
        year_start, year_end = st.sidebar.select_slider("Year range", options=year_options, value=(year_options[0], year_options[-1]))
        merged = merged[(merged["year"] >= year_start) & (merged["year"] <= year_end)]

    series_cols = [c for c in merged.columns if c != "year"]
    if not series_cols:
        st.warning("No series available after filtering.")
        return

    plot_df = merged.copy()
    if value_mode == "Indexed (Base=100)":
        for col in series_cols:
            first_valid = plot_df[col].dropna()
            if first_valid.empty:
                plot_df[col] = pd.NA
            else:
                base = first_valid.iloc[0]
                plot_df[col] = 100 if base == 0 else (plot_df[col] / base) * 100

    long_df = plot_df.melt(
        id_vars=["year"],
        value_vars=series_cols,
        var_name="series",
        value_name="series_value",
    )

    idx_fig = px.line(
        long_df,
        x="year",
        y="series_value",
        color="series",
        markers=True,
        labels={
            "series_value": "Index (Base=100)" if value_mode == "Indexed (Base=100)" else "Value",
            "year": "Year",
        },
        title="Cross-dataset Trend Comparison",
    )
    idx_fig.update_traces(line=dict(width=2.5))
    idx_fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="left",
            x=0,
            title=None,
        ),
        margin=dict(b=120),
    )
    st.plotly_chart(idx_fig, use_container_width=True)

    # Correlation uses complete-case rows to avoid misleading values from missing years.
    corr_input = merged[["year"] + series_cols].dropna(subset=series_cols, how="any")
    if len(corr_input) < 3:
        st.info(
            "Correlation is based on very few overlapping years. "
            "Try switching to 'Only overlapping years' or selecting a poverty indicator with more years."
        )
    if len(corr_input) >= 2:
        corr = corr_input[series_cols].corr(numeric_only=True)
        corr_fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1, title="Correlation Matrix")
        st.plotly_chart(corr_fig, use_container_width=True)
    else:
        corr = pd.DataFrame()
        st.warning("Not enough overlapping rows to compute correlation.")

    if (not corr.empty) and food_series_names and poverty_series_name in corr.columns and economy_series_name in corr.columns:
        summary_rows = []
        for name in food_series_names:
            if name in corr.columns:
                summary_rows.append(
                    {
                        "food_series": name,
                        "corr_with_poverty": round(float(corr.loc[name, poverty_series_name]), 3),
                        "corr_with_economy": round(float(corr.loc[name, economy_series_name]), 3),
                    }
                )
        if summary_rows:
            st.markdown("### Food Correlation Summary")
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    if series_cols:
        availability = []
        for col in series_cols:
            col_non_null = merged[["year", col]].dropna()
            if not col_non_null.empty:
                availability.append(
                    {
                        "series": col,
                        "start_year": int(col_non_null["year"].min()),
                        "end_year": int(col_non_null["year"].max()),
                        "points": int(len(col_non_null)),
                    }
                )
        if availability:
            st.markdown("### Series Availability")
            st.dataframe(pd.DataFrame(availability), use_container_width=True)

    with st.expander("Show comparison dataset"):
        st.dataframe(merged, use_container_width=True)


def main():
    st.sidebar.title("PhilsPulse")
    page = st.sidebar.radio(
        "Page",
        ["Overview", "Food Prices", "Poverty", "Economic Growth", "Cross-dataset"],
    )

    client = _bigquery_client()

    if page == "Overview":
        overview_page(client)
    elif page == "Food Prices":
        food_page(client)
    elif page == "Poverty":
        poverty_page(client)
    elif page == "Economic Growth":
        economy_page(client)
    else:
        cross_dataset_page(client)


if __name__ == "__main__":
    main()