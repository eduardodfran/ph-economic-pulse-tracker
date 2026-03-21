import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery
from plotly.subplots import make_subplots


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/google_credentials.json"

client = bigquery.Client()


st.set_page_config(page_title="PhilsPulse: Economic Tracker", layout="wide")


@st.cache_data
def get_data() -> pd.DataFrame:
    query = """
        SELECT *
        FROM `zoomcamp-data-engineer-484608.ph_economy_staging.fct_economy_pulse`
        ORDER BY report_month ASC
    """
    return client.query(query).to_dataframe()


def render_header() -> None:
    st.title("🇵🇭 PhilsPulse: Food Price Inflation Tracker")
    st.markdown("Monitoring the 'heartbeat' of the Philippine economy using WFP data.")


def render_sidebar(df: pd.DataFrame) -> tuple[str, str]:
    st.sidebar.header("Filter Options")
    region = st.sidebar.selectbox("Select Region", options=sorted(df["region"].unique()))
    item = st.sidebar.selectbox("Select Commodity", options=sorted(df["item_name"].unique()))
    return region, item


def filter_data(df: pd.DataFrame, region: str, item: str) -> pd.DataFrame:
    return df[(df["region"] == region) & (df["item_name"] == item)].sort_values("report_month")


def render_summary(filtered_df: pd.DataFrame, item: str) -> None:
    col1, col2 = st.columns(2)

    with col1:
        if not filtered_df.empty:
            latest = filtered_df.iloc[-1]
            st.metric(
                label=f"Current Price ({item})",
                value=f"₱{latest['avg_price_php']:.2f}",
                delta=f"{latest['mom_inflation_rate'] * 100:.2f}% (MoM)",
            )
        else:
            st.warning("No data found for this selection.")

    with col2:
        st.info(
            "💡 **Pulse Check:** Positive green deltas in Streamlit usually mean prices went up (Inflation), while red means they went down."
        )


def render_price_trend(filtered_df: pd.DataFrame, region: str, item: str) -> None:
    st.subheader(f"Price Trend: {item} in {region}")
    fig = px.line(
        filtered_df,
        x="report_month",
        y="avg_price_php",
        labels={"avg_price_php": "Price (PHP)", "report_month": "Month"},
        template="plotly_dark",
        line_shape="spline",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_raw_data(filtered_df: pd.DataFrame) -> None:
    with st.expander("View Raw Data Mart"):
        st.dataframe(filtered_df)


def render_correlation_chart(filtered_df: pd.DataFrame, region: str, item: str) -> None:
    st.subheader(f"📈 Price vs. Poverty Correlation: {item}")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=filtered_df["report_month"], y=filtered_df["avg_price_php"], name="Price (PHP)"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=filtered_df["report_month"],
            y=filtered_df["poverty_rate_pct"],
            name="Poverty Rate (%)",
            line=dict(dash="dash", color="red"),
        ),
        secondary_y=True,
    )

    fig.update_layout(title_text=f"The Economic Pulse of {region}", template="plotly_dark")
    fig.update_yaxes(title_text="<b>Price</b> (PHP)", secondary_y=False)
    fig.update_yaxes(title_text="<b>Poverty Rate</b> (%)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    render_header()

    df = get_data()
    region, item = render_sidebar(df)
    filtered_df = filter_data(df, region, item)

    render_summary(filtered_df, item)
    render_price_trend(filtered_df, region, item)
    render_raw_data(filtered_df)
    render_correlation_chart(filtered_df, region, item)


if __name__ == "__main__":
    main()