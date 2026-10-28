#!/usr/bin/env python3
"""Write data/README.md (the dataset card), data/LICENSE and data/provenance.yaml.  uv run python scripts/04_card.py"""

import json
from pathlib import Path

import fcm

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"

CARD = """---
license: cc0-1.0
language:
- en
- ja
tags:
- ecology
- forestry
- japan
- masting
- fagus-crenata
- phenology
size_categories:
- 1K<n<10K
configs:
- config_name: study_sites
  data_files: parquet/study_sites.parquet
- config_name: seed_rank_and_cues
  data_files: parquet/seed_rank_and_cues.parquet
- config_name: kanumazawa_traps
  data_files: parquet/kanumazawa_traps.parquet
- config_name: model_estimates
  data_files: parquet/model_estimates.parquet
---

# Fagus crenata seed production at 102 sites in northern Japan (Dryad, v{run})

ブナ(Fagus crenata)の種子生産の調査データ(東北 98 地点と北海道渡島半島 4 地点、1989〜2008 年)の凍結コピーです。

A frozen copy of the Dryad dataset "{title}" by Takashi Masaki et al.
DOI: [{doi}]({page}). Version {version} of {date}. Licence: CC0 1.0 (the Dryad record's licence field).
Nothing was changed in the values; the Parquet files are the four CSVs with `NA` turned into null.

## Contents

| config / Parquet | upstream CSV | rows | what it holds |
| --- | --- | ---: | --- |
{table_rows}

The original zip, the four CSVs and the upstream README are under `raw/{run}/` (the CSVs are inside the zip,
unchanged, with their UTF-8 byte order mark). `raw/{run}/dataset.json` is the Dryad metadata
(the authors' e-mail addresses are removed). Column meanings, the seeding rank key, the weather cues and the
model parameters are described in the upstream README, inside the zip.

## Things to know

- Seed rank has the value -1 in 61 cells of `seed_rank_and_cues`: 54 in 1999 (sites ID 49 to 102, all in the
  Tohoku region) and 7 in 2004 (IDs 5 to 10 and 16). The upstream README defines ranks 0 to 3 and NA only, so
  what -1 means is not stated there. It is kept as published. Do not read it as a rank.
- Missing values: 60 `NA` in the rank columns (1989 to 1993 and 2004 to 2008), which are null here.
- `model_estimates` is long form, one row per site and parameter: 44 to 68 parameters per site (latent variables
  P, F, S per year plus eight process parameters), not the same set for every site.
- `T.HSM` and `T.LSP` in `seed_rank_and_cues` are standardised cues (mean 0, SD 1). In `kanumazawa_traps` they are
  not: T.HSM runs 0 to 180.7 (mean 58.7) and T.LSP -95.3 to -0.3 (mean -35.9), which looks like the original
  degree-day scale with T.LSP still negative, although the upstream column table says they are standardised.
  The values are kept as published.
- The climate averages of the 102 sites (WorldClim-derived) are a separate record on Zenodo
  (10.5281/zenodo.20550356, CC BY 4.0). They are not in this repository.

## Verification

`scripts/03_verify.py` reads each CSV a second way (DuckDB, all text) and compares every cell with the Parquet
(102, 102, 19 and 6,747 rows, no difference). It also checks that the 102 site IDs and names agree across the
files, rank values, the years 1990 to 2008 in the trap table, that every P, F, S mean lies in 0 to 1, that
no (site, parameter) pair repeats, and that the -1 cells are the 61 described above.
The zip was downloaded by hand in a browser (Dryad refuses anonymous scripts for files: 401 for the API,
403 for the site) and every member matches the sha256 the Dryad API lists (`raw/{run}/MANIFEST.json`).

## Citation

The authors ask for citation of the Dryad record and the paper:

- Masaki T., et al. Data on seed production from 102 Fagus crenata sites in northern Japan and process model
  parameters for predicting annual variation. Dryad. https://doi.org/{doi}
- Masaki T., Hoshizaki K., Homma C. (2025) Disentangling the effects of geographical location and local climate
  on masting in Fagus crenata using a comprehensive population model. Basic and Applied Ecology.
  https://doi.org/10.1016/j.baae.2025.05.004

The Tohoku seeding ranks were assessed by the Tohoku Regional Forest Office, Forest Agency; the weather cues
are derived from Japan Meteorological Agency stations (see the upstream README).

Collection code: https://github.com/yuiseki/fagus-crenata-masting-jp-2026-06
"""


def main() -> None:
    run = sorted((DATA / "raw").glob("*/MANIFEST.json"))[-1].parent
    meta = json.loads((run / "dataset.json").read_text())
    info = json.loads((DATA / "parquet" / "tables.json").read_text())
    what = {
        "study_sites": "id, region, names (Roman and Japanese), latitude, longitude (WGS84), altitude of the sites",
        "seed_rank_and_cues": "seeding rank 1989 to 2008 and two weather cues per year, per site (wide)",
        "kanumazawa_traps": "seed-trap counts at Kanumazawa, 1990 to 2008",
        "model_estimates": "posterior summaries of latent variables and process parameters (long)",
    }
    rows = "\n".join(
        f"| `{t}` | `{v['source']}` | {v['rows']:,} | {what[t]} |"
        for t, v in info["tables"].items()
    )
    card = CARD.format(run=run.name, title=meta["title"].replace("<em>", "").replace("</em>", ""),
                       doi=fcm.DOI, page=fcm.PAGE_URL, version=meta["versionNumber"],
                       date=meta["publicationDate"], table_rows=rows)  # fmt: skip
    (DATA / "README.md").write_text(card, encoding="utf-8")
    (DATA / "LICENSE").write_text(
        "CC0 1.0 Universal (https://creativecommons.org/publicdomain/zero/1.0/legalcode)\n\n"
        f"The data are the Dryad dataset doi:{fcm.DOI}, whose licence field is {fcm.LICENSE_URL}.\n"
    )
    (DATA / "provenance.yaml").write_text(
        f"source: Dryad doi:{fcm.DOI}\nurl: {fcm.PAGE_URL}\nlicense: CC0 1.0\n"
        f"version: {meta['versionNumber']}\npublicationDate: {meta['publicationDate']}\n"
        f"acquired: manual browser download of the zip, verified against the Dryad API sha256\n"
    )
    print("wrote card, LICENSE, provenance.yaml")


if __name__ == "__main__":
    main()
