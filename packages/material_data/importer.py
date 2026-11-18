"""Import a pinned refractiveindex.info snapshot without inventing constants.

The source is CC0; the snapshot commit, file path and SHA256 remain in SQLite.
The catalog importer consumes an already extracted local tree. Network access
is only retained for the backwards-compatible four-file pilot command. Every
YAML file is inspected independently and unsupported sections are recorded in
the source manifest instead of being guessed or silently discarded.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from hashlib import sha1, sha256
from pathlib import Path
from typing import Any

from packages.material_data.parser import (
    DataFormatError,
    SourceInspection,
    inspect_source,
    parse_dataset,
)
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


@dataclass(frozen=True)
class CatalogCoverage:
    """Deterministic coverage metrics for one extracted source tree."""

    source_root: str
    snapshot: str
    records: tuple[SourceInspection, ...]

    @property
    def discovered_files(self) -> int:
        return len(self.records)

    @property
    def importable_datasets(self) -> int:
        return sum(item.dataset is not None for item in self.records)

    @property
    def fully_supported_datasets(self) -> int:
        return sum(item.status == "imported" for item in self.records)

    @property
    def partially_imported_datasets(self) -> int:
        return sum(item.status == "partial" for item in self.records)

    @property
    def unsupported_files(self) -> int:
        return sum(item.status == "unsupported" for item in self.records)

    @property
    def invalid_files(self) -> int:
        return sum(item.status == "invalid" for item in self.records)

    @property
    def supported_sections(self) -> int:
        return sum(len(item.dataset.sections) for item in self.records if item.dataset is not None)

    @property
    def unsupported_sections(self) -> int:
        return sum(len(item.unsupported_sections) for item in self.records)

    def as_dict(self) -> dict[str, Any]:
        discovered = self.discovered_files
        return {
            "source_root": self.source_root,
            "snapshot": self.snapshot,
            "pattern": "database/data/main/**/nk/*.yml",
            "discovered_files": discovered,
            "importable_datasets": self.importable_datasets,
            "fully_supported_datasets": self.fully_supported_datasets,
            "partially_imported_datasets": self.partially_imported_datasets,
            "unsupported_files": self.unsupported_files,
            "invalid_files": self.invalid_files,
            "supported_sections": self.supported_sections,
            "unsupported_sections": self.unsupported_sections,
            "file_coverage_fraction": (
                self.importable_datasets / discovered if discovered else 0.0
            ),
            "full_support_fraction": (
                self.fully_supported_datasets / discovered if discovered else 0.0
            ),
            "records": [
                {
                    "source_path": item.source_path,
                    "source_sha256": item.source_sha256,
                    "status": item.status,
                    "dataset_id": item.dataset.id if item.dataset is not None else None,
                    "unsupported_sections": [
                        {
                            "ordinal": section.ordinal,
                            "source_type": section.source_type,
                            "reason": section.reason,
                        }
                        for section in item.unsupported_sections
                    ],
                    "error": item.error,
                }
                for item in self.records
            ],
        }


def _invalid_inspection(
    source_path: str, content: bytes, error: str, snapshot: str
) -> SourceInspection:
    return SourceInspection(
        source_path=source_path,
        source_sha256=sha256(content).hexdigest(),
        source_commit=snapshot,
        status="invalid",
        error=error,
    )


def scan_catalog(source_root: str | Path, *, snapshot: str = SNAPSHOT) -> CatalogCoverage:
    """Scan every local ``database/data/main/**/nk/*.yml`` independently."""
    root = Path(source_root).resolve()
    paths = sorted(
        path for path in root.glob("database/data/main/**/nk/*.yml") if path.is_file()
    )
    inspections: list[SourceInspection] = []
    for path in paths:
        source_path = path.relative_to(root).as_posix()
        content = path.read_bytes()
        try:
            inspections.append(inspect_source(source_path, content, snapshot))
        except (DataFormatError, UnicodeError, OSError) as exc:
            inspections.append(_invalid_inspection(source_path, content, str(exc), snapshot))
    return CatalogCoverage(str(root), snapshot, tuple(inspections))


def import_catalog(
    database: str | Path,
    source_root: str | Path,
    *,
    snapshot: str = SNAPSHOT,
    report_path: str | Path | None = None,
) -> CatalogCoverage:
    """Import all safely parsed records and persist the complete source manifest."""
    report = scan_catalog(source_root, snapshot=snapshot)
    records = [item.dataset for item in report.records if item.dataset is not None]
    import_datasets(database, records, source_records=list(report.records))
    if report_path is not None:
        write_coverage_report(report, report_path)
    return report


def write_coverage_report(report: CatalogCoverage, destination: str | Path) -> None:
    """Write JSON or Markdown coverage output, including every source outcome."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = report.as_dict()
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    lines = [
        "# RefractiveIndex.INFO catalog coverage",
        "",
        f"- Snapshot: `{report.snapshot}`",
        f"- Source root: `{report.source_root}`",
        f"- Pattern: `{data['pattern']}`",
        f"- Discovered YAML files: **{report.discovered_files}**",
        f"- Importable datasets: **{report.importable_datasets}**",
        f"- Fully supported datasets: **{report.fully_supported_datasets}**",
        f"- Partially imported datasets: **{report.partially_imported_datasets}**",
        f"- Unsupported files: **{report.unsupported_files}**",
        f"- Invalid files: **{report.invalid_files}**",
        f"- Supported sections: **{report.supported_sections}**",
        f"- Unsupported sections: **{report.unsupported_sections}**",
        f"- File coverage: **{data['file_coverage_fraction']:.2%}**",
        "",
        "| Status | Source | Dataset | Details |",
        "|---|---|---|---|",
    ]
    for item in report.records:
        details = item.error or "; ".join(
            f"DATA {section.ordinal}: {section.source_type or 'unknown'} — {section.reason}"
            for section in item.unsupported_sections
        )
        details = details.replace("|", "\\|") or "—"
        lines.append(
            f"| {item.status} | `{item.source_path}` | "
            f"`{item.dataset.id if item.dataset is not None else '—'}` | {details} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    parser = argparse.ArgumentParser(description="Import pinned refractiveindex.info data")
    parser.add_argument("--db", default="data/processed/optical-lab.sqlite")
    parser.add_argument("--cache-dir", default="data/raw/refractiveindex-info")
    parser.add_argument(
        "--source-root",
        help="Extracted repository root containing database/data/main/**/nk/*.yml",
    )
    parser.add_argument(
        "--coverage-report",
        help="Write catalog coverage as .json or Markdown (any other suffix)",
    )
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.source_root:
        report = import_catalog(
            args.db,
            args.source_root,
            report_path=args.coverage_report,
        )
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        count = import_pilots(args.db, cache_dir=args.cache_dir, offline=args.offline)
        print(f"Imported {count} independent optical datasets into {args.db}")


if __name__ == "__main__":
    main()
