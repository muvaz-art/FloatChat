import xarray as xr
import pandas as pd
import numpy as np

def parse_netcdf_file(uploaded_file):
    """
    Phase 2 NetCDF ingestion engine using xarray.
    Parses uploaded ARGO .nc files and returns structured DataFrames and diagnostic metadata.
    """
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
