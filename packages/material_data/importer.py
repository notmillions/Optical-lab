"""Retrieve a pinned refractiveindex.info snapshot and import selected YAML records.

The source is CC0; the snapshot commit, file path and SHA256 remain in SQLite.
Only the selected pilot records are fetched by default. No runtime network
access is needed after importing.
"""

from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from hashlib import sha1
from pathlib import Path

from packages.material_data.parser import parse_dataset
from packages.material_data.store import import_datasets

REPOSITORY = "https://github.com/polyanskiy/refractiveindex.info-database"
SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"
PINNED_GIT_BLOBS = {
    "database/data/main/Cu/nk/Johnson.yml": "209fcb1cb6c07a817639c5effad9dc7598a857ba",
    "database/data/main/Al/nk/Rakic.yml": "9c3df1ed997a058969d4f5efde7a42d19e8cbb41",
    "database/data/main/SiO2/nk/Malitson.yml": "ba642520422d831d0ad13356596c64dcfd7770a2",
    "database/data/main/SiO2/nk/Gao.yml": "4853fe87aa9da46dbadd677745cc2f106f32f5dd",
}
PILOT_PATHS = (
    "database/data/main/Cu/nk/Johnson.yml",
    "database/data/main/Al/nk/Rakic.yml",
    "database/data/main/SiO2/nk/Malitson.yml",
    "database/data/main/SiO2/nk/Gao.yml",
)


def verify_blob(relative_path: str, data: bytes) -> None:
    """Detect changed or corrupted content, even when loading an offline cache."""
    expected = PINNED_GIT_BLOBS.get(relative_path)
    if expected is None:
        raise ValueError(f"No trusted source blob for {relative_path}")
    blob = b"blob " + str(len(data)).encode("ascii") + bytes([0]) + data
    actual = sha1(blob).hexdigest()  # Git blob SHA-1, not a security signature
    if actual != expected:
        raise ValueError(f"Source checksum mismatch for {relative_path}")


def fetch_pinned(relative_path: str, *, snapshot: str = SNAPSHOT) -> bytes:
    if relative_path not in PILOT_PATHS:
        raise ValueError(f"Unapproved pilot source path: {relative_path}")
    url = (
        "https://raw.githubusercontent.com/polyanskiy/"
        f"refractiveindex.info-database/{snapshot}/{relative_path}"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "OpticalLab-educational-material-import/0.1"}
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(5_000_001)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Cannot retrieve source file {relative_path}: {exc}") from exc
    if len(data) > 5_000_000:
        raise ValueError("Unexpectedly large source file")
    return data


def import_pilots(
    database: str | Path,
    *,
    cache_dir: str | Path | None = None,
    offline: bool = False,
) -> int:
    records = []
    for source_path in PILOT_PATHS:
        cache_file = Path(cache_dir) / source_path if cache_dir else None
        if offline:
            if cache_file is None:
                raise ValueError("--offline requires --cache-dir")
            data = cache_file.read_bytes()
        else:
            data = fetch_pinned(source_path)
            if cache_file is not None:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_bytes(data)
        verify_blob(source_path, data)
        records.append(parse_dataset(source_path, data, SNAPSHOT))
    return import_datasets(database, records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import pinned refractiveindex.info pilot data")
    parser.add_argument("--db", default="data/processed/optical-lab.sqlite")
    parser.add_argument("--cache-dir", default="data/raw/refractiveindex-info")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    count = import_pilots(args.db, cache_dir=args.cache_dir, offline=args.offline)
    print(f"Imported {count} independent optical datasets into {args.db}")


if __name__ == "__main__":
    main()
