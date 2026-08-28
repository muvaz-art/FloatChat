from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import get_db_engine
from ingestion.netcdf_ingest import parse_netcdf_file


def discover_files(path: Path) -> list[Path]:
    return [path] if path.is_file() else sorted(path.rglob("*.nc"))


def ingest_file(engine, path: Path) -> tuple[int, int, int, list[str]]:
    payload = type("Upload", (), {"name": path.name, "getvalue": lambda self: path.read_bytes()})()
    measurements, metadata = parse_netcdf_file(payload)
    if measurements.empty:
        return 0, 0, 0, metadata["warnings"]
    measurements["source_file"] = path.name
    profiles = measurements[["profile_id", "float_id", "timestamp", "latitude", "longitude"]].drop_duplicates("profile_id")
    floats = profiles.groupby("float_id", as_index=False).agg(latitude=("latitude", "first"), longitude=("longitude", "first"))
    floats["status"] = "ACTIVE"
    floats["max_depth"] = measurements.groupby("float_id")["depth"].max().reindex(floats["float_id"]).to_numpy()
    floats["region"] = "Indian Ocean"
    floats["source_file"] = path.name
    with engine.begin() as connection:
        for row in floats.itertuples(index=False):
            connection.execute(text("""INSERT INTO floats (float_id, latitude, longitude, status, max_depth, region, source_file, geom) VALUES (:id, :lat, :lon, :status, :depth, :region, :source, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) ON CONFLICT (float_id) DO UPDATE SET latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude, max_depth=EXCLUDED.max_depth, source_file=EXCLUDED.source_file"""), {"id": int(row.float_id), "lat": float(row.latitude), "lon": float(row.longitude), "status": row.status, "depth": float(row.max_depth), "region": row.region, "source": row.source_file})
        for row in profiles.itertuples(index=False):
            connection.execute(text("""INSERT INTO profiles (profile_id, float_id, timestamp, latitude, longitude, source_file, geom) VALUES (:profile, :float, :timestamp, :lat, :lon, :source, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) ON CONFLICT (profile_id) DO NOTHING"""), {"profile": row.profile_id, "float": int(row.float_id), "timestamp": row.timestamp, "lat": float(row.latitude), "lon": float(row.longitude), "source": path.name})
        allowed = ["profile_id", "depth", "pressure", "temperature", "salinity", "oxygen", "chlorophyll", "bbp700", "nitrate", "ph"]
        columns = ", ".join(allowed)
        binds = ", ".join(f":{column}" for column in allowed)
        for row in measurements[allowed].itertuples(index=False, name=None):
            connection.execute(text(f"INSERT INTO measurements ({columns}) VALUES ({binds})"), dict(zip(allowed, row)))
    return len(floats), len(profiles), len(measurements), metadata["warnings"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest ARGO NetCDF files into FloatChat PostgreSQL/PostGIS tables")
    parser.add_argument("path", type=Path, help="An .nc file or directory containing .nc files")
    args = parser.parse_args()
    engine = get_db_engine()
    if engine is None:
        raise SystemExit("Could not create a PostgreSQL engine. Check your .env settings.")
    files = discover_files(args.path)
    totals = [0, 0, 0]
    failed = 0
    for path in files:
        try:
            counts = ingest_file(engine, path)
            totals = [left + right for left, right in zip(totals, counts[:3])]
            print(f"{path.name}: {counts[0]} floats, {counts[1]} profiles, {counts[2]} measurements")
            if counts[3]:
                print("  warnings:", "; ".join(counts[3]))
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")
    print(f"\nARGO ingestion complete\nFiles processed: {len(files)}\nFloats: {totals[0]}\nProfiles: {totals[1]}\nMeasurements: {totals[2]}\nFailed files: {failed}")


if __name__ == "__main__":
    main()
