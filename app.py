from __future__ import annotations

from io import BytesIO
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_data, add_time_granularities, aggregate_by_period


st.set_page_config(page_title="APR Cycling Club - Performance Dashboard", layout="wide")


def apply_bw_theme() -> None:
    """Inject a simple black-and-white theme for the app and tables."""
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #ffffff !important;
            color: #000000 !important;
        }
        /* Reserve space for fixed footer only */
        body { padding-bottom: 56px; }
        h1, h2, h3, h4, h5, h6 { color: #000000 !important; }
        /* Dataframe container overrides */
        [data-testid="stDataFrame"] * { color: #000000 !important; }
        [data-testid="stDataFrame"] .blank { background-color: #ffffff !important; }
        /* Metric labels */
        [data-testid="stMetricLabel"] { color: #000000 !important; }
        /* Keep default Streamlit delta colors (green/red) */
        /* Bigger, bold tab labels */
        [data-testid="stTabs"] button p {
            font-weight: 700 !important;
            font-size: 1.08rem !important;
        }
        /* Center the tab list (header not fixed) */
        [data-testid="stTabs"] > div[role="tablist"] { justify-content: center !important; }
        /* Fixed footer */
        #site-footer { position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; border-top: 1px solid #e5e5e5; padding: 8px 0; z-index: 1000; text-align: center; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_df(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    return (
        df.style.set_properties(**{"color": "black", "background-color": "white"})
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "white"), ("color", "black")]},
            {"selector": "td", "props": [("background-color", "white"), ("color", "black")]},
        ])
    )


def sidebar_inputs() -> dict:
    st.sidebar.header("Data Source")
    uploaded = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

    st.sidebar.divider()
    st.sidebar.header("Column Mapping (optional)")
    st.sidebar.caption("Map your columns to canonical names only if needed.")

    def mapping_input(label):
        return st.sidebar.text_input(label, value="", placeholder="leave empty if auto")

    col_map: Dict[str, str] = {}
    col_map["timestamp"] = mapping_input("timestamp → your column")
    col_map["rider_name"] = mapping_input("rider_name → your column")
    col_map["team_name"] = mapping_input("team_name → your column")
    col_map["distance_km"] = mapping_input("distance_km → your column")
    col_map["duration_sec"] = mapping_input("duration_sec → your column")
    col_map["power_watts"] = mapping_input("power_watts → your column")
    col_map["heart_rate_bpm"] = mapping_input("heart_rate_bpm → your column")
    col_map["elevation_gain_m"] = mapping_input("elevation_gain_m → your column")

    col_map = {k: v for k, v in col_map.items() if v.strip()}

    st.sidebar.divider()
    st.sidebar.header("Grouping & Metric")
    period = st.sidebar.selectbox(
        "Time Resolution",
        ["hour", "day", "week", "month", "quarter", "year"],
        index=3,
    )
    group_by = st.sidebar.multiselect(
        "Group by",
        options=["rider_name", "team_name"],
        default=["rider_name"],
    )
    metric = st.sidebar.selectbox(
        "Metric",
        options=["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m", "speed_kmh"],
        index=0,
    )
    agg_func = st.sidebar.selectbox("Aggregation", options=["sum", "mean", "max", "min"], index=0)

    st.sidebar.divider()
    st.sidebar.header("Filters")
    rider_filter = st.sidebar.text_input("Filter by Rider (contains)", "")
    team_filter = st.sidebar.text_input("Filter by Team (contains)", "")

    return {
        "uploaded": uploaded,
        "col_map": col_map,
        "period": period,
        "group_by": group_by,
        "metric": metric,
        "agg_func": agg_func,
        "rider_filter": rider_filter.strip(),
        "team_filter": team_filter.strip(),
    }


@st.cache_data(show_spinner=False)
def load_sample() -> pd.DataFrame:
    return load_data("data/sample_cycling.csv")


def get_dataframe(inputs: dict) -> pd.DataFrame:
    if inputs["uploaded"] is not None:
        data_bytes = inputs["uploaded"].read()
        try:
            return load_data(
                data_bytes,
                uploaded_mime=inputs["uploaded"].type,
                user_mapping=inputs["col_map"],
            )
        except Exception:
            detected = inputs["uploaded"].type or "unknown"
            st.error(
                f"Bad file format (detected: {detected}). Please upload CSV (.csv) or Excel (.xlsx, .xls)."
            )
            return load_sample()
    else:
        return load_sample()


def apply_filters(df: pd.DataFrame, rider_contains: str, team_contains: str) -> pd.DataFrame:
    view = df.copy()
    if rider_contains:
        view = view[view["rider_name"].str.contains(rider_contains, case=False, na=False)]
    if team_contains:
        view = view[view["team_name"].str.contains(team_contains, case=False, na=False)]
    return view


def main() -> None:
    apply_bw_theme()

    inputs = sidebar_inputs()

    df = get_dataframe(inputs)
    df = add_time_granularities(df)
    df = apply_filters(df, inputs["rider_filter"], inputs["team_filter"])

    # Pre-compute leaderboards
    # (Optional) Global precompute; tabs also compute locally for safety
    leaderboard_rider = aggregate_by_period(df, inputs["period"], ["rider_name"], inputs["metric"], inputs["agg_func"]) if "rider_name" in df.columns else pd.DataFrame()
    leaderboard_team = aggregate_by_period(df, inputs["period"], ["team_name"], inputs["metric"], inputs["agg_func"]) if "team_name" in df.columns else pd.DataFrame()

    # Top navigation tabs
    tab_home, tab_riders, tab_teams, tab_results, tab_about = st.tabs(["Home", "Riders", "Teams", "Results", "About"])

    with tab_home:
        st.title("APR Cycling Club - Performance Dashboard")
        st.caption("Analyze rider and team performance across multiple time resolutions.")
        # Date Range under caption (Home)
        min_date = pd.to_datetime(df["day"]).min()
        max_date = pd.to_datetime(df["day"]).max()
        with st.expander("Date Range", expanded=False):
            start_home, end_home = st.slider(
                "Select Date Range",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                key="date_range_home",
            )
        df_tab = df[(df["day"] >= pd.to_datetime(start_home)) & (df["day"] <= pd.to_datetime(end_home))]
        # Overview KPIs
        st.subheader("Overview KPIs")
        kpi_cols = st.columns(5)
        # Previous equal-length window
        window_len = pd.to_datetime(end_home) - pd.to_datetime(start_home)
        prev_end = pd.to_datetime(start_home) - pd.Timedelta(seconds=1)
        prev_start = prev_end - window_len
        df_prev = df[(df["day"] >= prev_start) & (df["day"] <= prev_end)]

        total_distance = df_tab["distance_km"].sum() if "distance_km" in df_tab else 0.0
        total_distance_prev = df_prev["distance_km"].sum() if "distance_km" in df_prev else 0.0
        total_duration_h = (df_tab["duration_sec"].sum() / 3600.0) if "duration_sec" in df_tab else 0.0
        total_duration_h_prev = (df_prev["duration_sec"].sum() / 3600.0) if "duration_sec" in df_prev else 0.0
        avg_power = df_tab["power_watts"].mean() if "power_watts" in df_tab else float("nan")
        avg_power_prev = df_prev["power_watts"].mean() if "power_watts" in df_prev else float("nan")
        avg_hr = df_tab["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_tab else float("nan")
        avg_hr_prev = df_prev["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_prev else float("nan")
        total_elev = df_tab["elevation_gain_m"].sum() if "elevation_gain_m" in df_tab else 0.0
        total_elev_prev = df_prev["elevation_gain_m"].sum() if "elevation_gain_m" in df_prev else 0.0

        kpi_cols[0].metric("Total Distance (km)", f"{total_distance:,.1f}", f"{(total_distance-total_distance_prev):+.1f}")
        kpi_cols[1].metric("Total Duration (h)", f"{total_duration_h:,.1f}", f"{(total_duration_h-total_duration_h_prev):+.1f}")
        power_delta = (avg_power - avg_power_prev) if pd.notna(avg_power) and pd.notna(avg_power_prev) else 0.0
        kpi_cols[2].metric("Avg Power (W)", f"{avg_power:,.0f}" if pd.notna(avg_power) else "—", f"{power_delta:+.0f}")
        hr_delta = (avg_hr - avg_hr_prev) if pd.notna(avg_hr) and pd.notna(avg_hr_prev) else 0.0
        kpi_cols[3].metric("Avg HR (bpm)", f"{avg_hr:,.0f}" if pd.notna(avg_hr) else "—", f"{hr_delta:+.0f}")
        kpi_cols[4].metric("Elev Gain (m)", f"{total_elev:,.0f}", f"{(total_elev-total_elev_prev):+,.0f}")
        st.subheader("Time Series")
        agg_ts = aggregate_by_period(df_tab, inputs["period"], [], inputs["metric"], inputs["agg_func"])
        fig = px.line(
            agg_ts,
            x=inputs["period"],
            y=inputs["metric"],
            markers=True,
            title=f"{inputs['metric']} by {inputs['period']}",
        )
        st.plotly_chart(fig, width='stretch')

        st.subheader("Distributions")
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            hist_fig = px.histogram(
                df_tab,
                x=inputs["metric"],
                nbins=30,
                title=f"Histogram of {inputs['metric']}",
            )
            st.plotly_chart(hist_fig, width='stretch')
        with dcol2:
            pie_group = st.selectbox("Pie by", options=["rider_name", "team_name"], index=1)
            pie_df = aggregate_by_period(df_tab, inputs["period"], [pie_group], inputs["metric"], inputs["agg_func"]).rename(columns={inputs["metric"]: "value"})
            pie_fig = px.pie(
                pie_df,
                values="value",
                names=pie_group,
                title=f"{inputs['metric']} by {pie_group}",
            )
            st.plotly_chart(pie_fig, width='stretch')

        st.subheader("Additional Charts")
        acol1, acol2 = st.columns(2)
        with acol1:
            bar_group = st.selectbox("Bar by", options=["rider_name", "team_name"], index=1, key="bar_group")
            bar_df = aggregate_by_period(df_tab, inputs["period"], [bar_group], inputs["metric"], inputs["agg_func"]).rename(columns={inputs["metric"]: "value"})
            bar_fig = px.bar(
                bar_df,
                x=bar_group,
                y="value",
                title=f"{inputs['metric']} by {bar_group}",
            )
            st.plotly_chart(bar_fig, width='stretch')
        with acol2:
            box_group = st.selectbox("Box group", options=["rider_name", "team_name"], index=0, key="box_group")
            box_fig = px.box(
                df_tab.dropna(subset=[inputs["metric"], box_group]),
                x=box_group,
                y=inputs["metric"],
                points="suspectedoutliers",
                title=f"Distribution of {inputs['metric']} by {box_group}",
            )
            st.plotly_chart(box_fig, width='stretch')

        st.subheader("Pivot by Group")
        if inputs["group_by"]:
            agg_grouped = aggregate_by_period(df_tab, inputs["period"], inputs["group_by"], inputs["metric"], inputs["agg_func"])
            st.dataframe(style_df(agg_grouped), width='stretch')

        with st.expander("Raw Data"):
            st.dataframe(style_df(df_tab), width='stretch')

    with tab_riders:
        st.title("APR Cycling Club - Performance Dashboard")
        st.caption("Analyze rider and team performance across multiple time resolutions.")
        # Date Range under caption (Riders)
        min_date = pd.to_datetime(df["day"]).min()
        max_date = pd.to_datetime(df["day"]).max()
        with st.expander("Date Range", expanded=False):
            start_r, end_r = st.slider(
                "Select Date Range",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                key="date_range_riders",
            )
        df_tab = df[(df["day"] >= pd.to_datetime(start_r)) & (df["day"] <= pd.to_datetime(end_r))]
        # Overview KPIs
        st.subheader("Overview KPIs")
        kpi_cols = st.columns(5)
        window_len = pd.to_datetime(end_r) - pd.to_datetime(start_r)
        prev_end = pd.to_datetime(start_r) - pd.Timedelta(seconds=1)
        prev_start = prev_end - window_len
        df_prev = df[(df["day"] >= prev_start) & (df["day"] <= prev_end)]

        total_distance = df_tab["distance_km"].sum() if "distance_km" in df_tab else 0.0
        total_distance_prev = df_prev["distance_km"].sum() if "distance_km" in df_prev else 0.0
        total_duration_h = (df_tab["duration_sec"].sum() / 3600.0) if "duration_sec" in df_tab else 0.0
        total_duration_h_prev = (df_prev["duration_sec"].sum() / 3600.0) if "duration_sec" in df_prev else 0.0
        avg_power = df_tab["power_watts"].mean() if "power_watts" in df_tab else float("nan")
        avg_power_prev = df_prev["power_watts"].mean() if "power_watts" in df_prev else float("nan")
        avg_hr = df_tab["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_tab else float("nan")
        avg_hr_prev = df_prev["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_prev else float("nan")
        total_elev = df_tab["elevation_gain_m"].sum() if "elevation_gain_m" in df_tab else 0.0
        total_elev_prev = df_prev["elevation_gain_m"].sum() if "elevation_gain_m" in df_prev else 0.0

        kpi_cols[0].metric("Total Distance (km)", f"{total_distance:,.1f}", f"{(total_distance-total_distance_prev):+.1f}")
        kpi_cols[1].metric("Total Duration (h)", f"{total_duration_h:,.1f}", f"{(total_duration_h-total_duration_h_prev):+.1f}")
        power_delta = (avg_power - avg_power_prev) if pd.notna(avg_power) and pd.notna(avg_power_prev) else 0.0
        kpi_cols[2].metric("Avg Power (W)", f"{avg_power:,.0f}" if pd.notna(avg_power) else "—", f"{power_delta:+.0f}")
        hr_delta = (avg_hr - avg_hr_prev) if pd.notna(avg_hr) and pd.notna(avg_hr_prev) else 0.0
        kpi_cols[3].metric("Avg HR (bpm)", f"{avg_hr:,.0f}" if pd.notna(avg_hr) else "—", f"{hr_delta:+.0f}")
        kpi_cols[4].metric("Elev Gain (m)", f"{total_elev:,.0f}", f"{(total_elev-total_elev_prev):+,.0f}")
        st.subheader("Rider Leaderboard")
        riders_lb = aggregate_by_period(df_tab, inputs["period"], ["rider_name"], inputs["metric"], inputs["agg_func"]) if "rider_name" in df.columns else pd.DataFrame()
        if not riders_lb.empty:
            latest_period = riders_lb[inputs["period"]].max()
            top_rider = riders_lb[riders_lb[inputs["period"]] == latest_period] \
                .sort_values(inputs["metric"], ascending=False).head(20)
            st.dataframe(style_df(top_rider.reset_index(drop=True)), width='stretch')
        else:
            st.info("No rider data available.")

        st.subheader("Rider Comparison")
        compare_by = "rider_name"
        available_entities = sorted(df_tab[compare_by].dropna().unique().tolist()) if compare_by in df.columns else []
        selected_entities = st.multiselect("Select rider(s)", options=available_entities, default=available_entities[:2], key="cmp_riders")
        cmp_metric = st.selectbox("Metric", options=["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m", "speed_kmh"], index=["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m", "speed_kmh"].index(inputs["metric"]), key="cmp_metric_r")
        cmp_period = st.selectbox("Time Resolution", options=["hour", "day", "week", "month", "quarter", "year"], index=["hour", "day", "week", "month", "quarter", "year"].index(inputs["period"]), key="cmp_period_r")
        cmp_agg = st.selectbox("Aggregation", options=["sum", "mean", "max", "min"], index=["sum", "mean", "max", "min"].index(inputs["agg_func"]), key="cmp_agg_r")
        cmp_df = aggregate_by_period(df_tab, cmp_period, [compare_by], cmp_metric, cmp_agg)
        if selected_entities:
            cmp_df = cmp_df[cmp_df[compare_by].isin(selected_entities)]
        cmp_fig = px.line(cmp_df, x=cmp_period, y=cmp_metric, color=compare_by, title=f"{cmp_metric} by {cmp_period} — Riders")
        st.plotly_chart(cmp_fig, width='stretch')

    with tab_teams:
        st.title("APR Cycling Club - Performance Dashboard")
        st.caption("Analyze rider and team performance across multiple time resolutions.")
        # Date Range under caption (Teams)
        min_date = pd.to_datetime(df["day"]).min()
        max_date = pd.to_datetime(df["day"]).max()
        with st.expander("Date Range", expanded=False):
            start_t, end_t = st.slider(
                "Select Date Range",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                key="date_range_teams",
            )
        df_tab = df[(df["day"] >= pd.to_datetime(start_t)) & (df["day"] <= pd.to_datetime(end_t))]
        # Overview KPIs
        st.subheader("Overview KPIs")
        kpi_cols = st.columns(5)
        window_len = pd.to_datetime(end_t) - pd.to_datetime(start_t)
        prev_end = pd.to_datetime(start_t) - pd.Timedelta(seconds=1)
        prev_start = prev_end - window_len
        df_prev = df[(df["day"] >= prev_start) & (df["day"] <= prev_end)]

        total_distance = df_tab["distance_km"].sum() if "distance_km" in df_tab else 0.0
        total_distance_prev = df_prev["distance_km"].sum() if "distance_km" in df_prev else 0.0
        total_duration_h = (df_tab["duration_sec"].sum() / 3600.0) if "duration_sec" in df_tab else 0.0
        total_duration_h_prev = (df_prev["duration_sec"].sum() / 3600.0) if "duration_sec" in df_prev else 0.0
        avg_power = df_tab["power_watts"].mean() if "power_watts" in df_tab else float("nan")
        avg_power_prev = df_prev["power_watts"].mean() if "power_watts" in df_prev else float("nan")
        avg_hr = df_tab["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_tab else float("nan")
        avg_hr_prev = df_prev["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_prev else float("nan")
        total_elev = df_tab["elevation_gain_m"].sum() if "elevation_gain_m" in df_tab else 0.0
        total_elev_prev = df_prev["elevation_gain_m"].sum() if "elevation_gain_m" in df_prev else 0.0

        kpi_cols[0].metric("Total Distance (km)", f"{total_distance:,.1f}", f"{(total_distance-total_distance_prev):+.1f}")
        kpi_cols[1].metric("Total Duration (h)", f"{total_duration_h:,.1f}", f"{(total_duration_h-total_duration_h_prev):+.1f}")
        power_delta = (avg_power - avg_power_prev) if pd.notna(avg_power) and pd.notna(avg_power_prev) else 0.0
        kpi_cols[2].metric("Avg Power (W)", f"{avg_power:,.0f}" if pd.notna(avg_power) else "—", f"{power_delta:+.0f}")
        hr_delta = (avg_hr - avg_hr_prev) if pd.notna(avg_hr) and pd.notna(avg_hr_prev) else 0.0
        kpi_cols[3].metric("Avg HR (bpm)", f"{avg_hr:,.0f}" if pd.notna(avg_hr) else "—", f"{hr_delta:+.0f}")
        kpi_cols[4].metric("Elev Gain (m)", f"{total_elev:,.0f}", f"{(total_elev-total_elev_prev):+,.0f}")
        st.subheader("Team Leaderboard")
        teams_lb = aggregate_by_period(df_tab, inputs["period"], ["team_name"], inputs["metric"], inputs["agg_func"]) if "team_name" in df.columns else pd.DataFrame()
        if not teams_lb.empty:
            latest_period_t = teams_lb[inputs["period"]].max()
            top_team = teams_lb[teams_lb[inputs["period"]] == latest_period_t] \
                .sort_values(inputs["metric"], ascending=False).head(20)
            st.dataframe(style_df(top_team.reset_index(drop=True)), width='stretch')
        else:
            st.info("No team data available.")

        st.subheader("Team Comparison")
        compare_by = "team_name"
        available_entities = sorted(df_tab[compare_by].dropna().unique().tolist()) if compare_by in df.columns else []
        selected_entities = st.multiselect("Select team(s)", options=available_entities, default=available_entities[:2], key="cmp_teams")
        cmp_metric = st.selectbox("Metric", options=["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m", "speed_kmh"], index=["distance_km", "duration_sec", "power_watts", "heart_rate_bpm", "elevation_gain_m", "speed_kmh"].index(inputs["metric"]), key="cmp_metric_t")
        cmp_period = st.selectbox("Time Resolution", options=["hour", "day", "week", "month", "quarter", "year"], index=["hour", "day", "week", "month", "quarter", "year"].index(inputs["period"]), key="cmp_period_t")
        cmp_agg = st.selectbox("Aggregation", options=["sum", "mean", "max", "min"], index=["sum", "mean", "max", "min"].index(inputs["agg_func"]), key="cmp_agg_t")
        cmp_df = aggregate_by_period(df_tab, cmp_period, [compare_by], cmp_metric, cmp_agg)
        if selected_entities:
            cmp_df = cmp_df[cmp_df[compare_by].isin(selected_entities)]
        cmp_fig = px.line(cmp_df, x=cmp_period, y=cmp_metric, color=compare_by, title=f"{cmp_metric} by {cmp_period} — Teams")
        st.plotly_chart(cmp_fig, width='stretch')

    with tab_results:
        st.title("APR Cycling Club - Performance Dashboard")
        st.caption("Analyze rider and team performance across multiple time resolutions.")
        # Date Range under caption (Results)
        min_date = pd.to_datetime(df["day"]).min()
        max_date = pd.to_datetime(df["day"]).max()
        with st.expander("Date Range", expanded=False):
            start_res, end_res = st.slider(
                "Select Date Range",
                min_value=min_date.to_pydatetime(),
                max_value=max_date.to_pydatetime(),
                value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
                key="date_range_results",
            )
        df_tab = df[(df["day"] >= pd.to_datetime(start_res)) & (df["day"] <= pd.to_datetime(end_res))]
        # Overview KPIs
        st.subheader("Overview KPIs")
        kpi_cols = st.columns(5)
        window_len = pd.to_datetime(end_res) - pd.to_datetime(start_res)
        prev_end = pd.to_datetime(start_res) - pd.Timedelta(seconds=1)
        prev_start = prev_end - window_len
        df_prev = df[(df["day"] >= prev_start) & (df["day"] <= prev_end)]

        total_distance = df_tab["distance_km"].sum() if "distance_km" in df_tab else 0.0
        total_distance_prev = df_prev["distance_km"].sum() if "distance_km" in df_prev else 0.0
        total_duration_h = (df_tab["duration_sec"].sum() / 3600.0) if "duration_sec" in df_tab else 0.0
        total_duration_h_prev = (df_prev["duration_sec"].sum() / 3600.0) if "duration_sec" in df_prev else 0.0
        avg_power = df_tab["power_watts"].mean() if "power_watts" in df_tab else float("nan")
        avg_power_prev = df_prev["power_watts"].mean() if "power_watts" in df_prev else float("nan")
        avg_hr = df_tab["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_tab else float("nan")
        avg_hr_prev = df_prev["heart_rate_bpm"].mean() if "heart_rate_bpm" in df_prev else float("nan")
        total_elev = df_tab["elevation_gain_m"].sum() if "elevation_gain_m" in df_tab else 0.0
        total_elev_prev = df_prev["elevation_gain_m"].sum() if "elevation_gain_m" in df_prev else 0.0

        kpi_cols[0].metric("Total Distance (km)", f"{total_distance:,.1f}", f"{(total_distance-total_distance_prev):+.1f}")
        kpi_cols[1].metric("Total Duration (h)", f"{total_duration_h:,.1f}", f"{(total_duration_h-total_duration_h_prev):+.1f}")
        power_delta = (avg_power - avg_power_prev) if pd.notna(avg_power) and pd.notna(avg_power_prev) else 0.0
        kpi_cols[2].metric("Avg Power (W)", f"{avg_power:,.0f}" if pd.notna(avg_power) else "—", f"{power_delta:+.0f}")
        hr_delta = (avg_hr - avg_hr_prev) if pd.notna(avg_hr) and pd.notna(avg_hr_prev) else 0.0
        kpi_cols[3].metric("Avg HR (bpm)", f"{avg_hr:,.0f}" if pd.notna(avg_hr) else "—", f"{hr_delta:+.0f}")
        kpi_cols[4].metric("Elev Gain (m)", f"{total_elev:,.0f}", f"{(total_elev-total_elev_prev):+,.0f}")
        st.subheader("Highlights")
        c1, c2 = st.columns(2)
        riders_lb = aggregate_by_period(df_tab, inputs["period"], ["rider_name"], inputs["metric"], inputs["agg_func"]) if "rider_name" in df.columns else pd.DataFrame()
        if not riders_lb.empty:
            latest_period = riders_lb[inputs["period"]].max()
            top_rider = riders_lb[riders_lb[inputs["period"]] == latest_period] \
                .sort_values(inputs["metric"], ascending=False).head(10)
            c1.write("Top Riders (latest period)")
            c1.dataframe(style_df(top_rider.reset_index(drop=True)), width='stretch')
        teams_lb = aggregate_by_period(df_tab, inputs["period"], ["team_name"], inputs["metric"], inputs["agg_func"]) if "team_name" in df.columns else pd.DataFrame()
        if not teams_lb.empty:
            latest_period_t = teams_lb[inputs["period"]].max()
            top_team = teams_lb[teams_lb[inputs["period"]] == latest_period_t] \
                .sort_values(inputs["metric"], ascending=False).head(10)
            c2.write("Top Teams (latest period)")
            c2.dataframe(style_df(top_team.reset_index(drop=True)), width='stretch')

    with tab_about:
        st.title("APR Cycling Club - Performance Dashboard")
        st.caption("Analyze rider and team performance across multiple time resolutions.")
        st.subheader("About APR Cycling Club")
        st.write("APR Cycling Club is dedicated to performance, teamwork, and community. This dashboard showcases training and race insights across riders and teams. ")
        st.write("For inquiries, please contact the APR Cycling Club committee.")

    # Footer
    st.markdown(
        """
        <div id=\"site-footer\" style=\"color:#000;\">
            © {year} APR Cycling Club • Performance Dashboard
        </div>
        """.format(year=pd.Timestamp.today().year),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
