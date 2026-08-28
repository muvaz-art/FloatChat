from __future__ import annotations

from datetime import date
from typing import Any

from app.query_plan import QueryPlan

ALLOWED_COLUMNS = {
    "float_id": "f.float_id",
    "latitude": "f.latitude",
    "longitude": "f.longitude",
    "status": "f.status",
    "region": "f.region",
    "max_depth": "f.max_depth",
    "timestamp": "p.timestamp",
    "depth": "m.depth",
    "temperature": "m.temperature",
    "salinity": "m.salinity",
    "oxygen": "m.oxygen",
    "chlorophyll": "m.chlorophyll",
    "bbp700": "m.bbp700",
    "nitrate": "m.nitrate",
    "ph": "m.ph",
}


def build_measurement_select(plan: QueryPlan) -> tuple[str, dict[str, Any]]:
    variable_columns = ", ".join(f"m.{name}" for name in plan.variables)
    sql = (
        "SELECT f.float_id, f.latitude, f.longitude, f.status, f.region, "
        "p.profile_id, p.timestamp, m.depth, m.pressure, " + variable_columns + " "
        "FROM measurements m JOIN profiles p ON p.profile_id = m.profile_id "
        "JOIN floats f ON f.float_id = p.float_id"
    )
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if plan.region:
        clauses.append("f.region = :region")
        params["region"] = plan.region
    if plan.status:
        clauses.append("f.status = :status")
        params["status"] = plan.status
    if plan.float_ids:
        clauses.append("f.float_id = ANY(:float_ids)")
        params["float_ids"] = plan.float_ids
    for field, expression, parameter in (("latitude_min", ">=", "latitude_min"), ("latitude_max", "<=", "latitude_max"), ("longitude_min", ">=", "longitude_min"), ("longitude_max", "<=", "longitude_max"), ("min_depth", ">=", "min_depth"), ("max_depth", "<=", "max_depth")):
        value = getattr(plan, field)
        if value is not None:
            column = "f.latitude" if "latitude" in field else "f.longitude" if "longitude" in field else "m.depth"
            clauses.append(f"{column} {expression} :{parameter}")
            params[parameter] = value
    if plan.start_date:
        clauses.append("p.timestamp >= :start_date")
        params["start_date"] = date.fromisoformat(str(plan.start_date))
    if plan.end_date:
        clauses.append("p.timestamp < :end_date")
        params["end_date"] = date.fromisoformat(str(plan.end_date))
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY {ALLOWED_COLUMNS[plan.sort_by]} LIMIT :limit"
    params["limit"] = plan.limit
    return sql, params


def reject_unsafe_sql(sql: str) -> None:
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise ValueError("Only SELECT statements are allowed")
    forbidden = ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", ";")
    if any(token in normalized for token in forbidden):
        raise ValueError("Unsafe SQL was rejected")
