from __future__ import annotations

from io import BytesIO
from urllib.request import Request, urlopen

import pandas as pd


COLUMN_ALIASES = {
    "float_id": ["platform_number", "PLATFORM_NUMBER", "float_id", "wmo"],
    "timestamp": ["timestamp", "JULD", "time", "TIME"],
    "latitude": ["latitude", "LATITUDE", "lat"],
    "longitude": ["longitude", "LONGITUDE", "lon"],
    "depth": ["depth", "DEPTH", "pressure", "PRES"],
    "temperature": ["temperature", "TEMP"],
    "salinity": ["salinity", "PSAL"],
    "oxygen": ["oxygen", "DOXY"],
    "chlorophyll": ["chlorophyll", "CHLA"],
    "bbp700": ["bbp700", "BBP700"],
    "nitrate": ["nitrate", "NITRATE"],
    "ph": ["ph", "PH"],
}


def _column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized = {str(column).lower(): column for column in frame.columns}
    return next((normalized[alias.lower()] for alias in aliases if alias.lower() in normalized), None)


def normalize_remote_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Convert an ERDDAP-style flat observation table to FloatChat tables."""
    selected = {}
    for target, aliases in COLUMN_ALIASES.items():
        source = _column(frame, aliases)
        if source:
            selected[target] = frame[source]
    required = {"float_id", "timestamp", "latitude", "longitude", "depth"}
    missing = required - selected.keys()
    if missing:
        raise ValueError(f"Remote dataset is missing required columns: {', '.join(sorted(missing))}")
    measurements = pd.DataFrame(selected)
    measurements["float_id"] = pd.to_numeric(measurements["float_id"], errors="coerce")
    measurements["latitude"] = pd.to_numeric(measurements["latitude"], errors="coerce")
    measurements["longitude"] = pd.to_numeric(measurements["longitude"], errors="coerce")
    measurements["depth"] = pd.to_numeric(measurements["depth"], errors="coerce")
    measurements["timestamp"] = pd.to_datetime(measurements["timestamp"], errors="coerce")
    measurements = measurements.dropna(subset=["float_id", "timestamp", "latitude", "longitude", "depth"])
    measurements = measurements[measurements["latitude"].between(-90, 90) & measurements["longitude"].between(-180, 180) & (measurements["depth"] >= 0)]
    measurements["float_id"] = measurements["float_id"].astype(int)
    measurements["profile_id"] = measurements.apply(lambda row: f"{row.float_id}_{row.timestamp.strftime('%Y%m%d%H%M')}", axis=1)
    profiles = measurements[["profile_id", "float_id", "timestamp", "latitude", "longitude"]].drop_duplicates("profile_id")
    floats = profiles.groupby("float_id", as_index=False).agg(latitude=("latitude", "last"), longitude=("longitude", "last"))
    floats["status"] = "ACTIVE"
    floats["max_depth"] = measurements.groupby("float_id")["depth"].max().reindex(floats["float_id"]).to_numpy()
    floats["region"] = "Remote ARGO"
    return floats, profiles, measurements


def fetch_erddap_csv(url: str, timeout: int = 30) -> tuple[pd.DataFrame, dict]:
    """Fetch and normalize an ERDDAP CSV endpoint without requiring requests."""
    request = Request(url, headers={"User-Agent": "FloatChat/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
    frame = pd.read_csv(BytesIO(payload))
    floats, profiles, measurements = normalize_remote_frame(frame)
    return (floats, profiles, measurements), {
        "source_url": url,
        "dataset_type": "Remote ERDDAP CSV",
        "float_count": len(floats),
        "profiles_count": len(profiles),
        "measurements_count": len(measurements),
        "available_variables": [column for column in measurements.columns if column in {"temperature", "salinity", "oxygen", "chlorophyll", "bbp700", "nitrate", "ph"}],
    }
