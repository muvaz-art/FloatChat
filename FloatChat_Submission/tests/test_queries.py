import pytest
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
