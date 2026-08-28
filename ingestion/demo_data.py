import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_demo_argo_data(num_floats=160, profiles_per_float=5):
    """
    Generates oceanographically plausible synthetic ARGO float profile data.
    Covers Indian Ocean, Arabian Sea, Bay of Bengal, Equatorial region, and Global ocean.
    """
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
