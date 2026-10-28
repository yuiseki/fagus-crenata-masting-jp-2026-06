#!/usr/bin/env python3
"""Write one Parquet per CSV, columns unchanged (NA becomes null).  uv run python scripts/02_export_parquet.py"""

import json
from pathlib import Path

import fcm
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).parents[1]
PA = {"int": pa.int64(), "text": pa.string(), "float": pa.float64()}


def main() -> None:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    out = ROOT / "data" / "parquet"
    out.mkdir(parents=True, exist_ok=True)
    info = {"run": run.name, "tables": {}}
    for csv_name, table in fcm.FILES.items():
        header, body = fcm.read_csv(run / "csv" / csv_name)
        cols = {c: [fcm.value(c, r[i]) for r in body] for i, c in enumerate(header)}
        schema = pa.schema([(c, PA[fcm.kind(c)]) for c in header])
        pq.write_table(pa.table(cols, schema=schema), out / f"{table}.parquet", compression="zstd")
        info["tables"][table] = {"source": csv_name, "rows": len(body), "columns": len(header)}
        print(f"{table}: {len(body)} rows, {len(header)} columns")
    (out / "tables.json").write_text(json.dumps(info, indent=1) + "\n")


if __name__ == "__main__":
    main()
