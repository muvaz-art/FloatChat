import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

DARK_THEME = {
    "paper_bgcolor": "rgba(3, 11, 30, 0.7)",
    "plot_bgcolor": "rgba(3, 11, 30, 0.7)",
    "font": {"color": "#E2E8F0", "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": "rgba(0, 242, 254, 0.1)", "zerolinecolor": "rgba(0, 242, 254, 0.2)"},
    "yaxis": {"gridcolor": "rgba(0, 242, 254, 0.1)", "zerolinecolor": "rgba(0, 242, 254, 0.2)"}
}

def render_global_map(floats_df: pd.DataFrame, selected_float_id=None, color_by="status"):
    """Generates high-contrast ocean scatter map of ARGO floats."""
    fig = px.scatter_scatter_geo if hasattr(px, "scatter_scatter_geo") else px.scatter_geo
    
    color_column = color_by if color_by in floats_df.columns else "status"
    color_map = {"ACTIVE": "#00F2FE", "INACTIVE": "#FF4B4B"} if color_column == "status" else None
    fig = px.scatter_geo(
        floats_df,
        lat="latitude",
        lon="longitude",
        color=color_column,
        size="max_depth",
        hover_name="float_id",
        hover_data={"region": True, "latitude": ":.2f", "longitude": ":.2f", "last_observation": True},
        color_discrete_map=color_map,
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


def render_3d_float_map(floats_df: pd.DataFrame, color_by="status"):
    """Render a futuristic 3D view of float positions and depth capability."""
    if floats_df.empty:
        return go.Figure(layout={"title": "No floats available for this view"})
    color_column = color_by if color_by in floats_df.columns else "status"
    marker = {"size": 7, "opacity": 0.9}
    if color_column == "status":
        marker["color"] = floats_df[color_column].map({"ACTIVE": "#00F2FE", "INACTIVE": "#FF4B4B"})
    else:
        marker["color"] = floats_df[color_column]
        marker["colorscale"] = "Turbo"
        marker["colorbar"] = {"title": color_column}
    fig = go.Figure(go.Scatter3d(
        x=floats_df["longitude"],
        y=floats_df["latitude"],
        z=-floats_df["max_depth"],
        mode="markers",
        text=floats_df["float_id"].astype(str),
        customdata=floats_df[["region", "status", "max_depth"]],
        hovertemplate="Float %{text}<br>Lon %{x:.2f}<br>Lat %{y:.2f}<br>Capability %{customdata[2]:.0f} m<extra></extra>",
        marker=marker,
        name="ARGO floats",
    ))
    fig.update_layout(
        **DARK_THEME,
        title="<b>3D OCEAN OBSERVATION VOLUME</b>",
        scene={
            "xaxis_title": "Longitude",
            "yaxis_title": "Latitude",
            "zaxis_title": "Depth capability (m)",
            "zaxis": {"autorange": "reversed", "gridcolor": "rgba(0, 242, 254, 0.14)"},
            "xaxis": {"gridcolor": "rgba(0, 242, 254, 0.14)"},
            "yaxis": {"gridcolor": "rgba(0, 242, 254, 0.14)"},
            "camera": {"eye": {"x": 1.55, "y": 1.45, "z": 1.15}},
            "bgcolor": "rgba(3, 11, 30, 0.7)",
        },
        height=560,
        margin=dict(l=0, r=0, t=45, b=0),
    )
    return fig

def render_profile_chart(meas_df: pd.DataFrame, parameter="temperature"):
    """Plots depth profile curve (Parameter vs Depth)."""
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
        height=450,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_yaxes(
        autorange="reversed",
        gridcolor="rgba(0, 242, 254, 0.1)",
        zerolinecolor="rgba(0, 242, 254, 0.2)"
    )
    return fig

def render_multi_profile_chart(meas_df: pd.DataFrame, parameter="salinity", max_floats=6):
    """Plots overlay comparison of multiple floats."""
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
        height=450
    )
    fig.update_yaxes(autorange="reversed")
    return fig

def render_trajectory_map(profiles_df: pd.DataFrame, float_id: int):
    """Plots historical drift trajectory of selected float."""
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


def render_trajectory_network(profiles_df: pd.DataFrame, float_ids) -> go.Figure:
    """Render recent trajectories for a filtered group of floats."""
    selected = profiles_df[profiles_df["float_id"].isin(list(float_ids))].copy()
    fig = go.Figure()
    for float_id, track in selected.groupby("float_id"):
        track = track.sort_values("timestamp")
        fig.add_trace(go.Scattergeo(
            lat=track["latitude"], lon=track["longitude"], mode="lines+markers",
            name=f"Float {float_id}", marker={"size": 5}, line={"width": 2},
            hovertemplate=f"Float {float_id}<br>Lat %{{lat:.2f}}<br>Lon %{{lon:.2f}}<extra></extra>",
        ))
    fig.update_geos(showocean=True, oceancolor="#020C1B", showland=True, landcolor="#0A192F", showcountries=True, countrycolor="rgba(0, 242, 254, 0.2)")
    fig.update_layout(**DARK_THEME, title="<b>ARGO TRAJECTORY NETWORK</b>", height=560, margin=dict(l=10, r=10, t=45, b=10), legend={"orientation": "h"})
    return fig


def render_depth_time_plot(meas_df: pd.DataFrame, parameter="temperature"):
    """Render a time/depth heatmap for an available measurement variable."""
    if meas_df.empty or parameter not in meas_df.columns:
        return go.Figure(layout={"title": "No observations available for this variable"})
    frame = meas_df.dropna(subset=["timestamp", "depth", parameter]).copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame = frame.dropna(subset=["timestamp"])
    pivot = frame.pivot_table(index="depth", columns="timestamp", values=parameter, aggfunc="mean")
    fig = go.Figure(go.Heatmap(x=pivot.columns, y=pivot.index, z=pivot.values, colorscale="Viridis", colorbar_title=parameter))
    fig.update_layout(**DARK_THEME, title=f"<b>DEPTH-TIME: {parameter.upper()}</b>", xaxis_title="Observation time", yaxis_title="Depth (meters)", height=500)
    fig.update_yaxes(autorange="reversed")
    return fig
