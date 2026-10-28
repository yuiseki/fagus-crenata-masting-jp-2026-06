#!/usr/bin/env python3
"""Push the card, licence, provenance, Parquet and the original zip to the Hub.

uv run python src/publish.py             # dry run
uv run python src/publish.py --push
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/fagus-crenata-masting-jp-2026-06"
DELETE_PATTERNS = ["raw/**", "parquet/**"]


def collect(data: Path) -> list[str]:
    card = (data / "README.md").read_text(encoding="utf-8")
    if "license: cc0-1.0" not in card:
        raise SystemExit("the card does not declare license: cc0-1.0")
    d = sorted((data / "raw").glob("*/MANIFEST.json"))[-1].parent
    m = json.loads((d / "MANIFEST.json").read_text())
    if f"raw/{d.name}/" not in card:
        raise SystemExit("the card does not name the current run")
    if hashlib.sha256((d / m["zip"]).read_bytes()).hexdigest() != m["zip_sha256"]:
        raise SystemExit("the zip is not the file in its manifest")
    info = json.loads((data / "parquet" / "tables.json").read_text())
    for t in info["tables"].values():
        if f"{t['rows']:,}" not in card:
            raise SystemExit(f"the card does not give {t['rows']:,} rows")
    files = ["README.md", "LICENSE", "provenance.yaml", f"raw/{d.name}/MANIFEST.json",
             f"raw/{d.name}/dataset.json", f"raw/{d.name}/{m['zip']}", "parquet/tables.json"]  # fmt: skip
    files += [f"parquet/{t}.parquet" for t in info["tables"]]
    missing = [f for f in files if not (data / f).is_file()]
    if missing:
        raise SystemExit(f"missing: {missing}")
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    files = collect(DATA)
    total = sum((DATA / f).stat().st_size for f in files)
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(folder_path=str(DATA), repo_id=a.repo, repo_type="dataset",
                      allow_patterns=files, delete_patterns=DELETE_PATTERNS)  # fmt: skip
    print(f"pushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
