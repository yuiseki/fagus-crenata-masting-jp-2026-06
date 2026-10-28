"""Shared constants and the CSV reader for the Fagus crenata masting dataset."""

import csv
from pathlib import Path

DOI = "10.5061/dryad.7sqv9s54n"
API = "https://datadryad.org/api/v2"
DATASET_URL = f"{API}/datasets/doi%3A10.5061%2Fdryad.7sqv9s54n"
PAGE_URL = "https://datadryad.org/dataset/doi%3A10.5061/dryad.7sqv9s54n"
LICENSE_URL = "https://spdx.org/licenses/CC0-1.0.html"
UA = "Mozilla/5.0 (research; yuiseki)"

FILES = {
    "List_of_study_sites.csv": "study_sites",
    "Data_used_in_this_study.csv": "seed_rank_and_cues",
    "Observations_at_Kanumazawa.csv": "kanumazawa_traps",
    "Model_estimates.csv": "model_estimates",
}
INT_COLUMNS = {"ID", "Altitude", "Year", "Obs.seed.rnk"}
TEXT_COLUMNS = {"Location", "Site name", "Site name in Japanese", "Parameter"}


def kind(column: str) -> str:
    """Column type in Parquet: 'int', 'text' or 'float'. Per-year columns follow their prefix."""
    if column in TEXT_COLUMNS:
        return "text"
    if column in INT_COLUMNS or column.startswith("Obs.seed.rnk."):
        return "int"
    return "float"


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    if any(len(r) != len(header) for r in body):
        raise SystemExit(f"{path.name}: ragged rows")
    return header, body


def value(column: str, cell: str):
    """NA is the upstream missing marker (its README); anything else must parse."""
    if cell == "NA":
        return None
    k = kind(column)
    if k == "text":
        return cell
    return int(cell) if k == "int" else float(cell)
