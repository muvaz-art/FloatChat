DOCUMENTS = [
    {"id": "argo-overview", "text": "ARGO floats are autonomous instruments that drift, dive, and measure ocean conditions. A profile is one vertical sampling event."},
    {"id": "variables-core", "text": "Temperature is measured in degrees Celsius. Salinity is measured in PSU. Pressure is related to depth in the water column."},
    {"id": "variables-bgc", "text": "BGC variables include dissolved oxygen, chlorophyll, nitrate, pH, and BBP700 backscatter. Availability depends on the source dataset."},
    {"id": "schema", "text": "FloatChat structured data uses floats, profiles, and measurements. Profiles belong to floats; measurements belong to profiles and include timestamp, coordinates, depth, and ocean variables."},
    {"id": "spatial", "text": "Spatial searches use latitude and longitude bounds. Nearest-float searches calculate distance from target coordinates and return the closest instruments."},
    {"id": "visualizations", "text": "Maps show positions, trajectories show float movement, depth profiles show variable change with depth, and comparison plots overlay multiple float profiles."},
    {"id": "safety", "text": "Natural language is converted into a validated QueryPlan. Application code builds parameterized SELECT queries; destructive SQL and arbitrary commands are not allowed."},
]
