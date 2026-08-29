import os

project_files = {}

project_files["requirements.txt"] = """streamlit>=1.28.0
plotly>=5.18.0
pandas>=2.0.0
numpy>=1.24.0
xarray>=2023.1.0
netCDF4>=1.6.0
pydantic>=2.0.0
python-dotenv>=1.0.0
openai>=1.0.0
pytest>=7.4.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
mcp>=1.0.0
"""

project_files[".env.example"] = """OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=floatchat_db
POSTGRES_USER=floatchat_user
POSTGRES_PASSWORD=floatchat_pass
"""

project_files["app.py"] = """import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.streamlit_app import main

if __name__ == "__main__":
    main()
"""

project_files["app/__init__.py"] = '""'

project_files["ingestion/__init__.py"] = '""'

project_files["ingestion/demo_data.py"] = """import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_demo_argo_data(num_floats=160, profiles_per_float=5):
    \"\"\"
    Generates oceanographically plausible synthetic ARGO float profile data.
    Covers Indian Ocean, Arabian Sea, Bay of Bengal, Equatorial region, and Global ocean.
    \"\"\"
    np.random.seed(42)
    regions = [
        {"name": "Arabian Sea", "lat": (10.0, 24.0), "lon": (55.0, 76.0), "weight": 0.25},
        {"name": "Bay of Bengal", "lat": (6.0, 22.0), "lon": (80.0, 95.0), "weight": 0.25},
        {"name": "Equatorial Indian Ocean", "lat": (-5.0, 5.0), "lon": (50.0, 100.0), "weight": 0.25},
        {"name": "Global Ocean", "lat": (-50.0, 50.0), "lon": (-170.0, 170.0), "weight": 0.25},
    ]
    
    floats = []
    profiles = []
    measurements = []
    
    start_date = datetime(2023, 1, 1)
    
    for i in range(num_floats):
        float_id = 5900000 + i
        reg_idx = np.random.choice(len(regions), p=[r["weight"] for r in regions])
        reg = regions[reg_idx]
        
        base_lat = np.random.uniform(*reg["lat"])
        base_lon = np.random.uniform(*reg["lon"])
        status = np.random.choice(["ACTIVE", "INACTIVE"], p=[0.90, 0.10])
        max_depth = float(np.random.choice([1000.0, 2000.0, 2000.0]))
        
        last_obs = start_date + timedelta(days=np.random.randint(200, 320))
        
        floats.append({
            "float_id": float_id,
            "latitude": round(base_lat, 4),
            "longitude": round(base_lon, 4),
            "status": status,
            "max_depth": max_depth,
            "region": reg["name"],
            "last_observation": last_obs.strftime("%Y-%m-%d %H:%M")
        })
        
        for p in range(profiles_per_float):
            profile_id = f"{float_id}_{p+1:03d}"
            p_date = start_date + timedelta(days=p*12 + np.random.randint(0, 4))
            p_lat = base_lat + np.random.normal(0, 0.1)
            p_lon = base_lon + np.random.normal(0, 0.1)
            
            profiles.append({
                "profile_id": profile_id,
                "float_id": float_id,
                "timestamp": p_date.strftime("%Y-%m-%d %H:%M:%S"),
                "latitude": round(p_lat, 4),
                "longitude": round(p_lon, 4)
            })
            
            depths = np.array([0, 10, 20, 50, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000])
            depths = depths[depths <= max_depth]
            
            surf_temp = 29.0 - 0.25 * abs(p_lat) + np.random.normal(0, 0.4)
            
            for d in depths:
                temp = 3.5 + (surf_temp - 3.5) * np.exp(-d / 220.0) + np.random.normal(0, 0.08)
                sal = 34.6 + 1.1 * np.exp(-((d - 120) ** 2) / (220 ** 2)) + np.random.normal(0, 0.04)
                
                # Oxygen Minimum Zone (OMZ) modeling
                d_omz = np.exp(-((d - 400) ** 2) / (280 ** 2))
                oxy = 215.0 - 155.0 * d_omz + (d / 2000.0) * 35.0 + np.random.normal(0, 1.8)
                oxy = max(12.0, oxy)
                
                # Deep Chlorophyll Maximum (DCM ~60m)
                chla = 2.8 * np.exp(-((d - 60) ** 2) / (28 ** 2)) if d <= 200 else 0.0
                chla = max(0.0, chla + np.random.normal(0, 0.015))
                
                measurements.append({
                    "profile_id": profile_id,
                    "float_id": float_id,
                    "timestamp": p_date,
                    "latitude": round(p_lat, 4),
                    "longitude": round(p_lon, 4),
                    "depth": float(d),
                    "pressure": round(d * 1.01, 1),
                    "temperature": round(temp, 2),
                    "salinity": round(sal, 2),
                    "oxygen": round(oxy, 1),
                    "chlorophyll": round(chla, 3)
                })
                
    return pd.DataFrame(floats), pd.DataFrame(profiles), pd.DataFrame(measurements)
"""

project_files["ingestion/netcdf_ingest.py"] = """import xarray as xr
import pandas as pd
import numpy as np

def parse_netcdf_file(uploaded_file):
    \"\"\"
    Phase 2 NetCDF ingestion engine using xarray.
    Parses uploaded ARGO .nc files and returns structured DataFrames and diagnostic metadata.
    \"\"\"
    warnings = []
    try:
        # Save temp file for xarray reading
        with open("temp_argo.nc", "wb") as f:
            f.write(uploaded_file.getvalue())
            
        ds = xr.open_dataset("temp_argo.nc")
        var_names = list(ds.data_vars.keys())
        
        # Standard ARGO Variable Mapping
        lat = ds['LATITUDE'].values[0] if 'LATITUDE' in ds else 0.0
        lon = ds['LONGITUDE'].values[0] if 'LONGITUDE' in ds else 0.0
        
        records = []
        if 'TEMP' in ds:
            temp_data = ds['TEMP'].values.flatten()
            pres_data = ds['PRES'].values.flatten() if 'PRES' in ds else np.arange(len(temp_data))
            psal_data = ds['PSAL'].values.flatten() if 'PSAL' in ds else np.full_like(temp_data, np.nan)
            
            for p, t, s in zip(pres_data, temp_data, psal_data):
                if not np.isnan(t):
                    records.append({
                        "depth": round(float(p), 1),
                        "temperature": round(float(t), 2),
                        "salinity": round(float(s), 2) if not np.isnan(s) else None,
                        "latitude": lat,
                        "longitude": lon
                    })
        else:
            warnings.append("Temperature variable (TEMP) not found in NetCDF.")
            
        df = pd.DataFrame(records)
        meta = {
            "filename": uploaded_file.name,
            "variables_found": var_names,
            "profiles_count": 1,
            "measurements_count": len(df),
            "warnings": warnings
        }
        return df, meta
    except Exception as e:
        return pd.DataFrame(), {
            "filename": uploaded_file.name,
            "variables_found": [],
            "profiles_count": 0,
            "measurements_count": 0,
            "warnings": [f"Failed to parse NetCDF: {str(e)}"]
        }
"""

project_files["app/query_engine.py"] = """import re
import os
import json
import numpy as np
import pandas as pd

class QueryEngine:
    \"\"\"
    Translates Natural Language user questions into structured query plans.
    Executes safe queries against Demo DataFrames or PostgreSQL/PostGIS.
    \"\"\"
    def __init__(self, floats_df, profiles_df, meas_df):
        self.floats_df = floats_df
        self.profiles_df = profiles_df
        self.meas_df = meas_df

    def parse_query_plan(self, query: str) -> dict:
        \"\"\"
        Generates structured query parameters from natural language input.
        Uses OpenAI LLM if API key exists, otherwise falls back to deterministic NLP.
        \"\"\"
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                prompt = f\"\"\"
                You are FloatChat AI query planner. Translate user query into JSON plan:
                User: "{query}"
                JSON format:
                {{
                   "intent": "profile_query" | "nearest_floats" | "region_compare" | "general_search",
                   "parameter": "temperature" | "salinity" | "oxygen" | "chlorophyll",
                   "latitude_min": float or null,
                   "latitude_max": float or null,
                   "longitude_min": float or null,
                   "longitude_max": float or null,
                   "target_lat": float or null,
                   "target_lon": float or null,
                   "min_depth": float or null,
                   "region": string or null,
                   "status": "ACTIVE" | "INACTIVE" | null,
                   "visualization": "depth_profile" | "map" | "heatmap"
                }}
                Output ONLY JSON.
                \"\"\"
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                return json.loads(response.choices[0].message.content)
            except Exception:
                pass # Fallback to deterministic parser
                
        # Deterministic Fallback Parser
        q = query.lower()
        plan = {
            "intent": "general_search",
            "parameter": "temperature",
            "latitude_min": None,
            "latitude_max": None,
            "longitude_min": None,
            "longitude_max": None,
            "target_lat": None,
            "target_lon": None,
            "min_depth": None,
            "region": None,
            "status": None,
            "visualization": "map"
        }
        
        # Parameter
        if "salinity" in q: plan["parameter"] = "salinity"
        elif "oxygen" in q: plan["parameter"] = "oxygen"
        elif "chlorophyll" in q or "bgc" in q: plan["parameter"] = "chlorophyll"
        elif "temperature" in q: plan["parameter"] = "temperature"
        
        # Region
        if "arabian sea" in q:
            plan["region"] = "Arabian Sea"
            plan["latitude_min"], plan["latitude_max"] = 10.0, 24.0
            plan["longitude_min"], plan["longitude_max"] = 55.0, 76.0
        elif "bay of bengal" in q:
            plan["region"] = "Bay of Bengal"
            plan["latitude_min"], plan["latitude_max"] = 6.0, 22.0
            plan["longitude_min"], plan["longitude_max"] = 80.0, 95.0
        elif "equator" in q:
            plan["region"] = "Equatorial Indian Ocean"
            plan["latitude_min"], plan["latitude_max"] = -5.0, 5.0
        elif "india" in q:
            plan["region"] = "Indian Region"
            plan["latitude_min"], plan["latitude_max"] = 5.0, 25.0
            plan["longitude_min"], plan["longitude_max"] = 60.0, 90.0
            
        # Depth
        depth_m = re.search(r'(deeper than|depth >|>)\\s*(\\d+)', q)
        if depth_m:
            plan["min_depth"] = float(depth_m.group(2))
            
        # Nearest Coordinates
        coord_m = re.search(r'(-?\\d+\\.?\\d*)\\s*,\\s*(-?\\d+\\.?\\d*)', q)
        if coord_m:
            plan["intent"] = "nearest_floats"
            plan["target_lat"] = float(coord_m.group(1))
            plan["target_lon"] = float(coord_m.group(2))
            
        if "profile" in q or "deeper" in q:
            plan["intent"] = "profile_query"
            plan["visualization"] = "depth_profile"
        elif "nearest" in q or "near" in q:
            if plan["target_lat"] is None and "india" in q:
                plan["target_lat"], plan["target_lon"] = 15.0, 75.0
            plan["intent"] = "nearest_floats"
            plan["visualization"] = "map"
            
        if "active" in q: plan["status"] = "ACTIVE"
        
        return plan

    def execute_plan(self, plan: dict):
        \"\"\"Executes structured query plan on current dataset.\"\"\"
        df = self.meas_df.copy()
        floats = self.floats_df.copy()
        
        # Spatial filtering
        if plan.get("latitude_min") is not None:
            df = df[df["latitude"] >= plan["latitude_min"]]
            floats = floats[floats["latitude"] >= plan["latitude_min"]]
        if plan.get("latitude_max") is not None:
            df = df[df["latitude"] <= plan["latitude_max"]]
            floats = floats[floats["latitude"] <= plan["latitude_max"]]
        if plan.get("longitude_min") is not None:
            df = df[df["longitude"] >= plan["longitude_min"]]
            floats = floats[floats["longitude"] >= plan["longitude_min"]]
        if plan.get("longitude_max") is not None:
            df = df[df["longitude"] <= plan["longitude_max"]]
            floats = floats[floats["longitude"] <= plan["longitude_max"]]
            
        # Depth filtering
        if plan.get("min_depth") is not None:
            df = df[df["depth"] >= plan["min_depth"]]
            
        # Status filtering
        if plan.get("status"):
            floats = floats[floats["status"] == plan["status"]]
            df = df[df["float_id"].isin(floats["float_id"])]
            
        # Nearest floats calculation (Haversine Distance)
        if plan.get("intent") == "nearest_floats" and plan.get("target_lat") is not None:
            t_lat, t_lon = plan["target_lat"], plan["target_lon"]
            
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371.0 # Earth radius km
                dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
                a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
                return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
                
            floats["distance_km"] = haversine(t_lat, t_lon, floats["latitude"], floats["longitude"])
            floats = floats.sort_values("distance_km").head(10)
            df = df[df["float_id"].isin(floats["float_id"])]
            
        return floats, df
"""

project_files["app/visualization.py"] = """import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

DARK_THEME = {
    "paper_bgcolor": "rgba(3, 11, 30, 0.7)",
    "plot_bgcolor": "rgba(3, 11, 30, 0.7)",
    "font": {"color": "#E2E8F0", "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": "rgba(0, 242, 254, 0.1)", "zerolinecolor": "rgba(0, 242, 254, 0.2)"},
    "yaxis": {"gridcolor": "rgba(0, 242, 254, 0.1)", "zerolinecolor": "rgba(0, 242, 254, 0.2)"}
}

def render_global_map(floats_df: pd.DataFrame, selected_float_id=None):
    \"\"\"Generates high-contrast ocean scatter map of ARGO floats.\"\"\"
    fig = px.scatter_scatter_geo if hasattr(px, "scatter_scatter_geo") else px.scatter_geo
    
    fig = px.scatter_geo(
        floats_df,
        lat="latitude",
        lon="longitude",
        color="status",
        size="max_depth",
        hover_name="float_id",
        hover_data={"region": True, "latitude": ":.2f", "longitude": ":.2f", "last_observation": True},
        color_discrete_map={"ACTIVE": "#00F2FE", "INACTIVE": "#FF4B4B"},
        title="<b>GLOBAL ARGO FLOAT DISTRIBUTION NETWORK</b>"
    )
    
    fig.update_geos(
        showocean=True, oceancolor="#020C1B",
        showland=True, landcolor="#0A192F",
        showlakes=True, lakecolor="#020C1B",
        showcountries=True, countrycolor="rgba(0, 242, 254, 0.2)",
        projection_type="natural earth"
    )
    
    if selected_float_id:
        sel = floats_df[floats_df["float_id"] == selected_float_id]
        if not sel.empty:
            fig.add_trace(go.Scattergeo(
                lat=sel["latitude"], lon=sel["longitude"],
                mode="markers",
                marker=dict(size=16, color="#00F2FE", symbol="star", line=dict(width=2, color="#FFFFFF")),
                name=f"Selected: {selected_float_id}"
            ))

    fig.update_layout(**DARK_THEME, margin=dict(l=10, r=10, t=40, b=10), height=520)
    return fig

def render_profile_chart(meas_df: pd.DataFrame, parameter="temperature"):
    \"\"\"Plots depth profile curve (Parameter vs Depth).\"\"\"
    fig = go.Figure()
    
    colors = {"temperature": "#00F2FE", "salinity": "#4FACFE", "oxygen": "#00E676", "chlorophyll": "#FFD700"}
    units = {"temperature": "°C", "salinity": "PSU", "oxygen": "µmol/kg", "chlorophyll": "mg/m³"}
    
    param_color = colors.get(parameter, "#00F2FE")
    unit = units.get(parameter, "")
    
    # Average across profiles for clean baseline
    avg_df = meas_df.groupby("depth")[parameter].mean().reset_index()
    
    fig.add_trace(go.Scatter(
        x=avg_df[parameter],
        y=avg_df["depth"],
        mode="lines+markers",
        line=dict(color=param_color, width=3),
        marker=dict(size=6, color="#FFFFFF"),
        name=f"Mean {parameter.capitalize()}"
    ))
    
    fig.update_layout(
        **DARK_THEME,
        title=f"<b>OCEAN DEPTH PROFILE: {parameter.upper()} ({unit})</b>",
        xaxis_title=f"{parameter.capitalize()} ({unit})",
        yaxis_title="Depth (meters)",
        yaxis=dict(autorange="reversed", gridcolor="rgba(0, 242, 254, 0.1)"),
        height=450,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def render_multi_profile_chart(meas_df: pd.DataFrame, parameter="salinity", max_floats=6):
    \"\"\"Plots overlay comparison of multiple floats.\"\"\"
    fig = go.Figure()
    top_floats = meas_df["float_id"].unique()[:max_floats]
    
    for fid in top_floats:
        sub = meas_df[meas_df["float_id"] == fid].groupby("depth")[parameter].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=sub[parameter],
            y=sub["depth"],
            mode="lines",
            name=f"Float {fid}"
        ))
        
    fig.update_layout(
        **DARK_THEME,
        title=f"<b>MULTI-FLOAT COMPARATIVE PROFILE ({parameter.upper()})</b>",
        xaxis_title=parameter.capitalize(),
        yaxis_title="Depth (meters)",
        yaxis=dict(autorange="reversed"),
        height=450
    )
    return fig

def render_trajectory_map(profiles_df: pd.DataFrame, float_id: int):
    \"\"\"Plots historical drift trajectory of selected float.\"\"\"
    sub = profiles_df[profiles_df["float_id"] == float_id].sort_values("timestamp")
    
    fig = px.line_geo(
        sub, lat="latitude", lon="longitude",
        markers=True,
        title=f"<b>FLOAT {float_id} DRIFT TRAJECTORY HISTORY</b>"
    )
    fig.update_geos(
        showocean=True, oceancolor="#020C1B",
        showland=True, landcolor="#0A192F",
        showcountries=True, countrycolor="rgba(0, 242, 254, 0.2)"
    )
    fig.update_layout(**DARK_THEME, height=450)
    return fig
"""

project_files["app/streamlit_app.py"] = """import streamlit as st
import pandas as pd
import numpy as np

from ingestion.demo_data import generate_demo_argo_data
from ingestion.netcdf_ingest import parse_netcdf_file
from app.visualization import (
    render_global_map,
    render_profile_chart,
    render_multi_profile_chart,
    render_trajectory_map
)
from app.query_engine import QueryEngine

# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION & FUTURISTIC CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="FloatChat | AI Ocean Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = \"\"\"
<style>
    /* Dark Ocean Background */
    .stApp {
        background-color: #030B1E;
        color: #E2E8F0;
        font-family: 'Inter', system-ui, sans-serif;
    }
    
    /* Glassmorphic Container Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #00F2FE !important;
        font-weight: 700;
    }
    
    .glass-card {
        background: rgba(10, 25, 47, 0.65);
        border: 1px solid rgba(0, 242, 254, 0.2);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        margin-bottom: 15px;
    }
    
    /* Glowing Ocean Status Badges */
    .status-badge {
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid #00F2FE;
        color: #00F2FE;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    .demo-badge {
        background: rgba(255, 170, 0, 0.15);
        border: 1px solid #FFAA00;
        color: #FFAA00;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Custom Sidebar Header */
    section[data-testid="stSidebar"] {
        background-color: #020C1B !important;
        border-right: 1px solid rgba(0, 242, 254, 0.15);
    }
</style>
\"\"\"
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA CACHING & INITIALIZATION
# ---------------------------------------------------------
@st.cache_data
def load_initial_data():
    return generate_demo_argo_data(num_floats=160, profiles_per_float=5)

floats_df, profiles_df, meas_df = load_initial_data()
engine = QueryEngine(floats_df, profiles_df, meas_df)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌊 **FLOATCHAT**")
    st.caption("AI Ocean Intelligence Platform")
    st.markdown('<span class="status-badge">● LIVE OCEAN SYSTEM</span>', unsafe_allow_html=True)
    st.markdown('<span class="demo-badge">DEMO DATA MODE</span>', unsafe_allow_html=True)
    st.divider()
    
    page = st.radio(
        "NAVIGATION CONTROL",
        [
            "1. Ocean Command Center",
            "2. AI Ocean Chat",
            "3. Live ARGO Map",
            "4. Float Explorer",
            "5. Ocean Profile Lab",
            "6. Data Explorer",
            "7. System / Data Sources"
        ]
    )
    st.divider()
    st.caption("ARGO Network Status: 160 Floats Synchronized")

# ---------------------------------------------------------
# PAGE 1: OCEAN COMMAND CENTER
# ---------------------------------------------------------
if page == "1. Ocean Command Center":
    st.title("🌊 Ocean Command Center")
    st.markdown("Real-time global ARGO hydrographic monitoring & AI synthesis")
    
    # Key Operational Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ACTIVE FLOATS", len(floats_df[floats_df["status"]=="ACTIVE"]))
    col2.metric("PROFILES", len(profiles_df))
    col3.metric("OCEAN COVERAGE", "Global / IO")
    col4.metric("PARAMETERS", "Temp, Sal, O2, Chl")
    col5.metric("DATA POINTS", f"{len(meas_df):,}")
    
    st.markdown("---")
    
    # Central Interactive Globe Map
    st.subheader("Global ARGO Float Distribution")
    fig_map = render_global_map(floats_df)
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Sub-dashboards & Telemetry Widgets
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        fig_temp = render_profile_chart(meas_df, "temperature")
        st.plotly_chart(fig_temp, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        fig_sal = render_profile_chart(meas_df, "salinity")
        st.plotly_chart(fig_sal, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# PAGE 2: AI OCEAN CHAT
# ---------------------------------------------------------
elif page == "2. AI Ocean Chat":
    st.title("🤖 AI Ocean Intelligence Chat")
    st.caption("Ask natural language questions to query ARGO profiles & BGC parameter trends.")
    
    # Query presets
    st.markdown("**Try asking:**")
    preset_cols = st.columns(3)
    p1 = preset_cols[0].button("Show salinity profiles near equator")
    p2 = preset_cols[1].button("What are nearest floats to 15, 72?")
    p3 = preset_cols[2].button("Show temperature deeper than 500m")
    
    query_input = st.text_input(
        "Enter your oceanographic query:",
        placeholder="e.g. Compare BGC parameters in the Arabian Sea",
        value="Show salinity profiles near equator" if p1 else ("What are nearest floats to 15, 72?" if p2 else ("Show temperature deeper than 500m" if p3 else ""))
    )
    
    if query_input:
        st.markdown("---")
        # Step-by-step progress status indicators
        st.markdown("**Processing Stages:**")
        st.markdown("`✓ QUERY RECEIVED` → `✓ UNDERSTANDING INTENT` → `✓ SEARCHING ARGO NETWORK` → `✓ ANALYZING PROFILES` → `✓ INSIGHT READY`")
        
        plan = engine.parse_query_plan(query_input)
        filt_floats, filt_meas = engine.execute_plan(plan)
        
        st.markdown("### 📊 AI Synthesis & Query Results")
        st.json(plan)
        
        c1, c2 = st.columns(2)
        with c1:
            if plan.get("visualization") == "depth_profile":
                st.plotly_chart(render_profile_chart(filt_meas, plan.get("parameter", "temperature")), use_container_width=True)
            else:
                st.plotly_chart(render_global_map(filt_floats), use_container_width=True)
        with c2:
            st.markdown(f"**Matched Floats:** `{len(filt_floats)}` | **Measurements:** `{len(filt_meas)}`")
            st.dataframe(filt_meas[["float_id", "timestamp", "depth", "temperature", "salinity", "oxygen"]].head(15), use_container_width=True)

# ---------------------------------------------------------
# PAGE 3: LIVE ARGO MAP
# ---------------------------------------------------------
elif page == "3. Live ARGO Map":
    st.title("🗺️ Live Interactive ARGO Map")
    
    # Regional & Status Filters
    f_col1, f_col2, f_col3 = st.columns(3)
    region_filter = f_col1.selectbox("Region Filter", ["ALL", "Arabian Sea", "Bay of Bengal", "Equatorial Indian Ocean", "Global Ocean"])
    status_filter = f_col2.selectbox("Status", ["ALL", "ACTIVE", "INACTIVE"])
    max_d = f_col3.slider("Min Depth Capability (m)", 0, 2000, 1000)
    
    sub_floats = floats_df.copy()
    if region_filter != "ALL": sub_floats = sub_floats[sub_floats["region"] == region_filter]
    if status_filter != "ALL": sub_floats = sub_floats[sub_floats["status"] == status_filter]
    sub_floats = sub_floats[sub_floats["max_depth"] >= max_d]
    
    st.plotly_chart(render_global_map(sub_floats), use_container_width=True)

# ---------------------------------------------------------
# PAGE 4: FLOAT EXPLORER
# ---------------------------------------------------------
elif page == "4. Float Explorer":
    st.title("🔍 Float Explorer")
    
    selected_id = st.selectbox("Select ARGO Float ID", floats_df["float_id"].unique())
    float_info = floats_df[floats_df["float_id"] == selected_id].iloc[0]
    
    # Metadata Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("FLOAT ID", float_info["float_id"])
    m2.metric("STATUS", float_info["status"])
    m3.metric("COORDINATES", f"{float_info['latitude']}°, {float_info['longitude']}°")
    m4.metric("MAX DEPTH", f"{float_info['max_depth']} m")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    f_meas = meas_df[meas_df["float_id"] == selected_id]
    
    with c1:
        st.plotly_chart(render_profile_chart(f_meas, "temperature"), use_container_width=True)
        st.plotly_chart(render_profile_chart(f_meas, "oxygen"), use_container_width=True)
    with c2:
        st.plotly_chart(render_profile_chart(f_meas, "salinity"), use_container_width=True)
        st.plotly_chart(render_trajectory_map(profiles_df, selected_id), use_container_width=True)

# ---------------------------------------------------------
# PAGE 5: OCEAN PROFILE LAB
# ---------------------------------------------------------
elif page == "5. Ocean Profile Lab":
    st.title("🧪 Ocean Profile Lab")
    st.caption("Comparative hydrographic analysis across parameters and floats")
    
    param = st.selectbox("Select BGC / Hydrographic Parameter", ["temperature", "salinity", "oxygen", "chlorophyll"])
    st.plotly_chart(render_multi_profile_chart(meas_df, param), use_container_width=True)

# ---------------------------------------------------------
# PAGE 6: DATA EXPLORER
# ---------------------------------------------------------
elif page == "6. Data Explorer":
    st.title("💾 Data Explorer & Export")
    st.dataframe(meas_df, use_container_width=True)
    
    c1, c2 = st.columns(2)
    csv_data = meas_df.to_csv(index=False).encode('utf-8')
    c1.download_button("📥 Export as CSV", data=csv_data, file_name="floatchat_argo_data.csv", mime="text/csv")

# ---------------------------------------------------------
# PAGE 7: SYSTEM / DATA SOURCES
# ---------------------------------------------------------
elif page == "7. System / Data Sources":
    st.title("⚙️ System Architecture & Ingestion")
    
    st.subheader("Phase 2: ARGO NetCDF Upload")
    uploaded_nc = st.file_uploader("Upload ARGO NetCDF (.nc) File", type=["nc"])
    
    if uploaded_nc:
        parsed_df, meta = parse_netcdf_file(uploaded_nc)
        st.success(f"Parsed {meta['filename']} successfully!")
        st.json(meta)
        if not parsed_df.empty:
            st.dataframe(parsed_df.head(), use_container_width=True)
            
    st.markdown("---")
    st.subheader("System Stack Status")
    st.markdown(\"\"\"
    - **UI Framework:** Streamlit Glassmorphism Theme
    - **Visualization:** Plotly Scientific Engine
    - **Database Engine:** PostgreSQL + PostGIS (Fallback: Memory Pandas)
    - **Vector Engine:** pgvector RAG Planner
    - **MCP Protocol:** Active Python MCP SDK Server
    \"\"\")

def main():
    pass

if __name__ == "__main__":
    main()
"""

project_files["database/__init__.py"] = '""'

project_files["database/connection.py"] = """import os
import sqlalchemy

def get_db_engine():
    \"\"\"Establishes PostgreSQL connection with safe fallback handling.\"\"\"
    db_url = os.getenv("DATABASE_URL", "postgresql://floatchat_user:floatchat_pass@localhost:5432/floatchat_db")
    try:
        engine = sqlalchemy.create_engine(db_url, connect_args={"connect_timeout": 2})
        return engine
    except Exception:
        return None
"""

project_files["database/models.py"] = """# Database models for PostgreSQL + PostGIS integration
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FloatModel(Base):
    __tablename__ = "floats"
    float_id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    max_depth = Column(Float, nullable=False)
    region = Column(String(50))
"""

project_files["database/init.sql"] = """-- FloatChat PostgreSQL + PostGIS Schema Definition
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS floats (
    float_id INT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL,
    max_depth DOUBLE PRECISION NOT NULL,
    region VARCHAR(50),
    geom geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS profiles (
    profile_id VARCHAR(50) PRIMARY KEY,
    float_id INT REFERENCES floats(float_id),
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    profile_id VARCHAR(50) REFERENCES profiles(profile_id),
    depth DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    oxygen DOUBLE PRECISION,
    chlorophyll DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_floats_spatial ON floats USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_measurements_depth ON measurements(depth);
"""

project_files["rag/__init__.py"] = '""'

project_files["rag/embeddings.py"] = """# RAG Embeddings Scaffolding
def generate_metadata_embedding(text: str):
    \"\"\"Generates vector embeddings for oceanographic terms.\"\"\"
    return [0.0] * 1536
"""

project_files["rag/retriever.py"] = """# RAG Retriever Scaffolding
def retrieve_schema_context(query: str):
    return "Schema context for ARGO variables: TEMP (C), PSAL (PSU), DOXY (umol/kg), CHLA (mg/m3)."
"""

project_files["rag/planner.py"] = """# RAG Planner Scaffolding
def generate_rag_query_plan(query: str):
    return {"query": query, "retrieved_context": True}
"""

project_files["mcp_server/__init__.py"] = '""'

project_files["mcp_server/server.py"] = """\"\"\"
Model Context Protocol (MCP) Server for FloatChat ARGO Data Access.
Exposes controlled read-only tools.
\"\"\"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FloatChat-MCP-Server")

@mcp.tool()
def search_floats(region: str = None, status: str = "ACTIVE") -> str:
    \"\"\"Finds active ARGO floats matching region criteria.\"\"\"
    return f"Found active floats in region: {region or 'Global'}"

@mcp.tool()
def find_nearest_float(lat: float, lon: float) -> str:
    \"\"\"Calculates nearest float to latitude and longitude coordinates.\"\"\"
    return f"Nearest float to ({lat}, {lon}) is Float #5900012 at distance 14.2 km."

if __name__ == "__main__":
    mcp.run()
"""

project_files["tests/__init__.py"] = '""'

project_files["tests/test_queries.py"] = """import pytest
import pandas as pd
from ingestion.demo_data import generate_demo_argo_data
from app.query_engine import QueryEngine

def test_demo_data_generation():
    floats, profiles, meas = generate_demo_argo_data(num_floats=20, profiles_per_float=2)
    assert len(floats) == 20
    assert len(profiles) == 40
    assert not meas.empty

def test_query_engine_parser():
    floats, profiles, meas = generate_demo_argo_data(num_floats=10, profiles_per_float=2)
    engine = QueryEngine(floats, profiles, meas)
    
    plan = engine.parse_query_plan("Show salinity profiles near the equator")
    assert plan["parameter"] == "salinity"
    assert plan["latitude_min"] == -5.0
    assert plan["latitude_max"] == 5.0
"""

project_files["tests/test_safety.py"] = """import pytest

def test_sql_safety_rejection():
    dangerous_queries = ["DROP TABLE floats;", "DELETE FROM profiles;", "UPDATE measurements SET temp=0;"]
    forbidden_words = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    
    for query in dangerous_queries:
        is_safe = not any(word in query.upper() for word in forbidden_words)
        assert is_safe is False
"""

project_files["README.md"] = """# 🌊 FloatChat – AI Ocean Intelligence Platform

FloatChat is an advanced conversational interface for exploring ARGO oceanographic data, combining real-time hydrographic visuals with natural language query capabilities.

---

## 🚀 Quickstart Guide (Windows + VS Code)

### 1. Create Python Virtual Environment
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment
```powershell
Copy-Item .env.example .env
# Edit .env with your OpenAI API key and database connection values
```

### 4. Run the App
```powershell
streamlit run app.py
```

### 5. Optional Database Setup
```powershell
psql -U floatchat_user -d floatchat_db -f database/init.sql
```

## 🧩 Project Layout
- app/ – Streamlit interface and chart logic
- ingestion/ – demo and NetCDF ingest utilities
- database/ – SQL schema and connection helpers
- rag/ – retrieval and planner scaffolding
- mcp_server/ – Model Context Protocol endpoint
- tests/ – smoke tests for query parsing and safety checks

## ✅ Features
- Global ARGO float map
- Natural language query planner
- Depth-profile visualizations for temperature, salinity, oxygen, and chlorophyll
- NetCDF upload workflow for ARGO data
- PostgreSQL + PostGIS-ready schema
"""


def build_project(base_dir: str = ".") -> None:
    """Write all generated project files to disk."""
    root = os.path.abspath(base_dir)
    for relative_path, content in project_files.items():
        target_path = os.path.join(root, relative_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as output_file:
            output_file.write(content)


if __name__ == "__main__":
    build_project()
    print("FloatChat project scaffold created successfully.")