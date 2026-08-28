from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import xarray as xr

VARIABLE_ALIASES = {
    "platform_number": ["PLATFORM_NUMBER", "PLATFORM", "WMO_INST_TYPE"],
    "timestamp": ["JULD", "TIME", "DATE"],
    "latitude": ["LATITUDE", "LAT", "latitude"],
    "longitude": ["LONGITUDE", "LON", "longitude"],
    "pressure": ["PRES", "PRESSURE", "pres"],
    "temperature": ["TEMP", "TEMPERATURE"],
    "salinity": ["PSAL", "SALINITY"],
    "oxygen": ["DOXY", "OXYGEN", "DISSOLVED_OXYGEN"],
    "chlorophyll": ["CHLA", "CHLOROPHYLL"],
    "bbp700": ["BBP700", "BBP_700", "BACKSCATTER"],
    "nitrate": ["NITRATE", "NO3"],
    "ph": ["PH", "pH", "PH_IN_SITU_TOTAL"],
}


def _find_variable(ds: xr.Dataset, aliases: list[str]) -> str | None:
    names = {name.upper(): name for name in list(ds.variables) + list(ds.coords)}
    for alias in aliases:
        if alias.upper() in names:
            return names[alias.upper()]
    return None


def _values(ds: xr.Dataset, name: str | None, size: int, default=np.nan) -> np.ndarray:
    if not name:
        return np.full(size, default)
    values = np.asarray(ds[name].values).reshape(-1)
    if values.size == 1:
        return np.repeat(values, size)
    return np.resize(values, size)


def parse_netcdf_file(uploaded_file) -> tuple[pd.DataFrame, dict]:
    """Normalize common ARGO core/BGC NetCDF variables into tabular records."""
    filename = getattr(uploaded_file, "name", "uploaded.nc")
    warnings: list[str] = []
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as handle:
            handle.write(uploaded_file.getvalue())
            path = Path(handle.name)
        with xr.open_dataset(path, mask_and_scale=True) as ds:
            found = {key: _find_variable(ds, aliases) for key, aliases in VARIABLE_ALIASES.items()}
            available = [name for name, present in found.items() if present]
            pressure_name = found["pressure"]
            temperature_name = found["temperature"]
            if not pressure_name:
                warnings.append("Pressure variable was not found; depth values cannot be validated.")
            if not temperature_name:
                warnings.append("Temperature variable (TEMP) was not found.")
            sizes = [ds[name].size for name in found.values() if name and ds[name].size > 1]
            size = max(sizes, default=0)
            if size == 0:
                return pd.DataFrame(), _metadata(filename, available, warnings, 0, 0, 0)
            frame = pd.DataFrame({
                "platform_number": _values(ds, found["platform_number"], size),
                "timestamp": _values(ds, found["timestamp"], size),
                "latitude": pd.to_numeric(_values(ds, found["latitude"], size), errors="coerce"),
                "longitude": pd.to_numeric(_values(ds, found["longitude"], size), errors="coerce"),
                "pressure": pd.to_numeric(_values(ds, pressure_name, size), errors="coerce"),
            })
            for key in ("temperature", "salinity", "oxygen", "chlorophyll", "bbp700", "nitrate", "ph"):
                frame[key] = pd.to_numeric(_values(ds, found[key], size), errors="coerce")
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", origin="1950-01-01", unit="D")
            frame.loc[~frame["latitude"].between(-90, 90), "latitude"] = np.nan
            frame.loc[~frame["longitude"].between(-180, 180), "longitude"] = np.nan
            frame.loc[frame["pressure"] < 0, "pressure"] = np.nan
            frame = frame.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
            if frame["timestamp"].isna().all():
                warnings.append("No valid profile timestamps were found.")
            measurements = frame.rename(columns={"pressure": "depth"})
            measurements["profile_id"] = [f"{filename}:{index + 1}" for index in range(len(measurements))]
            measurements["float_id"] = pd.to_numeric(measurements["platform_number"], errors="coerce").fillna(0).astype(int)
            profiles = measurements[["profile_id", "float_id", "timestamp", "latitude", "longitude"]].drop_duplicates("profile_id")
            floats = profiles.groupby("float_id", as_index=False).agg(latitude=("latitude", "first"), longitude=("longitude", "first"))
            return measurements, _metadata(filename, available, warnings, len(floats), len(profiles), len(measurements))
    except Exception as exc:
        return pd.DataFrame(), _metadata(filename, [], [f"Failed to parse NetCDF: {exc}"], 0, 0, 0)
    finally:
        if path:
            path.unlink(missing_ok=True)


def _metadata(filename, available, warnings, floats, profiles, measurements):
    return {
        "filename": filename,
        "source_file": filename,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_type": "ARGO NetCDF",
        "variables_found": available,
        "float_count": floats,
        "profiles_count": profiles,
        "measurements_count": measurements,
        "warnings": warnings,
    }
