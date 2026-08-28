from datetime import date

import pytest

from app.query_plan import QueryPlan
from database.queries import build_measurement_select, reject_unsafe_sql


def test_query_plan_rejects_invalid_ranges():
    with pytest.raises(ValueError):
        QueryPlan(latitude_min=10, latitude_max=-10)


def test_safe_sql_is_parameterized_and_select_only():
    plan = QueryPlan(region="Arabian Sea", variables=["salinity"], start_date=date(2023, 3, 1))
    sql, params = build_measurement_select(plan)
    assert sql.startswith("SELECT")
    assert ":region" in sql
    assert params["region"] == "Arabian Sea"
    with pytest.raises(ValueError):
        reject_unsafe_sql("DROP TABLE floats")
