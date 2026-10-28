#!/usr/bin/env python3
"""Check the Parquet against the CSVs read a second way (DuckDB all-varchar), then the
cross-file facts that the upstream README states.  uv run --with duckdb python scripts/03_verify.py"""

import json
import re
from pathlib import Path

import duckdb
import fcm
import pyarrow.parquet as pq

ROOT = Path(__file__).parents[1]


def main() -> None:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    pdir = ROOT / "data" / "parquet"
    con = duckdb.connect()
    tabs = {}
    for csv_name, table in fcm.FILES.items():
        t = pq.read_table(pdir / f"{table}.parquet")
        tabs[table] = t.to_pylist()
        raw = con.execute(
            "select * from read_csv(?, header=true, all_varchar=true, nullstr='NA', encoding='utf-8')",
            [str(run / "csv" / csv_name)],
        )
        names = [d[0].lstrip("﻿") for d in raw.description]
        rows = raw.fetchall()
        assert names == t.column_names, (csv_name, names[:3], t.column_names[:3])
        assert len(rows) == t.num_rows, (csv_name, len(rows), t.num_rows)
        for i, (r, p) in enumerate(zip(rows, tabs[table], strict=True)):
            for c, cell in zip(names, r, strict=True):
                v = p[c]
                ok = (
                    (v is None)
                    if cell is None
                    else (v == cell if fcm.kind(c) == "text" else float(v) == float(cell))
                )
                assert ok, (csv_name, i, c, cell, v)
        nulls = sum(v is None for p in tabs[table] for v in p.values())
        print(f"{table}: {t.num_rows} rows equal to the CSV; {nulls} nulls")
    sites, rank, kan, est = (
        tabs[k]
        for k in ("study_sites", "seed_rank_and_cues", "kanumazawa_traps", "model_estimates")
    )
    ids = {r["ID"] for r in sites}
    assert ids == set(range(1, 103)) and len(sites) == 102, "102 sites with ids 1..102"
    for name, rows in (("seed_rank_and_cues", rank), ("model_estimates", est)):
        assert {r["ID"] for r in rows} == ids, name
    names = {r["ID"]: (r["Site name"], r["Site name in Japanese"]) for r in sites}
    for rows in (rank, est):
        assert all(names[r["ID"]] == (r["Site name"], r["Site name in Japanese"]) for r in rows)
    assert all(len({r["ID"] for r in rows}) == 102 for rows in (rank,)), "one row per site"
    ranks = {v for r in rank for k, v in r.items() if k.startswith("Obs.seed.rnk.")} - {None}
    # The upstream README defines 0-3 and NA only; -1 is also present (documented in the card).
    assert ranks == {-1, 0, 1, 2, 3}, ranks
    minus = [
        (r["ID"], k[-4:])
        for r in rank
        for k, v in r.items()
        if k.startswith("Obs.seed.rnk.") and v == -1
    ]
    assert len(minus) == 61 and {y for _, y in minus} == {"1999", "2004"}, (
        len(minus),
        {y for _, y in minus},
    )
    assert all(names[i][0] and sites[i - 1]["Location"].startswith("Tohoku") for i, _ in minus)
    assert {r["Obs.seed.rnk"] for r in kan} <= {0, 1, 2, 3}
    assert sorted(r["Year"] for r in kan) == list(range(1990, 2009))
    assert sum(r["Location"].startswith("Oshima") for r in sites) == 4
    lat = [r["Latitude"] for r in sites]
    lon = [r["Longitude"] for r in sites]
    assert min(lat) > 36 and max(lat) < 43 and min(lon) > 138 and max(lon) < 142, (
        min(lat),
        max(lat),
        min(lon),
        max(lon),
    )
    pat = re.compile(
        r"^([PFS]\.\d{4}|alpha\.(const|HSM|LSP)|beta\.(EIP|RPF|SR)|gamma\.(BFMS|FPBF))$"
    )
    bad = {r["Parameter"] for r in est if not pat.match(r["Parameter"])}
    assert not bad, bad
    for r in est:
        if r["Parameter"][0] in "PFS" and r["Parameter"][1] == ".":
            assert 0 <= r["Mean"] <= 1, r
    assert len({(r["ID"], r["Parameter"]) for r in est}) == len(est), "duplicate (site, parameter)"
    per_site = {}
    for r in est:
        per_site.setdefault(r["ID"], set()).add(r["Parameter"])
    print("parameters per site:", sorted({len(v) for v in per_site.values()}))
    info = json.loads((pdir / "tables.json").read_text())
    print("OK", {k: v["rows"] for k, v in info["tables"].items()})


if __name__ == "__main__":
    main()
