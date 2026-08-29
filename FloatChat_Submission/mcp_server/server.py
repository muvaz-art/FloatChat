"""Controlled read-only MCP tools for FloatChat."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from app.services import build_query_service

mcp = FastMCP("FloatChat-MCP-Server")


def _engine():
    return build_query_service()[0]


def _json_result(floats, measurements) -> str:
    return json.dumps({"floats": floats.to_dict(orient="records"), "measurements": measurements.head(100).to_dict(orient="records")}, default=str)


@mcp.tool()
def search_floats(region: str | None = None, status: str = "ACTIVE") -> str:
    """Find floats by region and validated status."""
    if status not in {"ACTIVE", "INACTIVE"}:
        raise ValueError("status must be ACTIVE or INACTIVE")
    engine = _engine()
    plan = {"region": region, "status": status, "variables": ["temperature"], "limit": 1000}
    floats, measurements = engine.execute_plan(plan)
    return _json_result(floats, measurements)


@mcp.tool()
def find_nearest_float(lat: float, lon: float) -> str:
    """Return the nearest demo float using the safe QueryEngine path."""
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("latitude or longitude is out of range")
    engine = _engine()
    plan = {"intent": "nearest_floats", "target_latitude": lat, "target_longitude": lon, "variables": ["temperature"], "limit": 10}
    floats, measurements = engine.execute_plan(plan)
    return _json_result(floats, measurements)


@mcp.tool()
def get_float_profile(float_id: int, variable: str = "temperature") -> str:
    """Return a selected float profile for an allowlisted variable."""
    if variable not in {"temperature", "salinity", "oxygen", "chlorophyll"}:
        raise ValueError("unsupported variable")
    engine = _engine()
    floats, measurements = engine.execute_plan({"float_ids": [float_id], "variables": [variable], "visualization": "depth_profile", "limit": 1000})
    return _json_result(floats, measurements)


@mcp.tool()
def get_available_variables() -> str:
    """Return variables supported by the normalized application model."""
    return json.dumps(["temperature", "salinity", "oxygen", "chlorophyll", "bbp700", "nitrate", "ph"])


if __name__ == "__main__":
    mcp.run()
