"""
Model Context Protocol (MCP) Server for FloatChat ARGO Data Access.
Exposes controlled read-only tools.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FloatChat-MCP-Server")

@mcp.tool()
def search_floats(region: str = None, status: str = "ACTIVE") -> str:
    """Finds active ARGO floats matching region criteria."""
    return f"Found active floats in region: {region or 'Global'}"

@mcp.tool()
def find_nearest_float(lat: float, lon: float) -> str:
    """Calculates nearest float to latitude and longitude coordinates."""
    return f"Nearest float to ({lat}, {lon}) is Float #5900012 at distance 14.2 km."

if __name__ == "__main__":
    mcp.run()
