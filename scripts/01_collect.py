#!/usr/bin/env python3
"""Record the Dryad metadata, check the zip you downloaded against it, and unpack the CSVs.

Dryad answers anonymous scripts with 401 (API) or 403 (site) for the files, so the zip is
downloaded by hand in a browser ("Download dataset" on PAGE_URL) and given here:

    uv run python scripts/01_collect.py data/incoming/doi_10_5061_dryad_7sqv9s54n__v20260605.zip

The metadata calls are open. The author e-mail addresses in them are not kept.
"""

import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import fcm

ROOT = Path(__file__).parents[1]


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": fcm.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def strip_email(o):
    if isinstance(o, dict):
        return {k: strip_email(v) for k, v in o.items() if k != "email"}
    if isinstance(o, list):
        return [strip_email(v) for v in o]
    return o


def main() -> int:
    zpath = Path(sys.argv[1])
    meta = get_json(fcm.DATASET_URL)
    if meta["license"] != fcm.LICENSE_URL:
        raise SystemExit(f"the licence changed: {meta['license']}")
    version = get_json(fcm.API + meta["_links"]["stash:version"]["href"].removeprefix("/api/v2"))
    files = get_json(fcm.API + version["_links"]["stash:files"]["href"].removeprefix("/api/v2"))
    listed = {f["path"]: f for f in files["_embedded"]["stash:files"]}
    run = meta["publicationDate"].replace("-", "")
    if run not in zpath.name:
        raise SystemExit(f"{zpath.name} is not the {run} version that the API reports")
    out = ROOT / "data" / "raw" / run
    (out / "csv").mkdir(parents=True, exist_ok=True)
    shutil.copy2(zpath, out / zpath.name)
    manifest = {"doi": fcm.DOI, "publicationDate": meta["publicationDate"],
                "versionNumber": meta["versionNumber"], "zip": zpath.name,
                "zip_sha256": hashlib.sha256(zpath.read_bytes()).hexdigest(), "files": {}}  # fmt: skip
    with zipfile.ZipFile(zpath) as z:
        names = {i.filename for i in z.infolist()}
        if names != set(listed):
            raise SystemExit(f"zip members differ from the API list: {names ^ set(listed)}")
        for name, f in listed.items():
            b = z.read(name)
            sha = hashlib.sha256(b).hexdigest()
            if sha != f["digest"] or len(b) != f["size"]:
                raise SystemExit(f"{name} differs from the digest the API lists")
            (out / "csv" / name).write_bytes(b)
            manifest["files"][name] = {"sha256": sha, "size": len(b)}
    (out / "dataset.json").write_text(
        json.dumps(strip_email(meta), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{run}: {len(listed)} files match the API digests; wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
