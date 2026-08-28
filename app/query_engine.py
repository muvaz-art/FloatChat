import re
import os
import json
import numpy as np
import pandas as pd

class QueryEngine:
    """
    Translates Natural Language user questions into structured query plans.
    Executes safe queries against Demo DataFrames or PostgreSQL/PostGIS.
    """
    def __init__(self, floats_df, profiles_df, meas_df):
        self.floats_df = floats_df
        self.profiles_df = profiles_df
        self.meas_df = meas_df

    def parse_query_plan(self, query: str) -> dict:
        """
        Generates structured query parameters from natural language input.
        Uses OpenAI LLM if API key exists, otherwise falls back to deterministic NLP.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                prompt = f"""
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
                """
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
        depth_m = re.search(r'(deeper than|depth >|>)\s*(\d+)', q)
        if depth_m:
            plan["min_depth"] = float(depth_m.group(2))
            
        # Nearest Coordinates
        coord_m = re.search(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', q)
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
        """Executes structured query plan on current dataset."""
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
