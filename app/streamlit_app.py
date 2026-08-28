import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

from ingestion.demo_data import generate_demo_argo_data
from ingestion.netcdf_ingest import parse_netcdf_file
from app.visualization import (
    render_global_map,
    render_profile_chart,
    render_multi_profile_chart,
    render_trajectory_map,
    render_depth_time_plot,
    render_3d_float_map,
    render_trajectory_network,
)
from app.query_engine import QueryEngine
from rag.pipeline import RAGPipeline
from rag.vector_store import LocalVectorStore
from database.runtime import load_postgres_tables
from ingestion.erddap import fetch_erddap_csv


st.set_page_config(
    page_title="FloatChat | AI Ocean Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #020C1B 0%, #07182d 100%);
        color: #E2E8F0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: none !important;
        width: 100% !important;
        animation: page-enter 420ms ease-out both;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: none !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        width: 250px !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 1.1rem 0.9rem 1rem 0.9rem;
        background: linear-gradient(180deg, rgba(3, 14, 29, 0.98), rgba(5, 25, 42, 0.98)) !important;
        border-right: 1px solid rgba(126, 249, 255, 0.2);
    }
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin: 0.25rem 0 0.2rem 0;
    }
    .brand-mark {
        display: grid;
        place-items: center;
        width: 3rem;
        height: 3rem;
        border: 1px solid rgba(126, 249, 255, 0.65);
        border-radius: 14px;
        background: linear-gradient(145deg, rgba(0, 242, 254, 0.24), rgba(6, 65, 92, 0.7));
        color: #7EF9FF;
        font-size: 1.75rem;
        box-shadow: 0 8px 22px rgba(0, 242, 254, 0.13);
    }
    .brand-name {
        color: #F8FAFC;
        font-size: 1.45rem;
        font-weight: 850;
        line-height: 1;
        letter-spacing: 0.06em;
    }
    .brand-subtitle {
        margin-top: 0.3rem;
        color: #86A6BB;
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        letter-spacing: 0.08em;
        font-size: 1.1rem;
        margin-bottom: 0.15rem;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
        color: #7EF9FF;
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin: 0.65rem 0 0.35rem 0;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: 0.28rem;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 0.42rem 0.5rem;
        transition: background 180ms ease, border-color 180ms ease, transform 180ms ease;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: rgba(126, 249, 255, 0.08);
        border-color: rgba(126, 249, 255, 0.2);
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.18), rgba(0, 242, 254, 0.04));
        border-color: rgba(126, 249, 255, 0.48);
        box-shadow: inset 3px 0 0 #7EF9FF;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(126, 249, 255, 0.16);
        margin: 0.8rem 0;
    }
    .sidebar-status {
        padding: 0.7rem 0.75rem;
        border: 1px solid rgba(126, 249, 255, 0.16);
        border-radius: 12px;
        background: rgba(126, 249, 255, 0.05);
        color: #B7C7D9;
        font-size: 0.75rem;
        line-height: 1.55;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #7EF9FF !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.72rem !important; }
    .glass-card {
        background: rgba(8, 24, 39, 0.86);
        border: 1px solid rgba(126, 249, 255, 0.18);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow: 0 12px 30px rgba(2, 12, 27, 0.45);
    }
    .hero-panel {
        background: linear-gradient(135deg, rgba(9, 22, 38, 0.9), rgba(13, 38, 62, 0.75));
        border: 1px solid rgba(126, 249, 255, 0.24);
        border-radius: 22px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.25rem;
        animation: hero-enter 500ms 80ms ease-out both;
    }
    .hero-panel h1 { margin: 0 0 0.35rem 0; font-size: 2.2rem; color: #F8FAFC; }
    .hero-panel p { margin: 0; color: #B7C7D9; }
    .status-badge, .demo-badge, .chip {
        display: inline-block; padding: 6px 12px; border-radius: 999px; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.8rem;
    }
    .status-badge { background: rgba(0, 242, 254, 0.12); border: 1px solid rgba(0, 242, 254, 0.7); color: #7EF9FF; }
    .demo-badge { background: rgba(255, 170, 0, 0.12); border: 1px solid rgba(255, 170, 0, 0.7); color: #FFB84D; }
    .chip { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.7); color: #86EFAC; }
    .stSidebar { background: rgba(2, 12, 27, 0.96) !important; }
    .stButton > button { border-radius: 12px; background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(126, 249, 255, 0.3); color: #E0F7FF; transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease; }
    .stButton > button:hover { transform: translateY(-1px); border-color: rgba(126, 249, 255, 0.72); box-shadow: 0 8px 18px rgba(0, 242, 254, 0.12); }
    .chat-shell { background: rgba(7, 24, 38, 0.82); border: 1px solid rgba(126, 249, 255, 0.18); border-radius: 20px; padding: 1rem; }
    .chat-bubble { padding: 0.85rem 1rem; border-radius: 16px; margin: 0.5rem 0; border: 1px solid rgba(148, 163, 184, 0.18); background: rgba(15, 23, 42, 0.9); color: #E2E8F0; }
    .chat-bubble.user { background: linear-gradient(135deg, rgba(14, 116, 144, 0.35), rgba(30, 64, 175, 0.30)); }
    .chat-bubble.assistant { background: linear-gradient(135deg, rgba(4, 120, 87, 0.20), rgba(6, 182, 212, 0.14)); }
    [data-testid="stPlotlyChart"] { width: 100%; overflow: hidden; }
    [data-testid="stDataFrame"] { width: 100%; overflow-x: auto; }
    @keyframes page-enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes hero-enter { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 900px) {
        .block-container { padding: 1.25rem 1rem 2rem 1rem; }
        .hero-panel { padding: 1rem; border-radius: 16px; }
        .hero-panel h1 { font-size: 1.75rem; }
        .status-badge, .demo-badge, .chip { font-size: 0.66rem; padding: 5px 8px; }
        [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
        .chat-shell { padding: 0.75rem; border-radius: 14px; }
    }
    @media (max-width: 600px) {
        .block-container { padding: 0.75rem 0.65rem 1.5rem 0.65rem; }
        .hero-panel h1 { font-size: 1.45rem; }
        .hero-panel p { font-size: 0.88rem; }
        [data-testid="stMetricLabel"] { font-size: 0.62rem !important; letter-spacing: 0.04em; }
        [data-testid="stMetricValue"] { font-size: 1.15rem !important; }
    }
    @media (prefers-reduced-motion: reduce) {
        .block-container, .hero-panel { animation: none; }
        .stButton > button,
        section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label { transition: none; }
    }
</style>
"""


def render_page_header(title: str, subtitle: str, badge: str = "DEMO DATA MODE"):
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="status-badge">● LIVE OCEAN SYSTEM</div>
            <div class="chip">{badge}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_initial_data():
    return generate_demo_argo_data(num_floats=80, profiles_per_float=3)


@st.cache_data(show_spinner=False)
def load_runtime_data(data_mode: str):
    if data_mode.lower() == "postgres":
        return load_postgres_tables(), "REAL ARGO / POSTGRESQL"
    if data_mode.lower() in {"erddap", "remote"}:
        url = os.getenv("ERDDAP_URL")
        if not url:
            raise RuntimeError("ERDDAP_URL is required when DATA_MODE=erddap")
        return fetch_erddap_csv(url)[0], "REAL ARGO / ERDDAP"
    return load_initial_data(), "DEMO / SYNTHETIC"


@st.cache_data(show_spinner=False)
def build_summary(floats_df: pd.DataFrame, profiles_df: pd.DataFrame, meas_df: pd.DataFrame):
    active = int((floats_df["status"] == "ACTIVE").sum())
    return {
        "active": active,
        "inactive": len(floats_df) - active,
        "profiles": len(profiles_df),
        "measurements": len(meas_df),
        "regions": int(floats_df["region"].nunique()),
        "latest_profile": profiles_df["timestamp"].max(),
    }


def render_alerts(floats_df: pd.DataFrame, meas_df: pd.DataFrame):
    low_oxygen = int((meas_df["oxygen"] < 60).sum())
    stale_floats = int((floats_df["status"] == "INACTIVE").sum())
    alert_col, note_col = st.columns([1, 2])
    with alert_col:
        st.markdown("#### Network alerts")
        st.metric("Low oxygen observations", f"{low_oxygen:,}", delta="OMZ watch", delta_color="inverse")
    with note_col:
        st.markdown("#### Operational note")
        st.info(
            f"{stale_floats} floats are currently marked inactive. Review their last observation before using them for a live operational decision.",
            icon="⚠️",
        )


def render_region_table(floats_df: pd.DataFrame):
    region_table = (
        floats_df.groupby("region", as_index=False)
        .agg(Floats=("float_id", "count"), Active=("status", lambda values: int((values == "ACTIVE").sum())),
             MeanDepth=("max_depth", "mean"))
        .sort_values("Floats", ascending=False)
    )
    region_table["Active %"] = (region_table["Active"] / region_table["Floats"] * 100).round(0).astype(int)
    region_table["MeanDepth"] = region_table["MeanDepth"].round(0).astype(int)
    st.dataframe(
        region_table.rename(columns={"MeanDepth": "Mean max depth (m)"}),
        hide_index=True,
        width="stretch",
        column_config={"Active %": st.column_config.ProgressColumn("Active %", min_value=0, max_value=100, format="%d%%")},
    )


def render_chat_page(engine: QueryEngine, floats_df: pd.DataFrame, meas_df: pd.DataFrame, rag: RAGPipeline):
    render_page_header(
        "AI Ocean Intelligence Chat",
        "Ask questions in plain English or build a precise ARGO search step by step.",
        "QUERY ENGINE",
    )
    natural_tab, builder_tab, guide_tab = st.tabs(["Ask naturally", "Guided query builder", "How answers work"])

    with natural_tab:
        st.caption("Examples: nearest active floats to 15, 72 | salinity profiles in the Arabian Sea | oxygen deeper than 500m")
        st.session_state.setdefault("chat_history", [])
        st.session_state.setdefault("saved_queries", [])
        with st.form("natural_query_form", clear_on_submit=False):
            query_input = st.text_input(
                "Your ocean question",
                placeholder="e.g. Show temperature profiles near the equator",
                key="natural_query",
            )
            submitted = st.form_submit_button("Analyze question", type="primary")
        if submitted and query_input.strip():
            st.session_state.chat_history.append(query_input.strip())
        save_col, saved_col = st.columns([1, 2])
        with save_col:
            if st.button("Save current query", disabled=not query_input.strip()):
                if query_input.strip() not in st.session_state.saved_queries:
                    st.session_state.saved_queries.append(query_input.strip())
                    st.success("Query saved")
        with saved_col:
            if st.session_state.saved_queries:
                saved_query = st.selectbox("Saved queries", st.session_state.saved_queries, label_visibility="collapsed")
                st.caption(f"Saved workspace queries: {len(st.session_state.saved_queries)}")
        if st.session_state.chat_history:
            st.caption(f"Conversation history: {len(st.session_state.chat_history)} question(s)")
            for previous_query in st.session_state.chat_history[-3:]:
                st.markdown(f"- `{previous_query}`")
            if st.button("Clear chat history"):
                st.session_state.chat_history = []
                st.rerun()
        if submitted and query_input.strip():
            plan = engine.parse_query_plan(query_input)
            previous_context = st.session_state.chat_history[-2] if len(st.session_state.chat_history) > 1 else None
            st.markdown(f"**Interpreted as:** `{plan['intent']}` | `{plan['parameter']}` | `{plan['visualization']}`")
            if previous_context:
                st.caption(f"Context available from your previous question: {previous_context}")
            context = rag.retrieve_context(query_input)
            with st.expander("Retrieved ocean and schema context"):
                for item in context:
                    st.markdown(f"- **{item['id']}** ({item['score']:.2f}): {item['text']}")
            render_query_results(engine, plan, meas_df)

    with builder_tab:
        st.markdown("#### Build a query without knowing the vocabulary")
        b1, b2 = st.columns(2)
        intent = b1.selectbox("What do you want to find?", ["Compare profiles", "Find nearest floats", "Search observations"])
        parameter = b2.selectbox("Ocean variable", ["temperature", "salinity", "oxygen", "chlorophyll"])
        b3, b4 = st.columns(2)
        region = b3.selectbox("Region", ["All regions"] + sorted(floats_df["region"].unique().tolist()))
        status = b4.selectbox("Fleet status", ["Any status", "ACTIVE", "INACTIVE"])
        min_depth = st.slider("Minimum depth (metres)", 0, 2000, 0, step=50)

        if intent == "Find nearest floats":
            target_lat = st.number_input("Target latitude", min_value=-90.0, max_value=90.0, value=15.0, step=0.5)
            target_lon = st.number_input("Target longitude", min_value=-180.0, max_value=180.0, value=75.0, step=0.5)
            built_query = f"nearest active floats to {target_lat}, {target_lon}"
        else:
            region_text = "" if region == "All regions" else f" in the {region}"
            depth_text = "" if min_depth == 0 else f" deeper than {min_depth}m"
            built_query = f"Show {parameter} profiles{region_text}{depth_text}"
            if status != "Any status":
                built_query += f" {status.lower()}"

        st.code(built_query, language="text")
        if st.button("Run guided search", type="primary"):
            render_query_results(engine, engine.parse_query_plan(built_query), meas_df)

    with guide_tab:
        st.markdown("#### What the assistant does")
        st.markdown("1. Reads your question and identifies the variable, location, depth, and fleet status.\n2. Converts those choices into a structured, inspectable query plan.\n3. Filters the current ARGO catalog and chooses a map or depth profile.\n4. Shows the matching observations so you can verify the result.")
        st.info("When an OpenAI key is configured, the planner can use the language model. Without one, FloatChat uses its deterministic offline planner.", icon="ℹ️")


def render_query_results(engine: QueryEngine, plan: dict, meas_df: pd.DataFrame):
    filt_floats, filt_meas = engine.execute_plan(plan)
    st.json(plan, expanded=False)
    result_col, table_col = st.columns([1.3, 1])
    with result_col:
        if plan.get("visualization") == "depth_profile":
            if filt_meas.empty:
                st.warning("No measurements matched. Try a broader region or a shallower depth.")
            else:
                st.plotly_chart(render_profile_chart(filt_meas, plan.get("parameter", "temperature")), width="stretch")
        elif plan.get("visualization") == "comparison":
            if filt_meas.empty:
                st.warning("No observations matched the comparison request.")
            else:
                st.plotly_chart(render_multi_profile_chart(filt_meas, plan.get("parameter", "temperature")), width="stretch")
        elif plan.get("visualization") == "depth_time":
            if filt_meas.empty:
                st.warning("No observations matched the depth-time request.")
            else:
                st.plotly_chart(render_depth_time_plot(filt_meas, plan.get("parameter", "temperature")), width="stretch")
        elif filt_floats.empty:
            st.warning("No floats matched. Try a broader location or another status.")
        else:
            st.plotly_chart(render_global_map(filt_floats), width="stretch", config={"displayModeBar": False})
    with table_col:
        st.metric("Matching floats", len(filt_floats))
        st.metric("Matching observations", len(filt_meas))
        columns = ["float_id", "timestamp", "depth", "temperature", "salinity", "oxygen"]
        st.dataframe(filt_meas[columns].head(15), hide_index=True, width="stretch")
        st.download_button(
            "Download result CSV",
            data=filt_meas.to_csv(index=False).encode("utf-8"),
            file_name="floatchat_query_results.csv",
            mime="text/csv",
        )


def render_beginner_page():
    render_page_header(
        "FloatChat Field Guide",
        "A simple starting point for exploring ocean observations and understanding the dashboard.",
        "START HERE",
    )
    st.subheader("What is ARGO?")
    st.write("ARGO is a global network of robotic floats. A float drifts with the ocean, dives through the water column, and returns measurements such as temperature, salinity, oxygen, and chlorophyll.")
    st.info("Think of each float as a mobile underwater weather station. It samples the ocean at different depths and reports where and when each measurement was made.", icon="🌊")
    st.subheader("Read the dashboard in three steps")
    step1, step2, step3 = st.columns(3)
    step1.markdown("**1. Check the fleet**\nUse the Command Center to see how many floats are active and where they are located.")
    step2.markdown("**2. Ask a question**\nUse AI Ocean Chat to search by variable, region, depth, or coordinates.")
    step3.markdown("**3. Verify the result**\nUse the map, profile curve, and observation table together. The table is the evidence behind the chart.")
    st.subheader("A quick tour of every section")
    with st.expander("Ocean Command Center"):
        st.markdown("This is the overview screen. **Active floats** are currently available in the catalog, **profiles** are individual float sampling events, and **observations** are measurements taken at particular depths. The readiness bar shows the active share of the fleet. Regional coverage helps you see where the catalog is concentrated.")
    with st.expander("AI Ocean Chat"):
        st.markdown("Use **Ask naturally** when you know what you want to ask. Use **Guided query builder** when you prefer controls. A query can include a variable, region, depth threshold, status, or coordinates. The structured plan and result table let you check exactly what the assistant understood.")
        st.code("Find active floats near 15, 75\nShow oxygen profiles deeper than 500m\nCompare salinity profiles in the Arabian Sea", language="text")
    with st.expander("Live ARGO Map"):
        st.markdown("Filter the fleet by region, status, and maximum depth capability. A high minimum-depth setting shows only floats able to sample deeper water. If no markers remain, broaden one of the filters.")
    with st.expander("Float Explorer"):
        st.markdown("Choose one float to inspect its identity, location, depth capability, temperature and oxygen profiles, salinity profile, and historical drift trajectory. This is the best place to move from a network-level question to one instrument.")
    with st.expander("Ocean Profile Lab"):
        st.markdown("Select a variable and optionally choose regions to compare. The horizontal axis is the measured value; the vertical axis is depth, increasing downward. Curves that move sharply indicate a strong change through the water column.")
    with st.expander("Data Explorer and System / Data Sources"):
        st.markdown("Data Explorer provides a sortable observation table and filtered CSV export. System / Data Sources explains the NetCDF upload path, parser warnings, data-quality ranges, and the database integrations planned for production.")
    with st.expander("What does each variable mean?"):
        st.markdown("- **Temperature:** How warm or cold the water is, in degrees Celsius.\n- **Salinity:** The amount of dissolved salt, reported in PSU.\n- **Oxygen:** Dissolved oxygen, useful for finding low-oxygen zones.\n- **Chlorophyll:** A proxy for phytoplankton activity, often concentrated near the surface.")
    with st.expander("How do I interpret the alerts?"):
        st.markdown("Low-oxygen observations are a signal to inspect possible Oxygen Minimum Zones, not automatically a problem or a forecast. Inactive floats should be treated cautiously because their last recorded observation may be old. Always check the timestamp and the underlying observations before drawing a scientific conclusion.")
    with st.expander("What do the charts show?"):
        st.markdown("Maps show float positions. Depth profiles show how a variable changes from the surface downward; depth increases downward on purpose. Trajectories show how one float's sampling position changes over time.")
    with st.expander("Useful ocean terms"):
        st.markdown("- **Profile:** One vertical sampling event from the surface toward depth.\n- **Pressure:** A depth-related measurement often used by ocean instruments.\n- **BGC:** Biogeochemical variables such as oxygen and chlorophyll.\n- **OMZ:** Oxygen Minimum Zone, a depth range where dissolved oxygen is relatively low.\n- **DCM:** Deep Chlorophyll Maximum, where chlorophyll concentration can peak below the surface.")
    with st.expander("How trustworthy is an answer?"):
        st.markdown("FloatChat is a discovery and exploration tool. Treat the chart as a summary of the selected catalog, not as a substitute for quality-controlled scientific analysis. Check the query plan, timestamps, number of observations, missing values, and the source status before sharing a result.")
    with st.expander("What is live and what is demo data?"):
        st.markdown("This workspace currently runs on reproducible synthetic ARGO-like data. NetCDF upload is functional. PostgreSQL/PostGIS, RAG, and MCP integrations are prepared as extension points but are not connected to a live production service yet.")


def render_team_page():
    render_page_header(
        "Team HEXAHACK",
        "A collaborative team turning ocean observations into decisions people can understand.",
        "OUR TEAM",
    )
    st.subheader("Meet the team")
    st.write("FloatChat is presented by **HEXAHACK**, a six-member team combining science, software, AI, and product thinking.")
    members = [
        "Muvazulla Shaik",
        "Sanjitha Rokkam",
        "Pallavi",
        "Jai Vardhan",
        "Subramayanam",
        "Sai Kumar",
    ]
    member_columns = st.columns(3)
    for index, name in enumerate(members):
        with member_columns[index % 3]:
            st.markdown(f"#### {index + 1:02d}  {name}")
    st.subheader("Built across science, software, and communication")
    team = [
        ("Ocean Science", "Defines the oceanographic context, validates measurements, and turns patterns into meaningful questions."),
        ("Data Engineering", "Designs the ARGO ingestion pipeline, schemas, quality checks, and future live-data connections."),
        ("AI and Search", "Builds the query planner and retrieval workflows that translate natural-language questions into evidence."),
        ("Product and Design", "Makes complex ocean data approachable through clear explanations, maps, profiles, and guided workflows."),
    ]
    cols = st.columns(4)
    for column, (role, description) in zip(cols, team):
        with column:
            st.markdown(f"#### {role}")
            st.write(description)
    st.divider()
    st.markdown("#### Our working principles")
    principles = st.columns(3)
    principles[0].info("**Evidence first**\nEvery insight should lead back to an observable measurement or a clearly labelled assumption.", icon="🔎")
    principles[1].info("**Explainable by default**\nBeginners should be able to understand what was searched and why a chart appeared.", icon="💡")
    principles[2].info("**Production minded**\nThe demo is designed around real ingestion, database, and protocol boundaries for future deployment.", icon="⚙️")


def render_demo_page(floats_df: pd.DataFrame, meas_df: pd.DataFrame):
    render_page_header(
        "FloatChat Demo Walkthrough",
        "A short guided path for presenting the product from discovery to evidence.",
        "PRESENTATION MODE",
    )
    st.subheader("Four-minute product tour")
    tour = st.columns(4)
    tour[0].markdown("**01  Orient**\nStart at the Command Center and explain active fleet coverage, regions, and alerts.")
    tour[1].markdown("**02  Ask**\nOpen AI Ocean Chat and run: `Show oxygen profiles deeper than 500m`.")
    tour[2].markdown("**03  Explore**\nOpen Live ARGO Map, color markers by oxygen, and narrow the region.")
    tour[3].markdown("**04  Prove**\nOpen Data Explorer and download the filtered observations behind the chart.")
    st.divider()
    st.subheader("Presentation snapshot")
    snapshot_col, insight_col = st.columns([1, 1])
    with snapshot_col:
        st.metric("Catalog floats", len(floats_df))
        st.metric("Catalog observations", f"{len(meas_df):,}")
        st.download_button("Download demo observations", meas_df.to_csv(index=False).encode("utf-8"), "floatchat_demo_observations.csv", "text/csv")
    with insight_col:
        st.info("The strongest demo story is: locate the fleet, ask a focused ocean question, inspect the visualization, then verify the underlying observations.", icon="🎯")
    with st.expander("Research references"):
        st.markdown("- ARGO Program: [argo.ucsd.edu](https://argo.ucsd.edu/)\n- Global Ocean Observing System: [goosocean.org](https://goosocean.org/)\n- Copernicus Marine Service: [marine.copernicus.eu](https://marine.copernicus.eu/)\n- FloatChat demo data: reproducible synthetic observations generated locally for development and presentation.")


def main():
    load_dotenv()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    data_mode = os.getenv("DATA_MODE", "demo")
    try:
        (floats_df, profiles_df, meas_df), source_label = load_runtime_data(data_mode)
    except Exception as exc:
        st.warning(f"PostgreSQL mode is unavailable, so FloatChat is using demo data: {exc}", icon="⚠️")
        floats_df, profiles_df, meas_df = load_initial_data()
        source_label = "DEMO / SYNTHETIC (FALLBACK)"
    engine = QueryEngine(floats_df, profiles_df, meas_df)
    rag = RAGPipeline(LocalVectorStore(os.getenv("VECTOR_STORE_PATH", "data/vector_store.json")))
    summary = build_summary(floats_df, profiles_df, meas_df)

    with st.sidebar:
        st.markdown(
            '<div class="brand-lockup"><div class="brand-mark">≈</div><div><div class="brand-name">FLOATCHAT</div><div class="brand-subtitle">Ocean intelligence / HEXAHACK</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<span class="status-badge">● LIVE OCEAN SYSTEM</span>', unsafe_allow_html=True)
        st.markdown('<span class="demo-badge">DEMO DATA MODE</span>', unsafe_allow_html=True)
        st.divider()
        st.markdown("#### WORKSPACE")
        page = st.radio(
            "NAVIGATION CONTROL",
            [
                "1. Ocean Command Center",
                "2. AI Ocean Chat",
                "3. Live ARGO Map",
                "4. Float Explorer",
                "5. Ocean Profile Lab",
                "6. Data Explorer",
                "7. System / Data Sources",
                "8. FloatChat Field Guide",
                "9. Our Team",
                "10. Demo Walkthrough",
            ],
            index=0,
        )
        st.divider()
        st.markdown(
            f'<div class="sidebar-status"><strong>NETWORK STATUS</strong><br>{summary["active"]} active / {summary["inactive"]} inactive<br><span>Last profile: {summary["latest_profile"]}</span></div>',
            unsafe_allow_html=True,
        )

    if page == "2. AI Ocean Chat":
        render_chat_page(engine, floats_df, meas_df, rag)
        return

    if page == "8. FloatChat Field Guide":
        render_beginner_page()
        return

    if page == "9. Our Team":
        render_team_page()
        return

    if page == "10. Demo Walkthrough":
        render_demo_page(floats_df, meas_df)
        return

    if page == "1. Ocean Command Center":
        render_page_header(
            "Ocean Command Center",
            "Real-time global ARGO hydrographic monitoring & AI synthesis",
            "COASTAL AI OPS",
        )
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("ACTIVE FLOATS", summary["active"], delta=f"{summary['active'] / len(floats_df):.0%} of network")
        col2.metric("PROFILES", len(profiles_df))
        col3.metric("REGIONS", summary["regions"], delta="Indian Ocean focus")
        col4.metric("PARAMETERS", "Temp, Sal, O2, Chl")
        col5.metric("DATA POINTS", f"{len(meas_df):,}")
        st.markdown("---")
        map_col, status_col = st.columns([1.6, 1])
        with map_col:
            st.subheader("Global ARGO Float Distribution")
            st.plotly_chart(render_global_map(floats_df), width="stretch", config={"displayModeBar": False})
        with status_col:
            st.subheader("Network readiness")
            st.progress(summary["active"] / len(floats_df), text="Active fleet coverage")
            st.caption("Coverage is calculated from the current in-memory ARGO catalog.")
            render_region_table(floats_df)

        render_alerts(floats_df, meas_df)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Temperature baseline")
            st.plotly_chart(render_profile_chart(meas_df, "temperature"), width="stretch")
        with c2:
            st.subheader("Salinity baseline")
            st.plotly_chart(render_profile_chart(meas_df, "salinity"), width="stretch")

    elif page == "2. AI Ocean Chat":
        render_page_header(
            "AI Ocean Intelligence Chat",
            "Ask natural language questions to query ARGO profiles & BGC parameter trends.",
            "QUERY ENGINE",
        )
        st.markdown("**Try asking:**")
        preset_cols = st.columns(3)
        p1 = preset_cols[0].button("Show salinity profiles near equator")
        p2 = preset_cols[1].button("What are nearest floats to 15, 72?")
        p3 = preset_cols[2].button("Show temperature deeper than 500m")

        default_query = (
            "Show salinity profiles near equator" if p1 else
            ("What are nearest floats to 15, 72?" if p2 else
            ("Show temperature deeper than 500m" if p3 else ""))
        )

        st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble user">User: {default_query or "Ask a question about the ARGO network"}</div>', unsafe_allow_html=True)
        st.markdown('<div class="chat-bubble assistant">Assistant: I am translating your request into an oceanographic query, then filtering the float network and plotting the relevant profile or map view.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        query_input = st.text_input(
            "Enter your oceanographic query:",
            placeholder="e.g. Compare BGC parameters in the Arabian Sea",
            value=default_query,
        )

        if query_input:
            st.markdown("---")
            st.markdown("**Processing Stages:**")
            st.markdown("`✓ QUERY RECEIVED` → `✓ UNDERSTANDING INTENT` → `✓ SEARCHING ARGO NETWORK` → `✓ ANALYZING PROFILES` → `✓ INSIGHT READY`")
            plan = engine.parse_query_plan(query_input)
            filt_floats, filt_meas = engine.execute_plan(plan)
            st.json(plan)
            c1, c2 = st.columns(2)
            with c1:
                if plan.get("visualization") == "depth_profile":
                    if filt_meas.empty:
                        st.warning("No measurements matched that profile request. Try a broader region or a shallower depth.")
                    else:
                        st.plotly_chart(render_profile_chart(filt_meas, plan.get("parameter", "temperature")), width="stretch")
                else:
                    if filt_floats.empty:
                        st.warning("No floats matched that location or status filter.")
                    else:
                        st.plotly_chart(render_global_map(filt_floats), width="stretch")
            with c2:
                st.markdown(f"**Matched Floats:** `{len(filt_floats)}` | **Measurements:** `{len(filt_meas)}`")
                st.dataframe(
                    filt_meas[["float_id", "timestamp", "depth", "temperature", "salinity", "oxygen"]].head(15),
                    hide_index=True,
                    width="stretch",
                )

    elif page == "3. Live ARGO Map":
        render_page_header(
            "Live Interactive ARGO Map",
            "Regional monitoring across Indian Ocean float clusters and hydrographic anomalies.",
            "MAP MODE",
        )
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        region_filter = f_col1.selectbox("Region Filter", ["ALL", "Arabian Sea", "Bay of Bengal", "Equatorial Indian Ocean", "Global Ocean"])
        status_filter = f_col2.selectbox("Status", ["ALL", "ACTIVE", "INACTIVE"])
        max_d = f_col3.slider("Min Depth Capability (m)", 0, 2000, 1000)
        map_parameter = f_col4.selectbox("Color markers by", ["Fleet status", "temperature", "salinity", "oxygen", "chlorophyll"])
        map_view = st.radio("Map interface", ["2D globe", "3D ocean volume", "Trajectory network"], horizontal=True)
        observation_dates = pd.to_datetime(floats_df["last_observation"])
        date_range = st.slider(
            "Last observation window",
            min_value=observation_dates.min().date(),
            max_value=observation_dates.max().date(),
            value=(observation_dates.min().date(), observation_dates.max().date()),
        )

        sub_floats = floats_df.copy()
        if region_filter != "ALL":
            sub_floats = sub_floats[sub_floats["region"] == region_filter]
        if status_filter != "ALL":
            sub_floats = sub_floats[sub_floats["status"] == status_filter]
        sub_floats = sub_floats[sub_floats["max_depth"] >= max_d]
        sub_dates = pd.to_datetime(sub_floats["last_observation"])
        sub_floats = sub_floats[
            (sub_dates.dt.date >= date_range[0]) & (sub_dates.dt.date <= date_range[1])
        ]
        if map_parameter != "Fleet status":
            parameter_summary = meas_df.groupby("float_id", as_index=False)[map_parameter].mean()
            sub_floats = sub_floats.merge(parameter_summary, on="float_id", how="left")
        st.caption(f"Showing {len(sub_floats)} of {len(floats_df)} floats")
        if sub_floats.empty:
            st.warning("No floats match the current filters. Lower the depth requirement or broaden the region.")
        else:
            color_by = "status" if map_parameter == "Fleet status" else map_parameter
            if map_view == "2D globe":
                figure = render_global_map(sub_floats, color_by=color_by)
            elif map_view == "3D ocean volume":
                figure = render_3d_float_map(sub_floats, color_by=color_by)
            else:
                figure = render_trajectory_network(profiles_df, sub_floats["float_id"])
            st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})

    elif page == "4. Float Explorer":
        render_page_header(
            "Float Explorer",
            "Inspect individual ARGO float telemetry, drift history, and profile structure.",
            "FLOAT ANALYTICS",
        )
        selected_id = st.selectbox("Select ARGO Float ID", floats_df["float_id"].unique())
        float_info = floats_df[floats_df["float_id"] == selected_id].iloc[0]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("FLOAT ID", int(float_info["float_id"]))
        m2.metric("STATUS", float_info["status"])
        m3.metric("COORDINATES", f"{float_info['latitude']}°, {float_info['longitude']}°")
        m4.metric("MAX DEPTH", f"{float_info['max_depth']} m")

        st.markdown("---")
        c1, c2 = st.columns(2)
        f_meas = meas_df[meas_df["float_id"] == selected_id]
        with c1:
            st.plotly_chart(render_profile_chart(f_meas, "temperature"), width="stretch")
            st.plotly_chart(render_profile_chart(f_meas, "oxygen"), width="stretch")
        with c2:
            st.plotly_chart(render_profile_chart(f_meas, "salinity"), width="stretch")
            st.plotly_chart(render_trajectory_map(profiles_df, selected_id), width="stretch")

    elif page == "5. Ocean Profile Lab":
        render_page_header(
            "Ocean Profile Lab",
            "Comparative hydrographic analysis across parameters and floats.",
            "PROFILE LAB",
        )
        lab_col1, lab_col2, lab_col3 = st.columns(3)
        param = lab_col1.selectbox("Select BGC / Hydrographic Parameter", ["temperature", "salinity", "oxygen", "chlorophyll"])
        lab_regions = lab_col2.multiselect("Compare regions", sorted(floats_df["region"].unique().tolist()), default=[])
        lab_view = lab_col3.selectbox("View", ["Profile comparison", "Depth-time heatmap"])
        lab_measurements = meas_df
        if lab_regions:
            region_float_ids = floats_df[floats_df["region"].isin(lab_regions)]["float_id"]
            lab_measurements = meas_df[meas_df["float_id"].isin(region_float_ids)]
        st.caption(f"Comparing {len(lab_measurements['float_id'].unique())} float(s) across {len(lab_measurements):,} observations")
        if lab_measurements.empty:
            st.warning("No observations match the selected regions.")
        else:
            if lab_view == "Depth-time heatmap":
                st.plotly_chart(render_depth_time_plot(lab_measurements, param), width="stretch")
            else:
                st.plotly_chart(render_multi_profile_chart(lab_measurements, param), width="stretch")

    elif page == "6. Data Explorer":
        render_page_header(
            "Data Explorer & Export",
            "Review raw ARGO measurements, filter for diagnostics, and export datasets.",
            "DATA VIEW",
        )
        explorer_col1, explorer_col2 = st.columns(2)
        selected_region = explorer_col1.selectbox("Region", ["ALL"] + sorted(floats_df["region"].unique().tolist()))
        selected_parameter = explorer_col2.selectbox("Sort by parameter", ["temperature", "salinity", "oxygen", "chlorophyll"])
        explorer_df = meas_df.merge(floats_df[["float_id", "region"]], on="float_id", how="left")
        if selected_region != "ALL":
            explorer_df = explorer_df[explorer_df["region"] == selected_region]
        explorer_df = explorer_df.sort_values(selected_parameter, ascending=False)
        st.caption(f"{len(explorer_df):,} observations in the current view")
        st.dataframe(explorer_df, hide_index=True, width="stretch")

        c1, c2 = st.columns(2)
        csv_data = explorer_df.to_csv(index=False).encode("utf-8")
        c1.download_button("📥 Export as CSV", data=csv_data, file_name="floatchat_argo_data.csv", mime="text/csv")
        parquet_data = explorer_df.to_parquet(index=False)
        c2.download_button("Export as Parquet", data=parquet_data, file_name="floatchat_argo_data.parquet", mime="application/octet-stream")

    elif page == "7. System / Data Sources":
        render_page_header(
            "System Architecture & Ingestion",
            "Operational overview of the platform stack, ingestion pipeline, and system connectivity.",
            "SYSTEM STATUS",
        )
        st.subheader("Phase 2: ARGO NetCDF Upload")
        uploaded_nc = st.file_uploader("Upload ARGO NetCDF (.nc) File", type=["nc"])
        if uploaded_nc:
            parsed_df, meta = parse_netcdf_file(uploaded_nc)
            st.success(f"Parsed {meta['filename']} successfully!")
            st.json(meta)
            if meta.get("warnings"):
                for warning in meta["warnings"]:
                    st.warning(warning)
            if not parsed_df.empty:
                st.dataframe(parsed_df.head(), width="stretch")

        st.markdown("---")
        st.subheader("Data quality snapshot")
        quality_columns = ["temperature", "salinity", "oxygen", "chlorophyll"]
        quality = pd.DataFrame({
            "Variable": quality_columns,
            "Missing values": [int(meas_df[column].isna().sum()) for column in quality_columns],
            "Minimum": [round(float(meas_df[column].min()), 3) for column in quality_columns],
            "Maximum": [round(float(meas_df[column].max()), 3) for column in quality_columns],
        })
        st.dataframe(quality, hide_index=True, width="stretch")
        st.caption("Quality values describe the current reproducible demo catalog. Uploaded files receive their own parser warnings above.")

        st.markdown("---")
        st.subheader("System Stack Status")
        service_col1, service_col2, service_col3, service_col4 = st.columns(4)
        service_col1.metric("Demo catalog", "READY")
        service_col2.metric("NetCDF parser", "READY")
        service_col3.metric("AI planner", "LLM / FALLBACK")
        service_col4.metric("Database", "CONNECTED" if source_label.startswith("REAL") else "DEMO FALLBACK")
        st.caption(f"Data source: {source_label} | Local vector store: READY ({len(rag.store.documents)} documents)")
        st.markdown(
            """
            - **UI Framework:** Streamlit Glassmorphism Theme
            - **Visualization:** Plotly Scientific Engine
            - **Database Engine:** PostgreSQL + PostGIS (Fallback: Memory Pandas)
            - **Vector Engine:** Persistent local semantic store (FAISS/Chroma-ready boundary)
            - **MCP Protocol:** Controlled read-only Python MCP SDK tools
            """
        )


if __name__ == "__main__":
    main()
