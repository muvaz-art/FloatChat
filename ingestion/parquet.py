from pathlib import Path

import pandas as pd


def write_parquet_tables(tables: dict[str, pd.DataFrame], output_dir: str | Path) -> dict[str, str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, frame in tables.items():
        path = destination / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = str(path)
    return paths


def read_parquet_tables(input_dir: str | Path) -> dict[str, pd.DataFrame]:
    source = Path(input_dir)
    return {path.stem: pd.read_parquet(path) for path in source.glob("*.parquet")}
