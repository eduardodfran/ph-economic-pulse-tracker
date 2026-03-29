import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from plotly.subplots import make_subplots


BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(BASE_DIR / "config" / "google_credentials.json"))

client = bigquery.Client()


st.set_page_config(
    page_title="PhilsPulse: The Kamote Paradox Solved",
    page_icon="🇵🇭",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .hero {
        padding: 1.5rem 1.75rem;
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(8, 47, 73, 0.96));
        border: 1px solid rgba(148, 163, 184, 0.16);
        box-shadow: 0 20px 60px rgba(2, 6, 23, 0.35);
        margin-bottom: 1rem;
    }
    .hero h1 { color: #f8fafc; font-size: 2.2rem; margin-bottom: 0.25rem; }
    .hero p { color: #cbd5e1; margin: 0; font-size: 1rem; }
    .section-label { color: #94a3b8; font-size: 0.78rem; letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 0.25rem; }
    .footer {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(148, 163, 184, 0.2);
        color: #94a3b8;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_master_data() -> pd.DataFrame:
    query = """
        SELECT *
        FROM `zoomcamp-data-engineer-484608.ph_economy_staging.fct_economic_pulse`
        ORDER BY report_month ASC
    """
    frame = client.query(query).to_dataframe()
    frame["report_month"] = pd.to_datetime(frame["report_month"])
    return frame


@st.cache_data(show_spinner=False)
def get_correlation_data() -> pd.DataFrame:
    query = """
        SELECT *
        FROM `zoomcamp-data-engineer-484608.ph_economy_staging.fct_economic_correlation`
        ORDER BY report_year ASC
    """
    frame = client.query(query).to_dataframe()
    return frame


def format_money(value: float) -> str:
    return f"₱{value:,.2f}"


def safe_percent_change(first_value: float, last_value: float) -> float:
    if pd.isna(first_value) or pd.isna(last_value) or first_value == 0:
        return 0.0
    return ((last_value - first_value) / first_value) * 100


def calculate_pct_change(current: float, baseline: float) -> float:
    """Calculate percent change using (current - baseline) / baseline.

    Returns 0.0 if baseline is None, zero, or NaN to avoid division-by-zero
    and NaN display in the dashboard.
    """
    if baseline is None or baseline == 0 or pd.isna(baseline):
        return 0.0
    if pd.isna(current):
        return 0.0
    try:
        return ((current - baseline) / baseline) * 100
    except Exception:
        return 0.0


def build_yearly_view(df: pd.DataFrame, selected_region: str) -> pd.DataFrame:
    region_df = df[df["region"] == selected_region].copy()
    region_df = region_df[region_df["report_month"].dt.year >= 2006]

    yearly_df = (
        region_df.assign(report_year=region_df["report_month"].dt.year)
        .groupby("report_year", as_index=False)
        .agg(
            kamote_price=("avg_price_php", "mean"),
            affordability_index=("affordability_index", "mean"),
            net_income_per_capita=("net_income_per_capita", "mean"),
            poverty_rate_pct=("poverty_rate_pct", "mean"),
            gini_index=("gini_index", "mean"),
            slum_pop_pct=("slum_pop_pct", "mean"),
        )
        .sort_values("report_year")
    )

    return yearly_df


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="section-label">Kamote paradox dashboard</div>
            <h1>PhilsPulse: The Kamote Paradox Solved</h1>
            <p>Track how kamote prices, income, and poverty move together across Philippine regions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(df: pd.DataFrame) -> tuple[str, str]:
    st.sidebar.header("Explore")
    st.sidebar.caption("Use the controls below to compare regions and switch the left axis metric.")

    region = st.sidebar.selectbox(
        "Select Region",
        options=sorted(df["region"].dropna().unique()),
    )
    metric_choice = st.sidebar.selectbox(
        "Left-axis metric",
        options=["Nominal Price", "Affordability Index"],
        help="Nominal price shows kamote price in pesos; affordability shows how much income buys per peso of kamote.",
    )
    return region, metric_choice


def render_metrics(yearly_df: pd.DataFrame) -> None:
    if yearly_df.empty:
        st.warning("No data found for this region and time window.")
        return

    import numpy as np
    start = yearly_df.iloc[0]
    end = yearly_df.iloc[-1]

    def safe_display(val, fmt, na_val="N/A"):
        if pd.isna(val) or (isinstance(val, float) and not np.isfinite(val)):
            return na_val
        try:
            return fmt.format(val)
        except Exception:
            return na_val

    kamote_price_increase = calculate_pct_change(end["kamote_price"], start["kamote_price"])
    poverty_decrease = calculate_pct_change(end["poverty_rate_pct"], start["poverty_rate_pct"])
    affordability_shift_ratio = (end["affordability_index"] / start["affordability_index"]) if start["affordability_index"] else np.nan

    metric_cols = st.columns(3)

    with metric_cols[0]:
        st.metric(
            "Total % Increase in Kamote Price",
            safe_display(kamote_price_increase, "{:+.1f}%", na_val="0%"),
            delta=f"{safe_display(end['kamote_price'], '₱{:.2f}', 'N/A')} vs {safe_display(start['kamote_price'], '₱{:.2f}', 'N/A')}",
            delta_color="inverse",
        )

    with metric_cols[1]:
        st.metric(
            "Total % Decrease in Poverty Incidence",
            safe_display(abs(poverty_decrease), "{:.1f}%", na_val="0%"),
            delta=f"{safe_display(end['poverty_rate_pct'], '{:.1f}%', 'N/A')} today vs {safe_display(start['poverty_rate_pct'], '{:.1f}%', 'N/A')} in 2006",
        )

    with metric_cols[2]:
        if pd.isna(affordability_shift_ratio) or not np.isfinite(affordability_shift_ratio) or affordability_shift_ratio == 0:
            shift_delta = "No baseline"
            aff_val = "N/A"
        else:
            shift_delta = f"{((affordability_shift_ratio - 1) * 100):+.1f}% vs 2006"
            aff_val = f"{affordability_shift_ratio:.2f}x"
        st.metric(
            "Affordability Shift",
            aff_val,
            delta=shift_delta,
        )


def render_dual_axis_chart(yearly_df: pd.DataFrame, selected_region: str, metric_choice: str) -> None:
    st.subheader("Dual-Axis Kamote Paradox")
    st.caption("Kamote price is on the left axis. Net National Income is on the right axis.")

    left_metric = "kamote_price" if metric_choice == "Nominal Price" else "affordability_index"
    left_title = "Kamote Price (PHP)" if metric_choice == "Nominal Price" else "Affordability Index"
    left_name = "Kamote Price" if metric_choice == "Nominal Price" else "Affordability Index"
    left_color = "#f59e0b" if metric_choice == "Nominal Price" else "#38bdf8"

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=yearly_df["report_year"],
            y=yearly_df[left_metric],
            name=left_name,
            mode="lines+markers",
            line=dict(color=left_color, width=3),
            marker=dict(size=8),
            hovertemplate="Year %{x}<br>%{y:.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=yearly_df["report_year"],
            y=yearly_df["net_income_per_capita"],
            name="Net National Income",
            mode="lines+markers",
            line=dict(color="#22c55e", width=3),
            marker=dict(size=8),
            hovertemplate="Year %{x}<br>₱%{y:,.2f}<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template="plotly_dark",
        height=560,
        margin=dict(l=20, r=20, t=110, b=20),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(text=f"{selected_region}: Kamote price vs net income", x=0.02),
    )
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text=left_title, secondary_y=False)
    fig.update_yaxes(title_text="Net National Income (PHP)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def render_correlation_scatter(correlation_df: pd.DataFrame) -> None:
    st.subheader("Income vs Poverty")
    st.caption("The regression line highlights the downward relationship between income and poverty incidence.")

    scatter_df = correlation_df.dropna(subset=["net_income_per_capita", "poverty_rate_pct"]).copy()
    scatter_df = scatter_df[scatter_df["report_year"] >= 2006]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=scatter_df["net_income_per_capita"],
            y=scatter_df["poverty_rate_pct"],
            mode="markers",
            name="Yearly observations",
            marker=dict(
                size=12,
                color=scatter_df["report_year"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Year"),
                line=dict(width=0.6, color="rgba(255,255,255,0.35)"),
            ),
            text=scatter_df["report_year"],
            hovertemplate="Year %{text}<br>Income ₱%{x:,.2f}<br>Poverty %{y:.2f}%<extra></extra>",
        )
    )

    if len(scatter_df) >= 2:
        x_values = scatter_df["net_income_per_capita"].astype(float).to_numpy()
        y_values = scatter_df["poverty_rate_pct"].astype(float).to_numpy()
        slope, intercept = np.polyfit(x_values, y_values, 1)
        x_line = np.linspace(x_values.min(), x_values.max(), 100)
        y_line = slope * x_line + intercept

        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="Regression line",
                line=dict(color="#f97316", width=3, dash="dash"),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=20, r=20, t=80, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(text="Net income vs poverty incidence", x=0.02),
        xaxis_title="Net National Income (PHP)",
        yaxis_title="Poverty Incidence (%)",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_raw_preview(yearly_df: pd.DataFrame, correlation_df: pd.DataFrame) -> None:
    st.subheader("Raw Data Preview")
    tabs = st.tabs(["Master table", "Correlation table"])

    with tabs[0]:
        st.dataframe(
            yearly_df[
                [
                    "report_year",
                    "kamote_price",
                    "affordability_index",
                    "net_income_per_capita",
                    "poverty_rate_pct",
                    "slum_pop_pct",
                ]
            ],
            use_container_width=True,
        )

    with tabs[1]:
        st.dataframe(correlation_df, use_container_width=True)


def render_footer() -> None:
    github_url = "https://github.com/eduardodfran/ph-economic-pulse-tracker"
    lineage_graph = (BASE_DIR / "ph_pulse_dbt" / "target" / "index.html").as_uri()
    st.markdown(
        f"""
        <div class="footer">
            <strong>Links:</strong>
            <a href="{github_url}" target="_blank">GitHub</a>
            &nbsp;|&nbsp;
            <a href="{lineage_graph}" target="_blank">dbt Lineage Graph</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    render_hero()

    master_df = get_master_data()
    correlation_df = get_correlation_data()

    selected_region, metric_choice = render_sidebar(master_df)
    regional_df = master_df[master_df["region"] == selected_region].copy()
    yearly_df = build_yearly_view(regional_df, selected_region)

    if yearly_df.empty:
        st.warning("No kamote data found for this region in the selected time window.")
        st.stop()

    render_metrics(yearly_df)
    render_dual_axis_chart(yearly_df, selected_region, metric_choice)

    bottom_left, bottom_right = st.columns([1.25, 1])
    with bottom_left:
        render_correlation_scatter(correlation_df)
    with bottom_right:
        render_raw_preview(yearly_df, correlation_df)

    render_footer()


if __name__ == "__main__":
    main()